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
  // Guest Mode: Always authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(true)

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route
          path="/"
          element={<Dashboard setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route
          path="/chat"
          element={<Chat setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route
          path="/image-generator"
          element={<ImageGenerator setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route
          path="/grammar-checker"
          element={<GrammarChecker setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  )
}

export default App

