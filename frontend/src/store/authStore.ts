import { create } from 'zustand'

export interface UserProfile {
  id: string
  email: string
  role: string  // admin, auditor, developer
  is_active: boolean
}

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: UserProfile | null
  isAuthenticated: boolean
  login: (token: string, refreshToken: string, user: UserProfile) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => {
  // Try to load initial state from localStorage
  const token = localStorage.getItem('token')
  const refreshToken = localStorage.getItem('refreshToken')
  const userStr = localStorage.getItem('user')
  let user: UserProfile | null = null
  
  if (userStr) {
    try {
      user = JSON.parse(userStr)
    } catch {
      localStorage.removeItem('user')
    }
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated: !!token,
    login: (token, refreshToken, user) => {
      localStorage.setItem('token', token)
      localStorage.setItem('refreshToken', refreshToken)
      localStorage.setItem('user', JSON.stringify(user))
      set({ token, refreshToken, user, isAuthenticated: true })
    },
    logout: () => {
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
      set({ token: null, refreshToken: null, user: null, isAuthenticated: false })
    }
  }
})
