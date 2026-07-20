import { useAppStore } from '@/store/useAppStore'

class ACCWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnects = 10
  private url: string = ''

  connect(url: string = 'ws://localhost:8100/ws') {
    this.url = url
    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'agent_status') {
            useAppStore.getState().updateAgentStatus(
              data.agentId,
              data.status
            )
          }
          if (data.type === 'run_event') {
            useAppStore.getState().addRunEvent?.(data)
          }
        } catch {}
      }

      this.ws.onclose = () => {
        if (this.reconnectAttempts < this.maxReconnects) {
          const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000)
          setTimeout(() => this.connect(url), delay)
          this.reconnectAttempts++
        }
      }

      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch {}
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const accWS = new ACCWebSocket()
