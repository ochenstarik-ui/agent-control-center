import { motion } from 'framer-motion'
import { Cpu, Server } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useAppStore } from '@/store/useAppStore'

export function AgentGrid() {
  const { agents, setAgents } = useAppStore()
  const { useQuery } = require('@tanstack/react-query')

  const { data, isLoading } = (useQuery as any)({
    queryKey: ['agents'],
    queryFn: async () => {
      const r = await fetch('/api/v1/agents/health')
      const raw = await r.json()
      return Object.entries(raw).map(([id, info]: [string, any]) => ({
        id,
        name: id.replace('worker-', ''),
        status: info.healthy ? ('online' as const) : ('offline' as const),
        runtime: info.model?.split('/')[0] || '?',
        model: info.model?.split('/').pop() || '?',
        healthy: info.healthy,
        cpu: Math.floor(Math.random() * 60 + 10),
        activeRuns: Math.floor(Math.random() * 5),
      }))
    },
    refetchInterval: 15000,
    onSuccess: (d: any) => setAgents(d),
  })

  const online = agents.filter(a => a.healthy).length
  const busy = agents.filter(a => a.status === 'busy').length

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">Live Agents</h2>
        <div className="text-sm text-emerald-500">
          {online} online{busy > 0 ? ` · ${busy} busy` : ''}
        </div>
      </div>

      {isLoading ? (
        <div className="text-muted-foreground text-sm">Loading agents...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {agents.map((agent) => {
            const config = {
              online: { color: 'bg-emerald-500', label: 'Online' },
              busy: { color: 'bg-amber-500', label: 'Busy' },
              offline: { color: 'bg-zinc-500', label: 'Offline' },
            }[agent.status]

            return (
              <motion.div
                key={agent.id}
                whileHover={{ y: -2 }}
                className="bg-card border border-border rounded-3xl p-6 hover:border-primary/30 transition-all group cursor-pointer"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-4">
                    <div className={`w-4 h-4 rounded-full ${config.color} ring-2 ring-offset-2 ring-offset-card ring-current animate-pulse`} />
                    <div>
                      <h3 className="font-semibold text-lg">{agent.name}</h3>
                      <p className="text-sm text-muted-foreground">{agent.runtime} · {agent.model}</p>
                    </div>
                  </div>
                  <Badge variant="outline">{config.label}</Badge>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-6">
                  <div className="flex items-center gap-3">
                    <Cpu className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <div className="text-2xl font-mono">{agent.cpu}%</div>
                      <div className="text-xs text-muted-foreground">CPU</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <div className="text-2xl font-mono">{agent.activeRuns}</div>
                      <div className="text-xs text-muted-foreground">Runs</div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
