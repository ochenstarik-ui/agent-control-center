import { AgentGrid } from '@/components/agents/AgentGrid'
import { Kanban } from '@/components/tasks/Kanban'
import { UsageCard } from '@/components/usage/UsageCard'
import { MemoryCard } from '@/components/memory/MemoryCard'
import { useAppStore } from '@/store/useAppStore'

export function Dashboard() {
  const { agents } = useAppStore()
  const online = agents.filter(a => a.healthy).length

  return (
    <div className="p-8 space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tighter">Agent Control Center</h1>
          <p className="text-muted-foreground mt-1">Управление агентами, задачами и проектами</p>
        </div>
        <div className="text-right">
          <div className="text-emerald-500 text-sm font-medium">{online} online</div>
          <div className="text-muted-foreground text-xs">v0.2.0</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Live Agents — 7 колонок */}
        <div className="xl:col-span-7">
          <AgentGrid />
        </div>

        {/* Sidebar widgets */}
        <div className="xl:col-span-5 space-y-6">
          <UsageCard />
          <MemoryCard />
        </div>

        {/* Kanban на всю ширину */}
        <div className="xl:col-span-12">
          <Kanban />
        </div>
      </div>
    </div>
  )
}
