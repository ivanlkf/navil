import { Link } from 'react-router-dom'
import Icon from './Icon'

interface UpgradePromptProps {
  /** Short description of the gated feature. */
  feature: string
  /** Called when user clicks the temporary "Upgrade" button. */
  onUpgrade?: () => void
  /** Compact mode for inline use (e.g., inside alert rows). */
  compact?: boolean
}

/**
 * Paywall card shown in place of AI-powered features when the user is on
 * the free plan and has no BYOK key configured.
 */
export default function UpgradePrompt({ feature, onUpgrade, compact }: UpgradePromptProps) {
  if (compact) {
    return (
      <div className="flex items-center gap-3 p-3 rounded-lg bg-violet-500/5 border border-violet-500/20">
        <Icon name="sparkles" size={14} className="text-violet-400 shrink-0" />
        <p className="text-xs text-gray-400 flex-1">
          <span className="text-violet-400 font-medium">Pro</span> — {feature}.{' '}
          {onUpgrade && (
            <button onClick={onUpgrade} className="text-violet-400 hover:underline">
              Upgrade
            </button>
          )}{' '}
          or{' '}
          <Link to="/settings" className="text-indigo-400 hover:underline">
            add your own API key
          </Link>
        </p>
      </div>
    )
  }

  return (
    <div className="glass-card p-8 text-center animate-fadeIn">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-violet-500/10 mb-4">
        <Icon name="sparkles" size={32} className="text-violet-400" />
      </div>

      <div className="inline-block px-2.5 py-0.5 text-[10px] font-semibold bg-violet-500/15 text-violet-400 border border-violet-500/30 rounded-full mb-3">
        PRO FEATURE
      </div>

      <h3 className="text-lg font-medium text-gray-200 mb-2">{feature}</h3>
      <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
        This feature requires a Pro plan or your own API key. Upgrade to unlock AI-powered
        analysis, or bring your own key to use it for free.
      </p>

      <div className="flex items-center justify-center gap-3 flex-wrap">
        {onUpgrade && (
          <button
            onClick={onUpgrade}
            className="px-5 py-2.5 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-500 flex items-center gap-2"
          >
            <Icon name="sparkles" size={14} />
            Upgrade to Pro
          </button>
        )}
        <Link
          to="/settings"
          className="px-5 py-2.5 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 flex items-center gap-2"
        >
          <Icon name="key" size={14} />
          Configure API Key
        </Link>
      </div>
    </div>
  )
}
