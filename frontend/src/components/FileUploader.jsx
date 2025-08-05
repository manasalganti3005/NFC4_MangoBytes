// src/components/FileUploader.jsx
import React, { useState } from 'react';
import axios from 'axios';
import './FileUploader.css';

const FileUploader = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success', 'error', 'info'
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploadMessage('');
    setMessageType('');
    
    if (file) {
      // Validate file type
      const allowedTypes = ['.pdf', '.docx', '.txt'];
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      
      if (!allowedTypes.includes(fileExtension)) {
        setUploadMessage('Please select a valid file type (.pdf, .docx, .txt)');
        setMessageType('error');
        setSelectedFile(null);
        return;
      }
      
      // Show file selected message
      setUploadMessage(`Selected: ${file.name}`);
      setMessageType('info');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadMessage('Please select a file first');
      setMessageType('error');
      return;
    }

    setIsUploading(true);
    setUploadMessage('Uploading and processing...');
    setMessageType('info');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('http://localhost:5000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadMessage(response.data.message || 'Upload successful! You can now chat about your document.');
      setMessageType('success');
      
      // Clear selected file after successful upload
      setTimeout(() => {
        setSelectedFile(null);
        setUploadMessage('');
        setMessageType('');
      }, 3000);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadMessage(error.response?.data?.message || 'Upload failed. Please try again.');
      setMessageType('error');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="file-uploader-container">
      <h2 className="file-uploader-title">Upload Your Document</h2>
      
      <div className="file-upload-area">
        <div className="file-input-wrapper">
          <input 
            type="file" 
            id="file-input"
            accept=".pdf,.docx,.txt" 
            onChange={handleFileChange}
            disabled={isUploading}
          />
          <label 
            htmlFor="file-input" 
            className="file-input-label"
          >
            {selectedFile ? 'Change File' : 'Choose File'}
          </label>
        </div>
        
        <div className="supported-formats">
          Supported formats: PDF, DOCX, TXT
        </div>

        {selectedFile && !uploadMessage.includes('Selected:') && (
          <div className="selected-file">
            {selectedFile.name}
          </div>
        )}

        <button 
          className="upload-button" 
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
        >
          {isUploading ? 'Processing...' : 'Upload & Analyze'}
        </button>

        {uploadMessage && (
          <div className={`upload-message ${messageType}`}>
            {uploadMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploader;