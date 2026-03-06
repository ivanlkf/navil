export type IconName =
  | 'shield' | 'chart' | 'scan' | 'bot' | 'alert'
  | 'signal' | 'key' | 'check' | 'x' | 'chevron-down'
  | 'chevron-right' | 'warning' | 'lock' | 'unlock'
  | 'clock' | 'activity' | 'info' | 'terminal' | 'menu'
  | 'arrow-up' | 'arrow-down' | 'eye' | 'sparkles'
  | 'settings' | 'gateway' | 'pentest'

interface IconProps {
  name: IconName
  size?: number
  className?: string
}

const paths: Record<IconName, string[]> = {
  shield: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'],
  chart: ['M18 20V10', 'M12 20V4', 'M6 20v-6'],
  scan: ['M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'],
  bot: [
    'M12 8V4H8',
    'M5 12H3',
    'M21 12h-2',
    'M7 20v-2a4 4 0 014-4h2a4 4 0 014 4v2',
    'M9 8a3 3 0 106 0v1a2 2 0 01-2 2h-2a2 2 0 01-2-2V8z',
  ],
  alert: [
    'M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9',
    'M13.73 21a2 2 0 01-3.46 0',
  ],
  signal: [
    'M2 12l5-5 5 5 5-5 5 5',
  ],
  key: [
    'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4',
  ],
  check: ['M20 6L9 17l-5-5'],
  x: ['M18 6L6 18', 'M6 6l12 12'],
  'chevron-down': ['M6 9l6 6 6-6'],
  'chevron-right': ['M9 18l6-6-6-6'],
  warning: [
    'M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z',
    'M12 9v4',
    'M12 17h.01',
  ],
  lock: [
    'M19 11H5a2 2 0 00-2 2v7a2 2 0 002 2h14a2 2 0 002-2v-7a2 2 0 00-2-2z',
    'M7 11V7a5 5 0 0110 0v4',
  ],
  unlock: [
    'M19 11H5a2 2 0 00-2 2v7a2 2 0 002 2h14a2 2 0 002-2v-7a2 2 0 00-2-2z',
    'M7 11V7a5 5 0 019.9-1',
  ],
  clock: [
    'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z',
    'M12 6v6l4 2',
  ],
  activity: ['M22 12h-4l-3 9L9 3l-3 9H2'],
  info: [
    'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z',
    'M12 16v-4',
    'M12 8h.01',
  ],
  terminal: [
    'M4 17l6-6-6-6',
    'M12 19h8',
  ],
  menu: ['M3 12h18', 'M3 6h18', 'M3 18h18'],
  'arrow-up': ['M12 19V5', 'M5 12l7-7 7 7'],
  'arrow-down': ['M12 5v14', 'M19 12l-7 7-7-7'],
  eye: [
    'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z',
    'M12 9a3 3 0 100 6 3 3 0 000-6z',
  ],
  sparkles: [
    'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z',
    'M18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z',
  ],
  gateway: [
    'M12 2L2 7l10 5 10-5-10-5z',
    'M2 17l10 5 10-5',
    'M2 12l10 5 10-5',
  ],
  pentest: [
    'M12 2a10 10 0 100 20 10 10 0 000-20z',
    'M12 6a6 6 0 100 12 6 6 0 000-12z',
    'M12 10a2 2 0 100 4 2 2 0 000-4z',
  ],
  settings: [
    'M12.22 2h-.44a2 2 0 00-2 2v.18a2 2 0 01-1 1.73l-.43.25a2 2 0 01-2 0l-.15-.08a2 2 0 00-2.73.73l-.22.38a2 2 0 00.73 2.73l.15.1a2 2 0 011 1.72v.51a2 2 0 01-1 1.74l-.15.09a2 2 0 00-.73 2.73l.22.38a2 2 0 002.73.73l.15-.08a2 2 0 012 0l.43.25a2 2 0 011 1.73V20a2 2 0 002 2h.44a2 2 0 002-2v-.18a2 2 0 011-1.73l.43-.25a2 2 0 012 0l.15.08a2 2 0 002.73-.73l.22-.39a2 2 0 00-.73-2.73l-.15-.08a2 2 0 01-1-1.74v-.5a2 2 0 011-1.74l.15-.09a2 2 0 00.73-2.73l-.22-.38a2 2 0 00-2.73-.73l-.15.08a2 2 0 01-2 0l-.43-.25a2 2 0 01-1-1.73V4a2 2 0 00-2-2z',
    'M12 15a3 3 0 100-6 3 3 0 000 6z',
  ],
}

export default function Icon({ name, size = 20, className = '' }: IconProps) {
  const d = paths[name]
  if (!d) return null
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {d.map((path, i) => (
        <path key={i} d={path} />
      ))}
    </svg>
  )
}
