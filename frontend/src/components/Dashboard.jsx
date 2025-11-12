import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, uploadFile, removeToken } from '../utils/auth'
import './Dashboard.css'

function Dashboard({ setIsAuthenticated }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [summarizing, setSummarizing] = useState({})
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState(null)
  const [querying, setQuerying] = useState(false)
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadUser()
    loadDocuments()
  }, [])

  const loadUser = async () => {
    try {
      const userData = await apiRequest('/me')
      setUser(userData)
    } catch (err) {
      setError('Failed to load user data')
    }
  }

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const docs = await apiRequest('/documents')
      setDocuments(docs)
    } catch (err) {
      setError('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.name.match(/\.(pdf|txt)$/i)) {
      setError('Please upload a PDF or TXT file')
      return
    }

    setUploading(true)
    setError('')

    try {
      const result = await uploadFile(file)
      await loadDocuments()
      setError('')
    } catch (err) {
      setError('Upload failed: ' + err.message)
    } finally {
      setUploading(false)
      e.target.value = '' // Reset file input
    }
  }

  const handleSummarize = async (documentId) => {
    setSummarizing({ ...summarizing, [documentId]: true })
    setError('')

    try {
      const result = await apiRequest(`/summarize/${documentId}`, {
        method: 'POST',
      })
      await loadDocuments()
    } catch (err) {
      setError('Summarization failed: ' + err.message)
    } finally {
      setSummarizing({ ...summarizing, [documentId]: false })
    }
  }

  const handleQuery = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setQuerying(true)
    setError('')
    setQueryResult(null)

    try {
      const result = await apiRequest('/query', {
        method: 'POST',
        body: JSON.stringify({
          query: query,
          document_id: selectedDocumentId || null,
        }),
      })

      setQueryResult(result)
      setQuery('')
    } catch (err) {
      const errorMessage = err.message || 'Query failed'
      if (errorMessage.includes('No document chunks available') || errorMessage.includes('chunks')) {
        setError('Your documents need to be re-uploaded to enable RAG queries. Documents uploaded before the RAG feature was added don\'t have the required data. Please upload your documents again.')
      } else {
        setError('Query failed: ' + errorMessage)
      }
    } finally {
      setQuerying(false)
    }
  }

  const handleLogout = () => {
    removeToken()
    setIsAuthenticated(false)
    navigate('/login')
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Document Summarizer</h1>
          <div className="header-actions">
            {user && <span className="user-name">Welcome, {user.full_name || user.email}</span>}
            <button onClick={handleLogout} className="btn-logout">
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="upload-section">
          <div className="upload-card">
            <h2>Upload Document</h2>
            <p className="upload-description">Upload PDF or TXT files to get AI-powered summaries</p>
            <label className="upload-button">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileUpload}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              {uploading ? 'Uploading...' : 'Choose File'}
            </label>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {/* RAG Query Section */}
        {documents.length > 0 && (
          <div className="query-section">
            <div className="query-card">
              <h2>Ask Questions About Your Documents</h2>
              <p className="query-description">Query your documents using AI-powered RAG (Retrieval-Augmented Generation)</p>
              
              <div className="document-selector">
                <label>
                  Search in:
                  <select 
                    value={selectedDocumentId || ''} 
                    onChange={(e) => setSelectedDocumentId(e.target.value ? parseInt(e.target.value) : null)}
                    className="document-select"
                  >
                    <option value="">All Documents</option>
                    {documents.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.filename}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <form onSubmit={handleQuery} className="query-form">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about your documents..."
                  className="query-input"
                  disabled={querying}
                />
                <button type="submit" className="btn-query" disabled={querying || !query.trim()}>
                  {querying ? 'Searching...' : 'Ask'}
                </button>
              </form>

              {queryResult && (
                <div className="query-result">
                  <div className="result-header">
                    <h4>Answer:</h4>
                    <span className="result-source">From: {queryResult.filename}</span>
                  </div>
                  <div className="result-answer">{queryResult.answer}</div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="documents-section">
          <h2>Your Documents</h2>
          {loading ? (
            <div className="loading">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <p>No documents yet. Upload a file to get started!</p>
            </div>
          ) : (
            <div className="documents-grid">
              {documents.map((doc) => (
                <div key={doc.id} className="document-card">
                  <div className="document-header">
                    <h3>{doc.filename}</h3>
                    <span className="document-date">{formatDate(doc.uploaded_at)}</span>
                  </div>
                  {doc.summary ? (
                    <div className="summary-section">
                      <h4>Summary:</h4>
                      <p className="summary-text">{doc.summary}</p>
                    </div>
                  ) : (
                    <div className="no-summary">
                      <p>No summary yet</p>
                      <button
                        onClick={() => handleSummarize(doc.id)}
                        disabled={summarizing[doc.id]}
                        className="btn-summarize"
                      >
                        {summarizing[doc.id] ? 'Summarizing...' : 'Generate Summary'}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default Dashboard

