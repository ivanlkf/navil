interface SectionHeaderProps {
  eyebrow?: string
  title: string
  subtitle?: string
  centered?: boolean
}

export default function SectionHeader({
  eyebrow,
  title,
  subtitle,
  centered = true,
}: SectionHeaderProps) {
  return (
    <div className={centered ? 'text-center' : ''}>
      {eyebrow && (
        <p className="text-sm font-medium text-indigo-400 mb-2">{eyebrow}</p>
      )}
      <h2 className="text-3xl font-bold text-white">{title}</h2>
      {subtitle && (
        <p className="text-gray-400 mt-3 max-w-2xl mx-auto">{subtitle}</p>
      )}
    </div>
  )
}
