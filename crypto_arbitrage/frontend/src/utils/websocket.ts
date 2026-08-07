import { useAppStore } from '@/store'
import { WSMessage } from '@/types'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: any = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000 // 3秒

  constructor() {
    this.connect()
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onclose = this.handleClose.bind(this)

      console.log('WebSocket 连接中...', wsUrl)
    } catch (error) {
      console.error('WebSocket 连接失败:', error)
      this.scheduleReconnect()
    }
  }

  private handleOpen() {
    console.log('WebSocket 已连接')
    const store = useAppStore.getState()
    store.setWsConnected(true)

    // 订阅所有主题
    this.subscribe('*')

    // 重置重连计数
    this.reconnectAttempts = 0
  }

  private handleMessage(event: MessageEvent) {
    try {
      const message: WSMessage = JSON.parse(event.data)
      console.log('收到WebSocket消息:', message)

      const store = useAppStore.getState()

      switch (message.type) {
        case 'system_status':
          store.updateSystemStatus(message.data)
          break

        case 'price_update':
          store.updateMarketData(message.data)
          break

        case 'opportunity':
          console.log('新套利机会:', message.data)
          break

        case 'trade_update':
          // 重新加载交易历史
          store.fetchTrades()
          break

        case 'alert':
          // 添加新告警
          const alerts = [message.data, ...store.alerts]
          store.updateAlerts(alerts)
          break

        case 'performance_update':
          store.updateMonitoringMetrics(message.data)
          break

        default:
          console.warn('未知消息类型:', message.type)
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  private handleError(error: Event) {
    console.error('WebSocket 错误:', error)
    const store = useAppStore.getState()
    store.setWsConnected(false)
  }

  private handleClose() {
    console.log('WebSocket 连接关闭')
    const store = useAppStore.getState()
    store.setWsConnected(false)

    this.scheduleReconnect()
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket 重连失败，已达到最大重连次数')
      return
    }

    this.reconnectAttempts++

    console.log(`WebSocket 将在 ${this.reconnectDelay}ms 后尝试重连... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, this.reconnectDelay)
  }

  subscribe(topic: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'subscribe', topic }))
    }
  }

  unsubscribe(topic: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'unsubscribe', topic }))
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    const store = useAppStore.getState()
    store.setWsConnected(false)
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket 未连接，无法发送消息')
    }
  }
}

// 创建全局实例
let wsInstance: WebSocketService | null = null

export const getWebSocketService = (): WebSocketService => {
  if (!wsInstance) {
    wsInstance = new WebSocketService()
  }
  return wsInstance
}

export default WebSocketService
