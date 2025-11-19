import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useGoogleLogin } from '@react-oauth/google'
import { apiRequest, setToken } from '../utils/auth'
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

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
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

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        // Get user info from Google
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
          headers: {
            Authorization: `Bearer ${tokenResponse.access_token}`,
          },
        })
        
        if (!userInfoResponse.ok) {
          throw new Error('Failed to fetch user info from Google')
        }
        
        const userInfo = await userInfoResponse.json()
        
        // Send to backend
        const result = await apiRequest('/google-auth', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: userInfo.email,
            name: userInfo.name || '',
            google_id: userInfo.id,
          }),
        })

        setToken(result.access_token)
        setIsAuthenticated(true)
        navigate('/')
      } catch (err) {
        setError('Google signup failed: ' + err.message)
      }
    },
    onError: () => {
      setError('Google signup failed')
    },
  })

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

        <button onClick={googleLogin} className="btn-google">
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          {t('signInWithGoogle')}
        </button>

        <p className="auth-footer">
          {t('alreadyHaveAccount')} <Link to="/login">{t('signIn')}</Link>
        </p>
      </div>
    </div>
  )
}

export default Register

