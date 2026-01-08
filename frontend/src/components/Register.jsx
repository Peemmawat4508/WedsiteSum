import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiRequest, setToken, API_URL } from '../utils/auth'
import GoogleAuthButton from './GoogleAuthButton'
import { useLanguage } from '../contexts/LanguageContext'
import { getTranslation } from '../utils/translations'
import LanguageSwitcher from './LanguageSwitcher'
import './Auth.css'

function Register({ setIsAuthenticated }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
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
      const result = await apiRequest('/register', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      })

      // Auto-login after registration
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const loginResponse = await fetch(`${API_URL}/token`, {
        method: 'POST',
        body: formData,
      })

      const loginData = await loginResponse.json()

      if (!loginResponse.ok) {
        throw new Error(loginData.detail || 'Auto-login failed')
      }

      setToken(loginData.access_token)
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
        <h2>{t('register')}</h2>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="fullName">{t('fullName')}</label>
            <input
              type="text"
              id="fullName"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder={t('fullName')}
            />
          </div>

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
              minLength="6"
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? t('signUp') + '...' : t('signUp')}
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
          {t('alreadyHaveAccount')} <Link to="/login">{t('signIn')}</Link>
        </p>
      </div>
    </div>
  )
}

export default Register

