from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from .groq_api import groq_generate, test_groq_connection

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["documents"]
collection = db["mangobytes"]

def compare_documents(user_query, document_ids):
    try:
        if len(document_ids) < 2:
            return { "answer": "Please upload at least 2 documents for comparison." }

        # Fetch documents from MongoDB
        docs = list(collection.find({ "document_id": { "$in": document_ids } }))

        if len(docs) < 2:
            return { "answer": "Not enough documents found in DB for comparison." }

        filenames = [doc['filename'] for doc in docs]
        
        # Get document contents
        doc_contents = []
        for doc in docs:
            content = doc.get('raw_text', '')[:1500]  # Limit content to avoid timeouts
            doc_contents.append(f"Document: {doc['filename']}\nContent: {content}\n")

        # Use Groq API for comparison
        prompt = f"""Please compare the following documents based on the user's query: "{user_query}"

Documents:
{chr(10).join(doc_contents)}

Please provide a detailed comparison highlighting similarities, differences, and key insights."""

        try:
            print("🚀 Starting Groq API comparison...")
            comparison_result = groq_generate(prompt, max_tokens=600, temperature=0.3, timeout=120)
            
            if not comparison_result:
                comparison_result = f"Comparing documents: {filenames[0]} and {filenames[1]} based on query: '{user_query}'."
                
        except Exception as e:
            print(f"❌ Groq API comparison error: {str(e)}")
            comparison_result = f"Comparing documents: {filenames[0]} and {filenames[1]} based on query: '{user_query}'."

        return { "answer": comparison_result }
        
    except Exception as e:
        print(f"Comparison error: {str(e)}")
        return { "answer": f"Error performing comparison: {str(e)}" }
