from utils.rag_pipeline import handle_rag_query
from summarizer import summarize_documents
from comparison import compare_documents
import ollama

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
    prompt = route_query_prompt(user_query)
    response = ollama.chat(model='phi3', messages=[{"role": "user", "content": prompt}])

    try:
        intent_number = int(response['message']['content'].strip())
        return intent_number
    except Exception:
        return 1  # Default to RAG if detection fails

# Master Intent Router Function
def handle_query(user_query, document_ids):
    intent = detect_intent(user_query)

    if intent == 1:
        # RAG-Based Query
        return handle_rag_query(user_query, document_ids)

    elif intent == 2:
        # Summarization
        return summarize_documents(user_query, document_ids)

    elif intent == 3:
        # Comparison
        return compare_documents(user_query, document_ids)

    elif intent == 4:
        # RAG with Source Trace
        return handle_rag_query(user_query, document_ids, with_trace=True)

    else:
        # Fallback Error
        return {"answer": "[Error] Couldn't determine the intent of your query."}
