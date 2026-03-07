import { useState } from 'react'
import { SignUp as ClerkSignUp } from '@clerk/clerk-react'
import { Navigate, Link, useNavigate } from 'react-router-dom'
import { isAuthEnabled } from '../auth/ClerkProviderWrapper'
import { useLocalAuth } from '../auth/LocalAuthContext'
import Icon from '../components/Icon'

export default function SignUp() {
  if (isAuthEnabled()) {
    return <ClerkSignUpPage />
  }
  return <LocalSignUpPage />
}

function ClerkSignUpPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 px-4">
      <AuthBranding />
      <ClerkSignUp
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
        appearance={{
          elements: {
            rootBox: 'mx-auto',
            card: 'bg-gray-900/80 backdrop-blur-xl border border-gray-800/60 shadow-2xl',
          },
        }}
      />
    </div>
  )
}

function LocalSignUpPage() {
  const { user, signIn } = useLocalAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  if (user) return <Navigate to="/dashboard" replace />

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedEmail = email.trim()
    if (!trimmedEmail) { setError('Email is required'); return }
    if (!trimmedEmail.includes('@')) { setError('Enter a valid email'); return }
    signIn(trimmedEmail, name.trim() || undefined)
    navigate('/dashboard', { replace: true })
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 px-4">
      <AuthBranding />

      <div className="w-full max-w-sm">
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Create account</h2>
          <p className="text-sm text-gray-500 mb-5">Get started with Navil</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:border-indigo-500 focus:outline-none"
                placeholder="Your name"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => { setEmail(e.target.value); setError('') }}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:border-indigo-500 focus:outline-none"
                placeholder="you@example.com"
              />
              {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
            </div>

            <button
              type="submit"
              className="w-full py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center justify-center gap-2"
            >
              Get Started
              <Icon name="arrow-right" size={14} />
            </button>
          </form>

          <p className="text-xs text-gray-600 text-center mt-4">
            Already have an account?{' '}
            <Link to="/sign-in" className="text-indigo-400 hover:text-indigo-300">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

function AuthBranding() {
  return (
    <div className="mb-8 text-center">
      <Link to="/" className="inline-flex items-center justify-center gap-3 mb-3">
        <div className="relative">
          <div className="absolute inset-0 bg-indigo-500/20 rounded-lg blur-sm animate-pulseGlow" />
          <Icon name="shield" size={32} className="text-indigo-400 relative" />
        </div>
        <h1 className="text-2xl font-bold text-white">
          Navil{' '}
          <span className="text-sm font-normal text-indigo-400 bg-indigo-400/10 px-2 py-0.5 rounded">
            OSS
          </span>
        </h1>
      </Link>
      <p className="text-sm text-gray-500">Agent Security Dashboard</p>
    </div>
  )
}
