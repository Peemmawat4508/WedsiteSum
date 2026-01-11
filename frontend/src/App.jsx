import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Chat from './components/Chat'
import ImageGenerator from './components/ImageGenerator'
import GrammarChecker from './components/GrammarChecker'

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/image-generator" element={<ImageGenerator />} />
        <Route path="/grammar-checker" element={<GrammarChecker />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  )
}

export default App
