import { motion } from 'framer-motion'
import { Cpu, Activity, Clock } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

interface Agent {
  id: string
  model: string
  healthy: boolean
  activeRuns: number
  totalTokens: number
}

async function fetchAgents(): Promise<Agent[]> {
  const r = await fetch('/api/v1/agents/health')
  const data = await r.json()
  return Object.entries(data).map(([id, info]: [string, any]) => ({
    id,
    model: info.model?.split('/').pop() || '?',
    healthy: info.healthy,
    activeRuns: 0,
    totalTokens: 0,
  }))
}

export function AgentGrid() {
  const { data: agents, isLoading } = useQuery({ queryKey: ['agents'], queryFn: fetchAgents })

  if (isLoading) return <div className="text-muted-foreground text-sm p-4">Loading agents...</div>

  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">Live Agents</h3>
      <div className="grid grid-cols-2 gap-3">
        {agents?.map((agent) => (
          <motion.div
            key={agent.id}
            whileHover={{ scale: 1.02 }}
            className="bg-card border border-border rounded-2xl p-4 hover:border-primary/30 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className={`w-2.5 h-2.5 rounded-full ${agent.healthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <div>
                <h4 className="font-semibold text-sm">{agent.id.replace('worker-', '')}</h4>
                <p className="text-xs text-muted-foreground">{agent.model}</p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Cpu className="w-3.5 h-3.5" />
                {agent.activeRuns} runs
              </div>
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Activity className="w-3.5 h-3.5" />
                {agent.totalTokens} tokens
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
