import Icon from './Icon'

export default function MockRemediationEngine() {
  return (
    <div className="p-3 space-y-3 text-[11px]">
      {/* Trigger */}
      <div className="flex items-center gap-2 p-2 rounded-lg bg-red-500/5 border border-red-500/20">
        <Icon name="warning" size={12} className="text-red-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-gray-300 font-medium">Trigger: Data exfiltration detected</p>
          <p className="text-[10px] text-gray-600 mt-0.5">bot-beta → httpFetch → external endpoint</p>
        </div>
        <span className="text-[10px] text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded shrink-0">CRITICAL</span>
      </div>

      {/* AI analysis */}
      <div className="p-2 rounded-lg bg-violet-500/5 border border-violet-500/20">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Icon name="sparkles" size={11} className="text-violet-400" />
          <span className="text-violet-400 font-medium text-[10px] uppercase tracking-wider">AI Analysis</span>
        </div>
        <p className="text-gray-400 leading-relaxed">
          Agent <span className="text-white">bot-beta</span> attempted to exfiltrate 2.4MB of customer data
          via an unauthorized HTTP endpoint. The tool call pattern deviates significantly from
          established baselines.
        </p>
      </div>

      {/* Remediation steps */}
      <div className="space-y-1.5">
        <p className="text-[10px] text-gray-500 uppercase tracking-wider font-medium px-1">Remediations Applied</p>
        <div className="flex items-center gap-2 p-1.5 rounded bg-emerald-500/5">
          <Icon name="check" size={11} className="text-emerald-400" />
          <span className="text-gray-300">Block agent bot-beta from httpFetch</span>
          <span className="text-[10px] text-emerald-400 ml-auto">done</span>
        </div>
        <div className="flex items-center gap-2 p-1.5 rounded bg-emerald-500/5">
          <Icon name="check" size={11} className="text-emerald-400" />
          <span className="text-gray-300">Tighten network_access policy</span>
          <span className="text-[10px] text-emerald-400 ml-auto">done</span>
        </div>
        <div className="flex items-center gap-2 p-1.5 rounded bg-indigo-500/5">
          <Icon name="shield" size={11} className="text-indigo-400" />
          <span className="text-gray-300">Flag for manual review</span>
          <span className="text-[10px] text-indigo-400 ml-auto">pending</span>
        </div>
      </div>
    </div>
  )
}
