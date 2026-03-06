import { useState } from 'react'
import { Link } from 'react-router-dom'
import Icon, { type IconName } from './Icon'

interface LLMErrorCardProps {
  message: string
  errorType?: 'auth' | 'rate_limit' | 'quota' | 'billing' | 'unknown'
  onRetry?: () => void
  compact?: boolean
}

const errorConfig: Record<string, { icon: IconName; title: string; hint: string; accent: 'amber' | 'red'; showSettings: boolean }> = {
  auth: { icon: 'key', title: 'API Key Required', hint: 'Configure your LLM API key to enable AI features.', accent: 'amber', showSettings: true },
  rate_limit: { icon: 'clock', title: 'Rate Limit Reached', hint: 'Too many requests. Please wait a moment before trying again.', accent: 'amber', showSettings: false },
  quota: { icon: 'alert', title: 'API Quota Exceeded', hint: 'Your API quota has been reached. Check your provider account or wait for reset.', accent: 'amber', showSettings: false },
  billing: { icon: 'sparkles', title: 'Pro Plan Required', hint: 'Upgrade to Pro or configure your own API key to use AI features.', accent: 'amber', showSettings: true },
  unknown: { icon: 'warning', title: 'AI Analysis Failed', hint: 'An unexpected error occurred.', accent: 'red', showSettings: false },
}

const accentStyles = {
  amber: { border: 'border-amber-500/30', iconBg: 'bg-amber-500/10', iconText: 'text-amber-400', title: 'text-amber-400' },
  red: { border: 'border-red-500/30', iconBg: 'bg-red-500/10', iconText: 'text-red-400', title: 'text-red-400' },
}

export default function LLMErrorCard({ message, errorType = 'unknown', onRetry, compact }: LLMErrorCardProps) {
  const [showDetail, setShowDetail] = useState(false)
  const cfg = errorConfig[errorType] || errorConfig.unknown
  const styles = accentStyles[cfg.accent]

  if (compact) {
    return (
      <div className={`flex items-start gap-2 mt-2 p-2.5 rounded-lg bg-gray-800/50 border ${styles.border} animate-fadeIn`}>
        <Icon name={cfg.icon} size={14} className={`${styles.iconText} shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <p className={`text-xs font-medium ${styles.title}`}>{cfg.title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{cfg.hint}</p>
          <div className="flex gap-3 mt-1">
            {cfg.showSettings && (
              <Link to="/settings" className="text-xs text-indigo-400 hover:text-indigo-300">
                Go to Settings →
              </Link>
            )}
            {onRetry && (
              <button onClick={onRetry} className="text-xs text-indigo-400 hover:text-indigo-300">
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`glass-card ${styles.border} p-5 animate-fadeIn`}>
      <div className="flex items-start gap-4">
        <div className={`shrink-0 w-10 h-10 rounded-full ${styles.iconBg} flex items-center justify-center`}>
          <Icon name={cfg.icon} size={20} className={styles.iconText} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={`font-medium ${styles.title}`}>{cfg.title}</p>
          <p className="text-sm text-gray-400 mt-1">{cfg.hint}</p>

          {message && message !== cfg.hint && (
            <button
              onClick={() => setShowDetail(!showDetail)}
              className="text-xs text-gray-500 hover:text-gray-400 mt-2 flex items-center gap-1"
            >
              <Icon name={showDetail ? 'chevron-down' : 'chevron-right'} size={12} />
              Technical detail
            </button>
          )}
          {showDetail && (
            <pre className="mt-2 text-xs text-gray-500 bg-gray-900/60 rounded-lg p-3 overflow-x-auto font-mono max-h-32 overflow-y-auto">
              {message}
            </pre>
          )}

          <div className="flex gap-3 mt-3">
            {cfg.showSettings && (
              <Link
                to="/settings"
                className="px-3 py-1.5 text-xs bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 rounded-lg hover:bg-indigo-500/25 flex items-center gap-1.5"
              >
                <Icon name="settings" size={13} />
                Configure API Key
              </Link>
            )}
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-3 py-1.5 text-xs bg-gray-800 text-gray-400 border border-gray-700 rounded-lg hover:bg-gray-700 hover:text-gray-300 flex items-center gap-1.5"
              >
                <Icon name="activity" size={13} />
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
