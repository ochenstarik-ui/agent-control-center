import { useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Dashboard } from '@/pages/Dashboard'
import { CommandPalette } from '@/components/CommandPalette'
import { accWS } from '@/lib/websocket'

export default function App() {
  useEffect(() => {
    accWS.connect('ws://localhost:8100/ws')
  }, [])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Dashboard />
      </main>
      <CommandPalette />
    </div>
  )
}
