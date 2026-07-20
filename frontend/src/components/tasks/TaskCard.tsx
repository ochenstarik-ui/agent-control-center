import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const statusColors: Record<string, string> = {
  todo: 'bg-zinc-700',
  in_progress: 'bg-blue-600',
  review: 'bg-amber-600',
  done: 'bg-emerald-600',
}

export function TaskCard({ task }: { task: any }) {
  return (
    <Card className="p-4 hover:shadow-lg transition-shadow cursor-pointer border-border hover:border-primary/30">
      <div className="flex justify-between items-start">
        <h4 className="font-medium text-sm">{task.title}</h4>
        <Badge variant="outline">{task.status.replace('_', ' ')}</Badge>
      </div>
      {task.description && (
        <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{task.description}</p>
      )}
      {task.assignee_agent_id && (
        <div className="mt-3 text-xs text-muted-foreground flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          {task.assignee_agent_id}
        </div>
      )}
    </Card>
  )
}
