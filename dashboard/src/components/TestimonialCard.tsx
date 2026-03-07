interface TestimonialCardProps {
  quote: string
  author: string
  role: string
  company: string
}

function getInitials(name: string) {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const avatarColors = [
  'bg-indigo-500/20 text-indigo-400',
  'bg-violet-500/20 text-violet-400',
  'bg-emerald-500/20 text-emerald-400',
  'bg-amber-500/20 text-amber-400',
  'bg-rose-500/20 text-rose-400',
]

export default function TestimonialCard({
  quote,
  author,
  role,
  company,
}: TestimonialCardProps) {
  const colorIdx =
    author.split('').reduce((sum, ch) => sum + ch.charCodeAt(0), 0) %
    avatarColors.length

  return (
    <div className="glass-card p-6">
      <span className="text-4xl text-indigo-500/30 leading-none select-none">
        &ldquo;
      </span>
      <p className="italic text-gray-300 mt-2">{quote}</p>
      <div className="mt-4 pt-4 border-t border-gray-800/40 flex items-center gap-3">
        <div
          className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${avatarColors[colorIdx]}`}
        >
          {getInitials(author)}
        </div>
        <div>
          <p className="text-sm font-medium text-gray-200">{author}</p>
          <p className="text-xs text-gray-500">
            {role}, {company}
          </p>
        </div>
      </div>
    </div>
  )
}
