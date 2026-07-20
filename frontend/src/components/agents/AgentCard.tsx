import { motion } from 'framer-motion'
import { Cpu, Activity, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export function AgentCard({ agent }: { agent: any }) {
  const statusColor = {
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    offline: 'bg-zinc-500',
  }[agent.status] || 'bg-zinc-500'

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      className="group bg-card/80 border border-border hover:border-primary/50 rounded-3xl p-6 transition-all duration-300 backdrop-blur-xl"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className={`w-5 h-5 rounded-2xl ${statusColor} flex-shrink-0 ring-4 ring-background`} />
          <div>
            <div className="font-semibold text-xl tracking-tight">{agent.name}</div>
            <div className="text-muted-foreground text-sm">{agent.runtime} · {agent.model}</div>
          </div>
        </div>
        <Badge variant="outline">{agent.status}</Badge>
      </div>

      <div className="mt-8 flex gap-8">
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
            <div className="text-3xl font-mono font-semibold tabular-nums">{agent.activeRuns}</div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground -mt-1">RUNS</div>
          </div>
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
