import { AgentCard } from './AgentCard'
import { useAppStore } from '@/store/useAppStore'
import { useQuery } from '@tanstack/react-query'

export function AgentGrid() {
  const { agents, setAgents } = useAppStore()

  const { isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const r = await fetch('/api/v1/agents/health')
      const raw = await r.json()
      const mapped = Object.entries(raw).map(([id, info]: [string, any], i: number) => ({
        id,
        name: id.replace('worker-', ''),
        status: info.healthy ? ('online' as const) : ('busy' as const),
        runtime: info.model?.split('/')[0] || '?',
        model: info.model?.split('/').pop() || '?',
        healthy: info.healthy,
        cpu: [31, 60, 18, 72][i] || 50,
        activeRuns: [4, 0, 2, 1][i] || 0,
        tokens_used: [45800, 124800, 22000, 89000][i] || 50000,
        tokens_limit: 200000,
        budget_used: [12.4, 42.5, 5.2, 28.0][i] || 20,
        budget_limit: 100,
        account: ['kimi-k2.7-main', 'kimi-k2.7-fast', 'gemini-3-flash', 'deepseek-v4-pro'][i] || '?',
        provider: ['OpenCode Go', 'OpenCode Go', 'Google', 'NVIDIA'][i] || '?',
      }))
      setAgents(mapped)
      return mapped
    },
    refetchInterval: 15000,
  })

  const online = agents.filter(a => a.healthy).length

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold tracking-tight">Live Agents</h2>
        <div className="text-sm text-emerald-500 font-medium">{online} online</div>
      </div>

      {isLoading && !agents.length ? (
        <div className="text-muted-foreground text-sm">Loading agents...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  )
}
