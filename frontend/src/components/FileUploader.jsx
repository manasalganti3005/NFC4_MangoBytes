// src/components/FileUploader.jsx
import React, { useState, useRef } from 'react';
import axios from 'axios';
import './FileUploader.css';

const FileUploader = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const allowedTypes = ['.pdf', '.docx', '.txt'];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file) => {
    if (!file) return { isValid: false, message: 'No file selected' };
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      return { 
        isValid: false, 
        message: 'Invalid file type. Please select a PDF, DOCX, or TXT file.' 
      };
    }
    
    if (file.size > maxFileSize) {
      return { 
        isValid: false, 
        message: 'File size too large. Please select a file smaller than 10MB.' 
      };
    }
    
    return { isValid: true, message: '' };
  };

  const handleFileSelect = (file) => {
    const validation = validateFile(file);
    
    if (!validation.isValid) {
      setUploadMessage(validation.message);
      setMessageType('error');
      setSelectedFile(null);
      return;
    }
    
    setSelectedFile(file);
    setUploadMessage('');
    setMessageType('');
    setUploadProgress(0);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragDropClick = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadMessage('Please select a file first');
      setMessageType('error');
      return;
    }

    setIsUploading(true);
    setUploadMessage('Processing your document...');
    setMessageType('info');
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + Math.random() * 15;
        });
      }, 200);

      const response = await axios.post('http://localhost:5000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setUploadMessage('Upload successful! Redirecting to chat...');
      setMessageType('success');
      
      // Redirect to chat page after success
      setTimeout(() => {
        if (onUploadSuccess) {
          onUploadSuccess(response.data);
        }
      }, 2000);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadProgress(0);
      
      let errorMessage = 'Upload failed. Please try again.';
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Upload timeout. Please check your connection and try again.';
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setUploadMessage(errorMessage);
      setMessageType('error');
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadMessage('');
    setMessageType('');
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="file-uploader-container">
      <h1 className="main-title">Document Intelligence Hub</h1>
      <p className="subtitle">Transform your documents into interactive conversations</p>
      
      <div className="upload-section">
        <div 
          className={`drag-drop-zone ${isDragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleDragDropClick}
        >
          <div className="upload-icon"></div>
          
          <div className="upload-content">
            <h2 className="upload-title">
              {isDragOver ? 'Drop Your Document' : 'Upload Your Document'}
            </h2>
            <p className="upload-description">
              {isDragOver 
                ? 'Release to upload your file and unlock its potential' 
                : 'Drag and drop your file here, or click below to browse and select'
              }
            </p>

            <div className="file-input-wrapper">
              <input 
                ref={fileInputRef}
                type="file" 
                id="file-input"
                accept=".pdf,.docx,.txt" 
                onChange={handleFileChange}
                disabled={isUploading}
              />
              <label 
                htmlFor="file-input" 
                className="browse-button"
              >
                <span>📁</span>
                {selectedFile ? 'Change Document' : 'Browse Files'}
              </label>
            </div>
          </div>
        </div>

        <div className="supported-formats">
          Supported formats: PDF, DOCX, TXT files up to 10MB
        </div>

        {selectedFile && (
          <div className="selected-file-display">
            <div className="file-icon">✨</div>
            <div className="file-info">
              <div className="file-name">{selectedFile.name}</div>
              <div className="file-size">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </div>
            </div>
            <button 
              className="remove-file-btn"
              onClick={(e) => {
                e.stopPropagation();
                resetUpload();
              }}
              title="Remove file"
            >
              ✕
            </button>
          </div>
        )}

        {isUploading && uploadProgress > 0 && (
          <div className="progress-container">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        <button 
          className="upload-button" 
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
        >
          {isUploading && <span className="loading-spinner"></span>}
          {isUploading ? 'Processing Document...' : 'Upload & Start Chatting'}
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