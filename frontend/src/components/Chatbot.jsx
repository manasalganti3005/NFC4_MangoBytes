// src/components/Chatbot.jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import DocumentSummary from './DocumentSummary';
import './Chatbot.css';
//import './Summary.css';

const Chatbot = ({ documentNames, documentIds, onBackToUpload }) => {
  console.log('🤖 Chatbot initialized with:', { documentNames, documentIds });
  
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
      console.log('📤 Sending query with document IDs:', documentIds);
      
      // API call to your backend
      const response = await axios.post('http://localhost:5000/api/query', { 
        message: userMessage,
        // Send all document IDs for multi-document analysis
        document_ids: documentIds || []
      }, {
        timeout: 180000 // 180 second timeout for longer summaries
      });

      console.log('📥 Frontend received response:', response.data);
      console.log('🔍 Response keys:', Object.keys(response.data));
      console.log('📄 Answer field:', response.data.answer);
      console.log('📄 Reply field:', response.data.reply);
      const botReply = response.data.answer || response.data.reply || "I'm processing your request. Could you please try rephrasing your question?";
      console.log('💬 Bot reply:', botReply);
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

  const formatSummaryText = (text) => {
    // Check if this looks like a summary (has markdown headers)
    if (text.includes('# 📋') || text.includes('## 📊') || text.includes('## 📝')) {
      return (
        <div className="summary-container">
          <div dangerouslySetInnerHTML={{ 
            __html: text
              .replace(/# 📋 DOCUMENT SUMMARY/g, '<h1 class="summary-title">📋 DOCUMENT SUMMARY</h1>')
              .replace(/## 📊 OVERALL SUMMARY/g, '<h2 class="summary-section-title">📊 OVERALL SUMMARY</h2>')
              .replace(/## 📝 SECTION-WISE BREAKDOWN/g, '<h2 class="summary-section-title">📝 SECTION-WISE BREAKDOWN</h2>')
              .replace(/## 🔍 KEY FINDINGS & HIGHLIGHTS/g, '<h2 class="summary-section-title">🔍 KEY FINDINGS & HIGHLIGHTS</h2>')
              .replace(/## 🎯 MAIN TOPICS & THEMES/g, '<h2 class="summary-section-title">🎯 MAIN TOPICS & THEMES</h2>')
              .replace(/## 💡 RECOMMENDATIONS & INSIGHTS/g, '<h2 class="summary-section-title">💡 RECOMMENDATIONS & INSIGHTS</h2>')
              .replace(/## 📈 KEY STATISTICS/g, '<h2 class="summary-section-title">📈 KEY STATISTICS</h2>')
              .replace(/\*\*(.*?)\*\*/g, '<span class="summary-bold">$1</span>')
              .replace(/\n• /g, '<div class="summary-bullet">')
              .replace(/\n\n/g, '</div><div class="summary-bullet">')
              .replace(/\n### \*\*(.*?)\*\*/g, '<h3 class="summary-subsection">$1</h3>')
          }} />
        </div>
      );
    }
    return text;
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
          <h1 className="chat-title">Document Intelligence Hub</h1>
        </div>
        {documentNames && documentNames.length > 0 && (
          <div className="document-info">
            {documentNames.length === 1 ? (
              documentNames[0]
            ) : (
              <div className="multiple-docs">
                <span>📚 {documentNames.length} Documents</span>
                <div className="doc-list">
                  {documentNames.map((name, index) => (
                    <span key={index} className="doc-name">{name}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main layout with two panels */}
      <div className="chatbot-main-container">
        {/* Left panel - Chatbot */}
        <div className="chatbot-container">
          <div className="chatbox" ref={chatboxRef}>
            {messages.length === 0 ? (
              <div className="empty-chat-state">
                <div className="empty-icon">🤖</div>
                <div className="empty-title">Ready to analyze your documents!</div>
                <div className="empty-description">
                  Ask me anything about your documents. I can summarize, extract key information, answer questions, and provide detailed analysis.
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
                      {msg.sender === 'bot' ? formatSummaryText(msg.text) : msg.text}
                    </div>
                    <div className="message-time">
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
                placeholder="Ask something about your documents..."
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

        {/* Right panel - Document Summary */}
        <div className="document-summary-panel">
          <DocumentSummary 
            documentIds={documentIds} 
            documentNames={documentNames} 
          />
        </div>
      </div>
    </div>
  );
};

export default Chatbot;