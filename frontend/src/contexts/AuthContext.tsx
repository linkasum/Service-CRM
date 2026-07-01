/**
 * Контекст авторизации — централизованное управление состоянием пользователя
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import { login as apiLogin, getMe } from '../api'
import api from '../api'

interface UserInfo {
  id: number
  username: string
  full_name?: string
  role_id?: number
  role_name?: string
  email?: string | null
  phone?: string | null
  salary_config_id?: number | null
  salary_config_name?: string | null
  salary_formula?: string | null
  salary_config_type?: string | null
  salary_fixed_amount?: number | null
  salary_period?: string | null
  telegram_chat_id?: number | null
  created_at?: string
  permissions: string[]
  is_active: boolean
}

interface AuthContextType {
  user: UserInfo | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  hasPermission: (permission: string) => boolean
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    message.success('Вы вышли из системы')
  }, [])

  const refreshUser = useCallback(async () => {
    if (!token) return
    try {
      const userData = await getMe()
      try {
        const permRes = await api.get('/permissions/my')
        userData.permissions = permRes.data.permissions || userData.permissions
      } catch {}
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      console.error('Ошибка загрузки профиля:', error)
      logout()
    }
  }, [token, logout])

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await apiLogin(username, password)
      localStorage.setItem('token', response.access_token)
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token)
      }
      const userData = response.user
      try {
        const permRes = await api.get('/permissions/my')
        userData.permissions = permRes.data.permissions || userData.permissions
      } catch {}
      localStorage.setItem('user', JSON.stringify(userData))
      setToken(response.access_token)
      setUser(userData)
      message.success(`Добро пожаловать, ${response.user.username}!`)
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Ошибка входа'
      message.error(errorMsg)
      throw error
    }
  }, [])

  const hasPermission = useCallback((permission: string): boolean => {
    if (!user) return false
    // Админ всегда имеет все права
    if (user.role_name === 'admin') return true
    return user.permissions.includes(permission)
  }, [user])

  useEffect(() => {
    if (token && !user) {
      refreshUser()
    }
  }, [token, user, refreshUser])

  return (
    <AuthContext.Provider value={{
      user,
      token,
      isAuthenticated: !!token && !!user,
      login,
      logout,
      hasPermission,
      refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth должен использоваться внутри AuthProvider')
  }
  return context
}

export default AuthContext
