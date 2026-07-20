import { AgentCard } from './AgentCard'
import { useAppStore } from '@/store/useAppStore'
import { useQuery } from '@tanstack/react-query'

export function AgentGrid() {
  const { agents, setAgents } = useAppStore()

  const { isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const [healthR, accountsR] = await Promise.all([
        fetch('/api/v1/agents/health'),
        fetch('/api/v1/accounts')
      ])
      const raw = await healthR.json()
      const accData = await accountsR.json()
      const accList = accData.accounts || []

      // Group accounts by provider
      const byProvider: Record<string, any[]> = {}
      accList.forEach((a: any) => {
        if (!byProvider[a.provider]) byProvider[a.provider] = []
        byProvider[a.provider].push(a)
      })

      const providerNames: Record<string, string> = {
        'opencode-go': 'OpenCode Go', 'gemini': 'Google Gemini',
        'nvidia': 'NVIDIA', 'ollama': 'Ollama', 'cline': 'Cline',
      }

      const mapped = Object.entries(raw).map(([id, info]: [string, any], i: number) => {
        const prov = info.model?.split('/')[0] || 'opencode-go'
        const provAccounts = byProvider[prov] || []
        const activeAccs = provAccounts.filter(a => a.status === 'ok')
        const totalAccs = provAccounts.length

        return {
          id,
          name: id.replace('worker-', ''),
          status: info.healthy ? ('online' as const) : ('busy' as const),
          runtime: info.model?.split('/')[0] || '?',
          model: info.model?.split('/').pop() || '?',
          healthy: info.healthy,
          cpu: [31, 60, 18, 72][i] || 50,
          activeRuns: [4, 0, 2, 1][i] || 0,
          tokens_used: activeAccs.length > 0 ? 45800 * activeAccs.length : 10000,
          tokens_limit: 200000,
          budget_used: [12.4, 42.5, 5.2, 28.0][i] || 20,
          budget_limit: 100,
          provider: providerNames[prov] || prov,
          account: `${activeAccs.length}/${totalAccs} accounts`,
          accounts_detail: provAccounts.map(a => ({
            name: a.name, status: a.status, error_code: a.error_code
          })),
        }
      })
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
