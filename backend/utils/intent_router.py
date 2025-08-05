from utils.rag_pipeline import handle_rag_query
from utils.summarizer import summarize_documents
from utils.comparison import compare_documents
import requests

# Intent Routing Prompt
def route_query_prompt(user_query):
    return f"""
You are an intelligent document assistant. Based on the user's query below, decide which of the following four tasks is most appropriate. Respond ONLY with the task number.

1. RAG-Based Query:
   - The user is asking a specific question and wants an answer based on the uploaded document(s).

2. Summarization:
   - The user is asking for a summary, overview, or gist of the document(s).

3. Comparison:
   - The user wants a comparison or analysis between two or more documents.

4. RAG + Source Trace:
   - The user is asking a question and wants not just the answer, but also where in the document the answer came from (line, chunk, or filename).

User Query:
\"\"\"{user_query}\"\"\"

Which task (1, 2, 3, or 4) should be activated? Only respond with a number.
"""

# Intent Detection using Ollama
def detect_intent(user_query):
    try:
        prompt = route_query_prompt(user_query)
        
        response = requests.post(
            "http://localhost:11434/api/generate",
                            json={
                    "model": "tinyllama", 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                        "num_predict": 10,   # Very short response for intent detection
                        "temperature": 0.0,   # Deterministic for intent detection
                        "top_p": 0.1,         # Very fast sampling
                        "top_k": 1            # Very fast sampling
                    }
                },
            timeout=30  # 30 second timeout for intent detection
        )
        
        if response.status_code == 200:
            try:
                intent_number = int(response.json()['response'].strip())
                return intent_number
            except Exception:
                return 1  # Default to RAG if detection fails
        else:
            print(f"Ollama intent detection failed with status {response.status_code}")
            return 1  # Default to RAG
            
    except requests.exceptions.Timeout:
        print("⏰ Ollama intent detection timeout, using keyword fallback...")
        return detect_intent_keywords(user_query)
    except Exception as e:
        print(f"Ollama intent detection failed: {str(e)}")
        return detect_intent_keywords(user_query)

def detect_intent_keywords(user_query):
    """Simple keyword-based intent detection fallback"""
    query_lower = user_query.lower()
    if any(word in query_lower for word in ['summarize', 'summary', 'overview', 'gist']):
        return 2
    elif any(word in query_lower for word in ['compare', 'comparison', 'difference']):
        return 3
    else:
        return 1  # Default to RAG

# Master Intent Router Function
def handle_query(user_query, document_ids):
    try:
        print(f"🎯 Detecting intent for query: '{user_query}'")
        intent = detect_intent(user_query)
        print(f"📊 Detected intent: {intent}")

        if intent == 1:
            print("🔍 Using RAG-based query...")
            # RAG-Based Query
            return handle_rag_query(user_query, document_ids)

        elif intent == 2:
            print("📝 Using summarization...")
            # Summarization
            return summarize_documents(user_query, document_ids)

        elif intent == 3:
            print("⚖️ Using comparison...")
            # Comparison
            return compare_documents(user_query, document_ids)

        elif intent == 4:
            print("🔍 Using RAG with source trace...")
            # RAG with Source Trace
            return handle_rag_query(user_query, document_ids, with_trace=True)

        else:
            print(f"❌ Unknown intent: {intent}")
            # Fallback Error
            return {"answer": "[Error] Couldn't determine the intent of your query."}
    except Exception as e:
        print(f"❌ Intent router error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"answer": f"I encountered an error while processing your request: {str(e)}. Please try again."}
