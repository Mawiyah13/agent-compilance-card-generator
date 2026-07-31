import React, { useState } from 'react'
import { apiRequest } from '../utils/api'
import { useAuthStore } from '../store/authStore'
import { useNavigationStore } from '../store/navigationStore'
import { Lock, Mail, Shield, AlertTriangle, CheckCircle2 } from 'lucide-react'

export const Login: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('developer')  // developer, auditor, admin
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const { login } = useAuthStore()
  const { navigateTo } = useNavigationStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      if (isRegister) {
        // Register flow
        const response = await apiRequest('/auth/register', {
          method: 'POST',
          json: { email, password, role }
        })
        
        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || 'Registration failed')
        }
        
        // Auto sign in after registration
        setIsRegister(false)
        setSuccess('Account created successfully. Please login.')
      } else {
        // Login flow
        const formData = new URLSearchParams()
        formData.append('username', email)
        formData.append('password', password)

        const response = await apiRequest('/auth/login', {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || 'Login failed')
        }

        const tokenData = await response.json()

        // Get user profile via shared API helper so auth header handling stays consistent.
        const profileResponse = await apiRequest('/auth/me', {
          headers: {
            Authorization: `Bearer ${tokenData.access_token}`
          }
        })

        if (!profileResponse.ok) {
          const data = await profileResponse.json().catch(() => null)
          throw new Error(data?.detail || 'Failed to load user profile')
        }

        const userProfile = await profileResponse.json()
        login(tokenData.access_token, tokenData.refresh_token, userProfile)
        navigateTo('dashboard')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-card-dark border border-border-dark rounded-xl p-8 shadow-2xl relative overflow-hidden">
        {/* Border accent line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-brand-accent"></div>
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-12 h-12 rounded-lg bg-brand-accent flex items-center justify-center mb-3">
            <Shield className="text-bg-dark" size={24} />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-brand-primary">
            {isRegister ? 'Create compliance workspace' : 'AI Governance Console'}
          </h2>
          <p className="text-sm text-brand-secondary mt-1">
            {isRegister ? 'Register your auditor or developer profile' : 'Sign in to access compliance logs'}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-brand-critical/10 border border-brand-critical/30 text-brand-primary flex items-start gap-3 text-sm">
            <AlertTriangle className="text-brand-critical shrink-0 mt-0.5" size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Success Alert */}
        {success && (
          <div className="mb-6 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-brand-primary flex items-start gap-3 text-sm">
            <CheckCircle2 className="text-emerald-400 shrink-0 mt-0.5" size={16} />
            <span>{success}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-brand-secondary uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 text-brand-muted" size={18} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="auditor@company.internal"
                className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg py-2.5 pl-10 pr-4 text-sm text-brand-primary focus:border-brand-accent focus:ring-1 focus:ring-brand-accent transition-all outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-brand-secondary uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-brand-muted" size={18} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg py-2.5 pl-10 pr-4 text-sm text-brand-primary focus:border-brand-accent focus:ring-1 focus:ring-brand-accent transition-all outline-none"
              />
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-semibold text-brand-secondary uppercase tracking-wider mb-2">
                Workspace Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-[#1e1e1e] border border-border-dark rounded-lg py-2.5 px-3 text-sm text-brand-primary focus:border-brand-accent focus:ring-1 focus:ring-brand-accent transition-all outline-none"
              >
                <option value="developer">Developer</option>
                <option value="auditor">Auditor</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-accent hover:bg-brand-hover text-bg-dark font-bold text-sm py-2.5 rounded-lg transition-all cursor-pointer flex items-center justify-center disabled:opacity-50"
          >
            {loading ? 'Processing transaction...' : isRegister ? 'Initialize Account' : 'Authenticate Credentials'}
          </button>
        </form>

        {/* Footer link */}
        <div className="text-center mt-6">
          <button
            onClick={() => {
              setIsRegister(!isRegister)
              setError(null)
              setSuccess(null)
            }}
            className="text-xs text-brand-muted hover:text-brand-accent transition-all"
          >
            {isRegister ? 'Already registered? Login to existing profile' : 'Create new administrator or auditor profile'}
          </button>
        </div>
      </div>
    </div>
  )
}
