import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/Dashboard'
import Chat from './components/Chat'
import ImageGenerator from './components/ImageGenerator'
import GrammarChecker from './components/GrammarChecker'
import { getToken } from './utils/auth'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    setIsAuthenticated(!!token)
    setLoading(false)
  }, [])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route 
          path="/login" 
          element={!isAuthenticated ? <Login setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/register" 
          element={!isAuthenticated ? <Register setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/" 
          element={isAuthenticated ? <Dashboard setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/login" />} 
        />
        <Route 
          path="/chat" 
          element={isAuthenticated ? <Chat setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/login" />} 
        />
        <Route 
          path="/image-generator" 
          element={isAuthenticated ? <ImageGenerator setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/login" />} 
        />
        <Route 
          path="/grammar-checker" 
          element={isAuthenticated ? <GrammarChecker setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/login" />} 
        />
      </Routes>
    </Router>
  )
}

export default App

