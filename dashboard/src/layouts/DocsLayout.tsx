import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import DocsSidebar from '../components/DocsSidebar'
import Icon from '../components/Icon'

export default function DocsLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="max-w-7xl mx-auto px-6 flex">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-gray-950 border-r border-gray-800/60 transform transition-transform duration-300 lg:hidden
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="pt-20 px-4 overflow-y-auto h-full">
          <DocsSidebar onNavigate={() => setSidebarOpen(false)} />
        </div>
      </aside>

      {/* Mobile toggle button */}
      <button
        onClick={() => setSidebarOpen(true)}
        aria-label="Open docs navigation"
        className="lg:hidden fixed top-20 left-4 z-20 p-2 bg-gray-900/80 backdrop-blur border border-gray-800/60 rounded-lg text-gray-400 hover:text-gray-200"
      >
        <Icon name="menu" size={20} />
      </button>

      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <DocsSidebar />
      </div>

      {/* Main content */}
      <main className="flex-1 min-w-0 py-10 lg:pl-8">
        <Outlet />
      </main>
    </div>
  )
}
