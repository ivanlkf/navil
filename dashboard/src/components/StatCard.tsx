import Icon, { type IconName } from './Icon'
import AnimatedNumber from './AnimatedNumber'

interface StatCardProps {
  label: string
  value: number | string
  icon: IconName
  accent?: string
  index?: number
}

export default function StatCard({ label, value, icon, accent = 'indigo', index = 0 }: StatCardProps) {
  const accentMap: Record<string, string> = {
    indigo: 'from-indigo-500/20 to-indigo-500/5 border-indigo-500/20',
    red: 'from-red-500/20 to-red-500/5 border-red-500/20',
    emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/20',
    amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/20',
  }
  const iconColorMap: Record<string, string> = {
    indigo: 'text-indigo-400',
    red: 'text-red-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
  }

  const numericValue = typeof value === 'number' ? value : null

  return (
    <div
      className={`bg-gradient-to-br ${accentMap[accent] || accentMap.indigo} border rounded-xl p-5 animate-slideUp opacity-0`}
      style={{ animationDelay: `${index * 0.08}s` }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          {numericValue !== null ? (
            <AnimatedNumber value={numericValue} className="text-3xl font-bold mt-1 block" />
          ) : (
            <p className="text-3xl font-bold mt-1">{value}</p>
          )}
        </div>
        <div className={`${iconColorMap[accent] || 'text-indigo-400'} opacity-50`}>
          <Icon name={icon} size={28} />
        </div>
      </div>
    </div>
  )
}
