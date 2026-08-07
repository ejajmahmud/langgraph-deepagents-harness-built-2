// ==================== 系统状态 ====================

export interface SystemStatus {
  status: 'healthy' | 'unavailable'
  agent_running: boolean
  strategies_count: number
  timestamp: string
  uptime_hours?: number
  total_errors?: number
  price_stream?: PriceStreamStatus
}

export interface PriceStreamStatus {
  connected: boolean
  symbols: string[]
  last_update: string
}

// ==================== 策略相关 ====================

export interface Strategy {
  name: string
  type: 'cross_exchange' | 'triangular' | 'basis_trading' | 'funding_rate' | 'statistical_arbitrage'
  enabled: boolean
  state: 'running' | 'paused' | 'stopped' | 'error'
  min_profit_rate: number
  max_position_size: number
  performance: StrategyPerformance
  config: Record<string, any>
}

export interface StrategyPerformance {
  total_trades: number
  successful_trades: number
  total_profit: number
  average_profit_rate: number
  success_rate: number
  consecutive_losses: number
  total_scans: number
  uptime_seconds: number
}

// ==================== 交易相关 ====================

export interface Opportunity {
  strategy: string
  symbol: string
  profit_rate: number
  expected_profit: number
  buy_exchange: string
  sell_exchange: string
  buy_price: number
  sell_price: number
  timestamp: number
  liquidity?: number
  volatility?: number
}

export interface Trade {
  id: string
  strategy: string
  symbol: string
  status: 'completed' | 'failed' | 'rejected'
  expected_profit: number
  actual_profit: number
  expected_profit_rate: number
  actual_profit_rate: number
  order_ids: Record<string, string>
  error?: string
  timestamp: number
}

// ==================== 市场数据 ====================

export interface MarketData {
  symbol: string
  price: number
  change_24h: number
  volume_24h: number
  high_24h: number
  low_24h: number
  timestamp: number
}

export interface PriceHistory {
  timestamp: number
  price: number
  volume: number
}

// ==================== 风险管理 ====================

export interface RiskConfig {
  max_daily_loss: number
  max_position_size: number
  max_total_exposure: number
  max_drawdown: number
  min_liquidity_ratio: number
  base_stop_loss: number
  base_take_profit: number
  trailing_stop: number
  risk_reward_ratio: number
}

export interface HealthStatus {
  filesystem: boolean
  config: boolean
  python_env: boolean
  database: boolean
  strategies: boolean
  logs: boolean
  overall: boolean
  timestamp: string
}

// ==================== 告警相关 ====================

export interface Alert {
  id: string
  level: 'info' | 'warning' | 'error' | 'critical'
  message: string
  source: string
  timestamp: number
  acknowledged: boolean
}

// ==================== 监控指标 ====================

export interface MonitoringMetrics {
  total_trades: number
  successful_trades: number
  total_profit: number
  win_rate: number
  total_errors: number
  system_health: number
  timestamp: number
}

// ==================== V56 套利系统类型 ====================

// V55 执行模式
export type V55ExecutionMode = 'cross_chain' | 'traditional' | 'fusion' | 'backtest' | 'live'

// V55 交易所
export type Exchange = 'binance' | 'coinbase' | 'bybit' | 'okx' | 'kraken' | 'kucoin' | 'gateio'

// V55 套利信号
export interface V55ArbitrageSignal {
  signal_id: string
  opportunity_type: string
  token: string
  source: string
  target: string
  spread_pct: number
  expected_profit: number
  confidence: number
  risk_score: number
  ml_prediction: number
  bridge_fee_pct: number
  exchange_fees: Record<string, number>
  cross_chain_data?: Record<string, any>
  traditional_data?: Record<string, any>
  timestamp: number
}

// V55 套利决策
export interface V55ArbitrageDecision {
  decision_id: string
  signal: V55ArbitrageSignal
  position_size: number
  entry_price: number
  exit_price: number
  stop_loss: number
  expected_profit: number
  risk_adjusted_profit: number
  execution_plan: Record<string, any>[]
  execution_mode: V55ExecutionMode
  exchange_choice?: Exchange
  ttl: number
}

// V55 交易结果
export interface V55TradeResult {
  decision_id: string
  status: string
  executed: boolean
  profit?: number
  error?: string
  execution_time: number
  cross_chain_fees: number
  exchange_fees: number
  net_profit: number
  ml_metrics: Record<string, number>
}

// 持仓信息
export interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  size: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
  open_time: number
  exchange: Exchange
  strategy: string
}

// ==================== WebSocket 消息 ====================

export type WSMessageType =
  | 'price_update'
  | 'opportunity'
  | 'trade_update'
  | 'system_status'
  | 'alert'
  | 'performance_update'
  | 'signal_update'

export interface WSMessage<T = any> {
  type: WSMessageType
  topic?: string
  data: T
  timestamp: number
}
