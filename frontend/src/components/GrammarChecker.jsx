import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest } from '../utils/auth'
import { useLanguage } from '../contexts/LanguageContext'
import { getTranslation } from '../utils/translations'
import LanguageSwitcher from './LanguageSwitcher'
import './GrammarChecker.css'

function GrammarChecker() {
  const [text, setText] = useState('')
  const [correctedText, setCorrectedText] = useState('')
  const [corrections, setCorrections] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [hasErrors, setHasErrors] = useState(false)
  const { language } = useLanguage()
  const t = (key) => getTranslation(key, language)
  const navigate = useNavigate()

  const handleCheck = async (e) => {
    e.preventDefault()
    if (!text.trim() || loading) return

    setLoading(true)
    setError('')
    setCorrectedText('')
    setCorrections([])
    setHasErrors(false)

    try {
      const result = await apiRequest('/grammar-check', {
        method: 'POST',
        body: JSON.stringify({
          text: text.trim(),
        }),
      })

      setCorrectedText(result.corrected_text)
      setCorrections(result.corrections || [])
      setHasErrors(result.has_errors || false)
    } catch (err) {
      setError(t('grammarCheckFailed') + ': ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (correctedText) {
      navigator.clipboard.writeText(correctedText)
      // Show temporary feedback
      const originalError = error
      setError('')
      setTimeout(() => {
        setError(t('textCopied'))
        setTimeout(() => {
          setError(originalError)
        }, 2000)
      }, 100)
    }
  }

  const handleClear = () => {
    setText('')
    setCorrectedText('')
    setCorrections([])
    setError('')
    setHasErrors(false)
  }

  return (
    <div className="grammar-checker">
      <header className="grammar-checker-header">
        <div className="header-content">
          <h1>✏️ {t('grammarChecker')}</h1>
          <div className="header-actions">
            <LanguageSwitcher />
            <button onClick={() => navigate('/')} className="btn-nav">
              📄 {t('yourDocuments')}
            </button>
            <button onClick={() => navigate('/chat')} className="btn-nav">
              💬 {t('chatWithGPT')}
            </button>
            <button onClick={() => navigate('/image-generator')} className="btn-nav">
              🎨 {t('aiImageGenerator')}
            </button>
          </div>
        </div>
      </header>

      <main className="grammar-checker-main">
        <div className="grammar-section">
          <div className="grammar-card">
            <h2>{t('checkGrammar')}</h2>
            <p className="grammar-description">
              {t('grammarDescription')}
            </p>

            <form onSubmit={handleCheck} className="grammar-form">
              <div className="form-group">
                <label htmlFor="text">{t('enterText')}</label>
                <textarea
                  id="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={t('enterText')}
                  className="grammar-input"
                  rows="8"
                  disabled={loading}
                  required
                />
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="btn-check"
                  disabled={loading || !text.trim()}
                >
                  {loading ? `⏳ ${t('checking')}` : `✅ ${t('checkGrammar')}`}
                </button>
                <button
                  type="button"
                  onClick={handleClear}
                  className="btn-clear"
                  disabled={loading}
                >
                  🗑️ {t('clearText')}
                </button>
              </div>
            </form>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {correctedText && (
          <div className="result-section">
            <div className="result-card">
              <div className="result-header">
                <h3>{t('correctedText')}</h3>
                <button
                  onClick={handleCopy}
                  className="btn-copy"
                  title={t('copyCorrected')}
                >
                  📋 {t('copyCorrected')}
                </button>
              </div>
              <div className="corrected-text-container">
                <p className="corrected-text">{correctedText}</p>
              </div>

              {hasErrors && corrections.length > 0 && (
                <div className="corrections-section">
                  <h4>{t('corrections')}:</h4>
                  <div className="corrections-list">
                    {corrections.map((correction, index) => (
                      <div key={index} className="correction-item">
                        <div className="correction-row">
                          <span className="correction-label">{t('original')}:</span>
                          <span className="correction-original">{correction.original}</span>
                        </div>
                        <div className="correction-row">
                          <span className="correction-label">{t('corrected')}:</span>
                          <span className="correction-corrected">{correction.corrected}</span>
                        </div>
                        {correction.explanation && (
                          <div className="correction-explanation">
                            <span className="correction-label">{t('explanation')}:</span>
                            <span>{correction.explanation}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!hasErrors && (
                <div className="no-errors-message">
                  <p>✅ {t('noErrors')}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default GrammarChecker
