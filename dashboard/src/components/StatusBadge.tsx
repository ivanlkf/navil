const colors: Record<string, string> = {
  ACTIVE: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  ALLOW: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  EXPIRED: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  ALERT: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  REVOKED: 'bg-red-500/15 text-red-400 border-red-500/30',
  DENY: 'bg-red-500/15 text-red-400 border-red-500/30',
  INACTIVE: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
}

const dotColors: Record<string, string> = {
  ACTIVE: 'bg-emerald-400',
  ALLOW: 'bg-emerald-400',
  EXPIRED: 'bg-amber-400',
  ALERT: 'bg-amber-400',
  REVOKED: 'bg-red-400',
  DENY: 'bg-red-400',
  INACTIVE: 'bg-gray-400',
}

export default function StatusBadge({ status }: { status: string }) {
  const cls = colors[status] || colors.INACTIVE
  const dot = dotColors[status] || 'bg-gray-400'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded border ${cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {status}
    </span>
  )
}
