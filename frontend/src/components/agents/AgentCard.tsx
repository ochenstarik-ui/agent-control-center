import { motion } from 'framer-motion'

export function AgentCard({ agent }: { agent: any }) {
  const tokenPercent = Math.round((agent.tokens_used / agent.tokens_limit) * 100)
  const budgetPercent = Math.round((agent.budget_used / agent.budget_limit) * 100)

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-card border border-border p-8 hover:border-primary/50 transition-colors h-full flex flex-col"
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3">
            <div className={`w-4 h-4 ${agent.healthy !== false ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
            <div className="text-2xl font-mono font-bold tracking-tighter">{agent.name}</div>
          </div>
          <div className="mt-1 text-muted-foreground text-sm">{agent.runtime} · {agent.model}</div>
        </div>
        <div className="text-emerald-500 text-xs uppercase tracking-widest font-medium">
          {agent.healthy !== false ? 'ONLINE' : 'OFFLINE'}
        </div>
      </div>

      {/* Account */}
      <div className="mb-8 flex items-center gap-2 text-xs">
        <span className="bg-secondary px-3 py-1">{agent.provider}</span>
        <span className="font-mono text-muted-foreground">{agent.account}</span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-12 mb-10">
        <div>
          <div className="text-6xl font-mono font-bold tabular-nums">{agent.cpu}</div>
          <div className="text-xs uppercase tracking-widest text-muted-foreground">CPU %</div>
        </div>
        <div>
          <div className="text-6xl font-mono font-bold tabular-nums">{agent.activeRuns}</div>
          <div className="text-xs uppercase tracking-widest text-muted-foreground">RUNS</div>
        </div>
      </div>

      {/* Usage */}
      <div className="mt-auto space-y-8">
        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-2">
            <span className="uppercase tracking-wider">Tokens</span>
            <span className="font-mono">{agent.tokens_used?.toLocaleString()} / {agent.tokens_limit?.toLocaleString()}</span>
          </div>
          <div className="h-1 bg-secondary">
            <div className="h-1 bg-foreground transition-all duration-500" style={{ width: `${tokenPercent}%` }} />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-2">
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
        className="mt-10 w-full border border-border hover:bg-secondary py-4 text-sm tracking-widest uppercase font-medium transition-colors"
      >
        Quick Handoff
      </button>
    </motion.div>
  )
}
