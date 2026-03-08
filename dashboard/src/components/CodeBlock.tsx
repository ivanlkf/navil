import { useState } from 'react'
import Icon from './Icon'

interface CodeBlockProps {
  code: string
  language?: string
  filename?: string
}

export default function CodeBlock({ code, language, filename }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API may not be available in all contexts
    }
  }

  const headerLabel = filename || language

  return (
    <div className="code-block">
      {headerLabel && (
        <div className="code-block-header flex items-center justify-between">
          <span className="text-xs text-gray-400">{headerLabel}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            aria-label="Copy code"
          >
            <Icon name={copied ? 'check' : 'copy'} size={14} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      )}
      {!headerLabel && (
        <button
          onClick={handleCopy}
          className="absolute top-3 right-3 flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          aria-label="Copy code"
        >
          <Icon name={copied ? 'check' : 'copy'} size={14} />
          {copied ? 'Copied!' : 'Copy'}
        </button>
      )}
      <pre className="p-4 overflow-x-auto text-gray-300">
        <code>{code}</code>
      </pre>
    </div>
  )
}
