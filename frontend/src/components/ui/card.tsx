import { cn } from '@/lib/utils'

interface CardProps {
  className?: string
  children: React.ReactNode
}

export function Card({ className, children }: CardProps) {
  return (
    <div className={cn('bg-card border border-border rounded-2xl', className)}>
      {children}
    </div>
  )
}
