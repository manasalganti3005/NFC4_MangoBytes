// src/App.jsx
import React from 'react';
import FileUploader from './components/FileUploader';
import Chatbot from './components/Chatbot';

function App() {
  return (
    <div>
      <h1>Document Chatbot Interface</h1>
      <FileUploader />
      <Chatbot />
    </div>
  );
}

export default App;
