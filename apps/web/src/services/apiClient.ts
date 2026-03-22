import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { TokenResponse } from '@/types/api'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach Bearer token if available
axiosClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else if (token) {
      resolve(token)
    }
  })
  failedQueue = []
}

// Response interceptor: on 401, attempt token refresh once then retry
axiosClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            resolve(axiosClient(originalRequest))
          },
          reject,
        })
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    const refreshTokenValue = localStorage.getItem(REFRESH_TOKEN_KEY)

    if (!refreshTokenValue) {
      processQueue(error, null)
      isRefreshing = false
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      window.location.href = '/login'
      return Promise.reject(error)
    }

    try {
      const response = await axios.post<TokenResponse>(
        `${axiosClient.defaults.baseURL}/auth/refresh`,
        { refresh_token: refreshTokenValue },
        { headers: { 'Content-Type': 'application/json' } },
      )

      const { access_token, refresh_token } = response.data
      localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)

      processQueue(null, access_token)

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${access_token}`
      }
      return axiosClient(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)
