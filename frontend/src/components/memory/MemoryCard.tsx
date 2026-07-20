import { Card } from '@/components/ui/card'
import { BookOpen } from 'lucide-react'

export function MemoryCard() {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-5">
        <BookOpen className="w-5 h-5 text-violet-500" />
        <h3 className="font-semibold">Project Memory</h3>
      </div>

      <div className="space-y-4 text-sm">
        <div className="border-l-2 border-violet-500 pl-4">
          <div className="font-medium">Решение по OAuth</div>
          <div className="text-muted-foreground text-xs">2 hours ago · Hermes-01</div>
        </div>
        <div className="border-l-2 border-violet-500 pl-4">
          <div className="font-medium">API keys rotated</div>
          <div className="text-muted-foreground text-xs">Yesterday · Supervisor</div>
        </div>
      </div>

      <button className="mt-6 text-sm text-violet-400 hover:text-violet-300 w-full py-2 border border-dashed border-border rounded-2xl transition-colors">
        + Add new memory entry
      </button>
    </Card>
  )
}
