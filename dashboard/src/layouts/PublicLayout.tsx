import { Outlet } from 'react-router-dom'
import MegaNav from '../components/MegaNav'
import Footer from '../components/Footer'

export default function PublicLayout() {
  return (
    <div className="min-h-screen bg-gray-950">
      <MegaNav />
      <main className="pt-16">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
