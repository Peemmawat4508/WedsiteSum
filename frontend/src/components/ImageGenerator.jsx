import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, removeToken } from '../utils/auth'
import { useLanguage } from '../contexts/LanguageContext'
import { getTranslation } from '../utils/translations'
import LanguageSwitcher from './LanguageSwitcher'
import './ImageGenerator.css'

function ImageGenerator({ setIsAuthenticated }) {
  const [prompt, setPrompt] = useState('')
  const [size, setSize] = useState('1024x1024')
  const [quality, setQuality] = useState('standard')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [generatedImage, setGeneratedImage] = useState(null)
  const [user, setUser] = useState(null)
  const [history, setHistory] = useState([])
  const { language } = useLanguage()
  const t = (key) => getTranslation(key, language)
  const navigate = useNavigate()

  React.useEffect(() => {
    loadUser()
  }, [])

  const loadUser = async () => {
    try {
      const userData = await apiRequest('/me')
      setUser(userData)
    } catch (err) {
      setError('Failed to load user data')
    }
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!prompt.trim() || loading) return

    setLoading(true)
    setError('')
    setGeneratedImage(null)

    try {
      const result = await apiRequest('/generate-image', {
        method: 'POST',
        body: JSON.stringify({
          prompt: prompt,
          size: size,
          quality: quality,
        }),
      })

      setGeneratedImage(result)
      setHistory(prev => [...prev, {
        prompt: prompt,
        image_url: result.image_url,
        size: result.size,
        timestamp: new Date().toISOString()
      }])
      setPrompt('')
    } catch (err) {
      setError(t('imageGenerationFailed') + ': ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = () => {
    if (window.confirm(t('confirmClearHistory'))) {
      setHistory([])
      setGeneratedImage(null)
    }
  }

  const handleDownload = (imageUrl, prompt) => {
    fetch(imageUrl)
      .then(response => response.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `image-${Date.now()}.png`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      })
      .catch(err => {
        setError('Failed to download image')
      })
  }

  const handleLogout = () => {
    removeToken()
    setIsAuthenticated(false)
    navigate('/login')
  }

  return (
    <div className="image-generator">
      <header className="image-generator-header">
        <div className="header-content">
          <h1>🎨 {t('aiImageGenerator')}</h1>
          <div className="header-actions">
            <LanguageSwitcher />
            <button onClick={() => navigate('/')} className="btn-nav">
              📄 {t('yourDocuments')}
            </button>
            <button onClick={() => navigate('/chat')} className="btn-nav">
              💬 {t('chatWithGPT')}
            </button>
            <button onClick={() => navigate('/grammar-checker')} className="btn-nav">
              ✏️ {t('grammarChecker')}
            </button>
            {user && <span className="user-name">{t('welcome')}, {user.full_name || user.email}</span>}
            <button onClick={handleLogout} className="btn-logout">
              {t('logout')}
            </button>
          </div>
        </div>
      </header>

      <main className="image-generator-main">
        <div className="generator-section">
          <div className="generator-card">
            <h2>{t('createImages')}</h2>
            <p className="generator-description">
              {t('imageDescription')}
            </p>

            <form onSubmit={handleGenerate} className="generator-form">
              <div className="form-group">
                <label htmlFor="prompt">{t('imagePrompt')}</label>
                <textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={t('imagePromptPlaceholder')}
                  className="prompt-input"
                  rows="4"
                  disabled={loading}
                  required
                />
                <small className="hint">{t('imagePromptHint')}</small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="size">{t('imageSize')}</label>
                  <select
                    id="size"
                    value={size}
                    onChange={(e) => setSize(e.target.value)}
                    className="size-select"
                    disabled={loading}
                  >
                    <option value="1024x1024">Square (1024x1024)</option>
                    <option value="1792x1024">Landscape (1792x1024)</option>
                    <option value="1024x1792">Portrait (1024x1792)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="quality">{t('quality')}</label>
                  <select
                    id="quality"
                    value={quality}
                    onChange={(e) => setQuality(e.target.value)}
                    className="quality-select"
                    disabled={loading}
                  >
                    <option value="standard">{t('standard')}</option>
                    <option value="hd">{t('hd')}</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="btn-generate"
                disabled={loading || !prompt.trim()}
              >
                {loading ? `🎨 ${t('generating')}` : `✨ ${t('generateImage')}`}
              </button>
            </form>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {generatedImage && (
          <div className="result-section">
            <div className="result-card">
              <div className="result-header">
                <h3>{t('generatedImage')}</h3>
                <button
                  onClick={() => handleDownload(generatedImage.image_url, generatedImage.prompt)}
                  className="btn-download"
                >
                  💾 {t('download')}
                </button>
              </div>
              <div className="image-container">
                <img
                  src={generatedImage.image_url}
                  alt={generatedImage.prompt}
                  className="generated-image"
                />
              </div>
              <div className="image-info">
                <p><strong>Prompt:</strong> {generatedImage.prompt}</p>
                <p><strong>Size:</strong> {generatedImage.size}</p>
              </div>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="history-section">
            <div className="history-header">
              <h2>{t('generationHistory')}</h2>
              <button onClick={handleClearHistory} className="btn-clear">
                🗑️ {t('clearHistory')}
              </button>
            </div>
            <div className="history-grid">
              {history.map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-image-container">
                    <img
                      src={item.image_url}
                      alt={item.prompt}
                      className="history-image"
                    />
                    <button
                      onClick={() => handleDownload(item.image_url, item.prompt)}
                      className="btn-download-small"
                      title="Download"
                    >
                      💾
                    </button>
                  </div>
                  <p className="history-prompt" title={item.prompt}>
                    {item.prompt.length > 50 ? item.prompt.substring(0, 50) + '...' : item.prompt}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default ImageGenerator

