import { useEffect, useState } from 'react'

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return 'just now'
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

interface RelativeTimeProps {
  timestamp: string
  className?: string
}

export default function RelativeTime({ timestamp, className = '' }: RelativeTimeProps) {
  const [text, setText] = useState(() => formatRelativeTime(timestamp))

  useEffect(() => {
    setText(formatRelativeTime(timestamp))
    const interval = setInterval(() => {
      setText(formatRelativeTime(timestamp))
    }, 60_000)
    return () => clearInterval(interval)
  }, [timestamp])

  return (
    <time
      dateTime={timestamp}
      title={new Date(timestamp).toLocaleString()}
      className={className}
    >
      {text}
    </time>
  )
}
