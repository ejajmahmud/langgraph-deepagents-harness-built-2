import axios from 'axios'

// ==================== API 客户端 ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，清除本地存储
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ==================== API 接口 ====================

// 认证相关
export const authAPI = {
  login: (username: string, password: string) =>
    apiClient.post('/auth/login', { username, password }),

  register: (username: string, password: string) =>
    apiClient.post('/auth/register', { username, password }),

  refreshToken: (refreshToken: string) =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),

  getMe: () => apiClient.get('/auth/me'),

  createApiKey: () => apiClient.post('/auth/api-key'),
}

// 系统状态
export const systemAPI = {
  getHealth: () => apiClient.get('/health'),

  getStatus: () => apiClient.get('/api/status'),

  getPerformance: () => apiClient.get('/api/performance'),
}

// 策略管理
export const strategyAPI = {
  list: () => apiClient.get('/api/strategies'),

  get: (name: string) => apiClient.get(`/api/strategies/${name}`),

  update: (name: string, config: any) =>
    apiClient.put(`/api/strategies/${name}`, config),

  toggle: (name: string, enabled: boolean) =>
    apiClient.post(`/api/strategies/${name}/toggle`, { enabled }),

  scan: (strategyType: string = 'all') =>
    apiClient.post('/api/strategies/scan', { strategy_type: strategyType }),

  getRecommendations: () => apiClient.get('/api/strategies/recommendations'),

  optimize: (name: string, marketConditions: any) =>
    apiClient.post(`/api/strategies/${name}/optimize`, { market_conditions: marketConditions }),
}

// 交易管理
export const tradeAPI = {
  execute: (opportunityIndex: number, strategyType: string = 'all') =>
    apiClient.post('/api/trade/execute', {
      opportunity_index: opportunityIndex,
      strategy_type: strategyType,
    }),

  history: (params?: { limit?: number; offset?: number; strategy?: string }) =>
    apiClient.get('/api/trade/history', { params }),

  export: (params?: { start_date?: string; end_date?: string; strategy?: string }) =>
    apiClient.get('/api/trade/export', { params, responseType: 'blob' }),
}

// 市场数据
export const marketAPI = {
  getPrice: (symbol: string) => apiClient.get(`/api/market/price/${symbol}`),

  getPrices: (symbols: string[]) =>
    apiClient.post('/api/market/prices', { symbols }),

  getHistory: (symbol: string, period: string = '1h', limit: number = 100) =>
    apiClient.get(`/api/market/history/${symbol}`, {
      params: { period, limit },
    }),

  getOpportunities: () => apiClient.get('/api/market/opportunities'),
}

// 风险管理
export const riskAPI = {
  getConfig: () => apiClient.get('/api/risk/config'),

  updateConfig: (config: any) => apiClient.put('/api/risk/config', config),

  getHealth: () => apiClient.get('/api/risk/health'),

  getRecommendations: () => apiClient.get('/api/risk/recommendations'),
}

// 监控告警
export const monitoringAPI = {
  getMetrics: () => apiClient.get('/api/monitoring/metrics'),

  getAlerts: (params?: { limit?: number; acknowledged?: boolean }) =>
    apiClient.get('/api/monitoring/alerts', { params }),

  acknowledgeAlert: (alertId: string) =>
    apiClient.put(`/api/monitoring/alerts/${alertId}/acknowledge`),

  getHealth: () => apiClient.get('/api/monitoring/health'),
}

// 回测
export const backtestAPI = {
  run: (strategyName: string, priceData: number[], backtestType: string = 'simple') =>
    apiClient.post('/api/backtest/run', {
      strategy_name: strategyName,
      price_data: priceData,
      backtest_type: backtestType,
    }),

  runAll: (priceData: number[]) =>
    apiClient.post('/api/backtest/run-all', { price_data: priceData }),

  getResults: () => apiClient.get('/api/backtest/results'),
}

// 智能决策
export const intelligentAPI = {
  getRecommendation: (marketConditions: any, priceData?: number[]) =>
    apiClient.post('/api/intelligent/recommendation', {
      market_conditions: marketConditions,
      price_data: priceData,
    }),

  assessRisk: (strategyName: string, opportunity: any, marketConditions: any) =>
    apiClient.post('/api/intelligent/assess-risk', {
      strategy_name: strategyName,
      opportunity,
      market_conditions: marketConditions,
    }),

  detectAnomalies: (priceData: number[]) =>
    apiClient.post('/api/intelligent/detect-anomalies', { price_data: priceData }),

  getOptimizationSuggestions: (strategyName: string) =>
    apiClient.get(`/api/intelligent/optimization/${strategyName}`),
}

// V55/V56 套利系统 API - V56.2新增
export const v55API = {
  // 获取当前套利信号
  getSignals: () => apiClient.get('/api/v55/signals'),

  // 获取持仓列表
  getPositions: () => apiClient.get('/api/v55/positions'),

  // 执行套利决策
  executeArbitrage: (decision: any) =>
    apiClient.post('/api/v55/execute', decision),

  // 获取跨链数据
  getCrossChainData: (token?: string) =>
    apiClient.get('/api/v55/cross-chain', { params: { token } }),

  // 获取ML预测
  getMLPrediction: (token: string, horizon: string = '1h') =>
    apiClient.get('/api/v55/ml/prediction', { params: { token, horizon } }),

  // 获取交易所状态
  getExchangeStatus: () => apiClient.get('/api/v55/exchanges/status'),

  // 获取风险管理器状态
  getRiskStatus: () => apiClient.get('/api/v55/risk/status'),
}

export default apiClient
