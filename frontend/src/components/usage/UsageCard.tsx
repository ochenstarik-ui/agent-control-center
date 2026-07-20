import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Zap, Wallet } from 'lucide-react'

export function UsageCard() {
  const usage = {
    tokensUsed: 124800,
    tokensLimit: 200000,
    budgetUsed: 42.5,
    budgetLimit: 100,
  }

  const tokenPercent = Math.round((usage.tokensUsed / usage.tokensLimit) * 100)
  const budgetPercent = Math.round((usage.budgetUsed / usage.budgetLimit) * 100)

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Zap className="w-5 h-5 text-amber-500" />
          <h3 className="font-semibold">Usage & Limits</h3>
        </div>
        <span className="text-xs text-muted-foreground">Today</span>
      </div>

      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-muted-foreground">Tokens</span>
          <span className="font-mono text-sm">
            {usage.tokensUsed.toLocaleString()} / {usage.tokensLimit.toLocaleString()}
          </span>
        </div>
        <Progress value={tokenPercent} />
        <div className="text-right text-xs text-muted-foreground mt-1">{tokenPercent}% used</div>
      </div>

      <div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-muted-foreground flex items-center gap-1">
            <Wallet className="w-4 h-4" /> Budget
          </span>
          <span className="font-mono text-sm">${usage.budgetUsed} / ${usage.budgetLimit}</span>
        </div>
        <Progress value={budgetPercent} />
        <div className="text-right text-xs text-muted-foreground mt-1">
          {budgetPercent}% used · ${usage.budgetLimit - usage.budgetUsed} left
        </div>
      </div>
    </Card>
  )
}
