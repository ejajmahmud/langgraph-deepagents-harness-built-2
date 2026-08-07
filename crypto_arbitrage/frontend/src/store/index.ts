import { create } from 'zustand'
import {
  SystemStatus,
  Strategy,
  Opportunity,
  Trade,
  MarketData,
  Alert,
  MonitoringMetrics,
  V55ArbitrageSignal,
  Position,
} from '@/types'
import { systemAPI, strategyAPI, marketAPI, tradeAPI, v55API } from '@/api'

// ==================== 全局 Store ====================

interface AppState {
  // 系统状态
  systemStatus: SystemStatus | null
  isAgentRunning: boolean
  isLoading: boolean
  error: string | null

  // 策略
  strategies: Strategy[]
  opportunities: Opportunity[]

  // 交易
  trades: Trade[]
  totalProfit: number
  winRate: number
  totalTrades: number

  // 市场数据
  marketData: Record<string, MarketData>
  selectedSymbol: string

  // 告警
  alerts: Alert[]
  unreadAlerts: number

  // 监控指标
  monitoringMetrics: MonitoringMetrics | null

  // WebSocket 连接
  wsConnected: boolean

  // V55 套利系统状态 - V56.2新增
  v55Signals: V55ArbitrageSignal[]
  v55Positions: Position[]
  exchangeStatus: Record<string, boolean>

  // Actions
  fetchSystemStatus: () => Promise<void>
  fetchStrategies: () => Promise<void>
  fetchOpportunities: () => Promise<void>
  fetchTrades: () => Promise<void>
  fetchMarketData: (symbols: string[]) => Promise<void>
  fetchAlerts: () => Promise<void>
  fetchMonitoringMetrics: () => Promise<void>

  // V55 Actions - V56.2新增
  fetchV55Signals: () => Promise<void>
  fetchV55Positions: () => Promise<void>
  executeV55Arbitrage: (decision: any) => Promise<any>
  fetchExchangeStatus: () => Promise<void>

  updateSystemStatus: (status: SystemStatus) => void
  updateStrategies: (strategies: Strategy[]) => void
  updateOpportunities: (opportunities: Opportunity[]) => void
  updateTrades: (trades: Trade[]) => void
  updateMarketData: (data: MarketData) => void
  updateAlerts: (alerts: Alert[]) => void
  updateMonitoringMetrics: (metrics: MonitoringMetrics) => void

  setWsConnected: (connected: boolean) => void
  setSelectedSymbol: (symbol: string) => void
  clearError: () => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // 初始状态
  systemStatus: null,
  isAgentRunning: false,
  isLoading: false,
  error: null,

  strategies: [],
  opportunities: [],

  trades: [],
  totalProfit: 0,
  winRate: 0,
  totalTrades: 0,

  marketData: {},
  selectedSymbol: 'BTC/USDT',

  alerts: [],
  unreadAlerts: 0,

  monitoringMetrics: null,

  wsConnected: false,

  // V55 初始状态 - V56.2新增
  v55Signals: [],
  v55Positions: [],
  exchangeStatus: {},

  // ==================== 异步 Actions ====================

  fetchSystemStatus: async () => {
    try {
      set({ isLoading: true, error: null })
      const response = await systemAPI.getHealth()
      const status = response.data

      set({
        systemStatus: status,
        isAgentRunning: status.agent_running,
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || '获取系统状态失败',
      })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchStrategies: async () => {
    try {
      set({ isLoading: true, error: null })
      const response = await strategyAPI.list()
      set({ strategies: response.data.strategies || [] })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || '获取策略列表失败',
      })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchOpportunities: async () => {
    try {
      const response = await marketAPI.getOpportunities()
      set({ opportunities: response.data.opportunities || [] })
    } catch (error: any) {
      console.error('获取套利机会失败:', error)
    }
  },

  fetchTrades: async () => {
    try {
      set({ isLoading: true, error: null })
      const response = await tradeAPI.history({ limit: 100 })
      const trades = response.data.trades || []

      // 计算统计指标
      const completedTrades = trades.filter((t: Trade) => t.status === 'completed')
      const totalProfit = completedTrades.reduce(
        (sum: number, t: Trade) => sum + t.actual_profit,
        0
      )
      const winRate = completedTrades.length > 0
        ? (completedTrades.filter((t: Trade) => t.actual_profit > 0).length /
           completedTrades.length) * 100
        : 0

      set({
        trades,
        totalProfit,
        winRate,
        totalTrades: trades.length,
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || error.message || '获取交易历史失败',
      })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchMarketData: async (symbols: string[]) => {
    try {
      const response = await marketAPI.getPrices(symbols)
      const data = response.data.prices || {}

      set((state) => ({
        marketData: { ...state.marketData, ...data },
      }))
    } catch (error: any) {
      console.error('获取市场数据失败:', error)
    }
  },

  fetchAlerts: async () => {
    try {
      const response = await monitoringAPI.getAlerts({ limit: 50 })
      const alerts = response.data.alerts || []
      const unreadCount = alerts.filter((a: Alert) => !a.acknowledged).length

      set({ alerts, unreadAlerts: unreadCount })
    } catch (error: any) {
      console.error('获取告警失败:', error)
    }
  },

  fetchMonitoringMetrics: async () => {
    try {
      const response = await monitoringAPI.getMetrics()
      set({ monitoringMetrics: response.data.metrics })
    } catch (error: any) {
      console.error('获取监控指标失败:', error)
    }
  },

  // ==================== 同步 Actions ====================

  updateSystemStatus: (status: SystemStatus) => set({ systemStatus: status }),

  updateStrategies: (strategies: Strategy[]) => set({ strategies }),

  updateOpportunities: (opportunities: Opportunity[]) => set({ opportunities }),

  updateTrades: (trades: Trade[]) => set({ trades }),

  updateMarketData: (data: MarketData) =>
    set((state) => ({
      marketData: { ...state.marketData, [data.symbol]: data },
    })),

  updateAlerts: (alerts: Alert[]) => set({ alerts }),

  updateMonitoringMetrics: (metrics: MonitoringMetrics) =>
    set({ monitoringMetrics: metrics }),

  setWsConnected: (connected: boolean) => set({ wsConnected: connected }),

  setSelectedSymbol: (symbol: string) => set({ selectedSymbol: symbol }),

  // ==================== V55 Actions - V56.2新增 ====================

  fetchV55Signals: async () => {
    try {
      const response = await v55API.getSignals()
      set({ v55Signals: response.data.signals || [] })
    } catch (error: any) {
      console.error('获取V55信号失败:', error)
    }
  },

  fetchV55Positions: async () => {
    try {
      const response = await v55API.getPositions()
      set({ v55Positions: response.data.positions || [] })
    } catch (error: any) {
      console.error('获取V55持仓失败:', error)
    }
  },

  executeV55Arbitrage: async (decision: any) => {
    try {
      const response = await v55API.executeArbitrage(decision)
      return response.data
    } catch (error: any) {
      console.error('执行V55套利失败:', error)
      throw error
    }
  },

  fetchExchangeStatus: async () => {
    try {
      const response = await v55API.getExchangeStatus()
      set({ exchangeStatus: response.data.status || {} })
    } catch (error: any) {
      console.error('获取交易所状态失败:', error)
    }
  },

  clearError: () => set({ error: null }),
}))
