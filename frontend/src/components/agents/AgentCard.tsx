import { Cpu, Activity } from 'lucide-react'

export function AgentCard({ agent }: { agent: any }) {
  const statusColor = {
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    offline: 'bg-zinc-500',
  }[agent.status] || 'bg-emerald-500'

  const tokenPercent = Math.round((agent.tokens_used / agent.tokens_limit) * 100)
  const budgetPercent = Math.round((agent.budget_used / agent.budget_limit) * 100)

  return (
    <div className="bg-card border border-border hover:border-primary/50 p-8 transition-colors group">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className={`w-4 h-4 ${statusColor} flex-shrink-0`} />
            <div className="text-2xl font-mono font-bold tracking-tighter">{agent.name}</div>
          </div>
          <div className="text-muted-foreground mt-1 text-sm">{agent.runtime} · {agent.model}</div>
          {agent.provider && (
            <div className="mt-2 flex items-center gap-2 text-xs">
              <span className="bg-secondary px-3 py-1">{agent.provider}</span>
              <span className="font-mono text-muted-foreground">{agent.account}</span>
            </div>
          )}
        </div>
        <div className="text-emerald-500 text-xs uppercase tracking-[2px] font-medium">{agent.status}</div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-10 mb-10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground uppercase tracking-widest">CPU %</span>
          </div>
          <div className="text-5xl font-mono font-bold tabular-nums">{agent.cpu}</div>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground uppercase tracking-widest">RUNS</span>
          </div>
          <div className="text-5xl font-mono font-bold tabular-nums">{agent.active_runs || agent.activeRuns}</div>
        </div>
      </div>

      {/* Limits */}
      <div className="space-y-6">
        <div>
          <div className="flex justify-between text-xs mb-2 text-muted-foreground">
            <span className="uppercase tracking-wider">Tokens</span>
            <span className="font-mono">{agent.tokens_used?.toLocaleString()} / {agent.tokens_limit?.toLocaleString()}</span>
          </div>
          <div className="h-1 bg-secondary">
            <div className="h-1 bg-foreground transition-all duration-500" style={{ width: `${tokenPercent}%` }} />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-2 text-muted-foreground">
            <span className="uppercase tracking-wider">Budget</span>
            <span className="font-mono">${agent.budget_used} / ${agent.budget_limit}</span>
          </div>
          <div className="h-1 bg-secondary">
            <div className="h-1 bg-foreground transition-all duration-500" style={{ width: `${budgetPercent}%` }} />
          </div>
        </div>
      </div>

      <button
        onClick={() => alert('Handoff started for ' + agent.name)}
        className="mt-10 w-full border border-border hover:bg-secondary py-4 text-sm font-medium tracking-widest uppercase transition-colors"
      >
        Quick Handoff
      </button>
    </div>
  )
}
