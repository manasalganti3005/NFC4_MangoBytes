from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
import numpy as np

load_dotenv()

# Initialize Embedding Model & DB Connection
model = SentenceTransformer("all-MiniLM-L6-v2")

# MongoDB setup using env vars
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def get_similar_chunks(query, document_ids, top_k=3):
    try:
        print(f"Searching for documents: {document_ids}")
        query_embedding = model.encode(query).tolist()

        # First, get all documents that match the document_ids
        matching_docs = list(collection.find({"document_id": {"$in": document_ids}}))
        
        print(f"Found {len(matching_docs)} matching documents")
        
        if not matching_docs:
            return []
        
        # Flatten all chunks from matching documents
        all_chunks = []
        total_chunks = 0
        for doc in matching_docs:
            if 'chunks' in doc:
                total_chunks += len(doc['chunks'])
                for chunk in doc['chunks']:
                    all_chunks.append({
                        'text': chunk.get('text', ''),
                        'embedding': chunk.get('embedding', []),
                        'filename': doc.get('filename', 'Unknown'),
                        'document_id': doc.get('document_id', 'Unknown')
                    })
        
        print(f"Found {total_chunks} total chunks, {len(all_chunks)} with embeddings")
        
        if not all_chunks:
            return []
        
        # Calculate similarities manually since we can't use $vectorSearch with filtering
        similarities = []
        for chunk in all_chunks:
            if chunk['embedding']:
                try:
                    chunk_emb = np.array(chunk['embedding'])
                    query_emb = np.array(query_embedding)
                    
                    # Normalize vectors
                    chunk_norm = np.linalg.norm(chunk_emb)
                    query_norm = np.linalg.norm(query_emb)
                    
                    if chunk_norm > 0 and query_norm > 0:
                        similarity = np.dot(chunk_emb, query_emb) / (chunk_norm * query_norm)
                        similarities.append((similarity, chunk))
                except Exception as e:
                    print(f"Error calculating similarity for chunk: {str(e)}")
                    continue
        
        # Sort by similarity and get top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_chunks = similarities[:top_k]
        
        # Format results to match expected structure
        results = []
        for similarity, chunk in top_chunks:
            results.append({
                'chunk': chunk['text'],
                'filename': chunk['filename'],
                'document_id': chunk['document_id'],
                'similarity': float(similarity)
            })
        
        return results
        
    except Exception as e:
        print(f"Error in get_similar_chunks: {str(e)}")
        # Fallback: return first few chunks from documents
        return get_fallback_chunks(document_ids, top_k)

def get_fallback_chunks(document_ids, top_k=3):
    """Fallback method when vector search fails - returns first few chunks"""
    try:
        matching_docs = list(collection.find({"document_id": {"$in": document_ids}}))
        
        if not matching_docs:
            return []
        
        all_chunks = []
        for doc in matching_docs:
            if 'chunks' in doc:
                for chunk in doc['chunks'][:2]:  # Take first 2 chunks from each doc
                    all_chunks.append({
                        'chunk': chunk.get('text', ''),
                        'filename': doc.get('filename', 'Unknown'),
                        'document_id': doc.get('document_id', 'Unknown'),
                        'similarity': 0.0
                    })
        
        return all_chunks[:top_k]
        
    except Exception as e:
        print(f"Error in fallback chunks: {str(e)}")
        return []

def handle_rag_query(user_query, document_ids, with_trace=False):
    try:
        results = get_similar_chunks(user_query, document_ids)
        
        if not results:
            return {
                "answer": f"I couldn't find any relevant information in the uploaded documents to answer: '{user_query}'. Please try rephrasing your question or ask about a different topic."
            }
        
        context = "\n\n".join([r["chunk"] for r in results])

        prompt = f"""Answer the question based on the context below.

Context:
{context}

Question:
{user_query}

Answer:"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi3", "prompt": prompt, "stream": False},
                timeout=45  # 45 second timeout for RAG queries
            )
            
            if response.status_code == 200:
                answer = response.json().get('response', 'No response generated')
                
                if with_trace:
                    sources = ", ".join([r["filename"] for r in results])
                    return {
                        "answer": answer,
                        "sources": sources
                    }
                else:
                    return {
                        "answer": answer
                    }
            else:
                print(f"❌ Ollama returned status {response.status_code}, using simple fallback...")
                from utils.simple_rag import handle_simple_rag_query
                return handle_simple_rag_query(user_query, document_ids)
                
        except requests.exceptions.Timeout:
            print("⏰ Ollama timeout, using simple fallback...")
            from utils.simple_rag import handle_simple_rag_query
            return handle_simple_rag_query(user_query, document_ids)
        except requests.exceptions.ConnectionError:
            print("🔌 Ollama connection error, using simple fallback...")
            from utils.simple_rag import handle_simple_rag_query
            return handle_simple_rag_query(user_query, document_ids)
        except Exception as e:
            print(f"❌ Ollama API error: {str(e)}, using simple fallback...")
            from utils.simple_rag import handle_simple_rag_query
            return handle_simple_rag_query(user_query, document_ids)
            
    except Exception as e:
        print(f"RAG query error: {str(e)}")
        return {
            "answer": f"I encountered an error while processing your request: {str(e)}. Please try again."
        }
