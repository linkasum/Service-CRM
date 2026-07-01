import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { ThemeConfig, theme as antTheme } from 'antd'

type ThemeMode = 'light' | 'dark'

interface ThemeContextType {
  mode: ThemeMode
  toggle: () => void
  config: ThemeConfig
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

const lightConfig: ThemeConfig = {
  algorithm: antTheme.defaultAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
}

const darkConfig: ThemeConfig = {
  algorithm: antTheme.darkAlgorithm,
  token: {
    colorPrimary: '#177ddc',
    borderRadius: 6,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<ThemeMode>(
    (localStorage.getItem('theme') as ThemeMode) || 'light'
  )

  useEffect(() => {
    localStorage.setItem('theme', mode)
    // Убираем фон body — фон задаётся через компоненты
    document.body.style.background = 'transparent'
    document.documentElement.style.background = mode === 'dark' ? '#0f0f23' : '#f0f2f5'
  }, [mode])

  const toggle = useCallback(() => {
    setMode(prev => prev === 'light' ? 'dark' : 'light')
  }, [])

  return (
    <ThemeContext.Provider value={{ mode, toggle, config: mode === 'dark' ? darkConfig : lightConfig }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = (): ThemeContextType => {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
