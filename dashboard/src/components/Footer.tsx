import { Link } from 'react-router-dom'
import Icon from '../components/Icon'

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

interface FooterLink {
  label: string
  to: string
  external?: boolean
  /** Only used for mailto: or other protocol links. */
  href?: string
}

interface FooterColumn {
  title: string
  links: FooterLink[]
}

/* ------------------------------------------------------------------ */
/*  Data                                                              */
/* ------------------------------------------------------------------ */

const columns: FooterColumn[] = [
  {
    title: 'Product',
    links: [
      { label: 'Config Scanner', to: '/docs/configuration' },
      { label: 'Policy Engine', to: '/docs/policy-engine' },
      { label: 'Anomaly Detection', to: '/#features' },
      { label: 'Security Proxy', to: '/docs/proxy' },
      { label: 'Pentest Engine', to: '/docs/pentest' },
      { label: 'LLM Analysis', to: '/docs/llm' },
    ],
  },
  {
    title: 'Solutions',
    links: [
      { label: 'MCP Security', to: '/solutions/mcp-security' },
      { label: 'AI Compliance', to: '/solutions/ai-compliance' },
      { label: 'Pentest Automation', to: '/solutions/pentest-automation' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', to: '/docs' },
      { label: 'Blog', to: '/blog' },
      { label: 'Changelog', to: '/changelog' },
      {
        label: 'GitHub',
        to: 'https://github.com/ivanlkf/navil',
        external: true,
      },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', to: '/about' },
      { label: 'Contact', to: '#', href: 'mailto:info@pantheonlab.ai' },
      { label: 'Privacy', to: '#' },
      { label: 'Terms', to: '#' },
    ],
  },
]

const GITHUB_URL = 'https://github.com/ivanlkf/navil'

/* ------------------------------------------------------------------ */
/*  Footer                                                            */
/* ------------------------------------------------------------------ */

export default function Footer() {
  return (
    <footer className="border-t border-gray-800/60 bg-gray-950">
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Sitemap columns */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {columns.map((col) => (
            <div key={col.title} className="footer-col">
              <h4>{col.title}</h4>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <FooterAnchor link={link} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-800/60 mt-8 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-600">
            &copy; {new Date().getFullYear()} Pantheon Lab Limited. All rights
            reserved.
          </p>

          <div className="flex items-center gap-4">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-300 transition-colors"
              aria-label="GitHub"
            >
              <Icon name="github" size={18} />
            </a>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              Open Source
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}

/* ------------------------------------------------------------------ */
/*  FooterAnchor                                                      */
/* ------------------------------------------------------------------ */

function FooterAnchor({ link }: { link: FooterLink }) {
  /* mailto or other protocol links */
  if (link.href) {
    return (
      <a
        href={link.href}
        className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        {link.label}
      </a>
    )
  }

  /* External links */
  if (link.external) {
    return (
      <a
        href={link.to}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-gray-500 hover:text-gray-300 transition-colors inline-flex items-center gap-1.5"
      >
        {link.label}
        <Icon name="external-link" size={12} className="text-gray-600" />
      </a>
    )
  }

  /* Internal links */
  return (
    <Link
      to={link.to}
      className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
    >
      {link.label}
    </Link>
  )
}
