import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiRequest, setToken, API_URL } from '../utils/auth'
import GoogleAuthButton from './GoogleAuthButton'
import { useLanguage } from '../contexts/LanguageContext'
import { getTranslation } from '../utils/translations'
import LanguageSwitcher from './LanguageSwitcher'
import './Auth.css'

function Login({ setIsAuthenticated }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { language } = useLanguage()
  const t = (key) => getTranslation(key, language)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await fetch(`${API_URL}/token`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      setToken(data.access_token)
      setIsAuthenticated(true)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Google Login logic moved to GoogleAuthButton component

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
          <LanguageSwitcher />
        </div>
        <h1>{t('documentSummarizer')}</h1>
        <h2>{t('signIn')}</h2>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">{t('email')}</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder={t('email')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('password')}</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder={t('password')}
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? t('signIn') + '...' : t('signIn')}
          </button>
        </form>

        <div className="divider">
          <span>OR</span>
        </div>

        {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
          <GoogleAuthButton
            setIsAuthenticated={setIsAuthenticated}
            setError={setError}
            textKey="signInWithGoogle"
          />
        )}

        <p className="auth-footer">
          {t('dontHaveAccount')} <Link to="/register">{t('signUp')}</Link>
        </p>
      </div>
    </div>
  )
}

export default Login

