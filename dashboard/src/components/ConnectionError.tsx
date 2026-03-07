import Icon from './Icon'

interface ConnectionErrorProps {
  onRetry?: () => void
}

export default function ConnectionError({ onRetry }: ConnectionErrorProps) {
  return (
    <div className="max-w-lg mx-auto mt-16 text-center animate-fadeIn">
      <div className="glass-card p-8">
        <div className="w-14 h-14 mx-auto mb-5 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
          <Icon name="warning" size={24} className="text-red-400" />
        </div>
        <h2 className="text-lg font-semibold text-white mb-2">Unable to connect to Navil</h2>
        <p className="text-sm text-gray-400 mb-6">
          The backend API is not responding. Make sure the Navil server is running:
        </p>
        <div className="bg-gray-900 border border-gray-800/60 rounded-lg p-3 mb-6 font-mono text-sm text-indigo-300">
          $ navil cloud serve
        </div>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={onRetry}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 flex items-center gap-2"
          >
            <Icon name="activity" size={14} />
            Retry
          </button>
          <a
            href="https://navil.ai/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-700 flex items-center gap-2"
          >
            <Icon name="book" size={14} />
            Setup Guide
          </a>
        </div>
      </div>
    </div>
  )
}
