from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
import numpy as np
from .groq_api import groq_generate, test_groq_connection

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
        print(f"🔎 Searching for documents: {document_ids}")
        query_embedding = model.encode(query).tolist()

        # Get all documents matching the given document_ids
        matching_docs = list(collection.find({"document_id": {"$in": document_ids}}))
        print(f"📄 Found {len(matching_docs)} matching documents")

        if not matching_docs:
            return []

        # 🔧 Set more realistic thresholds for similarity filtering
        query_words = len(query.split())
        if query_words < 5:
            similarity_threshold = 0.65  # Higher for short queries
        elif query_words < 10:
            similarity_threshold = 0.6   # Medium
        else:
            similarity_threshold = 0.55  # Lower for longer queries

        print(f"🎯 Using similarity threshold: {similarity_threshold:.2f} (query length: {query_words} words)")

        # Collect all chunks
        all_chunks = []
        for doc in matching_docs:
            if 'chunks' in doc:
                for chunk in doc['chunks']:
                    all_chunks.append({
                        'text': chunk.get('text', ''),
                        'embedding': chunk.get('embedding', []),
                        'filename': doc.get('filename', 'Unknown'),
                        'document_id': doc.get('document_id', 'Unknown')
                    })

        print(f"📦 Total chunks collected: {len(all_chunks)}")

        # Calculate cosine similarity manually
        similarities = []
        query_emb = np.array(query_embedding)

        for chunk in all_chunks:
            if chunk['embedding']:
                try:
                    chunk_emb = np.array(chunk['embedding'])
                    sim = np.dot(chunk_emb, query_emb) / (np.linalg.norm(chunk_emb) * np.linalg.norm(query_emb))
                    
                    if sim > similarity_threshold:
                        similarities.append((sim, chunk))
                except Exception as e:
                    print(f"⚠️ Error calculating similarity: {e}")
                    continue

        print(f"✅ Chunks passing threshold ({similarity_threshold}): {len(similarities)}")

        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_chunks = similarities[:top_k]

        # Fallback if none pass threshold
        if not top_chunks and len(similarities) > 0:
            print("⚠️ No chunks met the initial threshold, trying with lower threshold...")
            lower_threshold = similarity_threshold * 0.95
            top_chunks = [(sim, chunk) for sim, chunk in similarities if sim > lower_threshold][:top_k]
            print(f"🔍 Found {len(top_chunks)} chunks with relaxed threshold ({lower_threshold:.2f})")

        # Log selected chunk similarities
        for i, (sim, chunk) in enumerate(top_chunks):
            print(f"{i+1}. Similarity: {sim:.3f} - Text preview: {chunk['text'][:50]}...")

        # Return results in expected format
        results = [{
            'chunk': chunk['text'],
            'filename': chunk['filename'],
            'document_id': chunk['document_id'],
            'similarity': float(sim)
        } for sim, chunk in top_chunks]

        return results

    except Exception as e:
        print(f"❌ Error in get_similar_chunks: {str(e)}")
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
        
        # Group chunks by document for better context
        chunks_by_doc = {}
        doc_names = {}
        
        # Get document names from MongoDB
        for doc_id in document_ids:
            doc = collection.find_one({"document_id": doc_id})
            if doc:
                doc_names[doc_id] = doc.get("filename", f"Document {doc_id}")
        
        for r in results:
            doc_id = r.get("document_id", "unknown")
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = []
            chunks_by_doc[doc_id].append(r["chunk"])
        
        # Create structured context with document separation
        context_parts = []
        for doc_id, chunks in chunks_by_doc.items():
            doc_name = doc_names.get(doc_id, f"Document {doc_id}")
            doc_context = f"\n--- Document: {doc_name} ---\n"
            doc_context += "\n".join(chunks)
            context_parts.append(doc_context)
        
        context = "\n\n".join(context_parts)

        # Enhanced prompt for multi-document analysis
        if len(chunks_by_doc) > 1:
            prompt = f"""You are an expert multi-document analyst. You are comparing {len(chunks_by_doc)} documents.

IMPORTANT INSTRUCTIONS:
- Analyze and compare information from ALL documents
- Highlight similarities, differences, and contradictions between documents
- Provide comprehensive answers that synthesize information across documents
- Explicitly mention which document(s) your information comes from
- If the context doesn't contain information to answer the question, say "The provided context doesn't contain information to answer this question."
- For comparisons, structure your response to clearly show differences and similarities

Context from multiple documents:
{context}

User Question: {user_query}

Please provide a comprehensive analysis that compares and synthesizes information from all relevant documents:"""
        else:
            prompt = f"""You are an expert document analyst. Answer the user's question based ONLY on the context provided below.

IMPORTANT INSTRUCTIONS:
- Analyze information from the provided document
- Provide comprehensive answers based on the context
- If the context doesn't contain information to answer the question, say "The provided context doesn't contain information to answer this question."

Context from document:
{context}

User Question: {user_query}

Please provide a comprehensive answer based on the document:"""

        try:
            print("🚀 Starting Groq API RAG generation...")
            answer = groq_generate(prompt, max_tokens=300, temperature=0.3, timeout=90)
            
            if answer:
                print("✅ Groq API RAG generation successful")
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
                print(f"❌ Groq API generation failed, using simple fallback...")
                from utils.simple_rag import handle_simple_rag_query
                return handle_simple_rag_query(user_query, document_ids)
                
        except Exception as e:
            print(f"❌ Groq API error: {str(e)}, using simple fallback...")
            from utils.simple_rag import handle_simple_rag_query
            return handle_simple_rag_query(user_query, document_ids)
            
    except Exception as e:
        print(f"RAG query error: {str(e)}")
        return {
            "answer": f"I encountered an error while processing your request: {str(e)}. Please try again."
        }
