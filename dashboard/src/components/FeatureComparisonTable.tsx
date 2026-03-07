import Icon from './Icon'

type CellValue = boolean | string

interface FeatureRow {
  name: string
  free: CellValue
  lite: CellValue
  elite: CellValue
  enterprise: CellValue
}

interface FeatureCategory {
  category: string
  features: FeatureRow[]
}

const data: FeatureCategory[] = [
  {
    category: 'Monitoring',
    features: [
      { name: 'Config Scanner', free: true, lite: true, elite: true, enterprise: true },
      { name: 'Policy Engine', free: true, lite: true, elite: true, enterprise: true },
      { name: 'Anomaly Detection', free: true, lite: true, elite: true, enterprise: true },
      { name: 'Real-time Alerts', free: true, lite: true, elite: true, enterprise: true },
      { name: 'Agent Limit', free: '3', lite: '10', elite: '50', enterprise: 'Unlimited' },
      { name: 'Events / month', free: '1,000', lite: '50,000', elite: '250,000', enterprise: 'Unlimited' },
    ],
  },
  {
    category: 'Security',
    features: [
      { name: 'Security Proxy', free: false, lite: true, elite: true, enterprise: true },
      { name: 'Credential Management', free: false, lite: true, elite: true, enterprise: true },
      { name: 'Traffic Logging', free: false, lite: true, elite: true, enterprise: true },
    ],
  },
  {
    category: 'AI Features',
    features: [
      { name: 'LLM Analysis', free: false, lite: true, elite: true, enterprise: true },
      { name: 'Auto-Remediation', free: false, lite: true, elite: true, enterprise: true },
      { name: 'AI Policy Generation', free: false, lite: true, elite: true, enterprise: true },
      { name: 'Pentest Engine', free: false, lite: true, elite: true, enterprise: true },
    ],
  },
  {
    category: 'Analytics',
    features: [
      { name: 'Agent Trust Score', free: false, lite: false, elite: true, enterprise: true },
      { name: 'Risk Analytics', free: false, lite: false, elite: true, enterprise: true },
      { name: 'Behavioral Profiling', free: false, lite: false, elite: true, enterprise: true },
      { name: 'Anomaly Trends', free: false, lite: false, elite: true, enterprise: true },
    ],
  },
  {
    category: 'Support',
    features: [
      { name: 'Community Support', free: true, lite: true, elite: true, enterprise: true },
      { name: 'Priority Support', free: false, lite: false, elite: true, enterprise: true },
      { name: 'SSO / SAML', free: false, lite: false, elite: true, enterprise: true },
      { name: 'Dedicated Engineer', free: false, lite: false, elite: false, enterprise: true },
      { name: 'SLA Guarantee', free: false, lite: false, elite: false, enterprise: true },
      { name: 'Self-host + Support', free: false, lite: false, elite: false, enterprise: true },
      { name: 'Dedicated Deployment', free: false, lite: false, elite: false, enterprise: true },
    ],
  },
]

function CellContent({ value }: { value: CellValue }) {
  if (typeof value === 'string') {
    return <span className="text-gray-300">{value}</span>
  }
  if (value) {
    return <Icon name="check" size={18} className="text-emerald-400 mx-auto" />
  }
  return <Icon name="x" size={18} className="text-gray-700 mx-auto" />
}

export default function FeatureComparisonTable() {
  return (
    <div className="glass-card overflow-x-auto">
      <table className="w-full min-w-[600px]">
        <thead>
          <tr className="border-b border-gray-800/50">
            <th className="text-sm font-medium text-gray-300 px-4 py-3 text-left w-1/3">
              Feature
            </th>
            <th className="text-sm font-medium text-gray-300 px-4 py-3 text-center">
              Free
            </th>
            <th className="text-sm font-medium text-gray-300 px-4 py-3 text-center">
              Lite
            </th>
            <th className="text-sm font-medium text-indigo-400 px-4 py-3 text-center">
              Elite
            </th>
            <th className="text-sm font-medium text-gray-300 px-4 py-3 text-center">
              Enterprise
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((group) => (
            <CategoryGroup key={group.category} group={group} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CategoryGroup({ group }: { group: FeatureCategory }) {
  return (
    <>
      <tr>
        <td
          colSpan={5}
          className="px-4 pt-5 pb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider"
        >
          {group.category}
        </td>
      </tr>
      {group.features.map((feature) => (
        <tr key={feature.name}>
          <td className="px-4 py-3 text-sm text-gray-400 border-t border-gray-800/30">
            {feature.name}
          </td>
          <td className="px-4 py-3 text-sm text-gray-400 border-t border-gray-800/30 text-center">
            <CellContent value={feature.free} />
          </td>
          <td className="px-4 py-3 text-sm text-gray-400 border-t border-gray-800/30 text-center">
            <CellContent value={feature.lite} />
          </td>
          <td className="px-4 py-3 text-sm text-gray-400 border-t border-gray-800/30 text-center">
            <CellContent value={feature.elite} />
          </td>
          <td className="px-4 py-3 text-sm text-gray-400 border-t border-gray-800/30 text-center">
            <CellContent value={feature.enterprise} />
          </td>
        </tr>
      ))}
    </>
  )
}
