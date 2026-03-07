interface DataPoint {
  label: string
  value: number
}

interface SparklineChartProps {
  data: DataPoint[]
  height?: number
  color?: string
  fillColor?: string
  className?: string
}

export default function SparklineChart({
  data,
  height = 120,
  color = 'rgb(129, 140, 248)',
  fillColor = 'rgba(129, 140, 248, 0.1)',
  className = '',
}: SparklineChartProps) {
  if (data.length < 2) return null

  const width = 100 // percentage-based, rendered in viewBox
  const padding = 2
  const maxVal = Math.max(...data.map((d) => d.value), 1)
  const minVal = Math.min(...data.map((d) => d.value), 0)
  const range = maxVal - minVal || 1

  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (width - padding * 2)
    const y = padding + (1 - (d.value - minVal) / range) * (height - padding * 2)
    return { x, y, ...d }
  })

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')

  const fillPath = `${linePath} L${points[points.length - 1].x},${height - padding} L${points[0].x},${height - padding} Z`

  const gradientId = `sparkline-grad-${Math.random().toString(36).slice(2, 8)}`

  return (
    <div className={`relative ${className}`}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="w-full"
        style={{ height }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={fillColor} />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
        {/* Fill area */}
        <path d={fillPath} fill={`url(#${gradientId})`} />
        {/* Line */}
        <path d={linePath} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
        {/* Dots on endpoints */}
        <circle cx={points[0].x} cy={points[0].y} r={2} fill={color} />
        <circle
          cx={points[points.length - 1].x}
          cy={points[points.length - 1].y}
          r={2}
          fill={color}
        />
      </svg>
      {/* X-axis labels */}
      <div className="flex justify-between mt-1.5 px-0.5">
        <span className="text-[10px] text-gray-600">{data[0].label}</span>
        <span className="text-[10px] text-gray-600">{data[data.length - 1].label}</span>
      </div>
    </div>
  )
}
