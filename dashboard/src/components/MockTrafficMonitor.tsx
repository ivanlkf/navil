import Icon from './Icon'

const trafficRows = [
  { time: '12:04:31', method: 'tools/call', tool: 'readFile', agent: 'bot-alpha', status: 'ok', ms: 42 },
  { time: '12:04:29', method: 'tools/call', tool: 'execCmd', agent: 'bot-beta', status: 'blocked', ms: 3 },
  { time: '12:04:27', method: 'tools/list', tool: '—', agent: 'bot-alpha', status: 'ok', ms: 18 },
  { time: '12:04:25', method: 'tools/call', tool: 'writeFile', agent: 'bot-gamma', status: 'ok', ms: 67 },
  { time: '12:04:22', method: 'tools/call', tool: 'httpFetch', agent: 'bot-beta', status: 'flagged', ms: 210 },
]

const statusStyle: Record<string, string> = {
  ok: 'text-emerald-400 bg-emerald-400/10',
  blocked: 'text-red-400 bg-red-400/10',
  flagged: 'text-yellow-400 bg-yellow-400/10',
}

export default function MockTrafficMonitor() {
  return (
    <div className="p-3 space-y-1.5 text-[11px] font-mono">
      {/* Header */}
      <div className="grid grid-cols-[56px_80px_72px_72px_52px_36px] gap-2 px-2 py-1 text-gray-600 uppercase tracking-wider text-[10px]">
        <span>Time</span>
        <span>Method</span>
        <span>Tool</span>
        <span>Agent</span>
        <span>Status</span>
        <span className="text-right">ms</span>
      </div>
      {trafficRows.map((row, i) => (
        <div
          key={i}
          className={`grid grid-cols-[56px_80px_72px_72px_52px_36px] gap-2 px-2 py-1.5 rounded ${
            row.status !== 'ok' ? 'bg-white/[0.02]' : ''
          }`}
        >
          <span className="text-gray-600">{row.time}</span>
          <span className="text-indigo-400">{row.method}</span>
          <span className="text-gray-300 truncate">{row.tool}</span>
          <span className="text-gray-500 truncate">{row.agent}</span>
          <span className={`px-1.5 py-0.5 rounded text-center text-[10px] ${statusStyle[row.status]}`}>
            {row.status}
          </span>
          <span className="text-gray-500 text-right">{row.ms}</span>
        </div>
      ))}
      {/* Streaming indicator */}
      <div className="flex items-center gap-2 px-2 pt-1 text-gray-600">
        <Icon name="activity" size={10} className="text-emerald-500 animate-pulse" />
        <span>Streaming — 847 requests/min</span>
      </div>
    </div>
  )
}
