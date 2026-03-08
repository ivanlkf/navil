import Icon, { type IconName } from './Icon'

interface LogoCloudProps {
  title?: string
}

const companies: { name: string; icon: IconName }[] = [
  { name: 'Acme Corp', icon: 'building' },
  { name: 'TechFlow', icon: 'activity' },
  { name: 'Sentinel AI', icon: 'shield' },
  { name: 'DataGuard', icon: 'lock' },
  { name: 'CloudSec', icon: 'globe' },
  { name: 'NeuralOps', icon: 'code' },
]

export default function LogoCloud({ title }: LogoCloudProps) {
  return (
    <div className="text-center">
      {title && (
        <p className="text-sm text-gray-500 mb-8">{title}</p>
      )}
      <div className="flex items-center justify-center gap-8 lg:gap-12 flex-wrap">
        {companies.map((c) => (
          <div
            key={c.name}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-400 transition-colors select-none"
          >
            <Icon name={c.icon} size={16} className="opacity-50" />
            <span className="font-semibold text-sm tracking-wide">{c.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
