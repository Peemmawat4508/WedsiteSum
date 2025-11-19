import React from 'react'
import { useLanguage } from '../contexts/LanguageContext'
import './LanguageSwitcher.css'

function LanguageSwitcher() {
  const { language, toggleLanguage } = useLanguage()

  return (
    <button 
      onClick={toggleLanguage} 
      className="language-switcher"
      title={language === 'en' ? 'เปลี่ยนเป็นภาษาไทย' : 'Switch to English'}
    >
      {language === 'en' ? '🇹🇭 TH' : '🇺🇸 EN'}
    </button>
  )
}

export default LanguageSwitcher

