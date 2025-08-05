from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from utils.text_utils import process_document
from utils.extract_text import extract_text_from_file
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB setup using env vars
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
@app.route('/api/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Get the file extension to decide how to extract text
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()

    # Read file bytes for processing
    file_bytes = file.read()

    # Extract raw text from file (directly from bytes)
    raw_text = extract_text_from_file(file_bytes, file_ext)

    # Process into JSON format (chunks, embeddings, etc.)
    document_json = process_document(file.filename, file.content_type, raw_text)

    # Store in MongoDB
    collection.insert_one(document_json)

    return jsonify({'message': 'Document uploaded and processed successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
