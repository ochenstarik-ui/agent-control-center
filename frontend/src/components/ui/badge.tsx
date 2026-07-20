import { cn } from '@/lib/utils'

interface BadgeProps {
  variant?: 'default' | 'outline'
  children: React.ReactNode
}

export function Badge({ variant = 'default', children }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variant === 'outline'
          ? 'border border-border text-muted-foreground'
          : 'bg-primary text-primary-foreground'
      )}
    >
      {children}
    </span>
  )
}
