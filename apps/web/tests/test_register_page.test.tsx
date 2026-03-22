import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthContext } from '@/context/AuthContext'
import { RegisterPage } from '@/pages/RegisterPage'
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
  register: (email: string, password: string, name: string) => Promise<void>
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

function renderRegisterPage(contextValue = makeAuthContext()) {
  return render(
    <AuthContext.Provider value={contextValue}>
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form fields', () => {
    renderRegisterPage()
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      expect(screen.getByText(/valid email/i)).toBeInTheDocument()
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('shows error when passwords do not match', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await user.type(screen.getByLabelText(/full name/i), 'Test User')
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'differentpassword')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('redirects to dashboard on successful registration', async () => {
    const user = userEvent.setup()
    renderRegisterPage()

    await user.type(screen.getByLabelText(/full name/i), 'Test User')
    await user.type(screen.getByLabelText(/email address/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true })
    })
  })

  it('shows server error on registration failure', async () => {
    const user = userEvent.setup()
    const registerFn = vi.fn().mockRejectedValue(new Error('Email already in use'))
    renderRegisterPage(makeAuthContext({ register: registerFn }))

    await user.type(screen.getByLabelText(/full name/i), 'Test User')
    await user.type(screen.getByLabelText(/email address/i), 'taken@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/registration failed/i)
    })
  })

  it('has a link to the login page', () => {
    renderRegisterPage()
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login')
  })
})
