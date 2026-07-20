import { AgentGrid } from '@/components/agents/AgentGrid'
import { Kanban } from '@/components/tasks/Kanban'
import { ActivityFeed } from '@/components/ActivityFeed'

export function Dashboard() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Agent Control Center</h1>
        <p className="text-muted-foreground mt-1">Управление агентами, задачами и проектами</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-card border border-border rounded-2xl p-6">
          <AgentGrid />
        </div>
        <div className="lg:col-span-7 bg-card border border-border rounded-2xl p-6">
          <Kanban />
        </div>
        <div className="lg:col-span-12 bg-card border border-border rounded-2xl p-6">
          <ActivityFeed />
        </div>
      </div>
    </div>
  )
}
