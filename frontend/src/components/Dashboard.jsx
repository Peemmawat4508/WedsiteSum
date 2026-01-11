import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, uploadFile } from '../utils/auth'
import { useLanguage } from '../contexts/LanguageContext'
import { getTranslation } from '../utils/translations'
import LanguageSwitcher from './LanguageSwitcher'
import './Dashboard.css'

function Dashboard() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [summarizing, setSummarizing] = useState({})
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState(null)
  const [querying, setQuerying] = useState(false)
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)
  const [exportFormat, setExportFormat] = useState('pdf')
  const [selectedDocsForExport, setSelectedDocsForExport] = useState([])
  const { language } = useLanguage()
  const t = (key) => getTranslation(key, language)
  const navigate = useNavigate()

  useEffect(() => {
    loadDocuments()
  }, [])

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

    // Check file size (Vercel limit 4.5MB, limit to 4MB for safety)
    if (file.size > 4.0 * 1024 * 1024) {
      setError(t('fileTooLarge') || 'File too large. Maximum size is 4MB.')
      return
    }

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
      setError(t('uploadFailed') + ': ' + err.message)
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
      setError(t('summaryFailed') + ': ' + err.message)
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
      const errorMessage = err.message || t('queryFailed')
      if (errorMessage.includes('No document chunks available') || errorMessage.includes('chunks')) {
        setError('Your documents need to be re-uploaded to enable RAG queries. Documents uploaded before the RAG feature was added don\'t have the required data. Please upload your documents again.')
      } else {
        setError(t('queryFailed') + ': ' + errorMessage)
      }
    } finally {
      setQuerying(false)
    }
  }

  const handleDelete = async (documentId) => {
    if (!window.confirm(t('confirmDelete'))) {
      return
    }

    try {
      await apiRequest(`/documents/${documentId}`, {
        method: 'DELETE',
      })
      await loadDocuments()
      setError('')
    } catch (err) {
      setError(t('deleteFailed') + ': ' + err.message)
    }
  }

  const handleExport = async () => {
    if (documents.length === 0) {
      setError(t('noDocumentsYet'))
      return
    }

    setExporting(true)
    setError('')

    try {
      const exportData = {
        format: exportFormat,
        document_ids: selectedDocsForExport.length > 0 ? selectedDocsForExport : null
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '/api')}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Export failed' }))
        throw new Error(error.detail || 'Export failed')
      }

      // Get the file blob
      const blob = await response.blob()

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `summaries_${new Date().toISOString().split('T')[0]}.${exportFormat}`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setShowExportModal(false)
      setSelectedDocsForExport([])
    } catch (err) {
      setError(t('exportFailed') + ': ' + err.message)
    } finally {
      setExporting(false)
    }
  }

  const toggleDocumentForExport = (docId) => {
    setSelectedDocsForExport(prev =>
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>{t('documentSummarizer')}</h1>
          <div className="header-actions">
            <LanguageSwitcher />
            <button onClick={() => navigate('/chat')} className="btn-nav">
              💬 {t('chatWithGPT')}
            </button>
            <button onClick={() => navigate('/image-generator')} className="btn-nav">
              🎨 {t('aiImageGenerator')}
            </button>
            <button onClick={() => navigate('/grammar-checker')} className="btn-nav">
              ✏️ {t('grammarChecker')}
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="upload-section">
          <div className="upload-card">
            <h2>{t('uploadDocument')}</h2>
            <p className="upload-description">{t('uploadDescription')}</p>
            <label className="upload-button">
              <input
                type="file"
                accept=".pdf,.txt,.docx,.doc,.xlsx,.xls,.csv,.md,.markdown,.html,.htm,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.webp"
                onChange={handleFileUpload}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              {uploading ? t('uploading') : t('chooseFile')}
            </label>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {/* RAG Query Section */}
        {documents.length > 0 && (
          <div className="query-section">
            <div className="query-card">
              <h2>{t('askQuestions')}</h2>
              <p className="query-description">{t('queryDescription')}</p>

              <div className="document-selector">
                <label>
                  {t('searchIn')}:
                  <select
                    value={selectedDocumentId || ''}
                    onChange={(e) => setSelectedDocumentId(e.target.value ? parseInt(e.target.value) : null)}
                    className="document-select"
                  >
                    <option value="">{t('allDocuments')}</option>
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
                  placeholder={t('askQuestion')}
                  className="query-input"
                  disabled={querying}
                />
                <button type="submit" className="btn-query" disabled={querying || !query.trim()}>
                  {querying ? t('searching') : t('ask')}
                </button>
              </form>

              {queryResult && (
                <div className="query-result">
                  <div className="result-header">
                    <h4>{t('answer')}:</h4>
                    <span className="result-source">{t('from')}: {queryResult.filename}</span>
                  </div>
                  <div className="result-answer">{queryResult.answer}</div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="documents-section">
          <div className="documents-header">
            <h2>{t('yourDocuments')}</h2>
            {documents.length > 0 && (
              <button
                onClick={() => setShowExportModal(true)}
                className="btn-export"
                title={t('exportSummaries')}
              >
                📥 {t('exportSummaries')}
              </button>
            )}
          </div>
          {loading ? (
            <div className="loading">
              <p>{t('loadingDocuments')}</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <p>{t('noDocumentsYet')}</p>
            </div>
          ) : (
            <div className="documents-grid">
              {documents.map((doc) => (
                <div key={doc.id} className="document-card">
                  <div className="document-header">
                    <h3>{doc.filename}</h3>
                    <div className="document-header-right">
                      <span className="document-date">{formatDate(doc.uploaded_at)}</span>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="btn-delete"
                        title={t('delete')}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  {doc.summary ? (
                    <div className="summary-section">
                      <h4>{t('summary')}:</h4>
                      <p className="summary-text">{doc.summary}</p>
                    </div>
                  ) : (
                    <div className="no-summary">
                      <p>{t('noSummaryYet')}</p>
                      <button
                        onClick={() => handleSummarize(doc.id)}
                        disabled={summarizing[doc.id]}
                        className="btn-summarize"
                      >
                        {summarizing[doc.id] ? t('summarizing') : t('generateSummary')}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Export Modal */}
        {showExportModal && (
          <div className="modal-overlay" onClick={() => !exporting && setShowExportModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>{t('exportSummaries')}</h3>
                <button
                  className="modal-close"
                  onClick={() => setShowExportModal(false)}
                  disabled={exporting}
                >
                  ×
                </button>
              </div>

              <div className="modal-body">
                <div className="form-group">
                  <label>{t('exportFormat')}</label>
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="export-select"
                    disabled={exporting}
                  >
                    <option value="pdf">{t('pdfDocument')}</option>
                    <option value="txt">{t('textFile')}</option>
                    <option value="json">{t('jsonData')}</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>{t('exportOptions')}</label>
                  <div className="export-options">
                    <label className="export-option-item">
                      <input
                        type="radio"
                        name="exportScope"
                        checked={selectedDocsForExport.length === 0}
                        onChange={() => setSelectedDocsForExport([])}
                        disabled={exporting}
                      />
                      <span>{t('exportAll')} ({documents.length})</span>
                    </label>
                    <label className="export-option-item">
                      <input
                        type="radio"
                        name="exportScope"
                        checked={selectedDocsForExport.length > 0}
                        onChange={() => setSelectedDocsForExport(documents.map(d => d.id))}
                        disabled={exporting}
                      />
                      <span>{t('selectSpecific')}</span>
                    </label>
                  </div>
                </div>

                {selectedDocsForExport.length > 0 && (
                  <div className="form-group">
                    <label>{t('selectedDocuments')} ({selectedDocsForExport.length} {t('selected')})</label>
                    <div className="export-docs-list">
                      {documents.map(doc => (
                        <label key={doc.id} className="export-doc-item">
                          <input
                            type="checkbox"
                            checked={selectedDocsForExport.includes(doc.id)}
                            onChange={() => toggleDocumentForExport(doc.id)}
                            disabled={exporting}
                          />
                          <span>{doc.filename}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button
                  className="btn-cancel"
                  onClick={() => setShowExportModal(false)}
                  disabled={exporting}
                >
                  {t('cancel')}
                </button>
                <button
                  className="btn-export-confirm"
                  onClick={handleExport}
                  disabled={exporting || documents.length === 0}
                >
                  {exporting ? t('exporting') : t('export')}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default Dashboard

