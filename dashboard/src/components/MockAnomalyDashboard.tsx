import Icon from './Icon'

const anomalies = [
  {
    severity: 'CRITICAL',
    title: 'Data exfiltration attempt',
    agent: 'bot-beta',
    time: '2 min ago',
    color: 'text-red-400 border-red-500/40',
    bg: 'bg-red-500/10',
    dot: 'bg-red-500',
  },
  {
    severity: 'HIGH',
    title: 'Unusual rate spike detected',
    agent: 'bot-gamma',
    time: '8 min ago',
    color: 'text-orange-400 border-orange-500/40',
    bg: 'bg-orange-500/10',
    dot: 'bg-orange-500',
  },
  {
    severity: 'MEDIUM',
    title: 'New tool invocation pattern',
    agent: 'bot-alpha',
    time: '23 min ago',
    color: 'text-yellow-400 border-yellow-500/40',
    bg: 'bg-yellow-500/10',
    dot: 'bg-yellow-500',
  },
]

/** Mini bar chart for the header stats */
function MiniSparkBars() {
  const bars = [3, 5, 2, 7, 4, 6, 8, 3, 5, 9, 4, 6]
  const max = Math.max(...bars)
  return (
    <div className="flex items-end gap-[2px] h-5">
      {bars.map((v, i) => (
        <div
          key={i}
          className="w-[3px] rounded-sm bg-indigo-500/60"
          style={{ height: `${(v / max) * 100}%` }}
        />
      ))}
    </div>
  )
}

export default function MockAnomalyDashboard() {
  return (
    <div className="p-3 space-y-3">
      {/* Stats row */}
      <div className="flex items-center gap-4 text-[11px]">
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Events (1h):</span>
          <span className="text-white font-medium">1,247</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500">Anomalies:</span>
          <span className="text-red-400 font-medium">3</span>
        </div>
        <div className="ml-auto"><MiniSparkBars /></div>
      </div>

      {/* Anomaly cards */}
      <div className="space-y-2">
        {anomalies.map((a, i) => (
          <div
            key={i}
            className={`flex items-start gap-2.5 p-2 rounded-lg border ${a.color} ${a.bg} border-opacity-30`}
          >
            <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${a.dot}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider opacity-80">
                  {a.severity}
                </span>
                <span className="text-[10px] text-gray-600 ml-auto">{a.time}</span>
              </div>
              <p className="text-[11px] text-gray-300 mt-0.5 truncate">{a.title}</p>
              <p className="text-[10px] text-gray-600 mt-0.5">agent: {a.agent}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-1.5 text-[10px] text-gray-600 pt-1">
        <Icon name="shield" size={10} className="text-emerald-500" />
        <span>12 detectors active — baselines healthy</span>
      </div>
    </div>
  )
}
