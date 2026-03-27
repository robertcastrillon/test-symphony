import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import type { User, TokenResponse } from '@/types/api'
import { axiosClient } from '@/services/apiClient'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

function parseJwtExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return typeof payload.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}

function isTokenExpired(token: string): boolean {
  const exp = parseJwtExpiry(token)
  if (exp === null) return true
  return Date.now() / 1000 >= exp
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setUser(null)
  }, [])

  const refreshToken = useCallback(async (): Promise<boolean> => {
    const storedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!storedRefresh) return false

    try {
      const response = await axiosClient.post<TokenResponse>('/auth/refresh', {
        refresh_token: storedRefresh,
      })
      const { access_token, refresh_token } = response.data
      localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
      return true
    } catch {
      logout()
      return false
    }
  }, [logout])

  const fetchCurrentUser = useCallback(async (): Promise<User | null> => {
    try {
      const response = await axiosClient.get<User>('/auth/me')
      return response.data
    } catch {
      return null
    }
  }, [])

  useEffect(() => {
    async function initAuth() {
      setIsLoading(true)
      const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)

      if (!accessToken) {
        setIsLoading(false)
        return
      }

      if (isTokenExpired(accessToken)) {
        const refreshed = await refreshToken()
        if (!refreshed) {
          setIsLoading(false)
          return
        }
      }

      const currentUser = await fetchCurrentUser()
      setUser(currentUser)
      setIsLoading(false)
    }

    void initAuth()
  }, [refreshToken, fetchCurrentUser])

  const login = useCallback(async (email: string, password: string) => {
    const response = await axiosClient.post<TokenResponse>('/auth/login', { email, password })
    const { access_token, refresh_token } = response.data
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)

    const currentUser = await axiosClient.get<User>('/auth/me')
    setUser(currentUser.data)
  }, [])

  const register = useCallback(async (email: string, password: string, name: string) => {
    const response = await axiosClient.post<TokenResponse>('/auth/register', {
      email,
      password,
      name,
    })
    const { access_token, refresh_token } = response.data
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)

    const currentUser = await axiosClient.get<User>('/auth/me')
    setUser(currentUser.data)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        register,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
