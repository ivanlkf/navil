interface MiniBarProps {
  value: number
  max: number
  color?: string
  height?: string
  className?: string
}

export default function MiniBar({ value, max, color = 'bg-indigo-500', height = 'h-1.5', className = '' }: MiniBarProps) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className={`w-full bg-gray-800 rounded-full overflow-hidden ${height} ${className}`}>
      <div
        className={`${color} ${height} rounded-full transition-all duration-700 ease-out`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
