// src/App.jsx
import React, { useState } from 'react';
import FileUploader from './components/FileUploader';
import Chatbot from './components/Chatbot';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('upload'); // 'upload' or 'chat'
  const [uploadedDocument, setUploadedDocument] = useState(null);

  const handleUploadSuccess = (uploadResponse) => {
    console.log('📤 Upload response received:', uploadResponse);
    
    // Store the uploaded document information
    const documentInfo = {
      name: uploadResponse.filename || 'Document',
      id: uploadResponse.documentId || 'unknown',
      uploadTime: new Date().toISOString()
    };
    
    console.log('📋 Setting document info:', documentInfo);
    setUploadedDocument(documentInfo);
    
    // Navigate to chat page
    setCurrentPage('chat');
  };

  const handleBackToUpload = () => {
    // Reset state and go back to upload page
    setUploadedDocument(null);
    setCurrentPage('upload');
  };

  return (
    <div className="App">
      {currentPage === 'upload' ? (
        <FileUploader onUploadSuccess={handleUploadSuccess} />
      ) : (
        <Chatbot 
          documentName={uploadedDocument?.name}
          documentId={uploadedDocument?.id}
          onBackToUpload={handleBackToUpload}
        />
      )}
    </div>
  );
}

export default App;