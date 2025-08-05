// src/components/Chatbot.jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './Chatbot.css';

const Chatbot = ({ documentName, documentId, onBackToUpload }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatboxRef = useRef(null);
  const inputRef = useRef(null);

  // Sample suggestions for empty state
  const suggestions = [
    "What is this document about?",
    "Summarize the main points",
    "What are the key findings?",
    "Extract important dates",
    "List the main topics"
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const sendMessage = async (messageText = null) => {
    const userMessage = messageText || input.trim();
    if (userMessage === '' || isLoading) return;

    const newMessages = [...messages, { sender: 'user', text: userMessage, timestamp: new Date() }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      // API call to your backend
      const response = await axios.post('http://localhost:5000/api/query', { 
        message: userMessage,
        // You can include document context or ID here
        document_ids: [documentId]
      }, {
        timeout: 30000 // 30 second timeout
      });

      const botReply = response.data.reply || "I'm processing your request. Could you please try rephrasing your question?";
      setMessages((prev) => [...prev, { 
        sender: 'bot', 
        text: botReply, 
        timestamp: new Date() 
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      let errorMessage = 'I apologize, but I encountered an issue processing your request. Please try again.';
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'The request timed out. Please try again with a shorter question.';
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      }
      
      setMessages((prev) => [...prev, { 
        sender: 'bot', 
        text: errorMessage, 
        timestamp: new Date() 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="chatbot-page">
      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <button className="back-button" onClick={onBackToUpload}>
            <span>←</span>
            New Document
          </button>
          <h1 className="chat-title">Document Chat</h1>
        </div>
        {documentName && (
          <div className="document-info">
            {documentName}
          </div>
        )}
      </div>

      {/* Main chat area */}
      <div className="chatbot-container">
        <div className="chatbox" ref={chatboxRef}>
          {messages.length === 0 ? (
            <div className="empty-chat-state">
              <div className="empty-icon">🤖</div>
              <div className="empty-title">Ready to analyze your document!</div>
              <div className="empty-description">
                Ask me anything about your document. I can summarize, extract key information, answer questions, and more.
              </div>
              <div className="suggestions-container">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    className="suggestion-chip"
                    onClick={() => handleSuggestionClick(suggestion)}
                    disabled={isLoading}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.sender}`}>
                  <div className="message-content">
                    {msg.text}
                  </div>
                  <div className="message-time" style={{
                    fontSize: '0.75rem',
                    opacity: 0.7,
                    marginTop: '0.5rem'
                  }}>
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="typing-message">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span>Analyzing...</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Input area */}
        <div className="input-area">
          <div className="input-wrapper">
            <div className="input-icon">💬</div>
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask something about your document..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              maxLength={500}
            />
          </div>
          <button 
            className="send-button" 
            onClick={() => sendMessage()}
            disabled={isLoading || input.trim() === ''}
          >
            {isLoading ? (
              <div className="button-spinner"></div>
            ) : (
              <>
                <span>Send</span>
                <span>➤</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;