import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './DocumentSummary.css';

// Helper function to clean up backend text before rendering
const cleanMarkdown = (text) => {
  if (!text) return "";
  return text
    // 1. Fix Bullet Points: Replace "•" with a newline and a standard markdown dash
    .replace(/•/g, '\n-')
    
    // 2. Fix Section Headers: Ensure "Section X:" starts on a new line
    .replace(/(#{1,6} |^)(\*\*Section \d+:)/gm, '\n$2')
    
    // 3. Fix Bold Headers running into text: Ensure "Key Points" and "Details" start on new lines
    .replace(/\*\*Key Points\*\*/g, '\n\n**Key Points**')
    .replace(/\*\*Details\*\*/g, '\n\n**Details**')
    .replace(/\*\*Unique Contributions\*\*/g, '\n\n**Unique Contributions**')
    
    // 4. Fix List Items: Ensure dashes have a newline before them if they are stuck to text
    .replace(/([^\n])\s*-\s/g, '$1\n- ')
    
    // 5. Cleanup: Remove excessive newlines
    .replace(/\n{3,}/g, '\n\n');
};

const DocumentSummary = ({ documentIds, documentNames, onSummariesUpdate }) => {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedDocs, setExpandedDocs] = useState(new Set());
  const [error, setError] = useState(null);

  useEffect(() => {
    if (documentIds && documentIds.length > 0) {
      loadSummaries();
    }
  }, [documentIds]);

  // Notify parent component when summaries are updated
  useEffect(() => {
    if (onSummariesUpdate && summaries.length > 0) {
      onSummariesUpdate(summaries);
    }
  }, [summaries, onSummariesUpdate]);

  const loadSummaries = async () => {
    try {
      setLoading(true);
      setError(null);

      if (documentIds.length === 1) {
        // Single document summary
        const summaryPromises = documentIds.map(async (docId, index) => {
          try {
            const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/query`, {
              message: 'Provide a comprehensive summary of this document with detailed analysis, key points, and insights',
              document_ids: [docId]
            }, {
              timeout: 120000 // 2 minutes timeout
            });

            return {
              id: docId,
              name: documentNames[index] || `Document ${index + 1}`,
              summary: response.data.answer || 'Summary not available',
              timestamp: new Date()
            };
          } catch (error) {
            console.error(`Failed to load summary for document ${docId}:`, error);
            return {
              id: docId,
              name: documentNames[index] || `Document ${index + 1}`,
              summary: 'Failed to load summary. Please try again.',
              timestamp: new Date(),
              error: true
            };
          }
        });

        const summaryResults = await Promise.all(summaryPromises);
        setSummaries(summaryResults);
        
        // Auto-expand first document if only one document
        if (summaryResults.length === 1) {
          setExpandedDocs(new Set([summaryResults[0].id]));
        }
      } else {
        // Multiple documents - get both individual summaries and comparison
        const allSummaries = [];
        
        // First, get individual summaries for each document
        const individualSummaryPromises = documentIds.map(async (docId, index) => {
          try {
            const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/query`, {
              message: 'Provide a comprehensive summary of this document with detailed analysis, key points, and insights',
              document_ids: [docId]
            }, {
              timeout: 120000 // 2 minutes timeout
            });

            return {
              id: docId,
              name: documentNames[index] || `Document ${index + 1}`,
              summary: response.data.answer || 'Summary not available',
              timestamp: new Date(),
              type: 'individual'
            };
          } catch (error) {
            console.error(`Failed to load summary for document ${docId}:`, error);
            return {
              id: docId,
              name: documentNames[index] || `Document ${index + 1}`,
              summary: 'Failed to load summary. Please try again.',
              timestamp: new Date(),
              error: true,
              type: 'individual'
            };
          }
        });

        const individualSummaries = await Promise.all(individualSummaryPromises);
        allSummaries.push(...individualSummaries);

        // Then, get the comparison summary
        try {
          console.log('🔄 Loading comparison summary for documents:', documentIds);
          const comparisonResponse = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/query`, {
            message: 'Create a comprehensive summary comparing all uploaded documents. Analyze similarities, differences, and provide insights across all documents.',
            document_ids: documentIds
          }, {
            timeout: 180000 // 3 minutes timeout for multi-doc
          });

          const comparisonSummary = {
            id: 'comparison',
            name: `📊 Comparison of ${documentIds.length} Documents`,
            summary: comparisonResponse.data.answer || 'Multi-document comparison not available',
            timestamp: new Date(),
            type: 'comparison'
          };

          allSummaries.push(comparisonSummary);
        } catch (error) {
          console.error('❌ Failed to load comparison summary:', error);
        }

        setSummaries(allSummaries);
        setExpandedDocs(new Set(['comparison']));
      }
    } catch (error) {
      console.error('Failed to load summaries:', error);
      setError('Failed to load document summaries. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const toggleDocument = (docId) => {
    const newExpanded = new Set(expandedDocs);
    if (newExpanded.has(docId)) {
      newExpanded.delete(docId);
    } else {
      newExpanded.add(docId);
    }
    setExpandedDocs(newExpanded);
  };

  const getDocumentIcon = (name) => {
    const extension = name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return '📕';
      case 'doc':
      case 'docx': return '📘';
      case 'txt': return '📄';
      case 'xls':
      case 'xlsx': return '📊';
      default: return '📄';
    }
  };

  if (loading) {
    return (
      <div className="document-summary-container">
        <div className="summary-header">
          <h2>📚 Document Summaries</h2>
          <div className="summary-count">{documentIds?.length || 0} document(s)</div>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Generating comprehensive summary...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-summary-container">
        <div className="summary-header">
          <h2>📚 Document Summaries</h2>
        </div>
        <div className="error-container">
          <p>❌ {error}</p>
          <button onClick={loadSummaries} className="retry-button">
            🔄 Retry Loading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="document-summary-container">
      <div className="summary-header">
        <h2>📚 Document Summaries</h2>
        <div className="summary-count">
          {summaries.some(s => s.type === 'comparison') 
            ? `${documentIds.length} documents + comparison` 
            : `${summaries.length} document(s)`}
        </div>
      </div>
      
      <div className="summaries-list">
        {summaries.map((summary) => (
          <div key={summary.id} className={`summary-item ${expandedDocs.has(summary.id) ? 'expanded' : ''}`}>
            <div 
              className="summary-header-item"
              onClick={() => toggleDocument(summary.id)}
            >
              <div className="summary-title-section">
                <span className="document-icon">{getDocumentIcon(summary.name)}</span>
                <span className="document-name" title={summary.name}>{summary.name}</span>
                {summary.error && <span className="error-indicator">⚠️</span>}
              </div>
              <div className="summary-controls">
                <span className="expand-icon">
                  {expandedDocs.has(summary.id) ? '▼' : '▶'}
                </span>
              </div>
            </div>
            
            {expandedDocs.has(summary.id) && (
              <div className="summary-content">
                {summary.error ? (
                  <div className="error-message">
                    <p>⚠️ Failed to generate summary.</p>
                    <button onClick={(e) => { e.stopPropagation(); loadSummaries(); }} className="retry-button-small">
                      🔄 Retry
                    </button>
                  </div>
                ) : (
                  // >>> THIS IS THE UPDATED PART USING REACT MARKDOWN <<<
                  <div className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {cleanMarkdown(summary.summary)}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentSummary;