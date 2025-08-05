from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["documents"]
collection = db["mangobytes"]

def summarize_documents(user_query, document_ids):
    try:
        # Fetch documents from MongoDB
        docs = collection.find({ "document_id": { "$in": document_ids } })

        combined_text = ""
        for doc in docs:
            combined_text += doc.get('raw_text', '') + "\n\n"

        if not combined_text.strip():
            return { "answer": "No document content found to summarize." }

        # Use Ollama for summarization
        prompt = f"""Please provide a comprehensive summary of the following document:

{combined_text[:3000]}  # Limit to first 3000 chars to avoid timeouts

Please provide a clear, structured summary that covers the main points and key information."""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi3", "prompt": prompt, "stream": False},
                timeout=60  # 60 second timeout for summarization
            )
            
            if response.status_code == 200:
                summary = response.json().get('response', 'Summary generation failed.')
            else:
                summary = f"Document summary: This document contains {len(combined_text)} characters of text across {len(document_ids)} document(s)."
                
        except requests.exceptions.Timeout:
            print("⏰ Ollama timeout for summarization, using simple fallback...")
            summary = generate_simple_summary(combined_text, document_ids)
        except requests.exceptions.ConnectionError:
            print("🔌 Ollama connection error for summarization, using simple fallback...")
            summary = generate_simple_summary(combined_text, document_ids)
        except Exception as e:
            print(f"❌ Summarization error: {str(e)}, using simple fallback...")
            summary = generate_simple_summary(combined_text, document_ids)

        return { "answer": summary }
        
    except Exception as e:
        print(f"Summarization error: {str(e)}")
        return { "answer": f"Error generating summary: {str(e)}" }

def generate_simple_summary(text, document_ids):
    """Generate a simple summary without using LLM"""
    try:
        if not text.strip():
            return "No document content found to summarize."
        
        # Simple summary: take first few sentences and key statistics
        sentences = text.split('.')
        first_sentences = '. '.join(sentences[:3]) + '.'
        
        # Count words and characters
        word_count = len(text.split())
        char_count = len(text)
        
        summary = f"""Document Summary:

Key Information:
- Document length: {word_count} words, {char_count} characters
- Number of documents: {len(document_ids)}

Main content preview:
{first_sentences}

This is a basic summary generated from the document content."""
        
        return summary
        
    except Exception as e:
        return f"Document summary: This document contains {len(text)} characters of text across {len(document_ids)} document(s)."
