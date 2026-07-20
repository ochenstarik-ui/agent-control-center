import { TaskCard } from './TaskCard'
import { useQuery } from '@tanstack/react-query'

const columns = ['todo', 'in_progress', 'review', 'done']

export function Kanban() {
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const res = await fetch('/api/v1/tasks')
      return res.json()
    },
  })

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Project Kanban</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {columns.map((status) => (
          <div key={status} className="bg-card border border-border rounded-3xl p-4">
            <h3 className="uppercase text-xs tracking-widest text-muted-foreground mb-4 px-1">
              {status.replace('_', ' ')}
              <span className="ml-2 text-zinc-600">
                {tasks.filter((t: any) => t.status === status).length}
              </span>
            </h3>
            <div className="space-y-3">
              {tasks
                .filter((t: any) => t.status === status)
                .map((task: any) => (
                  <TaskCard key={task.id} task={task} />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
