import { motion } from 'framer-motion'
import { Cpu, Activity, Zap, Wallet } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

export function AgentCard({ agent }: { agent: any }) {
  const statusColor = {
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    offline: 'bg-zinc-500',
  }[agent.status] || 'bg-emerald-500'

  const tokenPercent = Math.round((agent.tokens_used / agent.tokens_limit) * 100)
  const budgetPercent = Math.round((agent.budget_used / agent.budget_limit) * 100)

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      className="group bg-card/80 border border-border hover:border-primary/50 rounded-3xl p-6 transition-all duration-300 backdrop-blur-xl"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-4">
            <div className={`w-5 h-5 rounded-2xl ${statusColor} flex-shrink-0 ring-4 ring-background`} />
            <div>
              <div className="font-semibold text-xl tracking-tight">{agent.name}</div>
              <div className="text-muted-foreground text-sm">{agent.runtime} · {agent.model}</div>
            </div>
          </div>
          {agent.provider && (
            <div className="mt-3 flex items-center gap-2 text-xs">
              <div className="px-2.5 py-0.5 bg-secondary rounded-full text-muted-foreground">
                {agent.provider}
              </div>
              <div className="text-muted-foreground font-mono">{agent.account}</div>
            </div>
          )}
        </div>
        <div className="text-xs uppercase tracking-widest text-emerald-500 font-medium">{agent.status}</div>
      </div>

      {/* Main metrics */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="flex items-center gap-3">
          <Cpu className="w-6 h-6 text-muted-foreground" />
          <div>
            <div className="text-3xl font-mono font-semibold tabular-nums">{agent.cpu}</div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground -mt-1">CPU %</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-muted-foreground" />
          <div>
            <div className="text-3xl font-mono font-semibold tabular-nums">{agent.active_runs || agent.activeRuns}</div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground -mt-1">RUNS</div>
          </div>
        </div>
      </div>

      {/* Per-agent Usage Limits */}
      <div className="space-y-4 text-sm border-t border-border pt-5">
        <div>
          <div className="flex justify-between mb-1.5">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Zap className="w-4 h-4" /> Tokens
            </span>
            <span className="font-mono text-muted-foreground text-xs">
              {agent.tokens_used?.toLocaleString()} / {agent.tokens_limit?.toLocaleString()}
            </span>
          </div>
          <Progress value={tokenPercent} />
        </div>

        <div>
          <div className="flex justify-between mb-1.5">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Wallet className="w-4 h-4" /> Budget
            </span>
            <span className="font-mono text-muted-foreground text-xs">
              ${agent.budget_used} / ${agent.budget_limit}
            </span>
          </div>
          <Progress value={budgetPercent} />
        </div>
      </div>

      <button
        onClick={() => alert('Handoff started for ' + agent.name)}
        className="mt-6 w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-2xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
      >
        <Zap className="w-4 h-4" />
        Quick Handoff
      </button>
    </motion.div>
  )
}
