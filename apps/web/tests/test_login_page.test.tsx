import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthContext } from '@/context/AuthContext'
import { LoginPage } from '@/pages/LoginPage'
import type { User } from '@/types/api'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function makeAuthContext(overrides: Partial<{
  login: (email: string, password: string) => Promise<void>
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}> = {}) {
  return {
    user: null,
    isLoading: false,
    isAuthenticated: false,
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
    refreshToken: vi.fn().mockResolvedValue(true),
    ...overrides,
  }
}

function renderLoginPage(contextValue = makeAuthContext()) {
  return render(
    <AuthContext.Provider value={contextValue}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<div>Register page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders email and password fields', () => {
    renderLoginPage()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument()
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('shows error on invalid credentials', async () => {
    const user = userEvent.setup()
    const loginFn = vi.fn().mockRejectedValue(new Error('Invalid credentials'))
    renderLoginPage(makeAuthContext({ login: loginFn }))

    await user.type(screen.getByLabelText(/email address/i), 'bad@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid email or password/i)
    })
  })

  it('redirects to dashboard on successful login', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true })
    })
  })

  it('has a link to the register page', () => {
    renderLoginPage()
    expect(screen.getByRole('link', { name: /create one/i })).toHaveAttribute('href', '/register')
  })
})
