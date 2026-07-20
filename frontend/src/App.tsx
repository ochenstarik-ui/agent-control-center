import { Sidebar } from '@/components/Sidebar'
import { Dashboard } from '@/pages/Dashboard'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Dashboard />
      </main>
    </div>
  )
}
