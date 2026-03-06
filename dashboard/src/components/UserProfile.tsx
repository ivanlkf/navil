import { useUser, useClerk } from '@clerk/clerk-react'
import { NavLink } from 'react-router-dom'
import { isAuthEnabled } from '../auth/ClerkProviderWrapper'
import Icon from './Icon'

/**
 * Sidebar footer: user avatar + sign-out when authenticated,
 * or the default version + settings link when auth is off.
 */
export default function UserProfile() {
  if (!isAuthEnabled()) {
    return <DefaultFooter />
  }
  return <AuthFooter />
}

function DefaultFooter() {
  return (
    <div className="relative p-4 border-t border-gray-800/60 flex items-center justify-between">
      <p className="text-xs text-gray-600">Navil v0.1.0</p>
      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `p-1.5 rounded-lg transition-colors ${
            isActive
              ? 'text-indigo-400 bg-indigo-500/10'
              : 'text-gray-600 hover:text-gray-400 hover:bg-gray-800/60'
          }`
        }
      >
        <Icon name="settings" size={14} />
      </NavLink>
    </div>
  )
}

function AuthFooter() {
  const { user } = useUser()
  const { signOut } = useClerk()

  return (
    <div className="relative border-t border-gray-800/60">
      {/* User info row */}
      <div className="p-3 flex items-center gap-3">
        {user?.imageUrl ? (
          <img
            src={user.imageUrl}
            alt=""
            className="w-7 h-7 rounded-full border border-gray-700 shrink-0"
          />
        ) : (
          <div className="w-7 h-7 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
            <Icon name="bot" size={14} className="text-indigo-400" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-300 truncate">
            {user?.firstName || user?.emailAddresses?.[0]?.emailAddress || 'User'}
          </p>
          <p className="text-[10px] text-gray-600 truncate">
            {user?.emailAddresses?.[0]?.emailAddress || ''}
          </p>
        </div>
      </div>

      {/* Actions row */}
      <div className="px-3 pb-3 flex items-center justify-between">
        <button
          onClick={() => signOut()}
          className="text-[10px] text-gray-500 hover:text-red-400 transition-colors flex items-center gap-1"
        >
          <Icon name="lock" size={10} />
          Sign out
        </button>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-gray-600">v0.1.0</span>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `p-1 rounded transition-colors ${
                isActive
                  ? 'text-indigo-400 bg-indigo-500/10'
                  : 'text-gray-600 hover:text-gray-400 hover:bg-gray-800/60'
              }`
            }
          >
            <Icon name="settings" size={12} />
          </NavLink>
        </div>
      </div>
    </div>
  )
}
