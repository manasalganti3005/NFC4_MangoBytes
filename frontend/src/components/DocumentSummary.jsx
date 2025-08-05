import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DocumentSummary.css';

const DocumentSummary = ({ documentIds, documentNames }) => {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedDocs, setExpandedDocs] = useState(new Set());
  const [error, setError] = useState(null);

  useEffect(() => {
    if (documentIds && documentIds.length > 0) {
      loadSummaries();
    }
  }, [documentIds]);

  const loadSummaries = async () => {
    try {
      setLoading(true);
      setError(null);

      if (documentIds.length === 1) {
        // Single document summary
        const summaryPromises = documentIds.map(async (docId, index) => {
          try {
            const response = await axios.post('http://localhost:5000/api/query', {
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
            const response = await axios.post('http://localhost:5000/api/query', {
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
          const comparisonResponse = await axios.post('http://localhost:5000/api/query', {
            message: 'Create a comprehensive summary comparing all uploaded documents. Analyze similarities, differences, and provide insights across all documents.',
            document_ids: documentIds
          }, {
            timeout: 180000 // 3 minutes timeout for multi-doc
          });

          console.log('✅ Comparison response received:', comparisonResponse.data);
          const comparisonSummary = {
            id: 'comparison',
            name: `📊 Comparison of ${documentIds.length} Documents`,
            summary: comparisonResponse.data.answer || 'Multi-document comparison not available',
            timestamp: new Date(),
            type: 'comparison'
          };

          allSummaries.push(comparisonSummary);
          console.log('📊 Added comparison summary to list');
        } catch (error) {
          console.error('❌ Failed to load comparison summary:', error);
          console.error('Error details:', error.response?.data || error.message);
          
          // Don't add fallback - let it fail naturally
        }

        setSummaries(allSummaries);
        // Auto-expand the comparison summary
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

  const formatSummaryText = (text) => {
    // Enhanced text formatting for better readability
    if (text.includes('# 📋') || text.includes('## 📊') || text.includes('## 📝') || 
        text.includes('# 📚') || text.includes('## 📊 OVERALL COMPARISON')) {
      return (
        <div className="summary-container">
          <div dangerouslySetInnerHTML={{ 
            __html: text
              .replace(/# 📋 DOCUMENT SUMMARY/g, '<h1 class="summary-title">📋 DOCUMENT SUMMARY</h1>')
              .replace(/# 📚 MULTI-DOCUMENT ANALYSIS/g, '<h1 class="summary-title">📚 MULTI-DOCUMENT ANALYSIS</h1>')
              .replace(/## 📊 OVERALL SUMMARY/g, '<h2 class="summary-section-title">📊 OVERALL SUMMARY</h2>')
              .replace(/## 📊 OVERALL COMPARISON/g, '<h2 class="summary-section-title">📊 OVERALL COMPARISON</h2>')
              .replace(/## 📝 SECTION-WISE BREAKDOWN/g, '<h2 class="summary-section-title">📝 SECTION-WISE BREAKDOWN</h2>')
              .replace(/## 📝 DOCUMENT-BY-DOCUMENT BREAKDOWN/g, '<h2 class="summary-section-title">📝 DOCUMENT-BY-DOCUMENT BREAKDOWN</h2>')
              .replace(/## 🔍 KEY FINDINGS & HIGHLIGHTS/g, '<h2 class="summary-section-title">🔍 KEY FINDINGS & HIGHLIGHTS</h2>')
              .replace(/## 🔍 CROSS-DOCUMENT FINDINGS/g, '<h2 class="summary-section-title">🔍 CROSS-DOCUMENT FINDINGS</h2>')
              .replace(/## 🎯 MAIN TOPICS & THEMES/g, '<h2 class="summary-section-title">🎯 MAIN TOPICS & THEMES</h2>')
              .replace(/## 🎯 SYNTHESIZED INSIGHTS/g, '<h2 class="summary-section-title">🎯 SYNTHESIZED INSIGHTS</h2>')
              .replace(/## 💡 RECOMMENDATIONS & INSIGHTS/g, '<h2 class="summary-section-title">💡 RECOMMENDATIONS & INSIGHTS</h2>')
              .replace(/## 💡 RECOMMENDATIONS/g, '<h2 class="summary-section-title">💡 RECOMMENDATIONS</h2>')
              .replace(/## 📈 KEY STATISTICS/g, '<h2 class="summary-section-title">📈 KEY STATISTICS</h2>')
              .replace(/\*\*(.*?)\*\*/g, '<span class="summary-bold">$1</span>')
              .replace(/\n• /g, '<div class="summary-bullet">')
              .replace(/\n\n/g, '</div><div class="summary-bullet">')
              .replace(/\n### \*\*(.*?)\*\*/g, '<h3 class="summary-subsection">$1</h3>')
              .replace(/Document \d+:/g, '<span class="doc-reference">$&</span>')
              .replace(/--- Document: (.*?) ---/g, '<div class="doc-separator">📄 $1</div>')
          }} />
        </div>
      );
    }

    // Format plain text with better structure
    const formattedText = text
      .replace(/\n\n/g, '</p><p>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n- /g, '<br/>• ')
      .replace(/\n• /g, '<br/>• ')
      .replace(/Document \d+:/g, '<span class="doc-reference">$&</span>')
      .replace(/--- Document: (.*?) ---/g, '<div class="doc-separator">📄 $1</div>');
    
    return (
      <div className="summary-container">
        <p>{formattedText}</p>
      </div>
    );
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
      case 'ppt':
      case 'pptx': return '📋';
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
          <p>
            {documentIds.length > 1 
              ? `Generating ${documentIds.length} individual summaries + comparison...` 
              : 'Generating comprehensive summary...'}
          </p>
          <p style={{ fontSize: '0.9rem', opacity: 0.7, marginTop: '0.5rem' }}>
            This may take a few moments
          </p>
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
        {summaries.map((summary, index) => (
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
                    <p>⚠️ Failed to generate summary for this document.</p>
                    <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                      The document might be too large or in an unsupported format.
                    </p>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        loadSummaries();
                      }} 
                      className="retry-button-small"
                    >
                      🔄 Retry Summary
                    </button>
                  </div>
                ) : (
                  formatSummaryText(summary.summary)
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {summaries.length === 0 && (
        <div className="no-summaries">
          <p>📂 No documents uploaded yet</p>
          <p>Upload documents to see their summaries here.</p>
          <p style={{ fontSize: '0.9rem', opacity: 0.7, marginTop: '1rem' }}>
            Summaries will be automatically generated when you upload documents.
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentSummary;