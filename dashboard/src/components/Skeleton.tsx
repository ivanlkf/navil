interface SkeletonProps {
  variant?: 'text' | 'rect' | 'circle'
  width?: string
  height?: string
  className?: string
}

export default function Skeleton({ variant = 'text', width, height, className = '' }: SkeletonProps) {
  const base = variant === 'circle'
    ? `skeleton rounded-full ${width || 'w-10'} ${height || 'h-10'}`
    : variant === 'rect'
    ? `skeleton ${width || 'w-full'} ${height || 'h-20'}`
    : `skeleton ${width || 'w-full'} ${height || 'h-4'}`
  return <div className={`${base} ${className}`} />
}

export function SkeletonCard() {
  return (
    <div className="glass-card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton variant="text" width="w-24" height="h-3" />
        <Skeleton variant="circle" width="w-8" height="h-8" className="opacity-40" />
      </div>
      <Skeleton variant="text" width="w-20" height="h-8" />
      <Skeleton variant="text" width="w-full" height="h-1.5" />
    </div>
  )
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800/60 flex gap-4">
        {Array.from({ length: cols }).map((_, c) => (
          <Skeleton key={c} variant="text" width="w-24" height="h-3" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="px-4 py-3 border-b border-gray-800/30 flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} variant="text" width={c === 0 ? 'w-32' : 'w-16'} height="h-3" />
          ))}
        </div>
      ))}
    </div>
  )
}
