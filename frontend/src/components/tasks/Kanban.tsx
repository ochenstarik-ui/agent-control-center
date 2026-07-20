import { CheckCircle2, Circle, Plus } from 'lucide-react'
import { useState } from 'react'

interface Task { id: string; title: string; done: boolean; project: string }

export function Kanban() {
  const [tasks] = useState<Task[]>([
    { id: '1', title: 'Реализовать EMA-кроссовер', done: true, project: 'Trading' },
    { id: '2', title: 'Настроить CI/CD пайплайн', done: false, project: 'ACC' },
    { id: '3', title: 'Добавить health-check эндпоинт', done: true, project: 'ACC' },
    { id: '4', title: 'Обновить документацию API', done: false, project: 'ACC' },
  ])

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Tasks</h3>
        <button className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors">
          <Plus className="w-4 h-4" />
        </button>
      </div>
      <div className="space-y-1.5">
        {tasks.map(task => (
          <div key={task.id} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-secondary/50 transition-colors cursor-pointer group">
            {task.done
              ? <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              : <Circle className="w-4 h-4 text-muted-foreground shrink-0" />
            }
            <span className={`text-sm flex-1 ${task.done ? 'line-through text-muted-foreground' : ''}`}>
              {task.title}
            </span>
            <span className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
              {task.project}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
