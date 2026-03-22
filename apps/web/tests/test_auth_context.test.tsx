import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { axiosClient } from '@/services/apiClient'

vi.mock('@/services/apiClient', () => ({
  axiosClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { baseURL: 'http://localhost:8000/api/v1' },
  },
}))

const mockAxios = vi.mocked(axiosClient)

function TestConsumer() {
  const auth = useAuth()
  return (
    <div>
      <span data-testid="user">{auth.user ? auth.user.email : 'null'}</span>
      <span data-testid="loading">{auth.isLoading ? 'loading' : 'ready'}</span>
      <span data-testid="authenticated">{auth.isAuthenticated ? 'yes' : 'no'}</span>
      <button
        onClick={() => auth.login('test@example.com', 'password123')}
        data-testid="login-btn"
      >
        Login
      </button>
      <button onClick={() => auth.logout()} data-testid="logout-btn">
        Logout
      </button>
    </div>
  )
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initial state: not authenticated, finishes loading', async () => {
    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready')
    })
    expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
    expect(screen.getByTestId('user')).toHaveTextContent('null')
  })

  it('login updates state to authenticated', async () => {
    const tokenResponse = {
      data: {
        access_token: 'fake-access-token',
        refresh_token: 'fake-refresh-token',
        token_type: 'bearer',
      },
    }
    const userResponse = {
      data: { id: 1, email: 'test@example.com', name: 'Test User' },
    }

    mockAxios.post = vi.fn().mockResolvedValueOnce(tokenResponse)
    mockAxios.get = vi.fn().mockResolvedValueOnce(userResponse)

    renderWithAuth()

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'))

    await act(async () => {
      screen.getByTestId('login-btn').click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
    })

    expect(localStorage.getItem('access_token')).toBe('fake-access-token')
    expect(localStorage.getItem('refresh_token')).toBe('fake-refresh-token')
  })

  it('logout clears state and localStorage', async () => {
    localStorage.setItem('access_token', 'some-token')
    localStorage.setItem('refresh_token', 'some-refresh')

    const userResponse = {
      data: { id: 1, email: 'test@example.com', name: 'Test User' },
    }

    // Mock token as not expired — provide a future exp
    const futurePayload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }))
    localStorage.setItem('access_token', `header.${futurePayload}.sig`)

    mockAxios.get = vi.fn().mockResolvedValueOnce(userResponse)

    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready')
    })

    await act(async () => {
      screen.getByTestId('logout-btn').click()
    })

    expect(screen.getByTestId('authenticated')).toHaveTextContent('no')
    expect(screen.getByTestId('user')).toHaveTextContent('null')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('auto-refreshes expired token on load', async () => {
    // Set an already-expired token
    const expiredPayload = btoa(JSON.stringify({ exp: 1 }))
    localStorage.setItem('access_token', `header.${expiredPayload}.sig`)
    localStorage.setItem('refresh_token', 'valid-refresh-token')

    const refreshResponse = {
      data: {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      },
    }
    const userResponse = {
      data: { id: 1, email: 'test@example.com', name: 'Test User' },
    }

    mockAxios.post = vi.fn().mockResolvedValueOnce(refreshResponse)
    mockAxios.get = vi.fn().mockResolvedValueOnce(userResponse)

    renderWithAuth()

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready')
    })

    expect(localStorage.getItem('access_token')).toBe('new-access-token')
    expect(screen.getByTestId('authenticated')).toHaveTextContent('yes')
  })
})
