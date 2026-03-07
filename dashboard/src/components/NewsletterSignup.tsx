import { type FormEvent, useState } from 'react'

export default function NewsletterSignup() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (email.trim()) {
      setSubmitted(true)
    }
  }

  return (
    <div className="glass-card p-8 text-center">
      <h3 className="text-xl font-bold text-white">Stay in the loop</h3>
      <p className="text-gray-400 text-sm mt-2">
        Get security insights and product updates.
      </p>

      {submitted ? (
        <p className="text-emerald-400 text-sm mt-6 animate-fadeIn">
          Thanks! We&rsquo;ll be in touch.
        </p>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="mt-6 flex items-center justify-center gap-3 flex-wrap sm:flex-nowrap"
        >
          <input
            type="email"
            required
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 w-full sm:w-64"
          />
          <button
            type="submit"
            className="bg-indigo-600 text-white rounded-lg px-5 py-2.5 text-sm font-medium hover:bg-indigo-500 transition-colors shrink-0"
          >
            Subscribe
          </button>
        </form>
      )}
    </div>
  )
}
