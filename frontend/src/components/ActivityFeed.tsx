import { GitBranch, MessageSquare, FileText, Clock } from 'lucide-react'

const events = [
  { icon: GitBranch, text: 'worker-code выполнил backtest', time: '2 min ago', color: 'text-emerald-400' },
  { icon: MessageSquare, text: 'worker-research завершил анализ', time: '15 min ago', color: 'text-blue-400' },
  { icon: FileText, text: 'Добавлен файл requirements.txt', time: '1 hour ago', color: 'text-muted-foreground' },
  { icon: Clock, text: 'Supervisor переключил worker-fast', time: '2 hours ago', color: 'text-amber-400' },
]

export function ActivityFeed() {
  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">Recent Activity</h3>
      <div className="space-y-3">
        {events.map((event, i) => (
          <div key={i} className="flex items-center gap-3 text-sm">
            <event.icon className={`w-4 h-4 shrink-0 ${event.color}`} />
            <span className="flex-1">{event.text}</span>
            <span className="text-xs text-muted-foreground">{event.time}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
