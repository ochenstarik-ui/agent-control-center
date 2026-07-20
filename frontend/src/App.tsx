import { useEffect } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Dashboard } from '@/pages/Dashboard'
import { CommandPalette } from '@/components/CommandPalette'
import { accWS } from '@/lib/websocket'
import { useAppStore } from '@/store/useAppStore'

export default function App() {
  const { agents } = useAppStore()
  const online = agents.filter(a => a.healthy).length

  useEffect(() => {
    accWS.connect('ws://localhost:8100/ws')
  }, [])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-border flex items-center px-8 bg-card/80 backdrop-blur-md z-10 shrink-0">
          <div className="flex-1 flex items-center justify-between">
            <h1 className="text-lg font-semibold tracking-tight">Agent Control Center</h1>
            <div className="text-sm text-emerald-500 font-medium">{online} online · v0.2.0</div>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-8 lg:p-10 max-w-[1600px] mx-auto w-full">
          <Dashboard />
        </main>
      </div>

      <CommandPalette />
    </div>
  )
}
