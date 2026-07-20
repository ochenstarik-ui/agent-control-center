import { cn } from '@/lib/utils'
import { Home, Users, FolderOpen, Zap, Settings, Activity } from 'lucide-react'

const menuItems = [
  { icon: Home, label: 'Dashboard', active: true },
  { icon: Users, label: 'Agents' },
  { icon: FolderOpen, label: 'Projects' },
  { icon: Zap, label: 'Tasks' },
  { icon: Activity, label: 'Activity' },
  { icon: Settings, label: 'Settings' },
]

export function Sidebar() {
  return (
    <div className="w-64 border-r border-border bg-card flex flex-col shrink-0">
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-sm">ACC</span>
          </div>
          <div>
            <div className="font-semibold text-sm">Control Center</div>
            <div className="text-xs text-muted-foreground">v0.2.0</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {menuItems.map((item) => (
          <a
            key={item.label}
            href="#"
            className={cn(
              'flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-colors',
              item.active
                ? 'bg-secondary text-foreground'
                : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
            )}
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </a>
        ))}
      </nav>

      <div className="p-4 border-t border-border text-xs text-muted-foreground">
        ● Connected · 4 Agents
      </div>
    </div>
  )
}
