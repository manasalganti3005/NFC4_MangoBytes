from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests

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
    query_embedding = model.encode(query).tolist()

    pipeline = [
        { "$match": { "document_id": { "$in": document_ids } } },  # Filter by document_ids
        { "$unwind": "$chunks" },  # Flatten chunks
        {
            "$vectorSearch": {
                "index": "vector2",
                "path": "chunks.embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "chunk": "$chunks.text",
                "filename": 1,
                "document_id": 1
            }
        }
    ]

    results = list(collection.aggregate(pipeline))
    return results

def handle_rag_query(user_query, document_ids, with_trace=False):
    results = get_similar_chunks(user_query, document_ids)
    context = "\n\n".join([r["chunk"] for r in results])

    prompt = f"""Answer the question based on the context below.

Context:
{context}

Question:
{user_query}

Answer:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi3", "prompt": prompt, "stream": False}
    )

    if with_trace:
        sources = ", ".join([r["filename"] for r in results])
        return {
            "answer": response.json()['response'],
            "sources": sources
        }
    else:
        return {
            "answer": response.json()['response']
        }
