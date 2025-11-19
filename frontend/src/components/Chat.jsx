import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, removeToken } from '../utils/auth'
import { useLanguage } from '../contexts/LanguageContext'
import { getTranslation } from '../utils/translations'
import LanguageSwitcher from './LanguageSwitcher'
import './Chat.css'

function Chat({ setIsAuthenticated }) {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const messagesEndRef = useRef(null)
  const { language } = useLanguage()
  const t = (key) => getTranslation(key, language)
  const navigate = useNavigate()

  useEffect(() => {
    loadUser()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadUser = async () => {
    try {
      const userData = await apiRequest('/me')
      setUser(userData)
    } catch (err) {
      setError('Failed to load user data')
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setError('')
    setLoading(true)

    // Add user message to chat
    const newUserMessage = { role: 'user', content: userMessage }
    setMessages(prev => [...prev, newUserMessage])

    try {
      // Prepare conversation history
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      // Get response from API
      const response = await apiRequest('/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage,
          conversation_history: conversationHistory
        }),
      })

      // Add assistant response to chat
      setMessages(prev => [...prev, { role: 'assistant', content: response.message }])
    } catch (err) {
      setError(t('chatFailed') + ': ' + err.message)
      // Remove the user message if there was an error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = () => {
    if (window.confirm(t('confirmClearChat'))) {
      setMessages([])
      setError('')
    }
  }

  const handleLogout = () => {
    removeToken()
    setIsAuthenticated(false)
    navigate('/login')
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="header-content">
          <h1>💬 {t('chatWithGPT')}</h1>
          <div className="header-actions">
            <LanguageSwitcher />
            <button onClick={() => navigate('/')} className="btn-nav">
              📄 {t('yourDocuments')}
            </button>
            <button onClick={() => navigate('/image-generator')} className="btn-nav">
              🎨 {t('aiImageGenerator')}
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

      <div className="chat-main">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-welcome">
              <h2>👋 {t('chatWelcome')}</h2>
              <p>{t('chatHint')}</p>
              <p className="chat-hint">{t('chatDescription')}</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">
                  <div className="message-role">
                    {msg.role === 'user' ? `👤 ${t('you')}` : `🤖 ${t('assistant')}`}
                  </div>
                  <div className="message-text">{msg.content}</div>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="message-role">🤖 {t('assistant')}</div>
                <div className="message-text typing">{t('thinking')}</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="chat-input-container">
          <div className="chat-actions">
            <button onClick={handleClearChat} className="btn-clear" disabled={messages.length === 0}>
              🗑️ {t('clearChat')}
            </button>
          </div>
          <form onSubmit={handleSend} className="chat-form">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={t('typeMessage')}
              className="chat-input"
              disabled={loading}
              autoFocus
            />
            <button type="submit" className="btn-send" disabled={loading || !inputMessage.trim()}>
              {loading ? '⏳' : '📤'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Chat

