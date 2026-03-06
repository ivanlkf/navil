import AnimatedNumber from './AnimatedNumber'

interface ScoreGaugeProps {
  score: number
  size?: number
  strokeWidth?: number
  className?: string
}

export default function ScoreGauge({ score, size = 140, strokeWidth = 10, className = '' }: ScoreGaugeProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const center = size / 2

  const color = score >= 80
    ? 'rgb(52 211 153)'   // emerald-400
    : score >= 60
    ? 'rgb(251 191 36)'   // yellow-400
    : 'rgb(248 113 113)'  // red-400

  const glowColor = score >= 80
    ? 'rgba(52, 211, 153, 0.35)'
    : score >= 60
    ? 'rgba(251, 191, 36, 0.35)'
    : 'rgba(248, 113, 113, 0.35)'

  return (
    <div className={`relative inline-flex flex-col items-center ${className}`}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="rgb(31 41 55)"
          strokeWidth={strokeWidth}
        />
        {/* Score arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="score-arc"
          style={{ '--score-offset': offset } as React.CSSProperties}
          filter={`drop-shadow(0 0 6px ${glowColor})`}
        />
      </svg>
      {/* Centered number */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <AnimatedNumber
          value={score}
          duration={1200}
          className="text-3xl font-bold"
          formatFn={n => `${n}`}
        />
        <span className="text-xs text-gray-500 mt-0.5">/ 100</span>
      </div>
    </div>
  )
}
