from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from utils.text_utils import process_document
from utils.extract_text import extract_text_from_file
import os

app = Flask(__name__)
CORS(app)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # adjust for Atlas if needed
db = client['legal_documents']
collection = db['documents']

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Extract raw text from uploaded file
    raw_text = extract_text_from_file(file_path)

    # Process into JSON format (chunks, embeddings, etc.)
    document_json = process_document(file.filename, file.content_type, raw_text)

    # Store in MongoDB
    collection.insert_one(document_json)

    return jsonify({'message': 'Document uploaded and processed successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
