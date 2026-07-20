import { useState, useEffect } from 'react'
import { Command } from 'cmdk'
import { Search, Plus, Play, Zap, User } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const { agents, currentProject } = useAppStore()

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen(o => !o)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command Menu"
      className="fixed inset-0 z-50"
    >
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
      <div className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <Search className="w-5 h-5 text-muted-foreground shrink-0" />
          <Command.Input
            placeholder="Поиск команд... (напр. 'новый агент')"
            className="flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
          />
        </div>

        <Command.List className="max-h-80 overflow-auto p-2">
          <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
            Ничего не найдено
          </Command.Empty>

          <Command.Group heading="Действия" className="text-xs text-muted-foreground px-2 py-1.5">
            <Command.Item className="flex items-center gap-2 px-2 py-2 rounded-lg text-sm cursor-pointer data-[selected=true]:bg-secondary">
              <Plus className="w-4 h-4" /> Новая задача
            </Command.Item>
            <Command.Item className="flex items-center gap-2 px-2 py-2 rounded-lg text-sm cursor-pointer data-[selected=true]:bg-secondary">
              <Play className="w-4 h-4" /> Запустить run
            </Command.Item>
            <Command.Item className="flex items-center gap-2 px-2 py-2 rounded-lg text-sm cursor-pointer data-[selected=true]:bg-secondary">
              <Zap className="w-4 h-4" /> Быстрый handoff
            </Command.Item>
          </Command.Group>

          <Command.Group heading="Агенты" className="text-xs text-muted-foreground px-2 py-1.5 mt-2">
            {agents.map(agent => (
              <Command.Item
                key={agent.id}
                className="flex items-center gap-2 px-2 py-2 rounded-lg text-sm cursor-pointer data-[selected=true]:bg-secondary"
              >
                <User className="w-4 h-4" />
                {agent.name}
                <span className={`ml-auto w-2 h-2 rounded-full ${agent.healthy ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>

        <div className="px-4 py-2 border-t border-border text-xs text-muted-foreground flex gap-3">
          <span>↑↓ navigate</span>
          <span>↵ select</span>
          <span>Esc close</span>
        </div>
      </div>
    </Command.Dialog>
  )
}
