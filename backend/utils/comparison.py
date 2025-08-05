from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests

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

        # Use Ollama for comparison
        prompt = f"""Please compare the following documents based on the user's query: "{user_query}"

Documents:
{chr(10).join(doc_contents)}

Please provide a detailed comparison highlighting similarities, differences, and key insights."""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi3", "prompt": prompt, "stream": False},
                timeout=60  # 60 second timeout for comparison
            )
            
            if response.status_code == 200:
                comparison_result = response.json().get('response', 'Comparison generation failed.')
            else:
                comparison_result = f"Comparing documents: {filenames[0]} and {filenames[1]} based on query: '{user_query}'."
                
        except requests.exceptions.Timeout:
            comparison_result = "Document comparison timed out. The documents may be too large for comparison."
        except requests.exceptions.ConnectionError:
            comparison_result = "Unable to perform comparison due to connection issues. Please check if Ollama is running."
        except Exception as e:
            print(f"Comparison error: {str(e)}")
            comparison_result = f"Comparing documents: {filenames[0]} and {filenames[1]} based on query: '{user_query}'."

        return { "answer": comparison_result }
        
    except Exception as e:
        print(f"Comparison error: {str(e)}")
        return { "answer": f"Error performing comparison: {str(e)}" }
