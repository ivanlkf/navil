const colors: Record<string, string> = {
  CRITICAL: 'bg-red-500/15 text-red-400 border-red-500/30',
  HIGH: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  MEDIUM: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  LOW: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  INFO: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  OK: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
}

const dotColors: Record<string, string> = {
  CRITICAL: 'bg-red-400',
  HIGH: 'bg-orange-400',
  MEDIUM: 'bg-yellow-400',
  LOW: 'bg-blue-400',
  INFO: 'bg-gray-400',
  OK: 'bg-emerald-400',
}

export default function SeverityBadge({ severity }: { severity: string }) {
  const cls = colors[severity] || colors.INFO
  const dot = dotColors[severity] || 'bg-gray-400'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded border ${cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {severity}
    </span>
  )
}
