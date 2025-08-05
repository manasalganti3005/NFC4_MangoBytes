from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.intent_router import handle_query
from utils.extract_text import extract_text_from_file
from utils.text_utils import process_document
from pymongo import MongoClient
import os
from dotenv import load_dotenv

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
    try:
        print(f"📤 Upload request received")
        print(f"📋 Request files: {list(request.files.keys())}")
        print(f"📋 Request form: {list(request.form.keys())}")
        
        # Handle multiple files
        uploaded_files = []
        
        # Check for multiple files (file0, file1, etc.)
        file_index = 0
        while f'file{file_index}' in request.files:
            file = request.files[f'file{file_index}']
            if file.filename != '':
                uploaded_files.append(file)
                print(f"📄 Found file{file_index}: {file.filename}")
            file_index += 1
        
        # Also check for single file with key 'file'
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                uploaded_files.append(file)
                print(f"📄 Found single file: {file.filename}")
        
        if not uploaded_files:
            print("❌ No valid files found")
            return jsonify({'error': 'No files uploaded'}), 400
        
        print(f"📁 Processing {len(uploaded_files)} file(s)")
        
        # Process all uploaded files
        uploaded_documents = []
        
        for file in uploaded_files:
            # Get the file extension to decide how to extract text
            filename = file.filename
            file_ext = os.path.splitext(filename)[1].lower()

            # Read file bytes for processing
            file_bytes = file.read()

            # Extract raw text from file (directly from bytes)
            raw_text = extract_text_from_file(file_bytes, file_ext)

            # Process into JSON format (chunks, embeddings, etc.)
            document_json = process_document(file.filename, file.content_type, raw_text)
            
            print(f"📄 Processing document: {document_json['filename']}")
            print(f"🆔 Generated document ID: {document_json['document_id']}")

            # Store in MongoDB
            result = collection.insert_one(document_json)
            print(f"💾 Document stored in MongoDB with ID: {result.inserted_id}")
            
            uploaded_documents.append({
                'documentId': document_json['document_id'],
                'filename': document_json['filename']
            })

        # Return information about all uploaded documents
        if len(uploaded_documents) == 1:
            response_data = {
                'message': 'Document uploaded and processed successfully',
                'documentId': uploaded_documents[0]['documentId'],
                'filename': uploaded_documents[0]['filename']
            }
        else:
            response_data = {
                'message': f'{len(uploaded_documents)} documents uploaded and processed successfully',
                'documentIds': [doc['documentId'] for doc in uploaded_documents],
                'filenames': [doc['filename'] for doc in uploaded_documents],
                'documentId': uploaded_documents[0]['documentId'],  # Keep for backward compatibility
                'filename': uploaded_documents[0]['filename']  # Keep for backward compatibility
            }
        
        print(f"📤 Sending response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Error in upload_document: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

# Unified Query Endpoint
@app.route('/api/query', methods=['POST'])
def query_documents():
    try:
        data = request.json
        if not data:
            print("❌ No JSON data provided")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        user_query = data.get('message') or data.get('query')  # Handle both 'message' and 'query' keys
        if not user_query:
            print("❌ No query or message provided")
            return jsonify({'error': 'No query or message provided'}), 400
            
        document_ids = data.get('document_ids', [])
        print(f"🔍 Processing query: '{user_query}' for documents: {document_ids}")

        if not document_ids:
            print("❌ No documents uploaded yet")
            return jsonify({'error': 'No documents uploaded yet.'}), 400

        print("🚀 Calling handle_query...")
        response = handle_query(user_query, document_ids)
        print(f"✅ Query completed, response: {response}")
        return jsonify(response)
    except Exception as e:
        print(f"❌ Error in query_documents: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
