import { SignIn as ClerkSignIn } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'
import { isAuthEnabled } from '../auth/ClerkProviderWrapper'
import Icon from '../components/Icon'

export default function SignIn() {
  if (!isAuthEnabled()) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 px-4">
      {/* Branding */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className="relative">
            <div className="absolute inset-0 bg-indigo-500/20 rounded-lg blur-sm animate-pulseGlow" />
            <Icon name="shield" size={32} className="text-indigo-400 relative" />
          </div>
          <h1 className="text-2xl font-bold text-white">
            Navil{' '}
            <span className="text-sm font-normal text-indigo-400 bg-indigo-400/10 px-2 py-0.5 rounded">
              Cloud
            </span>
          </h1>
        </div>
        <p className="text-sm text-gray-500">Agent Security Dashboard</p>
      </div>

      {/* Clerk Sign-In widget */}
      <ClerkSignIn
        routing="path"
        path="/sign-in"
        signUpUrl="/sign-up"
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
