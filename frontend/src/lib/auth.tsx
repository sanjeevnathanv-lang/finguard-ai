import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  UserProfile,
  UserRole,
  loginApi,
  logoutApi,
  getCurrentUserApi,
  getAuthToken,
  clearAuthToken,
} from './api'

interface AuthContextType {
  user: UserProfile | null
  role: UserRole
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  quickSwitchUser: (targetRole: UserRole) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Default credentials for the seeded accounts in local development
const SEEDED_CREDENTIALS: Record<UserRole, { u: string; p: string }> = {
  ADMIN: { u: 'admin', p: 'FinGuard@Admin2026!' },
  ANALYST: { u: 'analyst', p: 'FinGuard@Analyst2026!' },
  VIEWER: { u: 'viewer', p: 'FinGuard@Viewer2026!' },
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const refreshUser = async () => {
    const token = getAuthToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const profile = await getCurrentUserApi()
      setUser(profile)
    } catch (err) {
      console.warn('Session expired or invalid token:', err)
      clearAuthToken()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial check: if no token exists, log in as default Analyst for zero-friction local development
    const token = getAuthToken()
    if (!token) {
      quickSwitchUser('ANALYST')
    } else {
      refreshUser()
    }
  }, [])

  const login = async (username: string, password: string) => {
    setIsLoading(true)
    try {
      const data = await loginApi(username, password)
      setUser(data.user)
    } finally {
      setIsLoading(false)
    }
  }

  const quickSwitchUser = async (targetRole: UserRole) => {
    setIsLoading(true)
    try {
      const creds = SEEDED_CREDENTIALS[targetRole]
      const data = await loginApi(creds.u, creds.p)
      setUser(data.user)
    } catch (err) {
      console.error(`Failed to authenticate as ${targetRole}:`, err)
      clearAuthToken()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await logoutApi()
    } catch {
      clearAuthToken()
    } finally {
      setUser(null)
      setIsLoading(false)
    }
  }

  const role: UserRole = user?.role || 'VIEWER'
  const isAuthenticated = !!user

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated,
        isLoading,
        login,
        quickSwitchUser,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
