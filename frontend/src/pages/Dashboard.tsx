import { AgentGrid } from '@/components/agents/AgentGrid'
import { Kanban } from '@/components/tasks/Kanban'
import { UsageCard } from '@/components/usage/UsageCard'
import { MemoryCard } from '@/components/memory/MemoryCard'
import { useAppStore } from '@/store/useAppStore'

export function Dashboard() {
  const { agents } = useAppStore()
  const online = agents.filter(a => a.healthy).length

  return (
    <div className="space-y-10">
      <div>
        <h2 className="text-3xl font-bold tracking-tighter">Доброе утро, Operator</h2>
        <p className="text-muted-foreground mt-1">Вот что происходит с вашими агентами</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <div className="xl:col-span-7">
          <AgentGrid />
        </div>

        <div className="xl:col-span-5 space-y-8">
          <UsageCard />
          <MemoryCard />
        </div>

        <div className="xl:col-span-12">
          <Kanban />
        </div>
      </div>
    </div>
  )
}
