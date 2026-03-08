import Icon from '../components/Icon'

export default function Blog() {
  return (
    <div className="bg-gray-950">
      <div className="max-w-4xl mx-auto px-6 py-24">
        {/* Heading */}
        <h1
          className="text-4xl font-bold text-white mb-10 animate-slideUp opacity-0"
          style={{ animationDelay: '0.1s' }}
        >
          Blog
        </h1>

        {/* Coming soon card */}
        <div
          className="glass-card p-8 text-center mb-10 animate-slideUp opacity-0"
          style={{ animationDelay: '0.15s' }}
        >
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-4">
            <Icon name="sparkles" size={22} className="text-indigo-400" />
          </div>
          <p className="text-gray-400 leading-relaxed max-w-lg mx-auto">
            We're working on our first posts. Stay tuned for security insights,
            product updates, and MCP best practices.
          </p>
        </div>

        {/* Skeleton article cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="glass-card p-5 animate-slideUp opacity-0"
              style={{ animationDelay: `${0.2 + i * 0.08}s` }}
            >
              <div className="skeleton h-32 w-full rounded-lg mb-4" />
              <div className="skeleton h-4 w-3/4 mb-3" />
              <div className="skeleton h-3 w-full mb-2" />
              <div className="skeleton h-3 w-5/6 mb-4" />
              <div className="skeleton h-3 w-1/3" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
