from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

load_dotenv()

# MongoDB setup using env vars
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def simple_search(query, document_ids, top_k=3):
    """Simple keyword-based search without embeddings"""
    try:
        # Get documents
        matching_docs = list(collection.find({"document_id": {"$in": document_ids}}))
        
        if not matching_docs:
            return []
        
        # Extract keywords from query
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Score chunks based on keyword matches
        scored_chunks = []
        for doc in matching_docs:
            if 'chunks' in doc:
                for chunk in doc['chunks']:
                    chunk_text = chunk.get('text', '').lower()
                    chunk_words = set(re.findall(r'\b\w+\b', chunk_text))
                    
                    # Calculate simple keyword overlap score
                    overlap = len(query_words.intersection(chunk_words))
                    if overlap > 0:
                        scored_chunks.append({
                            'chunk': chunk.get('text', ''),
                            'filename': doc.get('filename', 'Unknown'),
                            'document_id': doc.get('document_id', 'Unknown'),
                            'score': overlap,
                            'similarity': overlap / len(query_words) if query_words else 0
                        })
        
        # Sort by score and return top_k
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]
        
    except Exception as e:
        print(f"Simple search error: {str(e)}")
        return []

def simple_answer(query, chunks):
    """Generate a simple answer from chunks without using LLM"""
    if not chunks:
        return "I couldn't find any relevant information in the uploaded documents to answer your question."
    
    # Combine relevant chunks
    context = "\n\n".join([chunk['chunk'] for chunk in chunks])
    
    # Simple answer generation based on query type
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['what is', 'define', 'explain']):
        # For definition/explanation queries, return the most relevant chunk
        return f"Based on the document, here's what I found:\n\n{chunks[0]['chunk'][:500]}..."
    
    elif any(word in query_lower for word in ['summarize', 'summary', 'overview']):
        # For summary queries, combine key points
        summary_parts = []
        for chunk in chunks[:2]:  # Use top 2 chunks
            summary_parts.append(chunk['chunk'][:200])
        return f"Summary:\n\n" + "\n\n".join(summary_parts)
    
    elif any(word in query_lower for word in ['how', 'process', 'method']):
        # For how-to queries, look for procedural information
        return f"Here's the process or method described in the document:\n\n{chunks[0]['chunk'][:400]}..."
    
    else:
        # Default response
        return f"Here's relevant information from the document:\n\n{chunks[0]['chunk'][:300]}..."

def handle_simple_rag_query(user_query, document_ids):
    """Handle RAG query using simple keyword search and answer generation"""
    try:
        print(f"🔍 Simple RAG search for: '{user_query}'")
        
        # Get relevant chunks
        chunks = simple_search(user_query, document_ids)
        
        if not chunks:
            return {
                "answer": f"I couldn't find any relevant information in the uploaded documents to answer: '{user_query}'. Please try rephrasing your question or ask about a different topic."
            }
        
        print(f"✅ Found {len(chunks)} relevant chunks")
        
        # Generate simple answer
        answer = simple_answer(user_query, chunks)
        
        return {
            "answer": answer,
            "sources": [chunk['filename'] for chunk in chunks]
        }
        
    except Exception as e:
        print(f"❌ Simple RAG error: {str(e)}")
        return {
            "answer": f"I encountered an error while processing your request: {str(e)}. Please try again."
        } 