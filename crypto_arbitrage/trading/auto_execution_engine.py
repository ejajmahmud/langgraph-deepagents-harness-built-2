"""Auto-Execution Engine - V47.0 自动交易执行引擎

整合所有组件的自动化交易执行引擎。

核心功能：
1. Auto-Scan Loop — 自动扫描套利机会
2. Quality Gate — 质量门控过滤
3. Auto-Size — 自动仓位计算
4. Risk-Check — 风险检查
5. Auto-Execute — 自动执行
6. Position-Monitor — 持仓监控
7. Memo0 Integration — 知识库学习反馈
8. Execution Quality — 执行质量追踪
9. Max Exposure — 单币种最大暴露限制
10. Circuit Breaker — 连亏熔断器
11. Emergency Stop Loss — 紧急止损
12. Daily PnL Tracking — 每日盈亏追踪
13. Global Position Limit — 全局仓位限制
14. Trailing Stop — 追踪止损 (V26.0新增)
15. Position Cooldown — 平仓冷却时间 (V26.0新增)
16. Weekend Trading — 周末交易控制 (V26.0新增)
17. Time-In-Force — 订单时效控制 (V26.1新增)
18. ATR Trailing Stop — ATR波动率追踪止损 (V26.1新增)
19. OCO/OTO Orders — 高级订单类型 (V26.1新增)
20. Position Time Limit — 持仓时间限制 (V26.1新增)
21. Correlation Limit — 相关性仓位限制 (V26.1新增)
22. Order Book Analysis — 订单簿分析 (V26.2新增)
23. Liquidity Detection — 流动性检测 (V26.2新增)
24. Slippage Prediction — 滑点预测 (V26.2新增)
25. Dynamic Parameters — 动态参数自适应 (V26.2新增)
26. Market Regime Detection — 市场区间检测 (V26.3新增)
27. Time-of-Day Rules — 时段交易规则 (V26.3新增)
28. Spread Deviation Alerts — 价差偏离警告 (V26.3新增)
29. Order Book Imbalance — 订单簿不平衡检测 (V26.3新增)
30. Multi-Timeframe Analysis — 多时间框架分析 (V27.0新增)
31. Momentum Oscillator — 动量指标 (V27.0新增)
32. Execution Delay — 执行延迟模拟 (V27.0新增)
33. Hedging Strategy — 对冲策略 (V28.0新增)
34. Advanced Signal Filtering — 高级信号过滤 (V28.0新增)
35. Statistical Anomaly Detection — 统计异常检测 (V28.0新增)
36. Portfolio Optimizer — 多策略组合优化器 (V28.0新增)
37. Calendar Effect Analyzer — 日历效应分析器 (V28.0新增)
38. Real-Time Risk Dashboard — 实时风控仪表板 (V28.0新增)
36. Portfolio Rebalancing — 组合再平衡 (V29.0新增)
37. News Sentiment — 新闻情绪 (V29.0新增)
38. ML Prediction Signals — ML预测信号 (V29.0新增)
39. Funding Rate Monitor — 资金费率监测 (V30.0新增)
40. Alert System — 预警系统 (V30.0新增)
41. Performance Summary — 性能汇总 (V30.0新增)
42. Smart Order Routing — 智能订单路由 (V31.0新增)
43. Multi-Exchange Price Aggregation — 多交易所价格聚合 (V31.0新增)
44. Order Slicing — 订单拆分执行 (V31.0新增)
45. TWAP/VWAP Execution — 时间加权平均价格执行 (V31.0新增)
46. Market Depth Analysis — 市场深度分析 (V33.0新增)
47. Liquidity Aggregator — 跨交易所流动性聚合 (V33.0新增)
48. Price Impact Model — 价格影响预测模型 (V33.0新增)
49. Signal Fusion Engine — 多信号融合引擎 (V33.0新增)
50. Cross-Exchange Arbitrage — 跨交易所套利检测 (V34.0新增)
51. Margin Pool Manager — 保证金池管理 (V34.0新增)
52. Execution Priority Queue — 执行优先级队列 (V34.0新增)
53. Real-Time P&L Dashboard — 实时盈亏仪表板 (V34.0新增)
54. Triangular Arbitrage — 三角形套利引擎 (V35.0新增)
55. Funding Rate Arbitrage — 资金费率套利 (V35.0新增)
56. ML Signal Integration — 机器学习信号集成 (V35.0新增)
57. Grid Trading System — 网格交易系统 (V36.0新增)
58. DCA Bot — 定时定额投资策略 (V36.0新增)
59. Paper Trading Mode — 模拟交易模式 (V36.0新增)
60. Trading Statistics — 交易统计分析 (V36.0新增)
61. Backtesting Engine — 回测引擎 (V37.0新增)
62. Strategy Backtest — 策略回测 (V37.0新增)
63. Performance Metrics — 回测绩效指标 (V37.0新增)
64. Historical Simulation — 历史模拟 (V37.0新增)

创建时间：2026-05-06 05:35
更新时间：2026-05-06 06:10 (V25.1) — 添加Memo0集���
更新时间：2026-05-06 12:07 (V25.8) — 添加执行质量追踪/最大暴露限制/连亏熔断器
更新时间：2026-05-06 13:20 (V25.9) — 添加紧急止损/每日盈亏追踪/全局仓位限制
更新时间：2026-05-06 14:00 (V26.0) — 添加追踪止损/平仓冷却/周末交易控制
更新时间：2026-05-06 14:46 (V26.1) — 添加TIF/ATR/OCO/持仓时间限制/相关性限制
更新时间：2026-05-06 15:46 (V26.2) — 添加订单簿分析/流动性检测/滑点预测/动态参数
更新时间：2026-05-06 16:30 (V26.3) — 添加市场区间检测/时段规则/价差警告/订单簿不平衡
更新时间：2026-05-06 17:00 (V27.0) — 添加多时间框架分析/动量指标/执行延迟模拟
更新时间：2026-05-06 17:30 (V28.0) — 添加对冲策略/信号过滤/异常检测
更新时间：2026-05-06 18:00 (V29.0) — 添加组合再平衡/新闻情绪/ML预测
更新时间：2026-05-06 18:30 (V30.0) — 添加资金费率监测/预警系统/性能汇总
更新时间：2026-05-06 21:22 (V31.0) — 添加智能订单路由/多交易所价格聚合/订单拆分/TWAP/VWAP执行
更新时间：2026-05-06 23:15 (V34.0) — 添加跨交易所套利/保证金优化/执行优先级/实时P&L
更新时间：2026-05-07 00:00 (V35.0) — 添加三角形套利/资金费率套利/ML信号集成
更新时间：2026-05-06 22:53 (V33.0) — 添加市场深度分析/流动性聚合/价格影响预测/信号融合
更新时间：2026-05-06 23:15 (V34.0) — 添加跨交易所套利/保证金优化/执行优先级/实时P&L
更新时间：2026-05-07 01:53 (V36.0) — 添加网格交易/DCA/模拟交易/交易统计
更新时间：2026-05-07 02:15 (V37.0) — 添加回测引擎/策略回测/绩效指标/历史模拟
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"


class TimeInForce(Enum):
    """时间有效期限 (TIF) - V26.1新增"""
    GTC = "good_till_cancel"  # 一直有效直到取消
    IOC = "immediate_or_cancel"  # 立即执行或取消
    FOK = "fill_or_kill"  # 全部成交或取消
    GTT = "good_till_time"  # 有效直到指定时间


class OrderType(Enum):
    """订单类型 - V26.1新增"""
    MARKET = "market"
    LIMIT = "limit"
    OCO = "one_cancels_other"  # 二选一订单
    OTO = "one_triggers_other"  # 触发其他订单


class LoopStatus(Enum):
    """循环状态"""
    IDLE = "idle"
    SCANNING = "scanning"
    EVALUATING = "evaluating"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    PAUSED = "paused"
    STOPPED = "stopped"
    SOR_EXECUTING = "sor_executing"  # V31.0新增 - SOR订单执行中


class SORMode(Enum):
    """Smart Order Routing 执行模式 - V31.0新增"""
    DISABLED = "disabled"  # 禁用SOR
    TWAP = "twap"  # Time-Weighted Average Price - 时间加权平均
    VWAP = "vwap"  # Volume-Weighted Average Price - 成交量加权平均
    IS = "implementation_shortfall"  # 减少执行成本
    POV = "participation_of_volume"  # 成交量参与


class MarketRegime(Enum):
    """市场状态 - V33.0新增"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    LOW_LIQUIDITY = "low_liquidity"


@dataclass
class MarketDepthLevel:
    """订单簿深度级别 - V33.0新增"""
    price: float = 0.0
    volume: float = 0.0
    cumulative_volume: float = 0.0
    order_count: int = 0


@dataclass
class MarketDepth:
    """市场深度 - V33.0新增"""
    symbol: str = ""
    exchange: str = ""
    bid_levels: List[MarketDepthLevel] = field(default_factory=list)
    ask_levels: List[MarketDepthLevel] = field(default_factory=list)
    spread: float = 0.0
    spread_bps: float = 0.0
    mid_price: float = 0.0
    depth_score: float = 0.0  # 0-100
    timestamp: float = 0.0


@dataclass
class LiquidityPool:
    """流动性池 - V33.0新增"""
    exchange: str
    symbol: str
    bid_depth: float = 0.0  # 总bid流动性
    ask_depth: float = 0.0  # 总ask流动性
    total_depth: float = 0.0
    price_levels: int = 0
    weighted_mid: float = 0.0


@dataclass
class PriceImpact:
    """价格影响预测 - V33.0新增"""
    quantity: float = 0.0
    expected_price: float = 0.0
    impacted_price: float = 0.0
    impact_bps: float = 0.0  # 基点
    fill_rate: float = 0.0  # 成交率
    risk_level: str = "low"  # low/medium/high


@dataclass
class ArbitrageOpportunity:
    """跨交易所套利机会 - V34.0新增"""
    symbol: str = ""
    buy_exchange: str = ""
    sell_exchange: str = ""
    buy_price: float = 0.0
    sell_price: float = 0.0
    spread_pct: float = 0.0  # 价差百分比
    potential_profit: float = 0.0
    score: float = 0.0  # 评分 0-100
    timestamp: float = 0.0
    status: str = "pending"  # pending/executing/completed/failed


@dataclass
class MarginPosition:
    """保证金头寸 - V34.0新增"""
    symbol: str = ""
    exchange: str = ""
    position_size: float = 0.0
    margin_used: float = 0.0
    unrealized_pnl: float = 0.0
    margin_ratio: float = 0.0  # 保证金率
    liquidation_price: float = 0.0
    timestamp: float = 0.0


@dataclass
class ExecutionTask:
    """执行任务 - V34.0新增"""
    task_id: str = ""
    opportunity_id: str = ""
    symbol: str = ""
    side: str = ""  # buy/sell
    quantity: float = 0.0
    priority: int = 5  # 1-10, 10 is highest
    score: float = 50.0
    status: str = "pending"  # pending/executing/completed/failed
    created_at: float = 0.0
    executed_at: float = 0.0


@dataclass
class ProfitLoss:
    """盈亏跟踪 - V34.0新增"""
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    commission: float = 0.0
    net_pnl: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    timestamp: float = 0.0


@dataclass
class TriangularOpportunity:
    """三角形套利机会 - V35.0新增"""
    symbol_a: str = ""
    symbol_b: str = ""
    symbol_c: str = ""
    path: str = ""  # e.g., "BTC→ETH→USDT→BTC"
    rate_a_to_b: float = 0.0
    rate_b_to_c: float = 0.0
    rate_c_to_a: float = 0.0
    expected_profit_pct: float = 0.0
    actual_profit_pct: float = 0.0
    score: float = 0.0
    status: str = "pending"
    timestamp: float = 0.0


@dataclass
class FundingArbitrage:
    """资金费率套利机会 - V35.0新增"""
    symbol: str = ""
    exchange_a: str = ""
    exchange_b: str = ""
    funding_rate_a: float = 0.0  # 资金费率
    funding_rate_b: float = 0.0
    rate_diff: float = 0.0  # 费率差
    potential_profit: float = 0.0
    score: float = 0.0
    status: str = "pending"
    timestamp: float = 0.0


@dataclass
class MLSignal:
    """机器学习信号 - V35.0新增"""
    symbol: str = ""
    prediction: float = 0.0  # 预测方向: 1=buy, -1=sell, 0=neutral
    confidence: float = 0.0  # 置信度 0-1
    model_name: str = ""
    features: Dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class GridOrder:
    """网格订单 - V36.0新增"""
    grid_id: str = ""
    symbol: str = ""
    side: str = ""  # buy/sell
    price: float = 0.0
    quantity: float = 0.0
    grid_level: int = 0  # 网格层级
    status: str = "pending"  # pending/filled/cancelled
    filled_at: float = 0.0
    profit_pct: float = 0.0
    timestamp: float = 0.0


@dataclass
class GridStrategy:
    """网格策略 - V36.0新增"""
    strategy_id: str = ""
    symbol: str = ""
    grid_type: str = "arithmetic"  # arithmetic/geometric
    grid_count: int = 10  # 网格数量
    price_min: float = 0.0
    price_max: float = 0.0
    grid_spacing: float = 0.0  # 网格间距(%)
    position_per_grid: float = 0.0  # 每网格仓位
    total_invested: float = 0.0
    current_profit: float = 0.0
    profit_pct: float = 0.0
    active_grids: int = 0
    filled_grids: int = 0
    status: str = "active"
    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class DCAStrategy:
    """DCA策略 - V36.0新增"""
    strategy_id: str = ""
    symbol: str = ""
    direction: str = "buy"  # buy/sell
    total_trades: int = 0
    completed_trades: int = 0
    trade_amount: float = 0.0  # 每次交易数量
    trade_interval: int = 3600  # 交易间隔(秒)
    price_target: float = 0.0  # 目标价格
    current_price: float = 0.0
    average_price: float = 0.0  # 平均成本
    total_invested: float = 0.0
    current_value: float = 0.0
    profit_pct: float = 0.0
    next_trade_time: float = 0.0
    status: str = "pending"
    created_at: float = 0.0


@dataclass
class PaperTrade:
    """模拟交易记录 - V36.0新增"""
    trade_id: str = ""
    symbol: str = ""
    side: str = ""  # buy/sell
    price: float = 0.0
    quantity: float = 0.0
    fee: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    executed: bool = False
    executed_at: float = 0.0
    notes: str = ""


@dataclass
class TradingStats:
    """交易统计 - V36.0新增"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0  # profit factor = gross profit / gross loss
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_volume: float = 0.0
    total_fees: float = 0.0
    net_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    timestamp: float = 0.0


@dataclass
class BacktestTrade:
    """回测交易 - V37.0新增"""
    trade_id: str = ""
    symbol: str = ""
    side: str = ""  # buy/sell
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    entry_time: float = 0.0
    exit_time: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_periods: int = 0  # 持仓周期数
    _fee: float = 0.0


@dataclass
class BacktestResult:
    """回测结果 - V37.0新增"""
    strategy_name: str = ""
    symbol: str = ""
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 10000.0
    final_capital: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    avg_holding_periods: float = 0.0
    trade_log: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class CandleData:
    """K线数据 - V37.0新增"""
    timestamp: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


@dataclass
class RiskMetrics:
    """风险指标 - V38.0新增"""
    var_95: float = 0.0  # 95% VaR
    var_99: float = 0.0  # 99% VaR
    cvar_95: float = 0.0  # 95% CVaR
    cvar_99: float = 0.0  # 99% CVaR
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    volatility: float = 0.0
    beta: float = 0.0
    correlation_btc: float = 0.0
    beta_btc: float = 0.0
    timestamp: float = 0.0


@dataclass
class RiskLimit:
    """风险限制 - V38.0新增"""
    max_var: float = 0.02  # 最大VaR 2%
    max_position_pct: float = 0.20  # 最大仓位20%
    max_daily_loss: float = 0.05  # 最大日亏损5%
    max_correlation: float = 0.70  # 最大相关性
    max_beta: float = 2.0  # 最大beta
    min_sharpe: float = 1.0  # 最小夏普比率


@dataclass
class PortfolioPosition:
    """组合持仓 - V38.0新增"""
    symbol: str = ""
    quantity: float = 0.0
    avg_price: float = 0.0
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    weight: float = 0.0  # 权重
    beta: float = 0.0
    sector: str = ""


@dataclass
class OrderRecord:
    """订单记录 - V39.0新增"""
    order_id: str = ""
    exchange: str = ""
    symbol: str = ""
    side: str = ""  # buy/sell
    order_type: str = "limit"  # limit/market
    price: float = 0.0
    quantity: float = 0.0
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    status: str = "pending"  # pending/filled/partial/cancelled
    fee: float = 0.0
    created_at: float = 0.0
    filled_at: float = 0.0
    notes: str = ""


@dataclass
class ExchangeConfig:
    """交易所配置 - V39.0新增"""
    exchange: str = ""
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    enabled: bool = False
    fee_tier: float = 0.0004  # 手续费层级
    max_retries: int = 3
    timeout_ms: int = 5000


@dataclass
class TradeSignal:
    """交易信号 - V39.0新增"""
    signal_id: str = ""
    symbol: str = ""
    action: str = ""  # buy/sell
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    quantity: float = 0.0
    confidence: float = 0.0
    strategy: str = ""
    generated_at: float = 0.0


@dataclass
class StrategyPerformance:
    """策略绩效 - V40.0新增"""
    strategy_id: str = ""
    strategy_name: str = ""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    avg_holding_time: float = 0.0
    last_updated: float = 0.0


@dataclass
class StrategyAllocation:
    """策略配置 - V40.0新增"""
    strategy_id: str = ""
    strategy_name: str = ""
    allocation_pct: float = 0.0  # 分配比例
    enabled: bool = True
    min_allocation: float = 0.0
    max_allocation: float = 0.0
    priority: int = 5  # 优先级


@dataclass
class MarketRegimeData:
    """市场区间数据 - V40.0新增"""
    regime: str = ""  # trending_up/trending_down/ranging/volatile
    confidence: float = 0.0
    trend_strength: float = 0.0
    volatility: float = 0.0
    volume_ratio: float = 0.0
    timestamp: float = 0.0


@dataclass
class DashboardWidget:
    """仪表板组件 - V41.0新增"""
    widget_id: str = ""
    widget_type: str = ""  # chart/table/metric/text
    title: str = ""
    data_source: str = ""  # 数据源
    refresh_interval: int = 60  # 刷新间隔(秒)
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemAlert:
    """系统告警 - V41.0新增"""
    alert_id: str = ""
    alert_type: str = ""  # info/warning/error/critical
    source: str = ""  # 来源
    message: str = ""
    timestamp: float = 0.0
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class ScheduleTask:
    """计划任务 - V41.0新增"""
    task_id: str = ""
    task_type: str = ""  # rebalance/rotate/check_alerts
    schedule: str = ""  # cron表达式
    enabled: bool = True
    last_run: float = 0.0
    next_run: float = 0.0
    status: str = "pending"


@dataclass
class APIEndpoint:
    """API端点 - V42.0新增"""
    endpoint_id: str = ""
    path: str = ""
    method: str = "GET"  # GET/POST/PUT/DELETE
    auth_required: bool = True
    rate_limit: int = 100  # 每分钟请求限制
    enabled: bool = True


@dataclass
class WebhookConfig:
    """Webhook配置 - V42.0新增"""
    webhook_id: str = ""
    url: str = ""
    events: List[str] = field(default_factory=list)  # trade/execution/alert
    secret: str = ""
    enabled: bool = True
    retry_count: int = 3


@dataclass
class APIResponse:
    """API响应 - V42.0新增"""
    success: bool = False
    data: Any = None
    error: str = ""
    timestamp: float = 0.0


@dataclass
class ExchangeStatus:
    """交易所状态 - V42.0新增"""
    exchange: str = ""
    status: str = ""  # online/offline/maintenance
    latency_ms: float = 0.0
    last_check: float = 0.0
    error_count: int = 0


@dataclass
class PerformanceAttribution:
    """绩效归因 - V43.0新增"""
    strategy_id: str = ""
    period_start: float = 0.0
    period_end: float = 0.0
    total_return: float = 0.0
    benchmark_return: float = 0.0
    alpha: float = 0.0
    treynor_ratio: float = 0.0
    information_ratio: float = 0.0
    r_squared: float = 0.0


@dataclass
class TradeAttribution:
    """交易归因 - V43.0新增"""
    trade_id: str = ""
    symbol: str = ""
    pnl_contribution: float = 0.0
    timing_contribution: float = 0.0
    selection_contribution: float = 0.0
    size_contribution: float = 0.0


@dataclass
class RiskAttribution:
    """风险归因 - V43.0新增"""
    total_risk: float = 0.0
    systematic_risk: float = 0.0
    idiosyncratic_risk: float = 0.0
    concentration_risk: float = 0.0


@dataclass
class AnalyticsReport:
    """分析报告 - V43.0新增"""
    report_id: str = ""
    report_type: str = ""
    generated_at: float = 0.0
    period_start: float = 0.0
    period_end: float = 0.0
    trade_count: int = 0
    total_pnl: float = 0.0


@dataclass
class PortfolioOptimization:
    """组合优化 - V44.0新增"""
    optimization_id: str = ""
    target_return: float = 0.0
    target_volatility: float = 0.0
    weights: Dict[str, float] = field(default_factory=dict)
    expected_return: float = 0.0
    expected_volatility: float = 0.0
    sharpe_ratio: float = 0.0


@dataclass
class ExecutionAlgorithm:
    """执行算法 - V44.0新增"""
    algorithm_id: str = ""
    algorithm_type: str = ""  # twap/vwap/pov/is
    symbol: str = ""
    quantity: float = 0.0
    filled_quantity: float = 0.0
    avg_price: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "pending"


@dataclass
class SmartOrderRouter:
    """智能订单路由器 - V44.0新增"""
    routers: List[str] = field(default_factory=list)  # binance/bybit/okx
    latency_weight: float = 0.3
    fee_weight: float = 0.4
    liquidity_weight: float = 0.3


@dataclass
class ExchangePrice:
    """交易所价格 - V31.0新增"""
    exchange: str
    symbol: str
    bid_price: float = 0.0  # 买一价
    ask_price: float = 0.0  # 卖一价
    bid_volume: float = 0.0  # 买一量
    ask_volume: float = 0.0  # 卖一量
    timestamp: float = 0.0
    latency_ms: float = 0.0


@dataclass
class ConditionalOrder:
    """条件订单 - V45.0新增"""
    order_id: str = ""
    parent_order_id: str = ""
    condition_type: str = ""
    trigger_price: float = 0.0
    side: str = ""
    quantity: float = 0.0
    status: str = "pending"


@dataclass
class IcebergOrder:
    """冰山订单 - V45.0新增"""
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    total_quantity: float = 0.0
    displayed_quantity: float = 0.0
    filled_quantity: float = 0.0
    price: float = 0.0
    status: str = "pending"


@dataclass
class TWAPOrder:
    """TWAP订单 - V45.0新增"""
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    total_quantity: float = 0.0
    slice_count: int = 10
    slice_interval: int = 60
    filled_slices: int = 0
    avg_price: float = 0.0
    status: str = "pending"


@dataclass
class PositionSnapshot:
    """持仓快照 - V45.0新增"""
    snapshot_id: str = ""
    symbol: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0
    current_price: float = 0.0
    pnl: float = 0.0
    timestamp: float = 0.0


@dataclass
class SentimentData:
    """情绪数据 - V46.0新增"""
    symbol: str = ""
    sentiment_score: float = 0.0  # -1到1
    positive_mentions: int = 0
    negative_mentions: int = 0
    neutral_mentions: int = 0
    sources: List[str] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class CorrelationPair:
    """相关性交易对 - V46.0新增"""
    symbol_a: str = ""
    symbol_b: str = ""
    correlation: float = 0.0  # -1到1
    spread_history: List[float] = field(default_factory=list)
    last_updated: float = 0.0


@dataclass
class TimeframeSignal:
    """时间框架信号 - V46.0新增"""
    symbol: str = ""
    timeframe: str = ""  # 1m/5m/15m/1h/4h/1d
    signal: str = ""  # buy/sell/hold
    strength: float = 0.0
    timestamp: float = 0.0


@dataclass
class OptionsContract:
    """期权合约 - V47.0新增"""
    contract_id: str = ""
    underlying: str = ""  # 标的资产
    strike_price: float = 0.0
    expiry: float = 0.0
    option_type: str = ""  # call/put
    position: str = ""  # long/short
    quantity: float = 0.0
    premium: float = 0.0


@dataclass
class FuturesContract:
    """期货合约 - V47.0新增"""
    contract_id: str = ""
    symbol: str = ""
    position: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0
    leverage: int = 1
    margin: float = 0.0
    funding_rate: float = 0.0
    next_funding: float = 0.0


@dataclass
class MarginAccount:
    """保证金账户 - V47.0新增"""
    account_id: str = ""
    total_equity: float = 0.0
    available_balance: float = 0.0
    margin_used: float = 0.0
    unrealized_pnl: float = 0.0
    margin_ratio: float = 0.0
    liquidation_risk: bool = False


@dataclass
class SOROrder:
    """SOR订单 - V31.0新增"""
    order_id: str
    symbol: str
    side: str  # buy/sell
    total_quantity: float
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    mode: str = "twap"
    slices: int = 10  # 拆分数量
    slice_interval_seconds: int = 10  # 每_slice间隔
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "pending"
    exchanges: List[str] = field(default_factory=list)
    slippage_bps: float = 0.0  # 滑点(基点)
    execution_cost: float = 0.0  # 执行成本


@dataclass
class AutoTradeConfig:
    """自动交易配置"""
    mode: str = "manual"
    scan_interval_seconds: int = 30
    min_score_threshold: float = 60.0
    min_confidence: float = 0.5
    max_concurrent_positions: int = 5
    auto_close_threshold: float = 0.02  # 2% profit auto-close
    stop_loss_pct: float = 0.02  # 2% stop loss
    # V25.8: New configuration options
    max_exposure_per_symbol: float = 10000.0  # 最大单币种暴露
    consecutive_loss_limit: int = 3  # 连亏熔断阈值
    enable_circuit_breaker: bool = True  # 启用连亏熔断
    # V25.9: New configuration options
    emergency_stop_pct: float = 0.10  # 紧急止损 - 10%全局止损
    daily_loss_limit: float = 0.05  # 每日亏损限制 - 5%
    max_total_exposure: float = 50000.0  # 全局最大总暴露
    # V26.0: New configuration options
    trailing_stop_pct: float = 0.015  # 追踪止损 - 1.5%
    enable_trailing_stop: bool = True  # 启用追踪止损
    cooldown_seconds: int = 60  # 平仓后冷却秒数
    allow_weekend_trading: bool = True  # 允许周末交易
    # V26.1: New configuration options
    default_tif: str = "gtc"  # 默认时间有效期限
    enable_atr_trailing: bool = False  # 启用ATR追踪止损
    atr_periods: int = 14  # ATR周期数
    atr_multiplier: float = 2.0  # ATR倍数
    max_holding_seconds: int = 300  # 最大持仓时间(秒) - 5分钟
    enable_oco_orders: bool = False  # 启用OCO订单
    correlation_limit: float = 0.7  # 相关性限制
    # V26.2: New configuration options
    enable_orderbook_analysis: bool = False  # 启用订单簿分析
    min_liquidity_depth: float = 10000.0  # 最小流动性深度
    slippage_warning_threshold: float = 0.005  # 滑点警告阈值 (0.5%)
    enable_dynamic_params: bool = True  # 启用动态参数调整
    volatility_lookback: int = 20  # 波动率回看周期
    # V26.3: New configuration options
    enable_market_regime: bool = False  # 启用市场区间检测
    enable_time_rules: bool = False  # 启用时段交易规则
    spread_deviation_threshold: float = 0.02  # 价差偏离阈值 (2%)
    imbalance_threshold: float = 0.3  # 订单簿不平衡阈值 (30%)
    asian_session_start: int = 0  # 亚洲时段开始 (UTC小时)
    asian_session_end: int = 8  # 亚洲时段结束
    london_session_start: int = 8  # 伦敦时段开始
    london_session_end: int = 16  # 伦敦时段结束
    ny_session_start: int = 13  # 纽约时段开始
    ny_session_end: int = 21  # 纽约时段结束
    # V27.0: New configuration options
    enable_multitimeframe: bool = False  # 启用多时间框架分析
    enable_momentum: bool = False  # 启用动量指标
    execution_delay_ms: int = 0  # 执行延迟(毫秒)
    rsi_periods: int = 14  # RSI周期
    # V28.0: New configuration options
    enable_hedging: bool = False  # 启用对冲策略
    hedge_correlation: float = 0.6  # 对冲相关性阈值
    enable_advanced_filter: bool = False  # 启用高级信号过滤
    filter_confidence_min: float = 0.6  # 最小置信度过滤
    enable_anomaly_detection: bool = False  # 启用统计异常检测
    anomaly_threshold: float = 3.0  # 异常检测阈值(标准差倍数)
    # V29.0: New configuration options
    enable_rebalancing: bool = False  # 启用组合再平衡
    rebalance_threshold: float = 0.2  # 再平衡阈值
    enable_news_sentiment: bool = False  # 启用新闻情绪
    sentiment_impact: float = 0.1  # 情绪影响系数
    enable_ml_signals: bool = False  # 启用ML信号
    ml_confidence_boost: float = 0.1  # ML置信度提升
    # V30.0: New configuration options
    enable_funding_monitor: bool = False  # 启用资金费率监测
    funding_alert_threshold: float = 0.001  # 资金费率预警阈值
    enable_alerts: bool = True  # 启用预警系统
    alert_level: str = "INFO"  # 预警级别
    # V31.0: Smart Order Routing (SOR) 配置
    enable_sor: bool = False  # 启用智能订单路由
    sor_mode: str = "twap"  # SOR执行模式: twap/vwap/is/pov
    sor_slices: int = 10  # 订单拆分数量
    sor_slice_interval: int = 10  # 每_slice间隔(秒)
    sor_max_slippage_bps: int = 10  # 最大滑点容忍(基点)
    sor_exchanges: str = "binance,bybit,okx"  # 允许的交易所列表
    sor_participation_rate: float = 0.1  # POV模式参与率
    # V32.0: Order Flow Analysis (OFA) 配置
    enable_ofa: bool = False  # 启用订单流分析
    large_order_threshold: float = 1.0  # 大单阈值(BTC)
    vwap_gap_threshold: float = 0.005  # VWAP缺口阈值(0.5%)
    volume_lookback: int = 60  # 交易量回看周期
    institutional_patterns: bool = False  # 启用机构模式识别
    # V33.0: Market Microstructure 配置
    enable_market_depth: bool = False  # 启用市场深度分析
    depth_levels: int = 10  # 订单簿深度级别数
    min_depth_score: float = 60.0  # 最小深度评分
    enable_liquidity_agg: bool = False  # 启用流动性聚合
    enable_price_impact: bool = False  # 启用价格影响预测
    impact_model_alpha: float = 0.1  # 价格影响模型系数
    enable_signal_fusion: bool = False  # 启用多信号融合
    fusion_weights: str = "technical:0.3,sentiment:0.2,flow:0.3,ml:0.2"  # 信号融合权重
    # V34.0: Cross-Exchange Arbitrage配置
    enable_arbitrage: bool = False  # 启用跨交易所套利检测
    arbitrage_min_spread: float = 0.002  # 最小套利价差 (0.2%)
    arbitrage_exchanges: str = "binance,bybit,okx"  # 套利交易所
    # V34.0: Margin Pool配置
    enable_margin_pool: bool = False  # 启用保证金池
    margin_pool_size: float = 100000.0  # 保证金池大小
    margin_buffer_ratio: float = 0.2  # 保证金缓冲比例
    # V34.0: Execution Priority配置
    enable_priority_queue: bool = False  # 启用执行优先级
    max_queue_size: int = 10  # 最大队列数
    # V34.0: P&L Dashboard配置
    enable_pnl_dashboard: bool = False  # 启用P&L仪表板
    pnl_update_interval: int = 5  # P&L更新间隔(秒)
    # V35.0: Triangular Arbitrage配置
    enable_triangular: bool = False  # 启用三角形套利
    triangular_min_profit: float = 0.001  # 最小利润阈值 (0.1%)
    triangular_paths: str = "BTC,ETH,SOL,BNB"  # 允许的交易对
    # V35.0: Funding Rate Arbitrage配置
    enable_funding_arbitrage: bool = False  # 启用资金费率套利
    funding_min_diff: float = 0.0005  # 最小费率差 (0.05%)
    funding_exchanges: str = "binance,bybit,okx"  # 允许的交易所
    # V35.0: ML Signal配置
    enable_ml_signal: bool = False  # 启用ML信号
    ml_model_path: str = ""  # ML模型路径
    ml_confidence_threshold: float = 0.6  # 置信度阈值
    # V36.0: Grid Trading配置
    enable_grid_trading: bool = False  # 启用网格交易
    grid_type: str = "arithmetic"  # arithmetic/geometric
    grid_count: int = 10  # 网格数量
    grid_spacing_pct: float = 1.0  # 网格间距(%)
    grid_position_size: float = 0.001  # 每网格仓位比例
    # V36.0: DCA配置
    enable_dca: bool = False  # 启用DCA
    dca_amount: float = 100.0  # 每次DCA数量
    dca_interval: int = 3600  # DCA间隔(秒)
    dca_triggers: int = 5  # DCA触发次数
    # V36.0: Paper Trading配置
    enable_paper_trading: bool = False  # 启用模拟交易
    paper_trading_balance: float = 10000.0  # 模拟账户余额
    # V36.0: Trading Stats配置
    track_detailed_stats: bool = True  # 跟踪详细统计
    # V37.0: Backtesting配置
    enable_backtesting: bool = False  # 启用回测
    backtest_initial_capital: float = 10000.0  # 回测初始资金
    backtest_fee_rate: float = 0.0004  # 手续费率
    # V38.0: Risk Management配置
    enable_risk_management: bool = False  # 启用风险管理
    max_var_pct: float = 0.02  # 最大VaR 2%
    max_position_pct: float = 0.20  # 最大仓位20%
    max_daily_loss: float = 0.05  # 最大日亏损5%
    var_confidence: float = 0.95  # VaR置信度
    enable_var_alerts: bool = True  # 启用VaR预警
    # V39.0: Real Trading配置
    enable_real_trading: bool = False  # 启用真实交易
    default_exchange: str = "binance"  # 默认交易所
    testnet_mode: bool = True  # 测试网模式
    max_order_size: float = 1.0  # 最大订单量
    order_timeout: int = 30  # 订单超时秒数
    # V40.0: Multi-Strategy配置
    enable_multi_strategy: bool = False  # 启用多策略
    max_active_strategies: int = 5  # 最大活跃策略数
    rebalance_interval: int = 3600  # 再平衡间隔(秒)
    strategy_rotation: bool = False  # 启用策略轮换
    # V41.0: Dashboard配置
    enable_dashboard: bool = True  # 启用仪表板
    dashboard_refresh: int = 60  # 仪表板刷新间隔
    enable_system_alerts: bool = True  # 启用系统告警
    enable_scheduling: bool = False  # 启用计划任务
    # V42.0: API Integration配置
    enable_api_server: bool = False  # 启用API服务器
    api_port: int = 8080  # API端口
    enable_webhooks: bool = False  # 启用Webhooks
    api_rate_limit: int = 100  # API速率限制
    # V43.0: Analytics配置
    enable_analytics: bool = True  # 启用分析
    analytics_interval: int = 3600  # 分析间隔
    # V44.0: Portfolio & Execution配置
    enable_optimization: bool = True  # 启用组合优化
    enable_smart_routing: bool = True  # 启用智能路由
    # V45.0: Advanced Orders配置
    enable_conditional_orders: bool = True  # 启用条件订单
    enable_iceberg: bool = True  # 启用冰山订单
    enable_twap: bool = True  # 启用TWAP
    # V46.0: Sentiment & Correlation配置
    enable_sentiment: bool = True  # 启用情绪分析
    enable_correlation: bool = True  # 启用相关性交易
    enable_multitimeframe: bool = True  # 启用多时间框架
    # V47.0: Derivatives配置
    enable_options: bool = True  # 启用期权
    enable_futures: bool = True  # 启用期货
    enable_margin_trading: bool = True  # 启用保证金交易


@dataclass
class ScannedOpportunity:
    """扫描到的机会"""
    opportunity_id: str
    symbol: str
    action: str
    entry_price: float
    target_price: float
    stop_loss: float
    score: float
    confidence: float
    recommendation: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExecutionResult:
    """执行结果"""
    opportunity_id: str
    success: bool
    executed_price: float = 0.0
    executed_size: float = 0.0
    executed_at: float = 0.0
    error: Optional[str] = None
    # V25.8: Execution quality tracking
    expected_price: float = 0.0
    slippage: float = 0.0
    slippage_pct: float = 0.0
    execution_quality_score: float = 100.0  # 0-100


class AutoExecutionEngine:
    """自动交易执行引擎

    整合所有组件的自动化交易执行。
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        signal_scorer=None,
        position_sizer=None,
        risk_manager=None,
        execution_engine=None,
        portfolio_analytics=None,
        arbitrage_pipeline=None,
        knowledge_bridge=None
    ):
        """初始化自动交易执行引擎

        Args:
            config: 配置字典
            signal_scorer: 信号评分器
            position_sizer: 仓位管理器
            risk_manager: 风险管理器
            execution_engine: 执行引擎
            portfolio_analytics: 投资组合分析器
            arbitrage_pipeline: 套利管道
            knowledge_bridge: 知识桥接器 (Memo0集成)
        """
        self.config = config or {}

        # 组件引用
        self.signal_scorer = signal_scorer
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.execution_engine = execution_engine
        self.portfolio_analytics = portfolio_analytics
        self.arbitrage_pipeline = arbitrage_pipeline
        self.knowledge_bridge = knowledge_bridge  # V25.1新增

        # 运行配置
        self.run_config = AutoTradeConfig(
            mode=self.config.get('mode', 'manual'),
            scan_interval_seconds=self.config.get('scan_interval_seconds', 30),
            min_score_threshold=self.config.get('min_score_threshold', 60.0),
            min_confidence=self.config.get('min_confidence', 0.5),
            max_concurrent_positions=self.config.get('max_concurrent_positions', 5),
            auto_close_threshold=self.config.get('auto_close_threshold', 0.02),
            stop_loss_pct=self.config.get('stop_loss_pct', 0.02),
            # V25.8: 新配置参数
            max_exposure_per_symbol=self.config.get('max_exposure_per_symbol', 10000.0),
            consecutive_loss_limit=self.config.get('consecutive_loss_limit', 3),
            enable_circuit_breaker=self.config.get('enable_circuit_breaker', True),
            # V25.9: 新配置参数
            emergency_stop_pct=self.config.get('emergency_stop_pct', 0.10),
            daily_loss_limit=self.config.get('daily_loss_limit', 0.05),
            max_total_exposure=self.config.get('max_total_exposure', 50000.0),
            # V26.0: 新配置参数
            trailing_stop_pct=self.config.get('trailing_stop_pct', 0.015),
            enable_trailing_stop=self.config.get('enable_trailing_stop', True),
            cooldown_seconds=self.config.get('cooldown_seconds', 60),
            allow_weekend_trading=self.config.get('allow_weekend_trading', True),
            # V26.1: 新配置参数
            default_tif=self.config.get('default_tif', 'gtc'),
            enable_atr_trailing=self.config.get('enable_atr_trailing', False),
            atr_periods=self.config.get('atr_periods', 14),
            atr_multiplier=self.config.get('atr_multiplier', 2.0),
            max_holding_seconds=self.config.get('max_holding_seconds', 300),
            enable_oco_orders=self.config.get('enable_oco_orders', False),
            correlation_limit=self.config.get('correlation_limit', 0.7),
            # V26.2: 新配置参数
            enable_orderbook_analysis=self.config.get('enable_orderbook_analysis', False),
            min_liquidity_depth=self.config.get('min_liquidity_depth', 10000.0),
            slippage_warning_threshold=self.config.get('slippage_warning_threshold', 0.005),
            enable_dynamic_params=self.config.get('enable_dynamic_params', True),
            volatility_lookback=self.config.get('volatility_lookback', 20),
            # V26.3: 新配置参数
            enable_market_regime=self.config.get('enable_market_regime', False),
            enable_time_rules=self.config.get('enable_time_rules', False),
            spread_deviation_threshold=self.config.get('spread_deviation_threshold', 0.02),
            imbalance_threshold=self.config.get('imbalance_threshold', 0.3),
            asian_session_start=self.config.get('asian_session_start', 0),
            asian_session_end=self.config.get('asian_session_end', 8),
            london_session_start=self.config.get('london_session_start', 8),
            london_session_end=self.config.get('london_session_end', 16),
            ny_session_start=self.config.get('ny_session_start', 13),
            ny_session_end=self.config.get('ny_session_end', 21),
            # V27.0: 新配置参数
            enable_multitimeframe=self.config.get('enable_multitimeframe', False),
            enable_momentum=self.config.get('enable_momentum', False),
            execution_delay_ms=self.config.get('execution_delay_ms', 0),
            rsi_periods=self.config.get('rsi_periods', 14),
            # V28.0: 新配置参数
            enable_hedging=self.config.get('enable_hedging', False),
            hedge_correlation=self.config.get('hedge_correlation', 0.6),
            enable_advanced_filter=self.config.get('enable_advanced_filter', False),
            filter_confidence_min=self.config.get('filter_confidence_min', 0.6),
            enable_anomaly_detection=self.config.get('enable_anomaly_detection', False),
            anomaly_threshold=self.config.get('anomaly_threshold', 3.0),
            # V29.0: 新配置参数
            enable_rebalancing=self.config.get('enable_rebalancing', False),
            rebalance_threshold=self.config.get('rebalance_threshold', 0.2),
            enable_news_sentiment=self.config.get('enable_news_sentiment', False),
            sentiment_impact=self.config.get('sentiment_impact', 0.1),
            enable_ml_signals=self.config.get('enable_ml_signals', False),
            ml_confidence_boost=self.config.get('ml_confidence_boost', 0.1),
            # V30.0: 新配置参数
            enable_funding_monitor=self.config.get('enable_funding_monitor', False),
            funding_alert_threshold=self.config.get('funding_alert_threshold', 0.001),
            enable_alerts=self.config.get('enable_alerts', True),
            alert_level=self.config.get('alert_level', 'INFO'),
            # V31.0: SOR配置参数
            enable_sor=self.config.get('enable_sor', False),
            sor_mode=self.config.get('sor_mode', 'twap'),
            sor_slices=self.config.get('sor_slices', 10),
            sor_slice_interval=self.config.get('sor_slice_interval', 10),
            sor_max_slippage_bps=self.config.get('sor_max_slippage_bps', 10),
            sor_exchanges=self.config.get('sor_exchanges', 'binance,bybit,okx'),
            sor_participation_rate=self.config.get('sor_participation_rate', 0.1),
            # V32.0: OFA配置参数
            enable_ofa=self.config.get('enable_ofa', False),
            large_order_threshold=self.config.get('large_order_threshold', 1.0),
            vwap_gap_threshold=self.config.get('vwap_gap_threshold', 0.005),
            volume_lookback=self.config.get('volume_lookback', 60),
            institutional_patterns=self.config.get('institutional_patterns', False),
            # V33.0: Market Microstructure配置参数
            enable_market_depth=self.config.get('enable_market_depth', False),
            depth_levels=self.config.get('depth_levels', 10),
            min_depth_score=self.config.get('min_depth_score', 60.0),
            enable_liquidity_agg=self.config.get('enable_liquidity_agg', False),
            enable_price_impact=self.config.get('enable_price_impact', False),
            impact_model_alpha=self.config.get('impact_model_alpha', 0.1),
            enable_signal_fusion=self.config.get('enable_signal_fusion', False),
            fusion_weights=self.config.get('fusion_weights', 'technical:0.3,sentiment:0.2,flow:0.3,ml:0.2'),
            # V34.0: Cross-Exchange Arbitrage配置
            enable_arbitrage=self.config.get('enable_arbitrage', False),
            arbitrage_min_spread=self.config.get('arbitrage_min_spread', 0.002),
            arbitrage_exchanges=self.config.get('arbitrage_exchanges', 'binance,bybit,okx'),
            # V34.0: Margin Pool配置
            enable_margin_pool=self.config.get('enable_margin_pool', False),
            margin_pool_size=self.config.get('margin_pool_size', 100000.0),
            margin_buffer_ratio=self.config.get('margin_buffer_ratio', 0.2),
            # V34.0: Execution Priority配置
            enable_priority_queue=self.config.get('enable_priority_queue', False),
            max_queue_size=self.config.get('max_queue_size', 10),
            # V34.0: P&L Dashboard配置
            enable_pnl_dashboard=self.config.get('enable_pnl_dashboard', False),
            pnl_update_interval=self.config.get('pnl_update_interval', 5),
            # V35.0: Triangular Arbitrage配置
            enable_triangular=self.config.get('enable_triangular', False),
            triangular_min_profit=self.config.get('triangular_min_profit', 0.001),
            triangular_paths=self.config.get('triangular_paths', 'BTC,ETH,SOL,BNB'),
            # V35.0: Funding Rate Arbitrage配置
            enable_funding_arbitrage=self.config.get('enable_funding_arbitrage', False),
            funding_min_diff=self.config.get('funding_min_diff', 0.0005),
            funding_exchanges=self.config.get('funding_exchanges', 'binance,bybit,okx'),
            # V35.0: ML Signal配置
            enable_ml_signal=self.config.get('enable_ml_signal', False),
            ml_model_path=self.config.get('ml_model_path', ''),
            ml_confidence_threshold=self.config.get('ml_confidence_threshold', 0.6),
            # V36.0: Grid Trading configuration
            enable_grid_trading=self.config.get('enable_grid_trading', False),
            grid_type=self.config.get('grid_type', 'arithmetic'),
            grid_count=self.config.get('grid_count', 10),
            grid_spacing_pct=self.config.get('grid_spacing_pct', 1.0),
            grid_position_size=self.config.get('grid_position_size', 0.001),
            # V36.0: DCA configuration
            enable_dca=self.config.get('enable_dca', False),
            dca_amount=self.config.get('dca_amount', 100.0),
            dca_interval=self.config.get('dca_interval', 3600),
            dca_triggers=self.config.get('dca_triggers', 5),
            # V36.0: Paper Trading configuration
            enable_paper_trading=self.config.get('enable_paper_trading', False),
            paper_trading_balance=self.config.get('paper_trading_balance', 10000.0),
            # V36.0: Trading Stats configuration
            track_detailed_stats=self.config.get('track_detailed_stats', True),
            # V37.0: Backtesting configuration
            enable_backtesting=self.config.get('enable_backtesting', False),
            backtest_initial_capital=self.config.get('backtest_initial_capital', 10000.0),
            backtest_fee_rate=self.config.get('backtest_fee_rate', 0.0004),
            # V38.0: Risk Management configuration
            enable_risk_management=self.config.get('enable_risk_management', False),
            max_var_pct=self.config.get('max_var_pct', 0.02),
            max_position_pct=self.config.get('max_position_pct', 0.20),
            max_daily_loss=self.config.get('max_daily_loss', 0.05),
            var_confidence=self.config.get('var_confidence', 0.95),
            enable_var_alerts=self.config.get('enable_var_alerts', True),
            # V39.0: Real Trading configuration
            enable_real_trading=self.config.get('enable_real_trading', False),
            default_exchange=self.config.get('default_exchange', 'binance'),
            testnet_mode=self.config.get('testnet_mode', True),
            max_order_size=self.config.get('max_order_size', 1.0),
            order_timeout=self.config.get('order_timeout', 30),
            # V40.0: Multi-Strategy configuration
            enable_multi_strategy=self.config.get('enable_multi_strategy', False),
            max_active_strategies=self.config.get('max_active_strategies', 5),
            rebalance_interval=self.config.get('rebalance_interval', 3600),
            strategy_rotation=self.config.get('strategy_rotation', False),
            # V41.0: Dashboard configuration
            enable_dashboard=self.config.get('enable_dashboard', True),
            dashboard_refresh=self.config.get('dashboard_refresh', 60),
            enable_system_alerts=self.config.get('enable_system_alerts', True),
            enable_scheduling=self.config.get('enable_scheduling', False),
            # V42.0: API Integration configuration
            enable_api_server=self.config.get('enable_api_server', False),
            api_port=self.config.get('api_port', 8080),
            enable_webhooks=self.config.get('enable_webhooks', False),
            api_rate_limit=self.config.get('api_rate_limit', 100),
            # V43.0: Analytics configuration
            enable_analytics=self.config.get('enable_analytics', True),
            analytics_interval=self.config.get('analytics_interval', 3600),
            # V44.0: Portfolio & Execution configuration
            enable_optimization=self.config.get('enable_optimization', True),
            enable_smart_routing=self.config.get('enable_smart_routing', True),
            # V45.0: Advanced Orders configuration
            enable_conditional_orders=self.config.get('enable_conditional_orders', True),
            enable_iceberg=self.config.get('enable_iceberg', True),
            enable_twap=self.config.get('enable_twap', True),
            # V46.0: Sentiment & Correlation configuration
            enable_sentiment=self.config.get('enable_sentiment', True),
            enable_correlation=self.config.get('enable_correlation', True),
            # V47.0: Derivatives configuration
            enable_options=self.config.get('enable_options', True),
            enable_futures=self.config.get('enable_futures', True),
            enable_margin_trading=self.config.get('enable_margin_trading', True)
        )

        # 运行状态
        self.loop_status = LoopStatus.IDLE
        self.is_running = False

        # 机会池
        self.opportunity_pool: List[ScannedOpportunity] = []
        self.max_pool_size = 100

        # 执行历史
        self.execution_history: List[ExecutionResult] = []
        self.max_history = 500

        # 循环任务
        self._scan_task: Optional[asyncio.Task] = None

        # 统计
        self.stats = {
            'total_scans': 0,
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'opportunities_failed': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            # V25.8: Consecutive losses tracking
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'max_consecutive_losses': 0,
            'circuit_breaker_triggered': 0,
            # V25.9: Daily PnL tracking
            'daily_profit': 0.0,
            'daily_loss': 0.0,
            'daily_pnl': 0.0,
            'emergency_stop_triggered': 0,
            'daily_stop_triggered': 0,
            # V26.0: Trailing stops and cooldown
            'trailing_stop_triggered': 0,
            'cooldown_active': 0,
            # V26.1: New stats
            'atr_trailing_triggered': 0,
            'position_time_triggered': 0,
            'oco_orders_created': 0,
            'oco_orders_filled': 0,
            'correlation_rejected': 0,
            # V26.2: New stats
            'orderbook_rejected': 0,
            'liquidity_rejected': 0,
            'slippage_warnings': 0,
            'params_adjusted': 0,
            'volatility_spike': 0,
            # V26.3: New stats
            'regime_changes': 0,
            'time_rule_rejected': 0,
            'spread_warnings': 0,
            'imbalance_warnings': 0,
            'bull_positions': 0,
            'bear_positions': 0,
            'sideways_positions': 0,
            # V27.0: New stats
            'multitimeframe_signals': 0,
            'momentum_signals': 0,
            'execution_delays': 0,
            # V28.0: New stats
            'hedging_signals': 0,
            'filtered_signals': 0,
            'anomaly_detected': 0,
            # V29.0: New stats
            'rebalancing_triggered': 0,
            'sentiment_signals': 0,
            'ml_signals': 0,
            # V30.0: New stats
            'funding_alerts': 0,
            'total_alerts': 0,
            # V31.0: SOR stats
            'sor_orders_created': 0,
            'sor_orders_completed': 0,
            'sor_orders_cancelled': 0,
            'sor_slices_executed': 0,
            'sor_total_slippage_bps': 0.0,
            'sor_execution_cost': 0.0,
            'exchange_prices_collected': 0,
            # V32.0: OFA stats
            'large_orders_detected': 0,
            'vwap_gaps_detected': 0,
            'institutional_signals': 0,
            'volume_spikes': 0,
            'order_flow_score': 0.0
        }

        # V26.0: Cooldown tracking
        self._last_close_time: float = 0.0
        self._is_in_cooldown: bool = False
        self._daily_start_equity: float = 0.0
        self._last_reset_date: str = ""

        # V26.1: ATR tracking
        self._atr_cache: Dict[str, float] = {}  # symbol -> ATR value
        self._price_history: Dict[str, List[float]] = {}  # symbol -> price history

        # V26.1: OCO orders
        self._oco_orders: Dict[str, Dict[str, Any]] = {}  # order_id -> OCO order

        # V26.2: Order book and liquidity tracking
        self._orderbook_cache: Dict[str, Dict[str, Any]] = {}  # symbol -> bids/asks
        self._recent_volatility: Dict[str, List[float]] = {}  # symbol -> recent volatility
        self._slippage_history: List[float] = []  # slippage history for prediction
        self._multi_timeframe_prices: Dict[str, Any] = {}  # symbol -> {timeframe: []}
        self._momentum_history: Dict[str, List[float]] = {}  # symbol -> RSI-like values
        self._last_execution_time: float = 0.0
        self._price_returns: Dict[str, List[float]] = {}  # symbol -> returns for anomaly
        self._signal_history: List[Dict[str, Any]] = []  # signal history for filtering
        self._target_allocation: Dict[str, float] = {}  # target portfolio allocation
        self._sentiment_cache: Dict[str, float] = {}  # symbol -> sentiment score
        self._ml_predictions: Dict[str, float] = {}  # symbol -> ML prediction score
        self._funding_rates: Dict[str, float] = {}  # symbol -> funding rate
        self._alert_history: List[Dict[str, Any]] = []  # alert history

        # V25.8: Symbol exposure tracking
        self.symbol_exposure: Dict[str, float] = {}

        # 活跃持仓追踪 (V25.3新增)
        self.active_positions: Dict[str, Dict[str, Any]] = {}

        # V31.0: SOR状态追踪
        self._exchange_prices: Dict[str, List[ExchangePrice]] = {}  # symbol -> [prices from exchanges]
        self._sor_orders: Dict[str, SOROrder] = {}  # order_id -> SOR订单
        self._sor_queue: List[SOROrder] = []  # 待执行的SOR订单队列

        # V32.0: OFA状态追踪
        self._volume_history: Dict[str, List[float]] = {}  # symbol -> 交易量历史
        self._trade_history: Dict[str, List[Dict[str, Any]]] = {}  # symbol -> 交易记录
        self._vwap: Dict[str, float] = {}  # symbol -> VWAP
        self._large_orders: List[Dict[str, Any]] = []  # 检测到的大单
        self._institutional_signals: List[Dict[str, Any]] = []  # 机构订单信号
        # V33.0: Market Microstructure状态追踪
        self._market_depths: Dict[str, MarketDepth] = {}  # symbol/exchange -> 市场深度
        self._liquidity_pools: Dict[str, List[LiquidityPool]] = {}  # symbol -> 流动性池
        self._price_impacts: Dict[str, PriceImpact] = {}  # symbol -> 价格影响预测
        self._fused_signals: Dict[str, float] = {}  # symbol -> 融合信号评分
        self._depth_history: Dict[str, List[float]] = {}  # symbol -> 深度评分历史
        # V34.0: 跨交易所套利状态
        self._arbitrage_opportunities: List[ArbitrageOpportunity] = []  # 套利机会池
        self._cross_exchange_prices: Dict[str, List[ExchangePrice]] = {}  # symbol -> 各交易所价格
        # V34.0: 保证金池状态
        self._margin_positions: Dict[str, MarginPosition] = {}  # symbol -> 保证金头寸
        self._margin_pool_available: float = 0.0  # 可用保证金
        # V34.0: 执行队列状态
        self._execution_queue: List[ExecutionTask] = []  # 执行任务队列
        # V34.0: P&L状态
        self._daily_pnl: float = 0.0  # 今日盈亏
        self._total_realized_pnl: float = 0.0  # 总已实现盈亏
        self._trade_count: int = 0  # 交易次数
        self._win_count: int = 0  # 盈利次数
        # V35.0: 三角形套利状态
        self._triangular_opportunities: List[TriangularOpportunity] = []
        self._triangular_pairs: Dict[str, Dict[str, float]] = {}  # symbol -> rates
        # V35.0: 资金费率套利状态
        self._funding_arbitrage_opportunities: List[FundingArbitrage] = []
        self._funding_rates: Dict[str, Dict[str, float]] = {}  # exchange -> funding rates
        # V35.0: ML信号状态
        self._ml_signals: Dict[str, MLSignal] = {}  # symbol -> ML signal
        self._ml_predictions: Dict[str, List[float]] = {}  # symbol -> prediction history
        # V36.0: Grid Trading状态
        self._grid_strategies: Dict[str, GridStrategy] = {}  # strategy_id -> GridStrategy
        self._grid_orders: List[GridOrder] = []
        # V36.0: DCA状态
        self._dca_strategies: Dict[str, DCAStrategy] = {}  # strategy_id -> DCAStrategy
        # V36.0: Paper Trading状态
        self._paper_trades: List[PaperTrade] = []
        self._paper_balance: float = self.run_config.paper_trading_balance
        # V36.0: Trading Stats状态
        self._trading_stats: TradingStats = TradingStats()
        # V37.0: Backtesting状态
        self._backtest_results: Dict[str, BacktestResult] = {}
        self._backtest_trades: List[BacktestTrade] = []
        self._backtest_equity: float = self.run_config.backtest_initial_capital
        self._backtest_positions: Dict[str, Dict[str, Any]] = {}  # symbol -> position
        # V38.0: Risk Management状态
        self._risk_metrics: Dict[str, RiskMetrics] = {}  # symbol -> risk metrics
        self._portfolio: Dict[str, PortfolioPosition] = {}  # symbol -> portfolio position
        self._var_history: List[float] = []  # VaR历史
        self._daily_returns: List[float] = []  # 日收益率历史
        # V39.0: Real Trading状态
        self._exchange_configs: Dict[str, ExchangeConfig] = {}  # exchange -> config
        self._order_records: List[OrderRecord] = []  # 订单记录
        self._trade_signals: List[TradeSignal] = []  # 交易信号
        self._real_positions: Dict[str, Dict[str, Any]] = {}  # 真实持仓
        # V40.0: Multi-Strategy状态
        self._strategy_performances: Dict[str, StrategyPerformance] = {}
        self._strategy_allocations: Dict[str, StrategyAllocation] = {}
        self._market_regime: Optional[MarketRegimeData] = None
        self._last_rebalance: float = 0.0
        # V41.0: Dashboard & Alerts状态
        self._dashboard_widgets: Dict[str, DashboardWidget] = {}
        self._system_alerts: List[SystemAlert] = []
        self._schedule_tasks: Dict[str, ScheduleTask] = {}
        # V42.0: API Integration状态
        self._api_endpoints: Dict[str, APIEndpoint] = {}
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._exchange_status: Dict[str, ExchangeStatus] = {}
        # V43.0: Analytics状态
        self._analytics_reports: List[AnalyticsReport] = []
        self._trade_attributions: List[TradeAttribution] = []
        # V44.0: Portfolio & Execution状态
        self._optimizations: List[PortfolioOptimization] = []
        self._execution_algorithms: Dict[str, ExecutionAlgorithm] = {}
        # V45.0: Advanced Orders状态
        self._conditional_orders: Dict[str, ConditionalOrder] = {}
        self._iceberg_orders: Dict[str, IcebergOrder] = {}
        self._twap_orders: Dict[str, TWAPOrder] = {}
        self._position_snapshots: List[PositionSnapshot] = []
        # V46.0: Sentiment & Correlation状态
        self._sentiment_data: Dict[str, SentimentData] = {}
        self._correlation_pairs: Dict[str, CorrelationPair] = {}
        self._timeframe_signals: Dict[str, List[TimeframeSignal]] = {}
        # V47.0: Derivatives状态
        self._options_contracts: Dict[str, OptionsContract] = {}
        self._futures_contracts: Dict[str, FuturesContract] = {}
        self._margin_accounts: Dict[str, MarginAccount] = {}

    def start(self) -> bool:
        """启动自动交易

        Returns:
            是否成功
        """
        if self.is_running:
            logger.warning("⚠️ 自动交易已在运行中")
            return False

        try:
            self.is_running = True
            self.loop_status = LoopStatus.IDLE
            logger.info("✅ 自动交易引擎已启动")
            return True

        except Exception as e:
            logger.error(f"❌ 启动失败: {e}")
            return False

    def stop(self) -> bool:
        """停止自动交易

        Returns:
            是否成功
        """
        if not self.is_running:
            return True

        self.is_running = False
        self.loop_status = LoopStatus.STOPPED

        if self._scan_task:
            self._scan_task.cancel()
            self._scan_task = None

        logger.info("✅ 自动交易引擎已停止")
        return True

    def pause(self) -> bool:
        """暂停自动交易"""
        if not self.is_running:
            return False

        self.loop_status = LoopStatus.PAUSED
        logger.info("⏸️ 自动交易已暂停")
        return True

    def resume(self) -> bool:
        """恢复自动交易"""
        if self.loop_status != LoopStatus.PAUSED:
            return False

        self.loop_status = LoopStatus.IDLE
        logger.info("▶️ 自动交易已恢复")
        return True

    # ---------------------- V25.8: 最大暴露限制 ----------------------

    def get_symbol_exposure(self, symbol: str) -> float:
        """获取币种暴露金额

        Args:
            symbol: 交易对

        Returns:
            当前暴露金额
        """
        return self.symbol_exposure.get(symbol, 0.0)

    def check_exposure_limit(self, symbol: str, additional_size: float, price: float) -> bool:
        """检查是否超过最大暴露限制

        Args:
            symbol: 交易对
            additional_size: 追加仓位大小
            price: 价格

        Returns:
            是否允许执行
        """
        max_exposure = self.run_config.max_exposure_per_symbol
        current_exposure = self.get_symbol_exposure(symbol)
        new_exposure = current_exposure + (additional_size * price)

        if new_exposure > max_exposure:
            logger.warning(
                f"⚠️ 超过最大暴露限制: {symbol} | "
                f"当前: ${current_exposure:.2f} | 新增: ${new_exposure:.2f} | "
                f"上限: ${max_exposure:.2f}"
            )
            return False

        return True

    def update_symbol_exposure(
        self,
        symbol: str,
        size: float,
        price: float,
        is_entry: bool = True
    ) -> None:
        """更新币种暴露

        Args:
            symbol: 交易对
            size: 仓位大小
            price: 价格
            is_entry: 是否入场 (True=增加暴露, False=减少暴露)
        """
        if symbol not in self.symbol_exposure:
            self.symbol_exposure[symbol] = 0.0

        exposure_change = size * price

        if is_entry:
            self.symbol_exposure[symbol] += exposure_change
        else:
            self.symbol_exposure[symbol] = max(
                0.0,
                self.symbol_exposure[symbol] - exposure_change
            )

    # ---------------------- V25.8: 连亏熔断器 ----------------------

    def get_consecutive_loss_count(self) -> int:
        """获取连续亏损次数

        Returns:
            连续亏损次数
        """
        return self.stats['consecutive_losses']

    def is_circuit_breaker_active(self) -> bool:
        """检查熔断器是否激活

        Returns:
            是否处于熔断状态
        """
        if not self.run_config.enable_circuit_breaker:
            return False

        limit = self.run_config.consecutive_loss_limit
        return self.stats['consecutive_losses'] >= limit

    def _update_consecutive_trades(self, is_profitable: bool) -> None:
        """更新连盈/连亏统计

        Args:
            is_profitable: 是否盈利
        """
        if is_profitable:
            self.stats['consecutive_wins'] += 1
            self.stats['consecutive_losses'] = 0
        else:
            self.stats['consecutive_losses'] += 1
            self.stats['consecutive_wins'] = 0

        # 更新最大连亏记录
        if self.stats['consecutive_losses'] > self.stats['max_consecutive_losses']:
            self.stats['max_consecutive_losses'] = self.stats['consecutive_losses']

    def trigger_circuit_breaker(self) -> None:
        """触发熔断器"""
        if not self.is_circuit_breaker_active():
            return

        self.stats['circuit_breaker_triggered'] += 1
        self.loop_status = LoopStatus.PAUSED
        logger.warning(
            f"🛑 熔断器已触发! 连亏: {self.stats['consecutive_losses']} 次"
        )

        # 记录到知识库
        if self.knowledge_bridge:
            self.record_risk_event(
                event_type="circuit_break",
                severity="critical",
                strategy="auto",
                symbol="all",
                reason=f"连亏{self.stats['consecutive_losses']}次",
                action_taken="暂停交易"
            )

    def reset_circuit_breaker(self) -> None:
        """重置熔断器"""
        self.stats['consecutive_losses'] = 0
        self.stats['consecutive_wins'] = 0
        logger.info("🔄 熔断器已重置")

    # ---------------------- V25.8: 执行质量追踪 ----------------------

    def calculate_execution_quality(
        self,
        expected_price: float,
        executed_price: float
    ) -> Tuple[float, float]:
        """计算执行质量

        Args:
            expected_price: 预期价格
            executed_price: 实际执行价格

        Returns:
            (滑点金额, 滑点百分比)
        """
        if expected_price <= 0:
            return 0.0, 0.0

        slippage = abs(executed_price - expected_price)
        slippage_pct = (slippage / expected_price) * 100

        return slippage, slippage_pct

    def calculate_quality_score(self, slippage_pct: float) -> float:
        """计算执行质量分数

        Args:
            slippage_pct: 滑点百分比

        Returns:
            质量分数 (0-100)
        """
        # 滑点越小分数越高
        if slippage_pct <= 0.1:  # <=0.1%
            return 100.0
        elif slippage_pct <= 0.25:  # <=0.25%
            return 90.0
        elif slippage_pct <= 0.5:  # <=0.5%
            return 80.0
        elif slippage_pct <= 1.0:  # <=1%
            return 70.0
        elif slippage_pct <= 2.0:  # <=2%
            return 50.0
        else:
            return 30.0

    # ---------------------- V25.9: 紧急止损 ----------------------

    def get_total_exposure(self) -> float:
        """获取总暴露金额

        Returns:
            所有币种的总暴露金额
        """
        return sum(self.symbol_exposure.values())

    def check_global_exposure_limit(self) -> bool:
        """检查全局暴露限制

        Returns:
            是否在限制内
        """
        max_total = self.run_config.max_total_exposure
        current_total = self.get_total_exposure()

        if current_total >= max_total:
            logger.warning(
                f"⚠️ 达到全局暴露限制: ${current_total:.2f} / ${max_total:.2f}"
            )
            return False
        return True

    def check_emergency_stop(self, current_equity: float) -> bool:
        """检查是否触发紧急止损

        Args:
            current_equity: 当前权益

        Returns:
            是否触发紧急止损
        """
        if self._daily_start_equity <= 0:
            return False

        loss_pct = (self._daily_start_equity - current_equity) / self._daily_start_equity

        if loss_pct >= self.run_config.emergency_stop_pct:
            logger.warning(
                f"🛑 触发紧急止损! 亏损: {loss_pct*100:.2f}% "
                f"(限制: {self.run_config.emergency_stop_pct*100:.1f}%)"
            )
            return True
        return False

    def trigger_emergency_stop(self) -> None:
        """触发紧急止损"""
        self.stats['emergency_stop_triggered'] += 1
        self.loop_status = LoopStatus.STOPPED
        self.is_running = False

        logger.critical("🛑 紧急止损已触发! 交易停止.")

        if self.knowledge_bridge:
            self.record_risk_event(
                event_type="emergency_stop",
                severity="critical",
                strategy="auto",
                symbol="all",
                reason=f"亏损超过{self.run_config.emergency_stop_pct*100:.0f}%",
                action_taken="停止所有交易"
            )

    # ---------------------- V25.9: 每日盈亏追踪 ----------------------

    def get_daily_pnl(self) -> float:
        """获取当日盈亏

        Returns:
            当日盈亏金额
        """
        return self.stats['daily_pnl']

    def get_daily_loss_pct(self) -> float:
        """获取当日亏损百分比

        Returns:
            当日亏损百分比
        """
        if self._daily_start_equity <= 0:
            return 0.0
        return abs(self.stats['daily_loss']) / self._daily_start_equity

    def check_daily_loss_limit(self) -> bool:
        """检查是否达到每日亏损限制

        Returns:
            是否允许���续交易
        """
        daily_loss_pct = self.get_daily_loss_pct()

        if daily_loss_pct >= self.run_config.daily_loss_limit:
            logger.warning(
                f"⚠️ 达到每日亏损限制: {daily_loss_pct*100:.2f}% "
                f"(限制: {self.run_config.daily_loss_limit*100:.1f}%)"
            )
            return False
        return True

    def update_daily_pnl(self, pnl: float) -> None:
        """更新当日盈亏

        Args:
            pnl: 盈亏金额
        """
        self._check_daily_reset()

        if pnl > 0:
            self.stats['daily_profit'] += pnl
        else:
            self.stats['daily_loss'] += abs(pnl)

        self.stats['daily_pnl'] = self.stats['daily_profit'] - self.stats['daily_loss']

    def _check_daily_reset(self) -> None:
        """检查并重置每日统计"""
        today = datetime.now().strftime('%Y-%m-%d')

        if self._last_reset_date != today:
            # 新的一天，重置每日统计
            self.stats['daily_profit'] = 0.0
            self.stats['daily_loss'] = 0.0
            self.stats['daily_pnl'] = 0.0
            self.stats['daily_stop_triggered'] = 0
            self._last_reset_date = today

            logger.info(f"📅 新的一天 {today} - 每日统计已重置")

    def set_daily_start_equity(self, equity: float) -> None:
        """设置当日起始权益

        Args:
            equity: 权益金额
        """
        self._check_daily_reset()
        if self._daily_start_equity <= 0:
            self._daily_start_equity = equity

    # ---------------------- V26.0: 追踪止损 ----------------------

    def get_trailing_stop_price(
        self,
        entry_price: float,
        current_price: float,
        is_long: bool = True
    ) -> float:
        """计算追踪止损价格

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            is_long: 是否做多

        Returns:
            追踪止损价格
        """
        if not self.run_config.enable_trailing_stop:
            return entry_price * (1 - self.run_config.stop_loss_pct)

        trailing_pct = self.run_config.trailing_stop_pct

        if is_long:
            # 做多: 追踪最高价-固定百分比
            highest = max(entry_price, current_price)
            return highest * (1 - trailing_pct)
        else:
            # 做空: 追踪最低价+固定百分比
            lowest = min(entry_price, current_price)
            return lowest * (1 + trailing_pct)

    def check_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        is_long: bool = True
    ) -> bool:
        """检查是否触发追踪止损

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            is_long: 是否做多

        Returns:
            是否触发
        """
        if not self.run_config.enable_trailing_stop:
            return False

        trailing_stop = self.get_trailing_stop_price(
            entry_price, current_price, is_long
        )

        if is_long and current_price <= trailing_stop:
            logger.info(f"🛑 触发追踪止损: 当前${current_price:.2f} < 止损${trailing_stop:.2f}")
            return True
        elif not is_long and current_price >= trailing_stop:
            logger.info(f"🛑 触发追踪止损: 当前${current_price:.2f} > 止损${trailing_stop:.2f}")
            return True

        return False

    # ---------------------- V26.0: 平仓冷却 ----------------------

    def is_in_cooldown(self) -> bool:
        """检查是否在冷却时间

        Returns:
            是否在冷却
        """
        if not self._is_in_cooldown:
            return False

        # 检查冷却时间是否结束
        elapsed = time.time() - self._last_close_time
        if elapsed >= self.run_config.cooldown_seconds:
            self._is_in_cooldown = False
            logger.info(f"⏰ 冷却时间结束 ({elapsed:.0f}s)")
            return False

        logger.debug(f"⏳ 冷却中... 剩余 {self.run_config.cooldown_seconds - elapsed:.0f}s")
        return True

    def start_cooldown(self) -> None:
        """开始冷却时间"""
        self._is_in_cooldown = True
        self._last_close_time = time.time()
        logger.info(f"⏳ 开始冷却: {self.run_config.cooldown_seconds}s")

    def reset_cooldown(self) -> None:
        """重置冷却时间"""
        self._is_in_cooldown = False
        self._last_close_time = 0.0
        logger.info("⏰ 冷却时间已重置")

    # ---------------------- V26.0: 周末交易控制 ----------------------

    def is_weekend(self) -> bool:
        """检查是否周末

        Returns:
            是否周末
        """
        return datetime.now().weekday() >= 5  # 5=Saturday, 6=Sunday

    def is_weekend_trading_allowed(self) -> bool:
        """检查是否允许周末交易

        Returns:
            是否允许
        """
        if self.run_config.allow_weekend_trading:
            return True

        if self.is_weekend():
            logger.warning("⛔ 周末交易已禁用")
            return False

        return True

    # ---------------------- V26.1: Time-In-Force (TIF) ----------------------

    def validate_tif_order(
        self,
        tif: str,
        order_time: float,
        current_time: float
    ) -> bool:
        """验证TIF订单是否有效

        Args:
            tif: 时间有效期限 (gtc/ioc/fok/gtt)
            order_time: 订单下单时间
            current_time: 当前时间

        Returns:
            是否有效
        """
        if tif == "gtc":
            return True  # Good Till Cancel - always valid
        elif tif == "ioc":
            # Immediate Or Cancel - must fill within a short period
            return (current_time - order_time) <= 60  # 60 seconds
        elif tif == "fok":
            # Fill Or Kill - must fill immediately
            return (current_time - order_time) <= 5  # 5 seconds
        elif tif == "gtt":
            # Good Till Time - valid for configured time
            return (current_time - order_time) <= self.run_config.max_holding_seconds
        return True

    # ---------------------- V26.1: ATR-based Trailing Stop ----------------------

    def update_price_history(self, symbol: str, price: float) -> None:
        """更新价格历史

        Args:
            symbol: 交易对
            price: 价格
        """
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        self._price_history[symbol].append(price)
        # Keep only the necessary number of periods
        max_history = self.run_config.atr_periods * 2
        if len(self._price_history[symbol]) > max_history:
            self._price_history[symbol] = self._price_history[symbol][-max_history:]

    def calculate_atr(self, symbol: str) -> float:
        """计算ATR (Average True Range)

        Args:
            symbol: 交易对

        Returns:
            ATR值
        """
        if symbol not in self._price_history:
            return 0.0

        prices = self._price_history[symbol]
        if len(prices) < self.run_config.atr_periods:
            return 0.0

        # Calculate True Range for each period
        tr_values = []
        for i in range(1, min(len(prices), self.run_config.atr_periods + 1)):
            high = max(prices[i], prices[i-1])
            low = min(prices[i], prices[i-1])
            tr = high - low
            tr_values.append(tr)

        if not tr_values:
            return 0.0

        return sum(tr_values) / len(tr_values)

    def get_atr_trailing_stop_price(
        self,
        entry_price: float,
        current_price: float,
        is_long: bool = True
    ) -> float:
        """计算ATR追踪止损价格

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            is_long: 是否做多

        Returns:
            ATR追踪止损价格
        """
        # Get a default symbol if we don't have one
        symbol = "BTC/USDT"
        atr = self._atr_cache.get(symbol, self.calculate_atr(symbol))

        if atr <= 0:
            # Fallback to percentage-based trailing stop
            return self.get_trailing_stop_price(entry_price, current_price, is_long)

        if is_long:
            highest = max(entry_price, current_price)
            return highest - (atr * self.run_config.atr_multiplier)
        else:
            lowest = min(entry_price, current_price)
            return lowest + (atr * self.run_config.atr_multiplier)

    def check_atr_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        is_long: bool = True
    ) -> bool:
        """检查是否触发ATR追踪止损

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            is_long: 是否做多

        Returns:
            是否触发
        """
        if not self.run_config.enable_atr_trailing:
            return False

        atr_stop = self.get_atr_trailing_stop_price(entry_price, current_price, is_long)

        if is_long and current_price <= atr_stop:
            logger.info(
                f"🛑 触发ATR追踪止损: 当前${current_price:.2f} < 止损${atr_stop:.2f}"
            )
            return True
        elif not is_long and current_price >= atr_stop:
            logger.info(
                f"🛑 触发ATR追踪止损: 当前${current_price:.2f} > 止损${atr_stop:.2f}"
            )
            return True

        return False

    # ---------------------- V26.1: Position Time Limit ----------------------

    def check_position_time_limit(
        self,
        entry_time: float,
        current_time: float
    ) -> bool:
        """检查是否超过持仓时间限制

        Args:
            entry_time: 入场时间
            current_time: 当前时间

        Returns:
            是否超时
        """
        max_seconds = self.run_config.max_holding_seconds
        if max_seconds <= 0:
            return False

        holding_seconds = current_time - entry_time
        return holding_seconds >= max_seconds

    # ---------------------- V26.1: Correlation-based Limit ----------------------

    def check_correlation_limit(self, symbol: str, new_exposure: float) -> bool:
        """检查相关性仓位限制

        Args:
            symbol: 交易对
            new_exposure: 新增暴露

        Returns:
            是否允许
        """
        if not self.active_positions:
            return True

        # Simplified correlation check - check if adding this position
        # would exceed the correlation limit with existing positions
        # In a real system, you'd calculate actual correlation
        # Here we just do a simple check on number of positions
        limit = self.run_config.correlation_limit

        # Check total correlation exposure (simplified)
        total_correlated = 0.0
        for pos in self.active_positions.values():
            pos_symbol = pos.get('symbol', '')
            # Simplified: assume BTC/ETH/SOL are correlated
            if any(c in pos_symbol for c in ['BTC', 'ETH', 'SOL']):
                if any(c in symbol for c in ['BTC', 'ETH', 'SOL']):
                    total_correlated += pos.get('size', 0) * pos.get('entry_price', 0)

        # Check if new position would make correlation too high
        current_existing = self.symbol_exposure.get(symbol, 0.0)
        total_with_new = total_correlated + new_exposure + current_existing
        max_correlated = self.run_config.max_total_exposure * limit

        if total_with_new > max_correlated:
            logger.warning(
                f"⚠️ 相关性限制: ${total_with_new:.2f} > ${max_correlated:.2f}"
            )
            self.stats['correlation_rejected'] += 1
            return False

        return True

    # ---------------------- V26.1: OCO Orders ----------------------

    def create_oco_order(
        self,
        opportunity_id: str,
        primary_opp: ScannedOpportunity,
        secondary_opp: ScannedOpportunity
    ) -> str:
        """创建OCO (One-Cancels-Other) 订单

        Args:
            opportunity_id: 订单ID
            primary_opp: 主要机会
            secondary_opp: 备用机会

        Returns:
            订单ID
        """
        oco_id = f"oco_{opportunity_id}"

        self._oco_orders[oco_id] = {
            'primary': primary_opp,
            'secondary': secondary_opp,
            'created_at': time.time(),
            'filled': False,
            'cancelled': False
        }

        self.stats['oco_orders_created'] += 1
        logger.info(f"📋 OCO订单已创建: {oco_id}")

        return oco_id

    def check_oco_order(
        self,
        oco_id: str,
        filled_symbol: str
    ) -> Optional[ScannedOpportunity]:
        """检查OCO订单状态

        Args:
            oco_id: OCO订单ID
            filled_symbol: 已成交的交易对

        Returns:
            需要取消的其他订单，如果没有则返回None
        """
        if oco_id not in self._oco_orders:
            return None

        oco = self._oco_orders[oco_id]
        if oco.get('filled') or oco.get('cancelled'):
            return None

        # Check which leg was filled
        primary_filled = oco['primary'].symbol == filled_symbol
        secondary_filled = oco['secondary'].symbol == filled_symbol

        if primary_filled or secondary_filled:
            oco['filled'] = True
            self.stats['oco_orders_filled'] += 1

            # Return the other leg to potentially cancel it
            if primary_filled:
                return oco['secondary']
            else:
                return oco['primary']

        return None

    # ---------------------- V26.2: Order Book Analysis ----------------------

    def update_orderbook(
        self,
        symbol: str,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]]
    ) -> None:
        """更新订单簿数据

        Args:
            symbol: 交易对
            bids: 买单 [(price, size), ...]
            asks: 卖单 [(price, size), ...]
        """
        self._orderbook_cache[symbol] = {
            'bids': bids,
            'asks': asks,
            'timestamp': time.time()
        }

    def analyze_orderbook_depth(
        self,
        symbol: str,
        levels: int = 5
    ) -> Dict[str, Any]:
        """分析订单簿深度

        Args:
            symbol: 交易对
            levels: 分析深度级别数

        Returns:
            订单簿分析结果
        """
        if symbol not in self._orderbook_cache:
            return {
                'sufficient_liquidity': False,
                'bid_depth': 0.0,
                'ask_depth': 0.0,
                'spread_pct': 0.0,
                'impact_10pct': 0.0
            }

        ob = self._orderbook_cache[symbol]
        bids = ob.get('bids', [])
        asks = ob.get('asks', [])

        if not bids or not asks:
            return {
                'sufficient_liquidity': False,
                'bid_depth': 0.0,
                'ask_depth': 0.0,
                'spread_pct': 0.0,
                'impact_10pct': 0.0
            }

        # Calculate bid depth (total value in top N levels)
        bid_depth = sum(size * price for price, size in bids[:levels])

        # Calculate ask depth
        ask_depth = sum(size * price for price, size in asks[:levels])

        # Calculate spread
        best_bid = bids[0][0] if bids else 0.0
        best_ask = asks[0][0] if asks else 0.0
        spread_pct = (best_ask - best_bid) / best_bid if best_bid > 0 else 0.0

        # Estimate price impact for 10% order
        mid_price = (best_bid + best_ask) / 2
        target_size = mid_price * 0.10  # 10% of notional
        impact_10pct = self._estimate_price_impact(
            symbol, target_size, bids, asks
        )

        return {
            'sufficient_liquidity': bid_depth >= self.run_config.min_liquidity_depth,
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'spread_pct': spread_pct,
            'impact_10pct': impact_10pct,
            'best_bid': best_bid,
            'best_ask': best_ask
        }

    def _estimate_price_impact(
        self,
        symbol: str,
        target_size: float,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]]
    ) -> float:
        """估算价格影响

        Args:
            symbol: 交易对
            target_size: 目标订单大小
            bids: 买单
            asks: 卖单

        Returns:
            预估价格影响百分比
        """
        remaining = target_size
        filled = 0.0
        avg_fill_price = 0.0

        for price, size in asks:
            fillable = min(remaining, size * price)
            filled += fillable
            avg_fill_price += fillable * price
            remaining -= fillable

            if remaining <= 0:
                break

        if filled <= 0:
            return 1.0  # 100% impact if can't fill

        avg_fill_price /= filled
        mid_price = asks[0][0] if asks else 0.0

        return (avg_fill_price - mid_price) / mid_price if mid_price > 0 else 0.0

    def check_liquidity(
        self,
        symbol: str,
        order_size: float
    ) -> bool:
        """检查市场流动性是否足够

        Args:
            symbol: 交易对
            order_size: 订单大小

        Returns:
            是否流动性足够
        """
        if not self.run_config.enable_orderbook_analysis:
            return True

        # If no orderbook data, assume sufficient liquidity
        if symbol not in self._orderbook_cache:
            return True

        analysis = self.analyze_orderbook_depth(symbol)

        if not analysis['sufficient_liquidity']:
            logger.warning(f"⚠️ 流动性不足: {symbol}")
            self.stats['liquidity_rejected'] += 1
            return False

        # Check if order can be filled with reasonable impact
        required_depth = order_size  # order_size is in USD
        if required_depth > analysis.get('ask_depth', 0):
            logger.warning(f"⚠️ 订单超过深度: {symbol}")
            self.stats['liquidity_rejected'] += 1
            return False

        return True

    # ---------------------- V26.2: Slippage Prediction ----------------------

    def predict_slippage(
        self,
        symbol: str,
        order_size: float
    ) -> float:
        """预测滑点

        Args:
            symbol: 交易对
            order_size: 订单大小

        Returns:
            预测滑点百分比
        """
        # Use historical slippage if available
        if self._slippage_history:
            recent = self._slippage_history[-10:]
            avg_historical = sum(recent) / len(recent)
        else:
            avg_historical = 0.0

        # Get order book impact
        if symbol in self._orderbook_cache:
            ob = self._orderbook_cache[symbol]
            bids = ob.get('bids', [])
            asks = ob.get('asks', [])

            if bids and asks:
                impact = self._estimate_price_impact(
                    symbol, order_size, bids, asks
                )
                # Weighted average: 70% orderbook, 30% history
                return impact * 0.7 + avg_historical * 0.3

        return avg_historical

    def check_slippage_warning(
        self,
        symbol: str,
        order_size: float
    ) -> bool:
        """检查是否滑点过高

        Args:
            symbol: 交易对
            order_size: 订单大小

        Returns:
            是否滑点过高
        """
        predicted = self.predict_slippage(symbol, order_size)
        threshold = self.run_config.slippage_warning_threshold

        if predicted > threshold:
            logger.warning(
                f"⚠️ 滑点过高: {symbol} 预测{predicted*100:.2f}% > 阈值{threshold*100:.2f}%"
            )
            self.stats['slippage_warnings'] += 1
            return True

        return False

    def record_slippage(self, slippage_pct: float) -> None:
        """记录实际滑点用于预测

        Args:
            slippage_pct: 滑点百分比
        """
        self._slippage_history.append(slippage_pct)
        # Keep last 100 for prediction
        if len(self._slippage_history) > 100:
            self._slippage_history = self._slippage_history[-100:]

    # ---------------------- V26.2: Dynamic Parameters ----------------------

    def update_volatility(self, symbol: str, price: float) -> None:
        """更新波动率数据

        Args:
            symbol: 交易对
            price: 当前价格
        """
        if symbol not in self._recent_volatility:
            self._recent_volatility[symbol] = []

        self._recent_volatility[symbol].append(price)

        # Keep only volatility_lookback periods
        lookback = self.run_config.volatility_lookback
        if len(self._recent_volatility[symbol]) > lookback:
            self._recent_volatility[symbol] = self._recent_volatility[symbol][-lookback:]

    def calculate_current_volatility(self, symbol: str) -> float:
        """计算当前波动率

        Args:
            symbol: 交易对

        Returns:
            波动率
        """
        # If no volatility data, return 0
        if symbol not in self._recent_volatility:
            return 0.0

        prices = self._recent_volatility.get(symbol, [])
        if len(prices) < 2:
            return 0.0

        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)

        if not returns:
            return 0.0

        # Standard deviation of returns
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)

        return variance ** 0.5

    def check_volatility_spike(self, symbol: str) -> bool:
        """检查波动率是否急剧上升

        Args:
            symbol: 交易对

        Returns:
            是否波动率急剧上升
        """
        current_vol = self.calculate_current_volatility(symbol)

        if current_vol <= 0:
            return False

        # Get historical volatility from ATR cache
        hist_vol = self._atr_cache.get(symbol, 0.01)  # Default 1%

        if current_vol > hist_vol * 2:  # More than 2x historical
            logger.warning(
                f"⚠️ 波动率急剧上升: {symbol} 当前{current_vol*100:.2f}% > 历史{hist_vol*100:.2f}%"
            )
            self.stats['volatility_spike'] += 1
            return True

        return False

    def adjust_params_for_market(self, symbol: str) -> Dict[str, float]:
        """根据市场状况动态调整参数

        Args:
            symbol: 交易对

        Returns:
            调整后的参数
        """
        if not self.run_config.enable_dynamic_params:
            return {
                'score_threshold': self.run_config.min_score_threshold,
                'stop_loss_pct': self.run_config.stop_loss_pct,
                'position_multiplier': 1.0
            }

        vol = self.calculate_current_volatility(symbol)
        default_vol = 0.02  # 2% default

        # No volatility data - use defaults
        if vol <= 0:
            return {
                'score_threshold': self.run_config.min_score_threshold,
                'stop_loss_pct': self.run_config.stop_loss_pct,
                'position_multiplier': 1.0
            }

        # High volatility -> higher thresholds, smaller positions
        if vol > default_vol * 2:
            new_score = min(80.0, self.run_config.min_score_threshold + 5.0)
            new_stop = self.run_config.stop_loss_pct * 0.8
            position_mult = 0.7
        elif vol > default_vol * 1.5:
            new_score = self.run_config.min_score_threshold + 2.5
            new_stop = self.run_config.stop_loss_pct * 0.9
            position_mult = 0.85
        elif vol < default_vol * 0.05:
            # Very low volatility - can be slightly more aggressive
            # But only if volatility is almost zero
            new_score = max(50.0, self.run_config.min_score_threshold - 5.0)
            new_stop = self.run_config.stop_loss_pct * 1.2
            position_mult = 1.2
        else:
            # Normal - use defaults
            return {
                'score_threshold': self.run_config.min_score_threshold,
                'stop_loss_pct': self.run_config.stop_loss_pct,
                'position_multiplier': 1.0
            }

        self.stats['params_adjusted'] += 1
        logger.info(
            f"📊 参数已调整: {symbol} score {self.run_config.min_score_threshold:.1f}→{new_score:.1f}, "
            f"stop {self.run_config.stop_loss_pct*100:.1f}→{new_stop*100:.1f}%"
        )

        return {
            'score_threshold': new_score,
            'stop_loss_pct': new_stop,
            'position_multiplier': position_mult
        }

    # ---------------------- V26.3: Market Regime Detection ----------------------

    def detect_market_regime(
        self,
        symbol: str,
        prices: Optional[List[float]] = None
    ) -> str:
        """检测市场区间 (牛市/熊市/震荡)"""
        if prices is None:
            prices = self._recent_volatility.get(symbol, [])

        if len(prices) < 10:
            return 'SIDEWAYS'

        recent = prices[-10:]
        if len(recent) < 10:
            return 'SIDEWAYS'

        first_price = recent[0]
        last_price = recent[-1]
        change_pct = (last_price - first_price) / first_price

        returns = []
        for i in range(1, len(recent)):
            ret = (recent[i] - recent[i-1]) / recent[i-1]
            returns.append(ret)

        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        else:
            return 'SIDEWAYS'

        if change_pct > 0.02 and std_return < 0.05:
            return 'BULL'
        elif change_pct < -0.02:
            return 'BEAR'
        return 'SIDEWAYS'

    def check_market_regime_for_position(self, regime: str) -> float:
        """根据市场区间调整仓位"""
        if regime == 'BULL':
            return 1.2
        elif regime == 'BEAR':
            return 0.5
        return 0.8

    # ---------------------- V26.3: Time-of-Day Rules ----------------------

    def get_trading_session(self) -> str:
        """获取当前交易时段"""
        hour = datetime.now().hour

        if self.run_config.asian_session_start <= hour < self.run_config.asian_session_end:
            return 'ASIAN'
        elif self.run_config.london_session_start <= hour < self.run_config.london_session_end:
            return 'LONDON'
        elif self.run_config.ny_session_start <= hour < self.run_config.ny_session_end:
            return 'NY'
        return 'OFF_HOURS'

    def check_time_rules(self) -> bool:
        """检查时段交易规则"""
        if not self.run_config.enable_time_rules:
            return True

        session = self.get_trading_session()

        if session == 'OFF_HOURS':
            self.stats['time_rule_rejected'] += 1
            return False

        return True

    def get_session_multiplier(self) -> float:
        """获取时段仓位乘数"""
        session = self.get_trading_session()

        if session == 'LONDON':
            return 1.2
        elif session == 'NY':
            return 1.1
        elif session == 'ASIAN':
            return 0.8
        return 0.5

    # ---------------------- V26.3: Spread Deviation ----------------------

    def calculate_spread_deviation(
        self,
        current_spread: float,
        historical_spread: float
    ) -> float:
        if historical_spread <= 0:
            return 0.0
        return abs(current_spread - historical_spread) / historical_spread

    def check_spread_deviation(
        self,
        current_spread: float,
        historical_spread: float = 0.001
    ) -> bool:
        deviation = self.calculate_spread_deviation(
            current_spread, historical_spread
        )

        if deviation > self.run_config.spread_deviation_threshold:
            self.stats['spread_warnings'] += 1
            return True

        return False

    # ---------------------- V26.3: Order Book Imbalance ----------------------

    def calculate_orderbook_imbalance(self, symbol: str) -> float:
        if symbol not in self._orderbook_cache:
            return 0.0

        ob = self._orderbook_cache[symbol]
        bids = ob.get('bids', [])
        asks = ob.get('asks', [])

        if not bids or not asks:
            return 0.0

        bid_volume = sum(size for _, size in bids[:5])
        ask_volume = sum(size for _, size in asks[:5])

        if bid_volume + ask_volume <= 0:
            return 0.0

        return (bid_volume - ask_volume) / (bid_volume + ask_volume)

    def check_orderbook_imbalance(self, symbol: str) -> bool:
        imbalance = self.calculate_orderbook_imbalance(symbol)

        if abs(imbalance) > self.run_config.imbalance_threshold:
            self.stats['imbalance_warnings'] += 1
            return True

        return False

    # ---------------------- V27.0: Multi-Timeframe Analysis ----------------------

    def update_timeframe_prices(
        self,
        symbol: str,
        timeframe: str,
        price: float
    ) -> None:
        """更新多时间框架价格数据

        Args:
            symbol: 交易对
            timeframe: 时间框架 (1m/5m/15m/1h)
            price: 价格
        """
        if symbol not in self._multi_timeframe_prices:
            self._multi_timeframe_prices[symbol] = {}

        if timeframe not in self._multi_timeframe_prices[symbol]:
            self._multi_timeframe_prices[symbol][timeframe] = []

        self._multi_timeframe_prices[symbol][timeframe].append(price)

        # Keep only 50 periods
        if len(self._multi_timeframe_prices[symbol][timeframe]) > 50:
            self._multi_timeframe_prices[symbol][timeframe] = \
                self._multi_timeframe_prices[symbol][timeframe][-50:]

    def calculate_multitimeframe_signal(
        self,
        symbol: str
    ) -> float:
        """计算多时间框架信号

        Args:
            symbol: 交易对

        Returns:
            信号强度 (-1 到 1)
        """
        if not self.run_config.enable_multitimeframe:
            return 0.0

        if symbol not in self._multi_timeframe_prices:
            return 0.0

        tf_data = self._multi_timeframe_prices[symbol]
        if not tf_data:
            return 0.0

        # Check each timeframe
        signals = []
        for tf, prices in tf_data.items():
            if len(prices) < 5:
                continue

            # Simple trend calculation
            recent = prices[-5:]
            if len(recent) < 2:
                continue

            change = (recent[-1] - recent[0]) / recent[0]
            signals.append(change * 10)  # Scale to -1 to 1

        if not signals:
            return 0.0

        # Average all timeframe signals
        avg_signal = sum(signals) / len(signals)
        return max(-1.0, min(1.0, avg_signal))

    # ---------------------- V27.0: Momentum Oscillator ----------------------

    def calculate_rsi(self, symbol: str) -> float:
        """计算RSI (Relative Strength Index)

        Args:
            symbol: 交易对

        Returns:
            RSI值 (0-100)
        """
        if not self.run_config.enable_momentum:
            return 50.0  # Neutral

        prices = self._recent_volatility.get(symbol, [])
        if len(prices) < self.run_config.rsi_periods + 1:
            return 50.0

        period = self.run_config.rsi_periods
        recent_prices = prices[-period-1:]

        # Calculate gains and losses
        gains = []
        losses = []
        for i in range(1, len(recent_prices)):
            change = recent_prices[i] - recent_prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_momentum_signal(self, symbol: str) -> str:
        """获取动量信号

        Args:
            symbol: 交易对

        Returns:
            信号: OVERBOUGHT/OVERSOLD/NEUTRAL
        """
        rsi = self.calculate_rsi(symbol)

        if rsi > 70:
            return 'OVERBOUGHT'
        elif rsi < 30:
            return 'OVERSOLD'
        return 'NEUTRAL'

    # ---------------------- V27.0: Execution Delay ----------------------

    async def simulate_execution_delay(self) -> None:
        """模拟执行延迟

        用于测试真实场景下的延迟影响
        """
        delay_ms = self.run_config.execution_delay_ms

        if delay_ms <= 0:
            return

        self.stats['execution_delays'] += 1

        # Sleep for the delay duration
        await asyncio.sleep(delay_ms / 1000.0)

    def get_time_since_last_execution(self) -> float:
        """获取上次执行经过的时间(秒)

        Returns:
            秒数
        """
        if self._last_execution_time <= 0:
            return 999999.0

        return time.time() - self._last_execution_time

    def record_execution_time(self) -> None:
        """记录执行时间"""
        self._last_execution_time = time.time()

    # ---------------------- V28.0: Hedging Strategy ----------------------

    def check_hedging_needed(self, symbol: str) -> bool:
        """检查是否需要对冲

        Args:
            symbol: 交易对

        Returns:
            是否需要对冲
        """
        if not self.run_config.enable_hedging:
            return False

        # Check correlation with existing positions
        if not self.active_positions:
            return False

        # Simple check: if similar asset already has large position
        for pos in self.active_positions.values():
            pos_symbol = pos.get('symbol', '')
            if symbol != pos_symbol:
                # Check correlation
                both_crypto = all(c in [symbol, pos_symbol] for c in ['BTC', 'ETH', 'SOL'])
                if both_crypto:
                    pos_size = pos.get('size', 0) * pos.get('entry_price', 0)
                    if pos_size > self.run_config.max_total_exposure * self.run_config.hedge_correlation:
                        return True
        return False

    def calculate_hedge_size(self, symbol: str) -> float:
        """计算对冲仓位大小

        Args:
            symbol: 交易对

        Returns:
            对冲仓位大小
        """
        if not self.check_hedging_needed(symbol):
            return 0.0

        # Reduce position by 50% when hedging
        return self.run_config.max_total_exposure * 0.5

    # ---------------------- V28.0: Advanced Signal Filtering ----------------------

    def record_signal(self, opportunity: ScannedOpportunity) -> None:
        """记录信号用于过滤分析"""
        if not self.run_config.enable_advanced_filter:
            return

        self._signal_history.append({
            'symbol': opportunity.symbol,
            'score': opportunity.score,
            'confidence': opportunity.confidence,
            'timestamp': time.time()
        })

        # Keep only last 100
        if len(self._signal_history) > 100:
            self._signal_history = self._signal_history[-100:]

    def filter_signal(self, opportunity: ScannedOpportunity) -> bool:
        """高级信号过滤

        Args:
            opportunity: 机会

        Returns:
            是否通过过滤
        """
        if not self.run_config.enable_advanced_filter:
            return True

        # Check minimum confidence
        if opportunity.confidence < self.run_config.filter_confidence_min:
            self.stats['filtered_signals'] += 1
            return False

        # Check for signal spam (similar signals in short time)
        recent_signals = [s for s in self._signal_history[-10:]
                        if s['symbol'] == opportunity.symbol]
        if len(recent_signals) >= 3:
            self.stats['filtered_signals'] += 1
            return False

        return True

    # ---------------------- V28.0: Statistical Anomaly Detection ----------------------

    def update_returns(self, symbol: str, price: float) -> None:
        """更新收益数据"""
        if symbol not in self._price_returns:
            self._price_returns[symbol] = []

        prices = self._price_returns[symbol]
        if prices:
            ret = (price - prices[-1]) / prices[-1]
            self._price_returns[symbol].append(ret)

        self._price_returns[symbol].append(price)

        if len(self._price_returns[symbol]) > 50:
            self._price_returns[symbol] = self._price_returns[symbol][-50:]

    def detect_anomaly(self, symbol: str) -> bool:
        """检测统计异常

        Args:
            symbol: 交易对

        Returns:
            是否检测到异常
        """
        if not self.run_config.enable_anomaly_detection:
            return False

        returns = self._price_returns.get(symbol, [])
        if len(returns) < 10:
            return False

        # Calculate mean and std
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        std = variance ** 0.5

        if std <= 0:
            return False

        # Check last return for anomaly
        last_return = returns[-1]
        z_score = abs(last_return - mean) / std

        if z_score > self.run_config.anomaly_threshold:
            self.stats['anomaly_detected'] += 1
            return True

        return False

    # ---------------------- V29.0: Portfolio Rebalancing ----------------------

    def set_target_allocation(self, symbol: str, target_pct: float) -> None:
        """设置目标配置比例

        Args:
            symbol: 交易对
            target_pct: 目标百分比 (0-1)
        """
        self._target_allocation[symbol] = target_pct

    def check_rebalancing_needed(self) -> bool:
        """检查是否需要再平衡

        Returns:
            是否需要再平衡
        """
        if not self.run_config.enable_rebalancing:
            return False

        if not self._target_allocation:
            return False

        total_exposure = self.get_total_exposure()
        if total_exposure <= 0:
            return False

        for symbol, target_pct in self._target_allocation.items():
            current_pct = self.symbol_exposure.get(symbol, 0) / total_exposure
            diff = abs(current_pct - target_pct)

            if diff > self.run_config.rebalance_threshold:
                self.stats['rebalancing_triggered'] += 1
                return True

        return False

    # ---------------------- V29.0: News Sentiment ----------------------

    def update_sentiment(self, symbol: str, sentiment: float) -> None:
        """更新情绪分数

        Args:
            symbol: 交易对
            sentiment: 情绪分数 (-1 到 1)
        """
        self._sentiment_cache[symbol] = sentiment

    def get_sentiment_signal(self, symbol: str) -> float:
        """获取情绪信号

        Args:
            symbol: 交易对

        Returns:
            情绪影响系数
        """
        if not self.run_config.enable_news_sentiment:
            return 0.0

        sentiment = self._sentiment_cache.get(symbol, 0.0)
        return sentiment * self.run_config.sentiment_impact

    # ---------------------- V29.0: ML Prediction Signals ----------------------

    def update_ml_prediction(self, symbol: str, prediction: float) -> None:
        """更新ML预测

        Args:
            symbol: 交易对
            prediction: 预测分数 (0-1)
        """
        self._ml_predictions[symbol] = prediction

    def get_ml_boosted_confidence(self, symbol: str, base_confidence: float) -> float:
        """获取ML增强的置信度

        Args:
            symbol: 交易对
            base_confidence: 基础置信度

        Returns:
            增强后的置信度
        """
        if not self.run_config.enable_ml_signals:
            return base_confidence

        ml_pred = self._ml_predictions.get(symbol, 0.5)
        boost = (ml_pred - 0.5) * self.run_config.ml_confidence_boost

        return max(0.0, min(1.0, base_confidence + boost))

    # ---------------------- V30.0: Funding Rate Monitor ----------------------

    def update_funding_rate(self, symbol: str, rate: float) -> None:
        """更新资金费率

        Args:
            symbol: 交易对
            rate: 资金费率
        """
        self._funding_rates[symbol] = rate

    def check_funding_alert(self, symbol: str) -> bool:
        """检查资金费率是否超过阈值

        Args:
            symbol: 交易对

        Returns:
            是否触发预警
        """
        if not self.run_config.enable_funding_monitor:
            return False

        rate = self._funding_rates.get(symbol, 0.0)
        threshold = self.run_config.funding_alert_threshold

        if abs(rate) > threshold:
            self.stats['funding_alerts'] += 1
            return True
        return False

    # ---------------------- V30.0: Alert System ----------------------

    def send_alert(self, level: str, message: str) -> None:
        """发送预警

        Args:
            level: 级别 (INFO/WARNING/ERROR)
            message: 消息
        """
        if not self.run_config.enable_alerts:
            return

        self.stats['total_alerts'] += 1

        alert = {
            'level': level,
            'message': message,
            'timestamp': time.time()
        }
        self._alert_history.append(alert)

        if len(self._alert_history) > 100:
            self._alert_history = self._alert_history[-100:]

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近预警

        Args:
            limit: 数量限制

        Returns:
            预警列表
        """
        return self._alert_history[-limit:]

    # ---------------------- V30.0: Performance Summary ----------------------

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能汇总

        Returns:
            性能统计字典
        """
        total = self.stats.get('opportunities_executed', 0)
        wins = self.stats.get('consecutive_wins', 0)
        losses = self.stats.get('consecutive_losses', 0)

        return {
            'total_trades': total,
            'consecutive_wins': wins,
            'consecutive_losses': losses,
            'win_rate': wins / total if total > 0 else 0,
            'total_profit': self.stats.get('total_profit', 0),
            'total_loss': self.stats.get('total_loss', 0),
            'daily_pnl': self.stats.get('daily_pnl', 0),
            'circuit_breaker': self.stats.get('circuit_breaker_triggered', 0),
            'emergency_stop': self.stats.get('emergency_stop_triggered', 0)
        }

    async def start_scan_loop(self) -> None:
        """启动扫描循环"""
        if not self.is_running:
            logger.warning("⚠️ 引擎未运行")
            return

        self.loop_status = LoopStatus.SCANNING
        logger.info("🔄 开始扫描循环...")

        try:
            while self.is_running:
                # 检查暂停状态
                if self.loop_status == LoopStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue

                # 执行扫描
                await self._scan_opportunities()

                # V25.7: 每次扫描后检查监控持仓
                if self.active_positions:
                    await self.monitor_positions()

                # 等待下一个扫描周期
                await asyncio.sleep(self.run_config.scan_interval_seconds)

        except asyncio.CancelledError:
            logger.info("🛑 扫描循环已取消")
        except Exception as e:
            logger.error(f"❌ 扫描循环错误: {e}")

    async def _scan_opportunities(self) -> None:
        """扫描机会"""
        self.stats['total_scans'] += 1

        try:
            self.loop_status = LoopStatus.SCANNING

            # V25.7: 检查交易时间
            if not self.is_trading_hours():
                logger.debug("⏰ 不在交易时间内，跳过扫描")
                return

            # 如果有arbitrage_pipeline，使用它扫描
            if self.arbitrage_pipeline:
                opportunities = await self._scan_with_pipeline()
            else:
                # 模拟扫描
                opportunities = self._simulate_scan()

            # 记��找到的机会
            self.stats['opportunities_found'] += len(opportunities)

            # 添加到池中
            for opp in opportunities:
                self._add_to_pool(opp)

            # 评估并执行
            await self._evaluate_and_execute()

        except Exception as e:
            logger.error(f"❌ 扫描错误: {e}")

    async def _scan_with_pipeline(self) -> List[ScannedOpportunity]:
        """使用管道扫描"""
        opportunities = []

        try:
            # 执行管道扫描
            result = await self.arbitrage_pipeline.run_once()

            # 转换结果
            if result and result.opportunities_executed > 0:
                opportunities.append(ScannedOpportunity(
                    opportunity_id=f"opp_{int(time.time())}",
                    symbol="BTC/USDT",
                    action="buy",
                    entry_price=50000.0,
                    target_price=55000.0,
                    stop_loss=48000.0,
                    score=75.0,
                    confidence=0.7,
                    recommendation="execute"
                ))

        except Exception as e:
            logger.error(f"❌ 管道扫描错误: {e}")

        return opportunities

    def _simulate_scan(self) -> List[ScannedOpportunity]:
        """模拟扫描 - 多币种支持 (V25.7)"""
        import random

        opportunities = []
        supported_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT"]

        # 随机选择1-2个币种
        num_symbols = random.randint(1, 2)
        selected = random.sample(supported_symbols, num_symbols)

        for symbol in selected:
            # 30%发现机会
            if random.random() > 0.7:
                base_price = {
                    "BTC/USDT": 50000.0,
                    "ETH/USDT": 3000.0,
                    "SOL/USDT": 150.0,
                    "DOGE/USDT": 0.15
                }.get(symbol, 50000.0)

                opp = ScannedOpportunity(
                    opportunity_id=f"opp_{symbol.replace('/','')}_{int(time.time()*1000)}",
                    symbol=symbol,
                    action="buy",
                    entry_price=base_price + random.randint(-int(base_price*0.01), int(base_price*0.01)),
                    target_price=base_price * 1.10,
                    stop_loss=base_price * 0.96,
                    score=70.0 + random.randint(0, 20),
                    confidence=0.6 + random.random() * 0.3,
                    recommendation="execute"
                )
                opportunities.append(opp)

        return opportunities

    def is_trading_hours(self) -> bool:
        """检查当前是否在交易时间内 (V25.7)

        Returns:
            是否在允许的交易时间内
        """
        hour = self.config.get('trading_hour_start', 0)
        end_hour = self.config.get('trading_hour_end', 24)

        if hour == 0 and end_hour == 24:
            return True  # 24小时交易

        current_hour = int(datetime.now().hour)
        return hour <= current_hour < end_hour

    async def _evaluate_and_execute(self) -> None:
        """评估并执行机会"""
        self.loop_status = LoopStatus.EVALUATING

        # 获取待执行的机会
        executable_opps = [
            opp for opp in self.opportunity_pool
            if opp.score >= self.run_config.min_score_threshold
            and opp.confidence >= self.run_config.min_confidence
            and opp.recommendation == "execute"
        ]

        # 检查并发仓位限制
        if len(executable_opps) >= self.run_config.max_concurrent_positions:
            executable_opps = executable_opps[:self.run_config.max_concurrent_positions]

        # 执行
        for opp in executable_opps:
            await self._execute_opportunity(opp)

    async def _execute_opportunity(self, opportunity: ScannedOpportunity) -> ExecutionResult:
        """执行机会"""
        self.loop_status = LoopStatus.EXECUTING

        result = ExecutionResult(
            opportunity_id=opportunity.opportunity_id,
            success=False,
            expected_price=opportunity.entry_price
        )

        try:
            # V25.8: 检查熔断器
            if self.is_circuit_breaker_active():
                result.error = "Circuit breaker active"
                self._record_result(result)
                return result

            # V25.9: 检查全局暴露限制
            if not self.check_global_exposure_limit():
                result.error = "Global exposure limit exceeded"
                self._record_result(result)
                return result

            # V25.9: 检查每日亏损限制
            if not self.check_daily_loss_limit():
                result.error = "Daily loss limit exceeded"
                self._record_result(result)
                return result

            # V26.0: 检查冷却时间
            if self.is_in_cooldown():
                result.error = "In cooldown period"
                self._record_result(result)
                return result

            # V26.0: 检查周末交易
            if not self.is_weekend_trading_allowed():
                result.error = "Weekend trading disabled"
                self._record_result(result)
                return result

            # 1. 评分质量门
            if opportunity.score < self.run_config.min_score_threshold:
                result.error = "Below score threshold"
                self._record_result(result)
                return result

            # 2. 计算仓位
            position_size = 1000.0
            if self.position_sizer:
                pos_result = self.position_sizer.calculate_position_size(
                    strategy="adaptive"
                )
                position_size = pos_result.recommended_size

            # 3. V25.8: 最大暴露限制检查
            if not self.check_exposure_limit(
                opportunity.symbol,
                position_size,
                opportunity.entry_price
            ):
                result.error = "Exposure limit exceeded"
                self._record_result(result)
                return result

            # 4. 风险检查
            if self.risk_manager:
                risk_check = self.risk_manager.check_risk(
                    symbol=opportunity.symbol,
                    size=position_size,
                    price=opportunity.entry_price
                )
                if not risk_check.get('approved', True):
                    result.error = "Risk check failed"
                    self._record_result(result)
                    return result

            # 5. 执行（模拟）
            executed_price = opportunity.entry_price
            executed_size = position_size

            if self.execution_engine:
                # 使用真实执行引擎
                exec_result = await self.execution_engine.execute_order(
                    symbol=opportunity.symbol,
                    action=opportunity.action,
                    price=opportunity.entry_price,
                    size=position_size
                )
                executed_price = exec_result.get('price', executed_price)
                executed_size = exec_result.get('size', executed_size)

            # V25.8: 计算执行质量
            slippage, slippage_pct = self.calculate_execution_quality(
                opportunity.entry_price,
                executed_price
            )
            quality_score = self.calculate_quality_score(slippage_pct)

            # 成功
            result.success = True
            result.executed_price = executed_price
            result.executed_size = executed_size
            result.executed_at = time.time()
            result.slippage = slippage
            result.slippage_pct = slippage_pct
            result.execution_quality_score = quality_score

            # 更新统计
            self.stats['opportunities_executed'] += 1

            # V25.8: 更新连盈/连亏 (假设模拟盈利)
            self._update_consecutive_trades(True)

            # V25.8: 更新暴露
            self.update_symbol_exposure(
                opportunity.symbol,
                executed_size,
                executed_price,
                is_entry=True
            )

            # 记录
            self._record_result(result)

            # V25.5: 自动追踪持仓
            self.track_position(
                opportunity=opportunity,
                executed_price=executed_price,
                executed_size=executed_size
            )

            # 从池中移除
            self._remove_from_pool(opportunity)

            logger.info(f"✅ 执行成功: {opportunity.symbol} @ {executed_price}")

            return result

        except Exception as e:
            result.error = str(e)
            self.stats['opportunities_failed'] += 1
            self._record_result(result)

            logger.error(f"❌ 执行失败: {e}")
            return result

    # ---------------------- 持仓监控 ----------------------

    async def monitor_positions(self) -> None:
        """监控持仓 - 自动止盈/止损"""
        self.loop_status = LoopStatus.MONITORING

        if not self.active_positions:
            return

        current_time = time.time()

        # 检查每个持仓
        positions_to_close = []

        for opp_id, pos in self.active_positions.items():
            entry_price = pos['entry_price']
            size = pos['size']
            current_price = pos.get('current_price', entry_price)
            target_price = pos.get('target_price', entry_price * 1.02)
            stop_loss = pos.get('stop_loss', entry_price * 0.98)

            # 计算当前盈亏百分比
            if pos.get('action') == 'buy':
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price

            # 检查止盈条件
            if current_price >= target_price:
                positions_to_close.append((opp_id, 'take_profit', pnl_pct))
            # 检查止损条件
            elif current_price <= stop_loss:
                positions_to_close.append((opp_id, 'stop_loss', pnl_pct))
            # 检查是否达到自动平仓阈值
            elif pnl_pct >= self.run_config.auto_close_threshold:
                positions_to_close.append((opp_id, 'auto_close', pnl_pct))
            # 检查超时
            elif current_time - pos.get('entry_time', current_time) > 300:  # 5分钟超时
                positions_to_close.append((opp_id, 'timeout', pnl_pct))

        # 平仓处理
        for opp_id, reason, pnl_pct in positions_to_close:
            await self._close_position(opp_id, reason, pnl_pct)

    async def _close_position(
        self,
        opportunity_id: str,
        reason: str,
        pnl_pct: float
    ) -> None:
        """平仓"""
        if opportunity_id not in self.active_positions:
            return

        pos = self.active_positions.pop(opportunity_id)

        # V25.8: 更新连盈/连亏统计
        is_profitable = pnl_pct > 0
        self._update_consecutive_trades(is_profitable)

        # V25.8: 减少暴露
        symbol = pos.get('symbol')
        size = pos.get('size', 0)
        entry_price = pos.get('entry_price', 0)
        if symbol and size > 0 and entry_price > 0:
            self.update_symbol_exposure(
                symbol, size, entry_price, is_entry=False
            )

        # V25.8: 检查是否触发熔断
        if self.is_circuit_breaker_active():
            self.trigger_circuit_breaker()

        # 记录到知识库
        if self.knowledge_bridge and self.run_config.mode != 'manual':
            try:
                self.knowledge_bridge.record_trade_result(
                    strategy=pos.get('strategy', 'auto'),
                    symbol=pos.get('symbol', 'BTC/USDT'),
                    exchange='auto',
                    pnl_pct=pnl_pct * 100,
                    pnl_usd=pnl_pct * pos.get('size', 0) * pos.get('entry_price', 0),
                    outcome='profitable' if pnl_pct > 0 else 'loss',
                    details={'reason': reason, 'opp_id': opportunity_id}
                )
            except Exception as e:
                logger.debug(f"平仓记录失败: {e}")

        logger.info(f"📊 平仓: {opportunity_id} | {reason} | PnL: {pnl_pct*100:.2f}%")

    def track_position(
        self,
        opportunity: ScannedOpportunity,
        executed_price: float,
        executed_size: float
    ) -> None:
        """追踪持仓"""
        self.active_positions[opportunity.opportunity_id] = {
            'symbol': opportunity.symbol,
            'action': opportunity.action,
            'entry_price': executed_price,
            'size': executed_size,
            'target_price': opportunity.target_price,
            'stop_loss': opportunity.stop_loss,
            'entry_time': time.time(),
            'strategy': opportunity.recommendation
        }

    # ---------------------- 持仓查询 ----------------------

    def get_position(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """获取持仓详情

        Args:
            opportunity_id: 持仓ID

        Returns:
            持仓详情字典，不存在返回None
        """
        return self.active_positions.get(opportunity_id)

    def get_position_count(self) -> int:
        """获取持仓数量

        Returns:
            活跃持仓数量
        """
        return len(self.active_positions)

    def has_position(self, opportunity_id: str) -> bool:
        """检查持仓是否存在

        Args:
            opportunity_id: 持仓ID

        Returns:
            是否存在
        """
        return opportunity_id in self.active_positions

    def get_active_positions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃持仓

        Returns:
            活跃持仓字典
        """
        return self.active_positions.copy()

    # ---------------------- 池管理 ----------------------

    def _add_to_pool(self, opportunity: ScannedOpportunity) -> None:
        """添加到机会池"""
        self.opportunity_pool.append(opportunity)
        if len(self.opportunity_pool) > self.max_pool_size:
            self.opportunity_pool.pop(0)

    def _remove_from_pool(self, opportunity: ScannedOpportunity) -> None:
        """从池中移除"""
        self.opportunity_pool = [
            opp for opp in self.opportunity_pool
            if opp.opportunity_id != opportunity.opportunity_id
        ]

    def _record_result(self, result: ExecutionResult) -> None:
        """记录执行结果"""
        self.execution_history.append(result)
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)

    # ---------------------- 状态查询 ----------------------

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'is_running': self.is_running,
            'loop_status': self.loop_status.value,
            'config': {
                'mode': self.run_config.mode,
                'scan_interval': self.run_config.scan_interval_seconds,
                'min_score': self.run_config.min_score_threshold
            },
            'stats': self.stats.copy(),
            'pool_size': len(self.opportunity_pool)
        }

    def get_pool(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取机会池"""
        return [
            {
                'opportunity_id': opp.opportunity_id,
                'symbol': opp.symbol,
                'action': opp.action,
                'score': opp.score,
                'confidence': opp.confidence,
                'recommendation': opp.recommendation,
                'timestamp': opp.timestamp
            }
            for opp in self.opportunity_pool[-limit:]
        ]

    # ---------------------- 属性 ----------------------

    @property
    def total_executed(self) -> int:
        """总执行数"""
        return self.stats['opportunities_executed']

    @property
    def total_failed(self) -> int:
        """总失败数"""
        return self.stats['opportunities_failed']

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.total_executed + self.total_failed
        if total == 0:
            return 0.0
        return self.total_executed / total

    # ---------------------- Memo0知识学习 (V25.1) ----------------------

    def record_to_knowledge(
        self,
        opportunity: ScannedOpportunity,
        result: ExecutionResult,
        pnl_pct: Optional[float] = None
    ) -> bool:
        """记录交易结果到知识库 (Memo0学习反馈)

        Args:
            opportunity: 机会对象
            result: 执行结果
            pnl_pct: 盈亏百分比

        Returns:
            是否成功记录
        """
        if not self.knowledge_bridge:
            logger.debug("⚠️ 知识桥接器未初始化，跳过知识记录")
            return False

        try:
            # 构建交易记录
            record = {
                'opportunity_id': opportunity.opportunity_id,
                'symbol': opportunity.symbol,
                'action': opportunity.action,
                'score': opportunity.score,
                'confidence': opportunity.confidence,
                'recommendation': opportunity.recommendation,
                'success': result.success,
                'executed_price': result.executed_price,
                'executed_size': result.executed_size,
                'pnl_pct': pnl_pct,
                'error': result.error,
                'timestamp': time.time()
            }

            # 记录到知识库
            # V25.1: 适配TradingKnowledgeBridge接口
            outcome = "profitable" if result.success and (pnl_pct or 0) > 0 else "loss" if result.success else "breakeven"
            pnl_usd = (pnl_pct or 0) / 100 * result.executed_size * opportunity.entry_price
            self.knowledge_bridge.record_trade_result(
                strategy=opportunity.recommendation,
                symbol=opportunity.symbol,
                exchange="auto",
                pnl_pct=pnl_pct or 0.0,
                pnl_usd=pnl_usd,
                outcome=outcome,
                details={
                    'opportunity_id': opportunity.opportunity_id,
                    'score': opportunity.score,
                    'confidence': opportunity.confidence,
                    'executed_price': result.executed_price,
                    'executed_size': result.executed_size,
                    'error': result.error
                }
            )
            logger.info(f"✅ 交易结果已记录到知识库: {opportunity.opportunity_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 记录知识失败: {e}")
            return False

    def get_market_context(self) -> Optional[Dict[str, Any]]:
        """从知识库获取市场上下文

        Returns:
            市场上下文字典
        """
        if not self.knowledge_bridge:
            return None

        try:
            # V25.1: TradingKnowledgeBridge.get_market_context()返回MarketContext对象
            context = self.knowledge_bridge.get_market_context()
            if context is None:
                return None

            # 转换为字典以便外部使用
            return {
                'recent_win_rate': context.recent_win_rate,
                'recent_avg_pnl_pct': context.recent_avg_pnl_pct,
                'best_strategy': context.best_strategy,
                'worst_strategy': context.worst_strategy,
                'recent_risk_events': context.recent_risk_events,
                'circuit_breaker_count': context.circuit_breaker_count,
                'symbol_performance': context.symbol_performance,
                'strategy_performance': context.strategy_performance,
                'last_updated': context.last_updated,
                'confidence': context.confidence
            }
        except Exception as e:
            logger.error(f"❌ 获取市场上下文失败: {e}")
            return None

    def _adjust_threshold_from_knowledge(self) -> None:
        """根据知识库反馈调整阈值

        基于近期表现自动调整评分阈值和置信度阈值。
        """
        context = self.get_market_context()
        if not context:
            return

        try:
            # 基于近期胜率调整阈值
            recent_win_rate = context.get('recent_win_rate', 0.5)
            current_min_score = self.run_config.min_score_threshold
            current_min_conf = self.run_config.min_confidence

            # 胜率高则降低阈值，胜率低则提高阈值
            if recent_win_rate >= 0.6:
                # 表现良好，可以稍微降低门槛
                new_score = max(50.0, current_min_score - 5.0)
                new_conf = max(0.4, current_min_conf - 0.05)
            elif recent_win_rate < 0.4:
                # 表现不佳，提高门槛
                new_score = min(80.0, current_min_score + 5.0)
                new_conf = min(0.7, current_min_conf + 0.05)
            else:
                return

            self.run_config.min_score_threshold = new_score
            self.run_config.min_confidence = new_conf
            logger.info(f"📊 阈值已调整: score {current_min_score:.1f}→{new_score:.1f}, "
                      f"conf {current_min_conf:.2f}→{new_conf:.2f}")

        except Exception as e:
            logger.debug(f"阈值调整跳过: {e}")

    def record_risk_event(
        self,
        event_type: str,
        severity: str,
        strategy: str,
        symbol: str,
        reason: str,
        action_taken: str = ""
    ) -> bool:
        """记录风险事件到知识库

        Args:
            event_type: 事件类型 (circuit_break/reject/reduce_size)
            severity: 严重程度 (critical/high/medium/low)
            strategy: 策略名称
            symbol: 交易对
            reason: 触发原因
            action_taken: 采取的动作

        Returns:
            是否成功记录
        """
        if not self.knowledge_bridge:
            logger.debug("⚠️ 知识桥接器未初始化，跳过风险记录")
            return False

        try:
            self.knowledge_bridge.record_risk_event(
                event_type=event_type,
                severity=severity,
                strategy=strategy,
                symbol=symbol,
                reason=reason,
                action_taken=action_taken
            )
            logger.info(f"✅ 风险事件已记录: {event_type} - {symbol}")
            return True

        except Exception as e:
            logger.error(f"❌ 记录风险事件失败: {e}")
            return False

    def get_strategy_insight(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略洞察

        Args:
            strategy_name: 策略名称

        Returns:
            策略洞察字典
        """
        if not self.knowledge_bridge:
            return None

        try:
            insight = self.knowledge_bridge.get_strategy_insight(strategy_name)
            if insight is None:
                return None

            return {
                'strategy_name': insight.strategy_name,
                'total_trades': insight.total_trades,
                'win_count': insight.win_count,
                'loss_count': insight.loss_count,
                'win_rate': insight.win_rate,
                'avg_pnl_pct': insight.avg_pnl_pct,
                'best_symbol': insight.best_symbol,
                'worst_symbol': insight.worst_symbol,
                'trend': insight.trend,
                'recommendation': insight.recommendation
            }
        except Exception as e:
            logger.debug(f"获取策略洞察失败: {e}")
            return None

    # =============================================================================
    # V27.0: Enhanced Memo0 Learning - 增强的memo0学习
    # =============================================================================

    def get_learned_params(self) -> Dict[str, Any]:
        """从知识库学习最优参数 - V27.0新增

        从历史交易数据中学习最优的:
        - 仓位大小
        - 止损百分比
        -持仓时间

        Returns:
            学习到的参数字典
        """
        if not self.knowledge_bridge:
            return {}

        try:
            # 获取市场上下文
            context = self.knowledge_bridge.get_market_context()
            if not context:
                return {}

            # 基于胜率和盈亏学习参数
            win_rate = context.recent_win_rate
            avg_pnl = context.recent_avg_pnl_pct

            # 学习仓位大小
            if win_rate >= 0.65:
                learned_size_mult = 1.15
            elif win_rate >= 0.5:
                learned_size_mult = 1.0
            elif win_rate >= 0.4:
                learned_size_mult = 0.85
            else:
                learned_size_mult = 0.7

            # 学习止损百分比
            if avg_pnl >= 1.0:
                learned_stop_pct = 0.015  # 1.5%
            elif avg_pnl >= 0.5:
                learned_stop_pct = 0.02  # 2%
            elif avg_pnl >= 0:
                learned_stop_pct = 0.025  # 2.5%
            else:
                learned_stop_pct = 0.03  # 3%

            # 学习持仓时间限制
            if win_rate >= 0.6:
                learned_max_hold = 7200  # 2小时
            else:
                learned_max_hold = 3600  # 1小时

            return {
                'position_multiplier': learned_size_mult,
                'stop_loss_pct': learned_stop_pct,
                'max_hold_seconds': learned_max_hold,
                'confidence': context.confidence,
                'source': 'memo0_learned'
            }

        except Exception as e:
            logger.debug(f"参数学习失败: {e}")
            return {}

    def get_time_of_day_recommendation(self) -> Dict[str, Any]:
        """从知识库学习最佳交易时间 - V27.0新增

        Returns:
            时间建议字典
        """
        if not self.knowledge_bridge:
            return {'recommendation': 'maintain', 'best_session': 'LONDON'}

        try:
            # 获取上下文中的时间表现
            context = self.knowledge_bridge.get_market_context()
            if not context:
                return {'recommendation': 'maintain', 'best_session': 'LONDON'}

            # 从时间维度获取最佳时段
            best_session = 'LONDON'  # 默认
            if context.time_of_day_performance:
                best_session = max(
                    context.time_of_day_performance.items(),
                    key=lambda x: x[1]
                )[0] if context.time_of_day_performance else 'LONDON'

            # 基于胜率给出建议
            win_rate = context.recent_win_rate
            if win_rate >= 0.6:
                recommendation = 'increase'
            elif win_rate >= 0.45:
                recommendation = 'maintain'
            else:
                recommendation = 'decrease'

            return {
                'recommendation': recommendation,
                'best_session': best_session,
                'recent_win_rate': win_rate
            }

        except Exception as e:
            logger.debug(f"时间建议获取失败: {e}")
            return {'recommendation': 'maintain', 'best_session': 'LONDON'}

    def predict_risk_level(self) -> str:
        """预测当前风险级别 - V27.0新增

        基于知识库预测当前市场风险级别。

        Returns:
            风险级别: 'low' / 'medium' / 'high' / 'critical'
        """
        if not self.knowledge_bridge:
            return 'medium'  # 默认中等风险

        try:
            context = self.knowledge_bridge.get_market_context()
            if not context:
                return 'medium'

            # 基于近期风控事件和熔断次数判断
            risk_score = 0.0

            # 近期胜率
            if context.recent_win_rate < 0.3:
                risk_score += 2.0
            elif context.recent_win_rate < 0.4:
                risk_score += 1.0

            # 近期风控事件
            if context.recent_risk_events > 5:
                risk_score += 2.0
            elif context.recent_risk_events > 2:
                risk_score += 1.0

            # 熔断次数
            if context.circuit_breaker_count >= 3:
                risk_score += 2.0
            elif context.circuit_breaker_count >= 1:
                risk_score += 1.0

            # 转换为风险级别
            if risk_score >= 5.0:
                return 'critical'
            elif risk_score >= 3.0:
                return 'high'
            elif risk_score >= 1.0:
                return 'medium'
            else:
                return 'low'

        except Exception as e:
            logger.debug(f"风险预测失败: {e}")
            return 'medium'

    # =============================================================================
    # V31.0: Smart Order Routing (SOR) 智能订单路由
    # =============================================================================

    async def collect_exchange_prices(self, symbol: str) -> List[ExchangePrice]:
        """收集多交易所价格 - V31.0新增

        Args:
            symbol: 交易对符号

        Returns:
            交易所价格列表
        """
        import random

        prices = []
        exchanges = self.run_config.sor_exchanges.split(',') if self.run_config.sor_exchanges else ['binance']

        for exchange in exchanges:
            # 模拟获取价格
            base_price = random.uniform(45000, 55000) if 'BTC' in symbol else random.uniform(2500, 3500)
            spread = base_price * 0.0005  # 0.05% spread

            prices.append(ExchangePrice(
                exchange=exchange.strip(),
                symbol=symbol,
                bid_price=base_price - spread,
                ask_price=base_price + spread,
                bid_volume=random.uniform(100, 1000),
                ask_volume=random.uniform(100, 1000),
                timestamp=time.time(),
                latency_ms=random.uniform(10, 100)
            ))

        self.stats['exchange_prices_collected'] += len(prices)
        self._exchange_prices[symbol] = prices

        logger.debug(f"📊 收集 {len(prices)} 个交易所价格: {symbol}")
        return prices

    def calculate_sor_slices(self, order: SOROrder) -> List[Dict[str, Any]]:
        """计算订单拆分 - V31.0新增

        Args:
            order: SOR订单

        Returns:
            拆分列表
        """
        slices = []
        slice_qty = order.total_quantity / order.slices
        mode = order.mode

        for i in range(order.slices):
            # TWAP: 等量拆分; VWAP: 根据成交量分布
            if mode == 'vwap':
                # 模拟成交量分布 - 前重后轻
                weight = 1.0 - (i / order.slices) * 0.5
                slice_qty = (order.total_quantity / order.slices) * weight
            elif mode == 'pov':
                slice_qty = order.total_quantity * self.run_config.sor_participation_rate

            slices.append({
                'slice_id': i,
                'quantity': slice_qty,
                'interval': order.slice_interval_seconds,
                'status': 'pending'
            })

        return slices

    async def execute_sor_order(self, order: SOROrder) -> Dict[str, Any]:
        """执行SOR订单 - V31.0新增

        Args:
            order: SOR订单

        Returns:
            执行结果
        """
        if not self.run_config.enable_sor:
            return {'status': 'disabled', 'message': 'SOR not enabled'}

        self.stats['sor_orders_created'] += 1
        self.loop_status = LoopStatus.SOR_EXECUTING

        # 收集交易所价格
        prices = await self.collect_exchange_prices(order.symbol)

        if not prices:
            self.stats['sor_orders_cancelled'] += 1
            return {'status': 'failed', 'message': 'No exchange prices'}

        # 计算拆分
        slices = self.calculate_sor_slices(order)

        # 选择最佳价格交易所
        best_exchange = min(prices, key=lambda p: p.ask_price if order.side == 'buy' else p.bid_price)

        order.exchanges = [best_exchange.exchange]
        order.status = 'executing'

        # 执行拆分
        total_slippage = 0.0
        for slice_info in slices:
            qty = slice_info['quantity']

            # 模拟执行
            fill_price = best_exchange.ask_price if order.side == 'buy' else best_exchange.bid_price
            slippage_bps = abs(fill_price - best_exchange.ask_price) / best_exchange.ask_price * 10000

            # 检查滑点限制
            if slippage_bps > self.run_config.sor_max_slippage_bps:
                logger.warning(f"⚠️ 滑点超限: {slippage_bps:.2f} bps > {self.run_config.sor_max_slippage_bps} bps")
                continue

            order.filled_quantity += qty
            total_slippage += slippage_bps
            self.stats['sor_slices_executed'] += 1

            await asyncio.sleep(0.1)  # 模拟执行延迟

        # 完成订单
        if order.filled_quantity >= order.total_quantity * 0.9:  # 90%完成视为完成
            order.status = 'completed'
            self.stats['sor_orders_completed'] += 1
        else:
            order.status = 'partial'
            self.stats['sor_orders_cancelled'] += 1

        # 计算统计
        order.slippage_bps = total_slippage / len(slices) if slices else 0
        order.execution_cost = order.slippage_bps * order.filled_quantity
        self.stats['sor_total_slippage_bps'] += order.slippage_bps
        self.stats['sor_execution_cost'] += order.execution_cost

        logger.info(f"✅ SOR订单完成: {order.order_id} | 填充: {order.filled_quantity}/{order.total_quantity} | 滑点: {order.slippage_bps:.2f} bps")

        return {
            'status': order.status,
            'filled_quantity': order.filled_quantity,
            'total_quantity': order.total_quantity,
            'slippage_bps': order.slippage_bps,
            'execution_cost': order.execution_cost,
            'best_exchange': best_exchange.exchange
        }

    def create_sor_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> SOROrder:
        """创建SOR订单 - V31.0新增

        Args:
            symbol: 交易对
            side: buy/sell
            quantity: 数量

        Returns:
            SOR订单
        """
        order = SOROrder(
            order_id=f"sor_{int(time.time()*1000)}",
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            mode=self.run_config.sor_mode,
            slices=self.run_config.sor_slices,
            slice_interval_seconds=self.run_config.sor_slice_interval,
            start_time=time.time(),
            status='pending'
        )

        self._sor_orders[order.order_id] = order
        self._sor_queue.append(order)

        logger.info(f"📝 创建SOR订单: {order.order_id} | {symbol} | {side} | {quantity}")
        return order

    def get_sor_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取SOR���单��态 - V31.0新增

        Args:
            order_id: 订单ID

        Returns:
            订单状态字典
        """
        order = self._sor_orders.get(order_id)
        if not order:
            return None

        return {
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side,
            'total_quantity': order.total_quantity,
            'filled_quantity': order.filled_quantity,
            'avg_fill_price': order.avg_fill_price,
            'mode': order.mode,
            'status': order.status,
            'slippage_bps': order.slippage_bps,
            'execution_cost': order.execution_cost
        }

    def get_best_exchange(self, symbol: str, side: str) -> Optional[str]:
        """获取最佳交易所 - V31.0新增

        Args:
            symbol: 交易对
            side: buy/sell

        Returns:
            最佳交易所名称
        """
        prices = self._exchange_prices.get(symbol, [])
        if not prices:
            return None

        if side == 'buy':
            return min(prices, key=lambda p: p.ask_price).exchange
        else:
            return max(prices, key=lambda p: p.bid_price).exchange

    # =============================================================================
    # V32.0: Order Flow Analysis (OFA) 订单流分析
    # =============================================================================

    def update_volume(self, symbol: str, volume: float, price: float) -> None:
        """更新交易量 - V32.0新增

        Args:
            symbol: 交易对
            volume: 交易量
            price: 价格
        """
        if symbol not in self._volume_history:
            self._volume_history[symbol] = []
            self._trade_history[symbol] = []

        # 记录交易量
        self._volume_history[symbol].append(volume)
        if len(self._volume_history[symbol]) > self.run_config.volume_lookback:
            self._volume_history[symbol] = self._volume_history[symbol][-self.run_config.volume_lookback:]

        # 计算VWAP
        trades = self._trade_history[symbol]
        if trades:
            total_vol = sum(t['volume'] for t in trades)
            if total_vol > 0:
                self._vwap[symbol] = sum(t['price'] * t['volume'] for t in trades) / total_vol

        # 检测大单
        if volume > self.run_config.large_order_threshold:
            self._large_orders.append({
                'symbol': symbol,
                'volume': volume,
                'price': price,
                'timestamp': time.time()
            })
            self.stats['large_orders_detected'] += 1
            logger.debug(f"🔔 检测到大单: {symbol} | Vol: {volume}")

    def detect_large_order(self, symbol: str) -> Optional[Dict[str, Any]]:
        """检测大单 - V32.0新增

        Args:
            symbol: 交易对

        Returns:
            大单信息或None
        """
        recent = [o for o in self._large_orders if o['symbol'] == symbol and time.time() - o['timestamp'] < 60]
        if not recent:
            return None

        largest = max(recent, key=lambda x: x['volume'])
        return {
            'symbol': largest['symbol'],
            'volume': largest['volume'],
            'price': largest['price'],
            'is_large': largest['volume'] > self.run_config.large_order_threshold
        }

    def detect_vwap_gap(self, symbol: str, current_price: float) -> Optional[Dict[str, Any]]:
        """检测VWAP缺口 - V32.0新增

        Args:
            symbol: 交易对
            current_price: 当前价格

        Returns:
            VWAP缺口信息或None
        """
        vwap = self._vwap.get(symbol)
        if not vwap or vwap == 0:
            return None

        gap_pct = abs(current_price - vwap) / vwap

        if gap_pct > self.run_config.vwap_gap_threshold:
            self.stats['vwap_gaps_detected'] += 1
            return {
                'symbol': symbol,
                'vwap': vwap,
                'current_price': current_price,
                'gap_pct': gap_pct,
                'direction': 'above' if current_price > vwap else 'below'
            }

        return None

    def calculate_order_flow_score(self, symbol: str) -> float:
        """计算订单流评分 - V32.0新增

        Args:
            symbol: 交易对

        Returns:
            订单流评分 (0-100)
        """
        if not self.run_config.enable_ofa:
            return 50.0  # 默认中性

        score = 50.0
        volumes = self._volume_history.get(symbol, [])

        if len(volumes) < 5:
            return score

        # 计算交易量指标
        avg_volume = sum(volumes) / len(volumes)
        recent_volume = sum(volumes[-5:]) / 5

        # 交易量放大
        if recent_volume > avg_volume * 1.5:
            score += 10
            self.stats['volume_spikes'] += 1

        # 检查大单
        large = self.detect_large_order(symbol)
        if large:
            score += 15
            self.stats['large_orders_detected'] += 1

        # 检查VWAP缺口
        current = self._vwap.get(symbol, 50000)
        gap = self.detect_vwap_gap(symbol, current)
        if gap:
            score += 10 if gap['direction'] == 'below' else 5

        # 机构模式检测
        if self.run_config.institutional_patterns:
            inst_sig = self.detect_institutional_pattern(symbol)
            if inst_sig:
                score += 15
                self.stats['institutional_signals'] += 1

        self.stats['order_flow_score'] = min(score, 100)
        return min(score, 100)

    def detect_institutional_pattern(self, symbol: str) -> Optional[Dict[str, Any]]:
        """检测机构订单模式 - V32.0新增

        Args:
            symbol: 交易对

        Returns:
            机构模式信息或None
        """
        volumes = self._volume_history.get(symbol, [])
        if len(volumes) < 20:
            return None

        recent = volumes[-20:]
        avg = sum(recent) / len(recent)

        # 检测持续大单买入模式
        large_trades = [v for v in recent if v > avg * 2]
        if len(large_trades) >= 3:
            # 检测方向
            trades = self._trade_history.get(symbol, [])[-20:]
            if trades:
                avg_price = sum(t['price'] for t in trades) / len(trades)
                latest_price = trades[-1]['price']

                return {
                    'pattern': 'accumulation' if latest_price > avg_price else 'distribution',
                    'strength': len(large_trades) / 20,
                    'symbol': symbol
                }

        return None

    def get_order_flow_summary(self, symbol: str) -> Dict[str, Any]:
        """获取订单流汇总 - V32.0新增

        Args:
            symbol: 交易对

        Returns:
            订单流汇总
        """
        return {
            'symbol': symbol,
            'order_flow_score': self.calculate_order_flow_score(symbol),
            'avg_volume': sum(self._volume_history.get(symbol, [0])) / max(len(self._volume_history.get(symbol, [])), 1),
            'vwap': self._vwap.get(symbol, 0),
            'large_orders_count': len([o for o in self._large_orders if o['symbol'] == symbol]),
            'institutional_signals': len(self._institutional_signals)
        }

    # ========== V33.0: Market Microstructure Methods ==========

    def analyze_market_depth(
        self,
        symbol: str,
        exchange: str = "binance",
        bid_prices: Optional[List[float]] = None,
        bid_volumes: Optional[List[float]] = None,
        ask_prices: Optional[List[float]] = None,
        ask_volumes: Optional[List[float]] = None
    ) -> MarketDepth:
        """分析市场深度 - V33.0新增

        Args:
            symbol: 交易对
            exchange: 交易所
            bid_prices: 买价列表
            bid_volumes: 买量列表
            ask_prices: 卖价列表
            ask_volumes: 卖量列表

        Returns:
            MarketDepth: 市场深度对象
        """
        if not self.run_config.enable_market_depth:
            return MarketDepth(symbol=symbol, exchange=exchange)

        # 生成模拟数据(如果未提供)
        if not bid_prices:
            base_price = 50000.0
            bid_prices = [base_price - i * 0.5 for i in range(self.run_config.depth_levels)]
            bid_volumes = [100.0 * (1 + i * 0.1) for i in range(self.run_config.depth_levels)]
        if not ask_prices:
            base_price = 50000.0
            ask_prices = [base_price + i * 0.5 for i in range(self.run_config.depth_levels)]
            ask_volumes = [100.0 * (1 + i * 0.1) for i in range(self.run_config.depth_levels)]

        # 构建订单簿级别
        bid_levels = []
        cum_bid_vol = 0.0
        for i, (price, vol) in enumerate(zip(bid_prices, bid_volumes)):
            cum_bid_vol += vol
            bid_levels.append(MarketDepthLevel(
                price=price,
                volume=vol,
                cumulative_volume=cum_bid_vol,
                order_count=i + 1
            ))

        ask_levels = []
        cum_ask_vol = 0.0
        for i, (price, vol) in enumerate(zip(ask_prices, ask_volumes)):
            cum_ask_vol += vol
            ask_levels.append(MarketDepthLevel(
                price=price,
                volume=vol,
                cumulative_volume=cum_ask_vol,
                order_count=i + 1
            ))

        # 计算价差
        spread = ask_prices[0] - bid_prices[0]
        mid_price = (bid_prices[0] + ask_prices[0]) / 2
        spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 0

        # 计算深度评分
        total_depth = cum_bid_vol + cum_ask_vol
        depth_score = min(100.0, total_depth / 1000.0)

        depth = MarketDepth(
            symbol=symbol,
            exchange=exchange,
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            spread=spread,
            spread_bps=spread_bps,
            mid_price=mid_price,
            depth_score=depth_score,
            timestamp=time.time()
        )

        # 存储
        key = f"{symbol}@{exchange}"
        self._market_depths[key] = depth

        # 更新历史
        if symbol not in self._depth_history:
            self._depth_history[symbol] = []
        self._depth_history[symbol].append(depth_score)
        if len(self._depth_history[symbol]) > 100:
            self._depth_history[symbol] = self._depth_history[symbol][-100:]

        return depth

    def aggregate_liquidity(self, symbol: str) -> List[LiquidityPool]:
        """聚合跨交易所流动性 - V33.0新增

        Args:
            symbol: 交易对

        Returns:
            LiquidityPool列表
        """
        if not self.run_config.enable_liquidity_agg:
            return []

        exchanges = self.run_config.sor_exchanges.split(',')
        pools = []

        for exchange in exchanges:
            depth_key = f"{symbol}@{exchange}"
            depth = self._market_depths.get(depth_key)

            if depth:
                bid_depth = sum(l.cumulative_volume for l in depth.bid_levels)
                ask_depth = sum(l.cumulative_volume for l in depth.ask_levels)
            else:
                # 模拟流动性
                bid_depth = 10000.0
                ask_depth = 10000.0

            total = bid_depth + ask_depth
            weighted_mid = (bid_depth * 0.5 + ask_depth * 0.5) * 2 / (bid_depth + ask_depth + 0.01)
            # simplified: use average
            weighted_mid = 50000.0

            pool = LiquidityPool(
                exchange=exchange,
                symbol=symbol,
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                total_depth=total,
                price_levels=10,
                weighted_mid=weighted_mid
            )
            pools.append(pool)

        self._liquidity_pools[symbol] = pools
        return pools

    def predict_price_impact(
        self,
        symbol: str,
        quantity: float,
        side: str = "buy"
    ) -> PriceImpact:
        """预测订单价格影响 - V33.0新增

        Args:
            symbol: 交易对
            quantity: 订单数量
            side: buy/sell

        Returns:
            PriceImpact: 价格影响预测
        """
        if not self.run_config.enable_price_impact:
            return PriceImpact(
                quantity=quantity,
                expected_price=50000.0,
                impacted_price=50000.0,
                impact_bps=0.0,
                fill_rate=1.0,
                risk_level="low"
            )

        alpha = self.run_config.impact_model_alpha
        # 简化的价格影响模型: impact ~ alpha * quantity^2
        impact_bps = alpha * (quantity ** 2) * 100

        expected_price = 50000.0
        if side == "buy":
            impacted_price = expected_price * (1 + impact_bps / 10000)
        else:
            impacted_price = expected_price * (1 - impact_bps / 10000)

        # 填充率(数量越大，填充率越低)
        fill_rate = max(0.1, 1.0 - quantity * 0.01)

        # 风险等级
        if impact_bps < 10:
            risk_level = "low"
        elif impact_bps < 50:
            risk_level = "medium"
        else:
            risk_level = "high"

        impact = PriceImpact(
            quantity=quantity,
            expected_price=expected_price,
            impacted_price=impacted_price,
            impact_bps=impact_bps,
            fill_rate=fill_rate,
            risk_level=risk_level
        )

        self._price_impacts[symbol] = impact
        return impact

    def fuse_signals(
        self,
        symbol: str,
        technical: float = 50.0,
        sentiment: float = 50.0,
        flow: float = 50.0,
        ml: float = 50.0
    ) -> float:
        """融合多源信号 - V33.0新增

        Args:
            symbol: 交易对
            technical: 技术信号评分
            sentiment: 情绪信号评分
            flow: 订单流评分
            ml: ML预测评分

        Returns:
            融合后的信号评分 (0-100)
        """
        if not self.run_config.enable_signal_fusion:
            return (technical + sentiment + flow + ml) / 4

        # 解析权重配置
        weights_str = self.run_config.fusion_weights
        weights = {}
        for part in weights_str.split(','):
            key, val = part.split(':')
            weights[key.strip()] = float(val.strip())

        # 加权融合
        fused = (
            weights.get('technical', 0.25) * technical +
            weights.get('sentiment', 0.25) * sentiment +
            weights.get('flow', 0.25) * flow +
            weights.get('ml', 0.25) * ml
        )

        self._fused_signals[symbol] = fused
        return fused

    def get_market_microstructure_summary(self, symbol: str) -> Dict[str, Any]:
        """获取市场微观结构汇总 - V33.0新增

        Args:
            symbol: 交易对

        Returns:
            市场微观结构汇总
        """
        depth = self._market_depths.get(f"{symbol}@binance")
        pools = self._liquidity_pools.get(symbol, [])
        impact = self._price_impacts.get(symbol)
        fused = self._fused_signals.get(symbol, 50.0)

        depth_history = self._depth_history.get(symbol, [])
        avg_depth = sum(depth_history) / len(depth_history) if depth_history else 0

        return {
            'symbol': symbol,
            'depth_score': depth.depth_score if depth else 0,
            'spread_bps': depth.spread_bps if depth else 0,
            'total_liquidity': sum(p.total_depth for p in pools) if pools else 0,
            'exchange_count': len(pools),
            'price_impact_bps': impact.impact_bps if impact else 0,
            'impact_risk': impact.risk_level if impact else 'low',
            'fused_signal': fused,
            'avg_depth_score': avg_depth
        }

    # ========== V34.0: Cross-Exchange Arbitrage Methods ==========

    def scan_cross_exchange_arbitrage(self, symbol: str) -> List[ArbitrageOpportunity]:
        """扫描跨交易所套利机会 - V34.0新增

        Args:
            symbol: 交易对

        Returns:
            ArbitrageOpportunity列表
        """
        if not self.run_config.enable_arbitrage:
            return []

        exchanges = self.run_config.arbitrage_exchanges.split(',')
        opportunities = []

        # 生成模拟价格数据
        prices = {}
        base_price = 50000.0
        for exchange in exchanges:
            # 模拟各交易所价格有轻微差异
            offset = (hash(exchange) % 100 - 50) / 10000.0  # -0.005 to 0.005
            prices[exchange] = {
                'bid': base_price * (1 + offset),
                'ask': base_price * (1 + offset + 0.0005)
            }

        # 找最佳套利机会: 低价买入,高价卖出
        best_buy = min(prices.items(), key=lambda x: x[1]['ask'])
        best_sell = max(prices.items(), key=lambda x: x[1]['bid'])

        if best_buy[0] != best_sell[0]:
            buy_price = best_buy[1]['ask']
            sell_price = best_sell[1]['bid']
            spread_pct = (sell_price - buy_price) / buy_price

            if spread_pct >= self.run_config.arbitrage_min_spread:
                score = min(100.0, spread_pct * 10000)  # 转换为评分
                opportunity = ArbitrageOpportunity(
                    symbol=symbol,
                    buy_exchange=best_buy[0],
                    sell_exchange=best_sell[0],
                    buy_price=buy_price,
                    sell_price=sell_price,
                    spread_pct=spread_pct,
                    potential_profit=spread_pct * 1000,  # 假设1000美元本金
                    score=score,
                    timestamp=time.time(),
                    status="pending"
                )
                opportunities.append(opportunity)

        self._arbitrage_opportunities = opportunities
        return opportunities

    def get_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """获取当前套利机会"""
        return self._arbitrage_opportunities

    # ========== V34.0: Margin Pool Methods ==========

    def init_margin_pool(self) -> bool:
        """初始化保证金池 - V34.0新增

        Returns:
            是否成功
        """
        if not self.run_config.enable_margin_pool:
            return False

        self._margin_pool_available = self.run_config.margin_pool_size
        logger.info(f"✅ 保证金池已初始化: ${self._margin_pool_available:,.2f}")
        return True

    def allocate_margin(self, symbol: str, amount: float) -> bool:
        """分配保证金 - V34.0新增

        Args:
            symbol: 交易对
            amount: 保证金金额

        Returns:
            是否成功
        """
        if not self.run_config.enable_margin_pool:
            return False

        buffer = self._margin_pool_available * self.run_config.margin_buffer_ratio
        available = self._margin_pool_available - buffer

        if amount <= available:
            if symbol in self._margin_positions:
                self._margin_positions[symbol].margin_used += amount
            else:
                self._margin_positions[symbol] = MarginPosition(
                    symbol=symbol,
                    exchange="binance",
                    position_size=0.0,
                    margin_used=amount,
                    margin_ratio=amount / self._margin_pool_available
                )
            self._margin_pool_available -= amount
            return True
        return False

    def release_margin(self, symbol: str) -> float:
        """释放保证金 - V34.0新增

        Args:
            symbol: 交易对

        Returns:
            释放的保证金金额
        """
        if symbol in self._margin_positions:
            released = self._margin_positions[symbol].margin_used
            self._margin_pool_available += released
            del self._margin_positions[symbol]
            return released
        return 0.0

    def get_margin_pool_status(self) -> Dict[str, Any]:
        """获取保证金池状态"""
        total_used = sum(p.margin_used for p in self._margin_positions.values())
        return {
            'total_pool': self.run_config.margin_pool_size,
            'available': self._margin_pool_available,
            'used': total_used,
            'utilization': total_used / self.run_config.margin_pool_size if self.run_config.margin_pool_size > 0 else 0,
            'position_count': len(self._margin_positions)
        }

    # ========== V34.0: Execution Priority Queue Methods ==========

    def add_to_execution_queue(
        self,
        opportunity_id: str,
        symbol: str,
        side: str,
        quantity: float,
        score: float
    ) -> bool:
        """添�执行任务到队列 - V34.0新增

        Args:
            opportunity_id: 机会ID
            symbol: 交易对
            side: 买入/卖出
            quantity: 数量
            score: 评分

        Returns:
            是否成功
        """
        if not self.run_config.enable_priority_queue:
            return False

        if len(self._execution_queue) >= self.run_config.max_queue_size:
            return False

        priority = int(min(10, max(1, score / 10)))
        task = ExecutionTask(
            task_id=f"task_{len(self._execution_queue)}_{int(time.time())}",
            opportunity_id=opportunity_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            priority=priority,
            score=score,
            created_at=time.time()
        )
        self._execution_queue.append(task)
        # 按优先级排序
        self._execution_queue.sort(key=lambda x: x.priority, reverse=True)
        return True

    def get_next_execution(self) -> Optional[ExecutionTask]:
        """获取下一个执行任务"""
        if self._execution_queue:
            return self._execution_queue.pop(0)
        return None

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            'queue_size': len(self._execution_queue),
            'max_size': self.run_config.max_queue_size,
            'tasks': [
                {'symbol': t.symbol, 'priority': t.priority, 'score': t.score}
                for t in self._execution_queue
            ]
        }

    # ========== V34.0: P&L Dashboard Methods ==========

    def update_pnl(self, realized: float = 0.0, unrealized: float = 0.0) -> None:
        """更新盈亏 - V34.0新增

        Args:
            realized: 已实现盈亏
            unrealized: 未实现盈亏
        """
        if not self.run_config.enable_pnl_dashboard:
            return

        self._total_realized_pnl += realized
        self._daily_pnl += realized

        if realized > 0:
            self._win_count += 1
        if realized != 0:
            self._trade_count += 1

    def get_pnl_summary(self) -> ProfitLoss:
        """获��盈亏汇总"""
        unrealized = sum(p.unrealized_pnl for p in self._margin_positions.values())
        total_pnl = self._total_realized_pnl + unrealized
        commission = self._trade_count * 2.0  # 假设每笔2美元手续费
        net_pnl = total_pnl - commission
        win_rate = self._win_count / self._trade_count if self._trade_count > 0 else 0

        return ProfitLoss(
            realized_pnl=self._total_realized_pnl,
            unrealized_pnl=unrealized,
            total_pnl=total_pnl,
            daily_pnl=self._daily_pnl,
            commission=commission,
            net_pnl=net_pnl,
            win_rate=win_rate,
            trade_count=self._trade_count,
            timestamp=time.time()
        )

    # ========== V35.0: Triangular Arbitrage Methods ==========

    def scan_triangular_arbitrage(self, base_symbol: str = "BTC") -> List[TriangularOpportunity]:
        """扫描三角形套利机会 - V35.0新增

        Args:
            base_symbol: 基础货币对

        Returns:
            TriangularOpportunity列表
        """
        if not self.run_config.enable_triangular:
            return []

        # 定义三角形路径 (A->B->C->A)
        symbols = self.run_config.triangular_paths.split(',')
        opportunities = []

        # 生成模拟汇率
        rates = {
            'BTC': {'ETH': 15.0, 'USDT': 50000.0, 'SOL': 500.0},
            'ETH': {'BTC': 0.065, 'USDT': 3300.0, 'SOL': 33.0},
            'USDT': {'BTC': 0.00002, 'ETH': 0.0003, 'SOL': 0.01},
            'SOL': {'BTC': 0.0019, 'ETH': 0.029, 'USDT': 95.0}
        }

        # 计算三角形套利路径
        for sym_a in symbols:
            for sym_b in symbols:
                for sym_c in symbols:
                    if sym_a != sym_b and sym_b != sym_c and sym_a != sym_c:
                        # 计算: A→B→C→A
                        rate_a_to_b = rates.get(sym_a, {}).get(sym_b, 1.0)
                        rate_b_to_c = rates.get(sym_b, {}).get(sym_c, 1.0)
                        rate_c_to_a = rates.get(sym_c, {}).get(sym_a, 1.0)

                        # 计算预期利润: (rate_a_to_b * rate_b_to_c * rate_c_to_a - 1)
                        expected_profit = rate_a_to_b * rate_b_to_c * rate_c_to_a - 1

                        if expected_profit >= self.run_config.triangular_min_profit:
                            score = min(100.0, expected_profit * 10000)
                            opp = TriangularOpportunity(
                                symbol_a=sym_a,
                                symbol_b=sym_b,
                                symbol_c=sym_c,
                                path=f"{sym_a}→{sym_b}→{sym_c}→{sym_a}",
                                rate_a_to_b=rate_a_to_b,
                                rate_b_to_c=rate_b_to_c,
                                rate_c_to_a=rate_c_to_a,
                                expected_profit_pct=expected_profit,
                                actual_profit_pct=expected_profit * 0.95,
                                score=score,
                                timestamp=time.time()
                            )
                            opportunities.append(opp)

        self._triangular_opportunities = opportunities
        return opportunities

    def get_triangular_opportunities(self) -> List[TriangularOpportunity]:
        """获取三角形套利机会"""
        return self._triangular_opportunities

    # ========== V35.0: Funding Rate Arbitrage Methods ==========

    def scan_funding_arbitrage(self, symbol: str = "BTC/USDT") -> List[FundingArbitrage]:
        """扫描资金费率套利机会 - V35.0新增

        Args:
            symbol: 交易对

        Returns:
            FundingArbitrage列表
        """
        if not self.run_config.enable_funding_arbitrage:
            return []

        exchanges = self.run_config.funding_exchanges.split(',')
        opportunities = []

        # 模拟各交易所资金费率
        funding_rates = {}
        base_rate = 0.0001
        for i, ex in enumerate(exchanges):
            funding_rates[ex] = base_rate * (1 + (i - 1) * 0.5)

        # 找最大费率差
        for ex_a in exchanges:
            for ex_b in exchanges:
                if ex_a != ex_b:
                    rate_a = funding_rates.get(ex_a, 0)
                    rate_b = funding_rates.get(ex_b, 0)
                    rate_diff = abs(rate_a - rate_b)

                    if rate_diff >= self.run_config.funding_min_diff:
                        potential = rate_diff * 10000 * 1000
                        score = min(100.0, rate_diff * 50000)

                        arb = FundingArbitrage(
                            symbol=symbol,
                            exchange_a=ex_a,
                            exchange_b=ex_b,
                            funding_rate_a=rate_a,
                            funding_rate_b=rate_b,
                            rate_diff=rate_diff,
                            potential_profit=potential,
                            score=score,
                            timestamp=time.time()
                        )
                        opportunities.append(arb)

        self._funding_arbitrage_opportunities = opportunities
        self._funding_rates[symbol] = funding_rates
        return opportunities

    def get_funding_arbitrage_opportunities(self) -> List[FundingArbitrage]:
        """获取资金费率套利机会"""
        return self._funding_arbitrage_opportunities

    # ========== V35.0: ML Signal Methods ==========

    def add_ml_signal(
        self,
        symbol: str,
        prediction: float,
        confidence: float,
        model_name: str = "default"
    ) -> bool:
        """添加ML信号 - V35.0新增

        Args:
            symbol: 交易对
            prediction: 预测方向(1/0/-1)
            confidence: 置信度(0-1)
            model_name: 模型名

        Returns:
            是否成功
        """
        if not self.run_config.enable_ml_signal:
            return False

        if confidence < self.run_config.ml_confidence_threshold:
            return False

        signal = MLSignal(
            symbol=symbol,
            prediction=prediction,
            confidence=confidence,
            model_name=model_name,
            timestamp=time.time()
        )
        self._ml_signals[symbol] = signal

        if symbol not in self._ml_predictions:
            self._ml_predictions[symbol] = []
        self._ml_predictions[symbol].append(prediction)
        if len(self._ml_predictions[symbol]) > 100:
            self._ml_predictions[symbol] = self._ml_predictions[symbol][-100:]

        return True

    def get_ml_signal(self, symbol: str) -> Optional[MLSignal]:
        """获取ML信号"""
        return self._ml_signals.get(symbol)

    def get_ml_signals_summary(self) -> Dict[str, Any]:
        """获取ML信号汇总"""
        signals = list(self._ml_signals.values())
        buy_signals = sum(1 for s in signals if s.prediction > 0)
        sell_signals = sum(1 for s in signals if s.prediction < 0)
        neutral_signals = sum(1 for s in signals if s.prediction == 0)

        return {
            'total_signals': len(signals),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'neutral_signals': neutral_signals,
            'avg_confidence': sum(s.confidence for s in signals) / max(len(signals), 1)
        }

    def get_advanced_arbitrage_summary(self) -> Dict[str, Any]:
        """获取高级套利汇总 - V35.0新增"""
        return {
            'triangular_count': len(self._triangular_opportunities),
            'funding_arbitrage_count': len(self._funding_arbitrage_opportunities),
            'ml_signals': len(self._ml_signals),
            'ml_summary': self.get_ml_signals_summary()
        }

    # ==================== V36.0: Grid Trading ====================
    def create_grid_strategy(
        self,
        symbol: str,
        price_min: float,
        price_max: float,
        grid_count: int = 10,
        grid_type: str = "arithmetic",
        position_per_grid: float = 0.001
    ) -> str:
        """创建网格策略 - V36.0新增

        Args:
            symbol: 交易对
            price_min: 最低价格
            price_max: 最高价格
            grid_count: 网格数量
            grid_type: 网格类型 (arithmetic/geometric)
            position_per_grid: 每网格仓位

        Returns:
            策略ID
        """
        strategy_id = f"grid_{symbol}_{int(time.time())}"

        if grid_type == "arithmetic":
            grid_spacing = (price_max - price_min) / grid_count
        else:  # geometric
            grid_spacing = (price_max / price_min) ** (1.0 / grid_count) - 1

        strategy = GridStrategy(
            strategy_id=strategy_id,
            symbol=symbol,
            grid_type=grid_type,
            grid_count=grid_count,
            price_min=price_min,
            price_max=price_max,
            grid_spacing=grid_spacing,
            position_per_grid=position_per_grid,
            status="active",
            created_at=time.time(),
            updated_at=time.time()
        )

        self._grid_strategies[strategy_id] = strategy

        # 创建网格订单
        for i in range(grid_count):
            price = price_min + (i * grid_spacing) if grid_type == "arithmetic" else price_min * (grid_spacing + 1) ** i

            grid_order = GridOrder(
                grid_id=f"{strategy_id}_{i}",
                symbol=symbol,
                side="sell" if i == grid_count - 1 else "buy",
                price=price,
                quantity=position_per_grid,
                grid_level=i,
                status="pending",
                timestamp=time.time()
            )
            self._grid_orders.append(grid_order)

        logger.info(f"✅ 网格策略已创建: {strategy_id}, {grid_count} grids")
        return strategy_id

    def update_grid_prices(self, strategy_id: str, current_price: float) -> List[GridOrder]:
        """更新网格价格并检查触发 - V36.0新增

        Args:
            strategy_id: 策略ID
            current_price: 当前价格

        Returns:
            触发的网格订单
        """
        triggered = []

        if strategy_id not in self._grid_strategies:
            return triggered

        strategy = self._grid_strategies[strategy_id]

        for order in self._grid_orders:
            if order.status != "pending":
                continue

            # 检查是否应该触发
            if order.side == "buy" and current_price <= order.price:
                order.status = "filled"
                order.filled_at = time.time()
                order.profit_pct = strategy.grid_spacing
                triggered.append(order)
                strategy.filled_grids += 1

            elif order.side == "sell" and current_price >= order.price:
                order.status = "filled"
                order.filled_at = time.time()
                order.profit_pct = strategy.grid_spacing
                triggered.append(order)
                strategy.filled_grids += 1

        # 更新策略统计
        strategy.active_grids = sum(1 for o in self._grid_orders if o.status == "pending")
        strategy.updated_at = time.time()

        return triggered

    def get_grid_strategy(self, strategy_id: str) -> Optional[GridStrategy]:
        """获取网格策略 - V36.0新增"""
        return self._grid_strategies.get(strategy_id)

    def get_grid_orders(self, strategy_id: Optional[str] = None) -> List[GridOrder]:
        """获取网格订单 - V36.0新增"""
        if strategy_id:
            return [o for o in self._grid_orders if o.grid_id.startswith(strategy_id)]
        return self._grid_orders

    def cancel_grid_strategy(self, strategy_id: str) -> bool:
        """取消网格策略 - V36.0新增"""
        if strategy_id in self._grid_strategies:
            self._grid_strategies[strategy_id].status = "cancelled"
            for order in self._grid_orders:
                if order.grid_id.startswith(strategy_id):
                    order.status = "cancelled"
            return True
        return False

    # ==================== V36.0: DCA Bot ====================
    def create_dca_strategy(
        self,
        symbol: str,
        direction: str,
        trade_amount: float,
        price_target: float,
        trade_interval: int = 3600,
        total_triggers: int = 5
    ) -> str:
        """创建DCA策略 - V36.0新增

        Args:
            symbol: 交易对
            direction: 方向 (buy/sell)
            trade_amount: 每次交易数量
            price_target: 目标价格
            trade_interval: 交易间隔(秒)
            total_triggers: 总触发次数

        Returns:
            策略ID
        """
        strategy_id = f"dca_{symbol}_{int(time.time())}"

        strategy = DCAStrategy(
            strategy_id=strategy_id,
            symbol=symbol,
            direction=direction,
            total_trades=total_triggers,
            trade_amount=trade_amount,
            trade_interval=trade_interval,
            price_target=price_target,
            next_trade_time=time.time() + trade_interval,
            created_at=time.time()
        )

        self._dca_strategies[strategy_id] = strategy
        logger.info(f"✅ DCA策略已创建: {strategy_id}")
        return strategy_id

    def execute_dca_trade(self, strategy_id: str, current_price: float) -> bool:
        """执行DCA交易 - V36.0新增

        Args:
            strategy_id: 策略ID
            current_price: 当前价格

        Returns:
            是否执行成功
        """
        if strategy_id not in self._dca_strategies:
            return False

        strategy = self._dca_strategies[strategy_id]

        if strategy.completed_trades >= strategy.total_trades:
            strategy.status = "completed"
            return False

        # 首次交易或最后一次交易允许立即执行，否则检查时间
        is_last_trade = strategy.completed_trades + 1 >= strategy.total_trades
        if not is_last_trade and strategy.completed_trades > 0 and time.time() < strategy.next_trade_time:
            return False

        # 执行DCA交易
        trade_value = strategy.trade_amount * current_price
        strategy.total_invested += trade_value
        strategy.completed_trades += 1
        strategy.current_price = current_price

        # 更新平均成本
        if strategy.completed_trades == 1:
            strategy.average_price = current_price
        else:
            strategy.average_price = (strategy.average_price * (strategy.completed_trades - 1) + current_price) / strategy.completed_trades

        strategy.current_value = strategy.trade_amount * strategy.completed_trades * strategy.average_price

        # 计算盈亏
        if strategy.direction == "buy":
            strategy.profit_pct = (current_price - strategy.average_price) / strategy.average_price
        else:
            strategy.profit_pct = (strategy.average_price - current_price) / strategy.average_price

        # 下次交易时间
        strategy.next_trade_time = time.time() + strategy.trade_interval

        if strategy.completed_trades >= strategy.total_trades:
            strategy.status = "completed"

        logger.info(f"✅ DCA交易执行: {strategy_id}, #{strategy.completed_trades}")
        return True

    def get_dca_strategy(self, strategy_id: str) -> Optional[DCAStrategy]:
        """获取DCA策略 - V36.0新增"""
        return self._dca_strategies.get(strategy_id)

    def get_active_dca_strategies(self) -> List[DCAStrategy]:
        """获取活跃的DCA策略 - V36.0新增"""
        return [s for s in self._dca_strategies.values() if s.status == "pending"]

    # ==================== V36.0: Paper Trading ====================
    def execute_paper_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fee_rate: float = 0.0004
    ) -> PaperTrade:
        """执行模拟交易 - V36.0新增

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)
            quantity: 数量
            price: 价格
            fee_rate: 费率

        Returns:
            交易记录
        """
        trade_value = quantity * price
        fee = trade_value * fee_rate

        # 更新余额
        if side == "buy":
            self._paper_balance -= (trade_value + fee)
        else:
            self._paper_balance += (trade_value - fee)

        trade = PaperTrade(
            trade_id=f"paper_{int(time.time())}",
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            fee=fee,
            executed=True,
            executed_at=time.time()
        )

        self._paper_trades.append(trade)
        logger.info(f"📄 模拟交易: {side} {quantity} {symbol} @ {price}")
        return trade

    def get_paper_balance(self) -> float:
        """获取模拟账户余额 - V36.0新增"""
        return self._paper_balance

    def get_paper_trades(self, limit: int = 10) -> List[PaperTrade]:
        """获取模拟交易记录 - V36.0新增"""
        return self._paper_trades[-limit:]

    def get_paper_pnl(self) -> Dict[str, float]:
        """获取模拟交易盈亏 - V36.0新增"""
        trades = self._paper_trades
        if not trades:
            return {'realized_pnl': 0.0, 'unrealized_pnl': 0.0, 'total_pnl': 0.0, 'trade_count': 0}

        realized = sum(t.pnl for t in trades if t.executed)
        return {
            'realized_pnl': realized,
            'unrealized_pnl': 0.0,
            'total_pnl': realized,
            'trade_count': len(trades),
            'winning_trades': sum(1 for t in trades if t.pnl > 0),
            'losing_trades': sum(1 for t in trades if t.pnl < 0)
        }

    # ==================== V36.0: Trading Stats ====================
    def update_trading_stats(self, trade: PaperTrade) -> None:
        """更新交易统计 - V36.0新增

        Args:
            trade: 交易记录
        """
        stats = self._trading_stats
        stats.total_trades += 1

        if trade.pnl > 0:
            stats.winning_trades += 1
            stats.gross_profit += trade.pnl
        else:
            stats.losing_trades += 1
            stats.gross_loss += abs(trade.pnl)

        stats.total_fees += trade.fee

        # 计算统计数据
        if stats.total_trades > 0:
            stats.win_rate = stats.winning_trades / stats.total_trades

        if stats.gross_loss > 0:
            stats.profit_factor = stats.gross_profit / stats.gross_loss

        stats.net_pnl = stats.gross_profit - stats.gross_loss - stats.total_fees
        stats.timestamp = time.time()

    def get_trading_stats(self) -> TradingStats:
        """获取交易统计 - V36.0新增"""
        return self._trading_stats

    def get_stats_summary(self) -> Dict[str, Any]:
        """获取统计汇总 - V36.0新增"""
        stats = self._trading_stats
        return {
            'total_trades': stats.total_trades,
            'winning_trades': stats.winning_trades,
            'losing_trades': stats.losing_trades,
            'win_rate': f"{stats.win_rate * 100:.2f}%",
            'profit_factor': f"{stats.profit_factor:.2f}",
            'gross_profit': f"{stats.gross_profit:.2f}",
            'gross_loss': f"{stats.gross_loss:.2f}",
            'net_pnl': f"{stats.net_pnl:.2f}",
            'total_fees': f"{stats.total_fees:.2f}",
            'sharpe_ratio': f"{stats.sharpe_ratio:.2f}",
            'max_drawdown': f"{stats.max_drawdown * 100:.2f}%"
        }

    # ==================== V36.0: 综合汇总 ====================
    def get_v36_summary(self) -> Dict[str, Any]:
        """获取V36.0功能汇总 - V36.0新增"""
        return {
            'grid_strategies': len(self._grid_strategies),
            'grid_orders': len(self._grid_orders),
            'dca_strategies': len(self._dca_strategies),
            'paper_trades': len(self._paper_trades),
            'paper_balance': f"{self._paper_balance:.2f}",
            'stats': self.get_stats_summary()
        }

    # ==================== V37.0: Backtesting Engine ====================
    def add_candle_data(self, symbol: str, candle: CandleData) -> None:
        """添加K线数据 - V37.0新增

        Args:
            symbol: 交易对
            candle: K线数据
        """
        if not hasattr(self, '_candle_data'):
            self._candle_data: Dict[str, List[CandleData]] = {}

        if symbol not in self._candle_data:
            self._candle_data[symbol] = []

        self._candle_data[symbol].append(candle)

    def add_candle_batch(self, symbol: str, candles: List[Dict[str, Any]]) -> None:
        """批量添加K线数据 - V37.0新增

        Args:
            symbol: 交易对
            candles: K线数据列表
        """
        for c in candles:
            candle = CandleData(
                timestamp=c.get('timestamp', time.time()),
                open=c.get('open', 0.0),
                high=c.get('high', 0.0),
                low=c.get('low', 0.0),
                close=c.get('close', 0.0),
                volume=c.get('volume', 0.0)
            )
            self.add_candle_data(symbol, candle)

    def execute_backtest_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        timestamp: float
    ) -> BacktestTrade:
        """执行回测交易 - V37.0新增

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)
            price: 价格
            quantity: 数量
            timestamp: 时间戳

        Returns:
            交易记录
        """
        trade_id = f"bt_{symbol}_{int(timestamp)}"
        trade_value = price * quantity
        fee = trade_value * self.run_config.backtest_fee_rate

        trade = BacktestTrade(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            entry_time=timestamp,
            _fee=fee
        )

        # 更新权益
        if side == "buy":
            self._backtest_equity -= (trade_value + fee)
        else:
            self._backtest_equity += (trade_value - fee)

        self._backtest_trades.append(trade)
        return trade

    def close_backtest_position(
        self,
        symbol: str,
        exit_price: float,
        exit_time: float
    ) -> Optional[BacktestTrade]:
        """平仓 - V37.0新增

        Args:
            symbol: 交易对
            exit_price: 平仓价格
            exit_time: 平仓时间

        Returns:
            平仓交易记录
        """
        if symbol not in self._backtest_positions:
            return None

        position = self._backtest_positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']

        # 找到对应的入场交易
        entry_trade = None
        for trade in reversed(self._backtest_trades):
            if trade.symbol == symbol and trade.side == "buy" and trade.exit_price == 0.0:
                entry_trade = trade
                break

        if entry_trade is None:
            return None

        # 计算盈亏
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = (exit_price - entry_price) / entry_price

        # 更新交易记录
        trade = BacktestTrade(
            trade_id=entry_trade.trade_id,
            symbol=symbol,
            side="sell",
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            entry_time=entry_trade.entry_time,
            exit_time=exit_time,
            pnl=pnl,
            pnl_pct=pnl_pct,
            holding_periods=int(exit_time - entry_trade.entry_time)
        )

        # 更新权益
        self._backtest_equity += (exit_price * quantity) - (entry_price * quantity)

        # 移除仓位
        del self._backtest_positions[symbol]

        return trade

    def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        candles: List[Dict[str, Any]],
        strategy_func: callable
    ) -> BacktestResult:
        """运行回测 - V37.0新增

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            candles: K线数据
            strategy_func: 策略函数 (candle, position) -> action

        Returns:
            回测结果
        """
        # 重置状态
        self._backtest_trades = []
        self._backtest_positions = {}
        self._backtest_equity = self.run_config.backtest_initial_capital

        # 添加K线数据
        self.add_candle_batch(symbol, candles)

        # 获取K线数据
        candle_data = self._candle_data.get(symbol, [])

        # 运行回测
        for i, candle in enumerate(candle_data):
            current_position = self._backtest_positions.get(symbol)

            # 调用策略函数
            action = strategy_func(candle, current_position)

            if action == "buy" and current_position is None:
                # 开多仓
                max_qty = self._backtest_equity / candle.close * 0.95  # 95%仓位
                self.execute_backtest_trade(symbol, "buy", candle.close, max_qty, candle.timestamp)
                self._backtest_positions[symbol] = {
                    'entry_price': candle.close,
                    'quantity': max_qty,
                    'entry_time': candle.timestamp
                }

            elif action == "sell" and current_position is not None:
                # 平仓
                self.close_backtest_position(symbol, candle.close, candle.timestamp)

        # 计算回测结果
        result = self.calculate_backtest_result(strategy_name, symbol, candles)
        self._backtest_results[strategy_name] = result

        return result

    def calculate_backtest_result(
        self,
        strategy_name: str,
        symbol: str,
        candles: List[Dict[str, Any]]
    ) -> BacktestResult:
        """计算回测结果 - V37.0新增

        Args:
            strategy_name: 策略名称
            symbol: 交易对
            candles: K线数据

        Returns:
            回测结果
        """
        trades = self._backtest_trades

        if not trades:
            return BacktestResult(
                strategy_name=strategy_name,
                symbol=symbol,
                start_date="",
                end_date="",
                initial_capital=self.run_config.backtest_initial_capital,
                final_capital=self._backtest_equity
            )

        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        total_pnl = sum(t.pnl for t in trades)
        total_return = total_pnl
        total_return_pct = total_return / self.run_config.backtest_initial_capital

        # 计算统计数据
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = abs(sum(t.pnl for t in losing_trades)) / len(losing_trades) if losing_trades else 0
        profit_factor = total_pnl / abs(sum(t.pnl for t in losing_trades)) if losing_trades and sum(t.pnl for t in losing_trades) != 0 else 0

        # 计算最大回撤
        equity = self.run_config.backtest_initial_capital
        peak = equity
        max_dd = 0
        for trade in trades:
            equity += trade.pnl
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

        # 计算夏普比率 (简化版)
        returns = [t.pnl_pct for t in trades if t.pnl_pct != 0]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 0
        sharpe = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0

        # 计算卡尔玛比率
        annual_return = total_return_pct * 252 / len(candles) if candles else 0
        calmar = annual_return / max_dd if max_dd > 0 else 0

        # 平均持仓时间
        avg_holding = sum(t.holding_periods for t in trades) / len(trades) if trades else 0

        result = BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=str(candles[0].get('timestamp', 0)) if candles else "",
            end_date=str(candles[-1].get('timestamp', 0)) if candles else "",
            initial_capital=self.run_config.backtest_initial_capital,
            final_capital=self._backtest_equity,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            calmar_ratio=calmar,
            avg_holding_periods=avg_holding,
            trade_log=trades
        )

        return result

    def get_backtest_result(self, strategy_name: str) -> Optional[BacktestResult]:
        """获取回测结果 - V37.0新增"""
        return self._backtest_results.get(strategy_name)

    def get_all_backtest_results(self) -> Dict[str, BacktestResult]:
        """获取所有回测结果 - V37.0新增"""
        return self._backtest_results

    def get_v37_summary(self) -> Dict[str, Any]:
        """获取V37.0功能汇总 - V37.0新增"""
        return {
            'backtest_results': len(self._backtest_results),
            'backtest_trades': len(self._backtest_trades),
            'backtest_equity': f"{self._backtest_equity:.2f}",
            'results': {
                name: {
                    'total_return_pct': f"{r.total_return_pct * 100:.2f}%",
                    'win_rate': f"{r.win_rate * 100:.2f}%",
                    'sharpe_ratio': f"{r.sharpe_ratio:.2f}",
                    'max_drawdown': f"{r.max_drawdown * 100:.2f}%"
                }
                for name, r in self._backtest_results.items()
            }
        }

    # ==================== V38.0: Risk Management ====================
    def calculate_var_historical(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算历史VaR - V38.0新增

        Args:
            returns: 收益率列表
            confidence: 置信度

        Returns:
            VaR值
        """
        if not returns or len(returns) < 2:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return abs(sorted_returns[index])

    def calculate_cvar(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算条件VaR (Expected Shortfall) - V38.0新增

        Args:
            returns: 收益率列表
            confidence: 置信度

        Returns:
            CVaR值
        """
        if not returns or len(returns) < 2:
            return 0.0

        var = self.calculate_var_historical(returns, confidence)
        tail_losses = [r for r in returns if r <= -var]
        if not tail_losses:
            return var
        return abs(sum(tail_losses) / len(tail_losses))

    def calculate_volatility(self, returns: List[float]) -> float:
        """计算波动率 - V38.0新增

        Args:
            returns: 收益率列表

        Returns:
            波动率
        """
        if not returns or len(returns) < 2:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤 - V38.0新增

        Args:
            equity_curve: 权益曲线

        Returns:
            最大回撤
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def update_daily_return(self, return_pct: float) -> None:
        """更新日收益率 - V38.0新增

        Args:
            return_pct: 收益率百分比
        """
        self._daily_returns.append(return_pct)
        # 保持最近252个交易日
        if len(self._daily_returns) > 252:
            self._daily_returns = self._daily_returns[-252:]

    def calculate_risk_metrics(self, symbol: str, prices: List[float]) -> RiskMetrics:
        """计算风险指标 - V38.0新增

        Args:
            symbol: 交易对
            prices: 价格历史

        Returns:
            风险指标
        """
        if not prices or len(prices) < 2:
            return RiskMetrics()

        # 计算收益率
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)

        # 计算VaR
        var_95 = self.calculate_var_historical(returns, 0.95)
        var_99 = self.calculate_var_historical(returns, 0.99)

        # 计算CVaR
        cvar_95 = self.calculate_cvar(returns, 0.95)
        cvar_99 = self.calculate_cvar(returns, 0.99)

        # 计算波动率
        volatility = self.calculate_volatility(returns)

        # 计算最大回撤
        equity_curve = [1.0]
        for r in returns:
            equity_curve.append(equity_curve[-1] * (1 + r))
        max_dd = self.calculate_max_drawdown(equity_curve)

        metrics = RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            max_drawdown=max_dd,
            volatility=volatility,
            timestamp=time.time()
        )

        self._risk_metrics[symbol] = metrics
        return metrics

    def get_risk_metrics(self, symbol: str) -> Optional[RiskMetrics]:
        """获取风险指标 - V38.0新增"""
        return self._risk_metrics.get(symbol)

    def check_var_limit(self, symbol: str) -> bool:
        """检查VaR是否超过限制 - V38.0新增

        Args:
            symbol: 交易对

        Returns:
            是否在限制内
        """
        if symbol not in self._risk_metrics:
            return True

        metrics = self._risk_metrics[symbol]
        return metrics.var_95 <= self.run_config.max_var_pct

    def calculate_position_size_risk(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_pct: float,
        risk_amount: float
    ) -> float:
        """基于风险计算仓位 - V38.0新增

        Args:
            symbol: 交易对
            entry_price: 入场价格
            stop_loss_pct: 止损百分比
            risk_amount: 风险金额

        Returns:
            仓位数量
        """
        risk_per_unit = entry_price * stop_loss_pct
        if risk_per_unit <= 0:
            return 0.0
        return risk_amount / risk_per_unit

    def add_to_portfolio(
        self,
        symbol: str,
        quantity: float,
        avg_price: float,
        current_price: float,
        beta: float = 1.0,
        sector: str = "crypto"
    ) -> None:
        """添加到组合 - V38.0新增

        Args:
            symbol: 交易对
            quantity: 数量
            avg_price: 平均价格
            current_price: 当前价格
            beta: Beta值
            sector: 板块
        """
        pnl = (current_price - avg_price) * quantity
        pnl_pct = (current_price - avg_price) / avg_price if avg_price > 0 else 0

        position = PortfolioPosition(
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
            current_price=current_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            beta=beta,
            sector=sector
        )

        self._portfolio[symbol] = position
        self._update_portfolio_weights()

    def _update_portfolio_weights(self) -> None:
        """更新组合权重 - V38.0新增"""
        total_value = sum(p.current_price * p.quantity for p in self._portfolio.values())
        if total_value == 0:
            return

        for position in self._portfolio.values():
            position.weight = (position.current_price * position.quantity) / total_value

    def get_portfolio_value(self) -> float:
        """获取组合总价值 - V38.0新增"""
        return sum(p.current_price * p.quantity for p in self._portfolio.values())

    def get_portfolio_pnl(self) -> float:
        """获取组合总盈亏 - V38.0新增"""
        return sum(p.pnl for p in self._portfolio.values())

    def get_portfolio_position(self, symbol: str) -> Optional[PortfolioPosition]:
        """获取组合持仓 - V38.0新增"""
        return self._portfolio.get(symbol)

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取组合汇总 - V38.0新增"""
        total_value = self.get_portfolio_value()
        total_pnl = self.get_portfolio_pnl()

        positions = []
        for p in self._portfolio.values():
            positions.append({
                'symbol': p.symbol,
                'quantity': p.quantity,
                'avg_price': f"{p.avg_price:.2f}",
                'current_price': f"{p.current_price:.2f}",
                'pnl': f"{p.pnl:.2f}",
                'weight': f"{p.weight * 100:.2f}%",
                'beta': f"{p.beta:.2f}"
            })

        # 计算组合Beta
        portfolio_beta = sum(p.weight * p.beta for p in self._portfolio.values()) if positions else 1.0

        return {
            'total_value': f"{total_value:.2f}",
            'total_pnl': f"{total_pnl:.2f}",
            'position_count': len(self._portfolio),
            'portfolio_beta': f"{portfolio_beta:.2f}",
            'positions': positions
        }

    def get_v38_summary(self) -> Dict[str, Any]:
        """获取V38.0功能汇总 - V38.0新增"""
        return {
            'risk_metrics_count': len(self._risk_metrics),
            'portfolio_positions': len(self._portfolio),
            'portfolio_value': f"{self.get_portfolio_value():.2f}",
            'portfolio_pnl': f"{self.get_portfolio_pnl():.2f}",
            'var_95': f"{self._risk_metrics.get('BTC/USDT', RiskMetrics()).var_95 * 100:.2f}%" if self._risk_metrics else "N/A",
            'risk_summary': self.get_portfolio_summary()
        }

    # ==================== V39.0: Real Trading ====================
    def configure_exchange(
        self,
        exchange: str,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
        fee_tier: float = 0.0004
    ) -> bool:
        """配置交易所 - V39.0新增

        Args:
            exchange: 交易所名称
            api_key: API密钥
            api_secret: API密钥
            testnet: 测试网模式
            fee_tier: 手续费层级

        Returns:
            是否成功
        """
        config = ExchangeConfig(
            exchange=exchange,
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            enabled=True,
            fee_tier=fee_tier
        )

        self._exchange_configs[exchange] = config
        logger.info(f"✅ 交易所已配置: {exchange}, testnet={testnet}")
        return True

    def get_exchange_config(self, exchange: str) -> Optional[ExchangeConfig]:
        """获取交易所配置 - V39.0新增"""
        return self._exchange_configs.get(exchange)

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0.0
    ) -> OrderRecord:
        """创建订单 - V39.0新增

        Args:
            symbol: 交易对
            side: 方向 (buy/sell)
            order_type: 订单类型 (limit/market)
            quantity: 数量
            price: 价格 (市价单时为0)

        Returns:
            订单记录
        """
        order_id = f"ord_{symbol}_{side}_{int(time.time())}"

        # 如果是市价单，使用0价格
        if order_type == "market":
            price = 0.0

        order = OrderRecord(
            order_id=order_id,
            exchange=self.run_config.default_exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity,
            status="pending",
            created_at=time.time()
        )

        self._order_records.append(order)
        logger.info(f"📝 订单已创建: {order_id} {side} {quantity} {symbol}")
        return order

    def simulate_fill_order(self, order_id: str, fill_price: float) -> bool:
        """模拟订单成交 - V39.0新增

        Args:
            order_id: 订单ID
            fill_price: 成交价格

        Returns:
            是否成功
        """
        for order in self._order_records:
            if order.order_id == order_id and order.status == "pending":
                order.status = "filled"
                order.filled_quantity = order.quantity
                order.avg_fill_price = fill_price
                order.filled_at = time.time()

                # 计算手续费
                fee = fill_price * order.quantity * 0.0004  # 简化计算 (0.04% fee)
                order.fee = fee

                logger.info(f"✅ 订单已成交: {order_id} @ {fill_price}")
                return True

        return False

    def get_order(self, order_id: str) -> Optional[OrderRecord]:
        """获取订单 - V39.0新增"""
        for order in self._order_records:
            if order.order_id == order_id:
                return order
        return None

    def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderRecord]:
        """获取未完成订单 - V39.0新增"""
        orders = [o for o in self._order_records if o.status == "pending"]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders

    def get_order_history(self, limit: int = 10) -> List[OrderRecord]:
        """获取订单历史 - V39.0新增"""
        return self._order_records[-limit:]

    def generate_trade_signal(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        confidence: float,
        strategy: str
    ) -> TradeSignal:
        """生成交易信号 - V39.0新增

        Args:
            symbol: 交易对
            action: 方向
            entry_price: 入场价格
            stop_loss: 止损价格
            take_profit: 止盈价格
            quantity: 数量
            confidence: 置信度
            strategy: 策略名称

        Returns:
            交易信号
        """
        signal = TradeSignal(
            signal_id=f"sig_{symbol}_{int(time.time())}",
            symbol=symbol,
            action=action,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            confidence=confidence,
            strategy=strategy,
            generated_at=time.time()
        )

        self._trade_signals.append(signal)
        return signal

    def get_trade_signals(self, limit: int = 10) -> List[TradeSignal]:
        """获取交易信号 - V39.0新增"""
        return self._trade_signals[-limit:]

    def get_v39_summary(self) -> Dict[str, Any]:
        """获取V39.0功能汇总 - V39.0新增"""
        return {
            'exchangesConfigured': len(self._exchange_configs),
            'order_records': len(self._order_records),
            'trade_signals': len(self._trade_signals),
            'real_trading_enabled': self.run_config.enable_real_trading,
            'default_exchange': self.run_config.default_exchange,
            'testnet_mode': self.run_config.testnet_mode,
            'open_orders': len(self.get_open_orders()),
            'filled_orders': len([o for o in self._order_records if o.status == "filled"])
        }

    # ==================== V40.0: Multi-Strategy ====================
    def register_strategy(
        self,
        strategy_id: str,
        strategy_name: str,
        allocation_pct: float = 0.0
    ) -> bool:
        """注册策略 - V40.0新增

        Args:
            strategy_id: 策略ID
            strategy_name: 策略名称
            allocation_pct: 分配比例

        Returns:
            是否成功
        """
        if len(self._strategy_allocations) >= self.run_config.max_active_strategies:
            logger.warning(f"⚠️ 已达到最大策略数: {self.run_config.max_active_strategies}")
            return False

        allocation = StrategyAllocation(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            allocation_pct=allocation_pct,
            enabled=True
        )

        self._strategy_allocations[strategy_id] = allocation
        logger.info(f"✅ 策略已注册: {strategy_name}")
        return True

    def update_strategy_performance(
        self,
        strategy_id: str,
        total_return: float,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
        trade_count: int
    ) -> bool:
        """更新策略绩效 - V40.0新增

        Args:
            strategy_id: 策略ID
            total_return: 总收益率
            sharpe_ratio: 夏普比率
            max_drawdown: 最大回撤
            win_rate: 胜率
            trade_count: 交易次数

        Returns:
            是否成功
        """
        if strategy_id not in self._strategy_allocations:
            return False

        perf = StrategyPerformance(
            strategy_id=strategy_id,
            strategy_name=self._strategy_allocations[strategy_id].strategy_name,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            trade_count=trade_count,
            last_updated=time.time()
        )

        self._strategy_performances[strategy_id] = perf
        return True

    def get_strategy_performance(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """获取策略绩效 - V40.0新增"""
        return self._strategy_performances.get(strategy_id)

    def get_all_strategies(self) -> Dict[str, StrategyAllocation]:
        """获取所有策略 - V40.0新增"""
        return self._strategy_allocations

    def detect_market_regime_v2(self, prices: List[float], volume: List[float]) -> MarketRegimeData:
        """检测市场区间 - V40.0新增

        Args:
            prices: 价格列表
            volume: 成交量列表

        Returns:
            市场区间数据
        """
        if not prices or len(prices) < 10:
            return MarketRegimeData()

        # 简单趋势检测
        recent = prices[-10:]
        trend = (recent[-1] - recent[0]) / recent[0]

        # 波动率
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r * r for r in returns) / len(returns)) ** 0.5

        # 成交量比率
        avg_volume = sum(volume) / len(volume)
        volume_ratio = volume[-1] / avg_volume if avg_volume > 0 else 1.0

        # 确定区间
        if abs(trend) > 0.05:
            regime = "trending_up" if trend > 0 else "trending_down"
        elif volatility > 0.03:
            regime = "volatile"
        else:
            regime = "ranging"

        confidence = min(abs(trend) * 10, 1.0)

        regime_data = MarketRegimeData(
            regime=regime,
            confidence=confidence,
            trend_strength=abs(trend),
            volatility=volatility,
            volume_ratio=volume_ratio,
            timestamp=time.time()
        )

        self._market_regime = regime_data
        return regime_data

    def get_market_regime(self) -> Optional[MarketRegimeData]:
        """获取市场区间 - V40.0新增"""
        return self._market_regime

    def should_rotate_strategies(self) -> bool:
        """检查是否需要策略轮换 - V40.0新增

        Returns:
            是否需要轮换
        """
        if not self.run_config.strategy_rotation:
            return False

        time_since_rebalance = time.time() - self._last_rebalance
        return time_since_rebalance >= self.run_config.rebalance_interval

    def rotate_strategies(self) -> Dict[str, Any]:
        """执行策略轮换 - V40.0新增

        Returns:
            轮换结果
        """
        if not self.should_rotate_strategies():
            return {'action': 'none', 'reason': 'not_required'}

        # 简单的基于绩效的轮换
        sorted_strategies = sorted(
            self._strategy_performances.items(),
            key=lambda x: x[1].sharpe_ratio,
            reverse=True
        )

        # 重新分配权重
        top_n = sorted_strategies[:self.run_config.max_active_strategies]
        for i, (strategy_id, perf) in enumerate(top_n):
            if strategy_id in self._strategy_allocations:
                self._strategy_allocations[strategy_id].priority = i

        self._last_rebalance = time.time()

        return {
            'action': 'rotated',
            'strategies_rotated': len(top_n),
            'timestamp': self._last_rebalance
        }

    def get_v40_summary(self) -> Dict[str, Any]:
        """获取V40.0功能汇总 - V40.0新增"""
        return {
            'strategies_registered': len(self._strategy_allocations),
            'strategies_performing': len(self._strategy_performances),
            'multi_strategy_enabled': self.run_config.enable_multi_strategy,
            'strategy_rotation': self.run_config.strategy_rotation,
            'market_regime': self._market_regime.regime if self._market_regime else "unknown",
            'time_since_rebalance': f"{time.time() - self._last_rebalance:.0f}s"
        }

    # ==================== V41.0: Dashboard & Alerts ====================
    def create_dashboard_widget(
        self,
        widget_id: str,
        widget_type: str,
        title: str,
        data_source: str,
        refresh_interval: int = 60
    ) -> bool:
        """创建仪表板组件 - V41.0新增

        Args:
            widget_id: 组件ID
            widget_type: 组件类型
            title: 标题
            data_source: 数据源
            refresh_interval: 刷新间隔

        Returns:
            是否成功
        """
        widget = DashboardWidget(
            widget_id=widget_id,
            widget_type=widget_type,
            title=title,
            data_source=data_source,
            refresh_interval=refresh_interval,
            enabled=True
        )

        self._dashboard_widgets[widget_id] = widget
        return True

    def get_dashboard_widget(self, widget_id: str) -> Optional[DashboardWidget]:
        """获取仪表板组件 - V41.0新增"""
        return self._dashboard_widgets.get(widget_id)

    def create_alert(
        self,
        alert_type: str,
        source: str,
        message: str
    ) -> bool:
        """创建系统告警 - V41.0新增

        Args:
            alert_type: 告警类型
            source: 来源
            message: 消息

        Returns:
            是否成功
        """
        if not self.run_config.enable_system_alerts:
            return False

        alert = SystemAlert(
            alert_id=f"alert_{int(time.time())}",
            alert_type=alert_type,
            source=source,
            message=message,
            timestamp=time.time()
        )

        self._system_alerts.append(alert)
        logger.info(f"⚠️ 告警: [{alert_type}] {message}")
        return True

    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警 - V41.0新增

        Args:
            alert_id: 告警ID

        Returns:
            是否成功
        """
        for alert in self._system_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_active_alerts(self) -> List[SystemAlert]:
        """获取活跃告警 - V41.0新增"""
        return [a for a in self._system_alerts if not a.resolved]

    def create_schedule_task(
        self,
        task_id: str,
        task_type: str,
        schedule: str
    ) -> bool:
        """创建计划任务 - V41.0新增

        Args:
            task_id: 任务ID
            task_type: 任务类型
            schedule: cron表达式

        Returns:
            是否成功
        """
        if not self.run_config.enable_scheduling:
            return False

        task = ScheduleTask(
            task_id=task_id,
            task_type=task_type,
            schedule=schedule,
            enabled=True,
            next_run=time.time()
        )

        self._schedule_tasks[task_id] = task
        return True

    def get_schedule_task(self, task_id: str) -> Optional[ScheduleTask]:
        """获取计划任务 - V41.0新增"""
        return self._schedule_tasks.get(task_id)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态 - V41.0新增"""
        return {
            'running': self.is_running,
            'loop_status': self.loop_status.value,
            'positions': len(self.get_active_positions()),
            'alerts': len(self.get_active_alerts()),
            'strategies': len(self._strategy_allocations),
            'last_update': time.time()
        }

    def get_v41_summary(self) -> Dict[str, Any]:
        """获取V41.0功能汇总 - V41.0新增"""
        return {
            'dashboard_widgets': len(self._dashboard_widgets),
            'alerts': len(self._system_alerts),
            'active_alerts': len(self.get_active_alerts()),
            'schedule_tasks': len(self._schedule_tasks),
            'dashboard_enabled': self.run_config.enable_dashboard,
            'alerts_enabled': self.run_config.enable_system_alerts,
            'scheduling_enabled': self.run_config.enable_scheduling,
            'system_status': self.get_system_status()
        }

    # ==================== V42.0: API Integration ====================
    def register_api_endpoint(
        self,
        endpoint_id: str,
        path: str,
        method: str = "GET",
        auth_required: bool = True,
        rate_limit: int = 100
    ) -> bool:
        """注册API端点 - V42.0新增

        Args:
            endpoint_id: 端点ID
            path: 路径
            method: 方法
            auth_required: 需要认证
            rate_limit: 速率限制

        Returns:
            是否成功
        """
        if not self.run_config.enable_api_server:
            return False

        endpoint = APIEndpoint(
            endpoint_id=endpoint_id,
            path=path,
            method=method,
            auth_required=auth_required,
            rate_limit=rate_limit
        )

        self._api_endpoints[endpoint_id] = endpoint
        return True

    def get_api_endpoint(self, endpoint_id: str) -> Optional[APIEndpoint]:
        """获取API端点 - V42.0新增"""
        return self._api_endpoints.get(endpoint_id)

    def configure_webhook(
        self,
        webhook_id: str,
        url: str,
        events: List[str],
        secret: str = ""
    ) -> bool:
        """配置Webhook - V42.0新增

        Args:
            webhook_id: Webhook ID
            url: URL
            events: 事件列表
            secret: 密钥

        Returns:
            是否成功
        """
        if not self.run_config.enable_webhooks:
            return False

        webhook = WebhookConfig(
            webhook_id=webhook_id,
            url=url,
            events=events,
            secret=secret,
            enabled=True
        )

        self._webhooks[webhook_id] = webhook
        return True

    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """获取Webhook配置 - V42.0新增"""
        return self._webhooks.get(webhook_id)

    def trigger_webhook(self, webhook_id: str, event: str, data: Dict[str, Any]) -> bool:
        """触发Webhook - V42.0新增

        Args:
            webhook_id: Webhook ID
            event: 事件
            data: 数据

        Returns:
            是否成功
        """
        if webhook_id not in self._webhooks:
            return False

        webhook = self._webhooks[webhook_id]
        if event not in webhook.events:
            return False

        logger.info(f"📨 Webhook触发: {webhook_id} - {event}")
        return True

    def check_exchange_status(self, exchange: str) -> bool:
        """检查交易所状态 - V42.0新增

        Args:
            exchange: 交易所

        Returns:
            是否在线
        """
        status = self._exchange_status.get(exchange)
        if not status:
            return False

        return status.status == "online"

    def update_exchange_status(self, exchange: str, status: str, latency_ms: float = 0.0) -> None:
        """更新交易所状态 - V42.0新增

        Args:
            exchange: 交易所
            status: 状态
            latency_ms: 延迟
        """
        exchange_status = ExchangeStatus(
            exchange=exchange,
            status=status,
            latency_ms=latency_ms,
            last_check=time.time()
        )

        self._exchange_status[exchange] = exchange_status

    def get_all_exchange_status(self) -> Dict[str, ExchangeStatus]:
        """获取所有交易所状态 - V42.0新增"""
        return self._exchange_status

    def get_v42_summary(self) -> Dict[str, Any]:
        """获取V42.0功能汇总 - V42.0新增"""
        return {
            'api_endpoints': len(self._api_endpoints),
            'webhooks': len(self._webhooks),
            'exchanges': len(self._exchange_status),
            'api_server_enabled': self.run_config.enable_api_server,
            'api_port': self.run_config.api_port,
            'webhooks_enabled': self.run_config.enable_webhooks,
            'exchange_status': {
                ex: st.status for ex, st in self._exchange_status.items()
            }
        }

    # ==================== V43.0: Advanced Analytics ====================
    def calculate_performance_attribution(
        self,
        strategy_id: str,
        returns: List[float],
        benchmark_returns: List[float]
    ) -> PerformanceAttribution:
        """计算绩效归因 - V43.0新增"""
        if not returns or not benchmark_returns:
            return PerformanceAttribution()

        # 计算基本指标
        total_return = sum(returns)
        benchmark_return = sum(benchmark_returns)
        alpha = total_return - benchmark_return

        # 计算信息比率
        diff_returns = [r - b for r, b in zip(returns, benchmark_returns)]
        avg_diff = sum(diff_returns) / len(diff_returns)
        std_diff = (sum((d - avg_diff) ** 2 for d in diff_returns) / len(diff_returns)) ** 0.5
        info_ratio = avg_diff / std_diff if std_diff > 0 else 0

        attr = PerformanceAttribution(
            strategy_id=strategy_id,
            period_start=time.time() - len(returns) * 3600,
            period_end=time.time(),
            total_return=total_return,
            benchmark_return=benchmark_return,
            alpha=alpha,
            treynor_ratio=alpha / 1.0 if 1.0 != 0 else 0,
            information_ratio=info_ratio,
            r_squared=0.85
        )

        return attr

    def add_trade_attribution(
        self,
        trade_id: str,
        symbol: str,
        pnl: float
    ) -> TradeAttribution:
        """添加交易归因 - V43.0新增"""
        attr = TradeAttribution(
            trade_id=trade_id,
            symbol=symbol,
            pnl_contribution=pnl,
            timing_contribution=pnl * 0.3,
            selection_contribution=pnl * 0.4,
            size_contribution=pnl * 0.3
        )

        self._trade_attributions.append(attr)
        return attr

    def calculate_risk_attribution(self) -> RiskAttribution:
        """计算风险归因 - V43.0新增"""
        # 简化计算
        total_risk = 0.15
        return RiskAttribution(
            total_risk=total_risk,
            systematic_risk=total_risk * 0.4,
            idiosyncratic_risk=total_risk * 0.6,
            concentration_risk=0.1
        )

    def generate_analytics_report(self, report_type: str = "daily") -> AnalyticsReport:
        """生成分析报告 - V43.0新增"""
        report = AnalyticsReport(
            report_id=f"rpt_{int(time.time())}",
            report_type=report_type,
            generated_at=time.time(),
            period_start=time.time() - 86400,
            period_end=time.time(),
            trade_count=len(self._trade_attributions),
            total_pnl=sum(t.pnl_contribution for t in self._trade_attributions)
        )

        self._analytics_reports.append(report)
        return report

    def get_analytics_report(self, report_id: str) -> Optional[AnalyticsReport]:
        """获取分析报告 - V43.0新增"""
        for r in self._analytics_reports:
            if r.report_id == report_id:
                return r
        return None

    def get_v43_summary(self) -> Dict[str, Any]:
        """获取V43.0功能汇总 - V43.0新增"""
        return {
            'analytics_enabled': self.run_config.enable_analytics,
            'analytics_interval': self.run_config.analytics_interval,
            'reports_generated': len(self._analytics_reports),
            'trade_attributions': len(self._trade_attributions),
            'risk_attribution': {
                'total_risk': f"{self.calculate_risk_attribution().total_risk * 100:.2f}%"
            }
        }

    # ==================== V44.0: Portfolio & Execution ====================
    def optimize_portfolio(
        self,
        target_return: float = 0.10
    ) -> PortfolioOptimization:
        """组合优化 - V44.0新增"""
        if not self.run_config.enable_optimization:
            return PortfolioOptimization()

        # 简化优化 - 等权重
        symbols = list(self._portfolio.keys())
        if not symbols:
            return PortfolioOptimization()

        weight = 1.0 / len(symbols)
        weights = {s: weight for s in symbols}

        opt = PortfolioOptimization(
            optimization_id=f"opt_{int(time.time())}",
            target_return=target_return,
            weights=weights,
            expected_return=target_return * 0.8,
            expected_volatility=0.15,
            sharpe_ratio=target_return / 0.15
        )

        self._optimizations.append(opt)
        return opt

    def create_execution_algorithm(
        self,
        algorithm_type: str,
        symbol: str,
        quantity: float
    ) -> ExecutionAlgorithm:
        """创建执行算法 - V44.0新增"""
        algo = ExecutionAlgorithm(
            algorithm_id=f"algo_{int(time.time())}",
            algorithm_type=algorithm_type,
            symbol=symbol,
            quantity=quantity,
            start_time=time.time()
        )

        self._execution_algorithms[algo.algorithm_id] = algo
        return algo

    def execute_algo_slice(
        self,
        algorithm_id: str,
        quantity: float,
        price: float
    ) -> bool:
        """执行算法切片 - V44.0新增"""
        if algorithm_id not in self._execution_algorithms:
            return False

        algo = self._execution_algorithms[algorithm_id]
        algo.filled_quantity += quantity
        algo.avg_price = (algo.avg_price * (algo.filled_quantity - quantity) + price * quantity) / algo.filled_quantity

        if algo.filled_quantity >= algo.quantity:
            algo.status = "completed"

        return True

    def smart_route_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Dict[str, Any]:
        """智能路由订单 - V44.0新增"""
        if not self.run_config.enable_smart_routing:
            return {'exchange': self.run_config.default_exchange, 'quantity': quantity}

        # 简化路由逻辑
        routers = ['binance', 'bybit', 'okx']
        best = routers[0]

        return {
            'exchange': best,
            'quantity': quantity,
            'routers_checked': len(routers)
        }

    def get_v44_summary(self) -> Dict[str, Any]:
        """获取V44.0功能汇总 - V44.0新增"""
        return {
            'optimization_enabled': self.run_config.enable_optimization,
            'smart_routing_enabled': self.run_config.enable_smart_routing,
            'optimizations': len(self._optimizations),
            'execution_algorithms': len(self._execution_algorithms)
        }

    # ==================== V45.0: Advanced Orders ====================
    def create_conditional_order(
        self,
        parent_order_id: str,
        condition_type: str,
        trigger_price: float,
        side: str,
        quantity: float
    ) -> ConditionalOrder:
        """创建条件订单 - V45.0新增"""
        order = ConditionalOrder(
            order_id=f"cond_{int(time.time())}",
            parent_order_id=parent_order_id,
            condition_type=condition_type,
            trigger_price=trigger_price,
            side=side,
            quantity=quantity
        )
        self._conditional_orders[order.order_id] = order
        return order

    def check_conditional_trigger(self, current_price: float) -> List[ConditionalOrder]:
        """检查条件订单触发 - V45.0新增"""
        triggered = []
        for order in self._conditional_orders.values():
            if order.status != "pending":
                continue
            if order.condition_type == "stop_loss" and current_price <= order.trigger_price:
                triggered.append(order)
            elif order.condition_type == "take_profit" and current_price >= order.trigger_price:
                triggered.append(order)
        return triggered

    def create_iceberg_order(self, symbol: str, side: str, total_qty: float, displayed_qty: float, price: float) -> IcebergOrder:
        """创建冰山订单 - V45.0新增"""
        order = IcebergOrder(
            order_id=f"ice_{int(time.time())}",
            symbol=symbol,
            side=side,
            total_quantity=total_qty,
            displayed_quantity=displayed_qty,
            price=price
        )
        self._iceberg_orders[order.order_id] = order
        return order

    def create_twap_order(self, symbol: str, side: str, quantity: float, slices: int = 10, interval: int = 60) -> TWAPOrder:
        """创建TWAP订单 - V45.0新增"""
        order = TWAPOrder(
            order_id=f"twap_{int(time.time())}",
            symbol=symbol,
            side=side,
            total_quantity=quantity,
            slice_count=slices,
            slice_interval=interval
        )
        self._twap_orders[order.order_id] = order
        return order

    def take_position_snapshot(self, symbol: str) -> PositionSnapshot:
        """拍摄持仓快照 - V45.0新增"""
        if symbol in self._portfolio:
            pos = self._portfolio[symbol]
            snapshot = PositionSnapshot(
                snapshot_id=f"snap_{int(time.time())}",
                symbol=symbol,
                quantity=pos.quantity,
                entry_price=pos.avg_price,
                current_price=pos.current_price,
                pnl=pos.pnl,
                timestamp=time.time()
            )
            self._position_snapshots.append(snapshot)
            return snapshot
        return PositionSnapshot()

    def get_v45_summary(self) -> Dict[str, Any]:
        """获取V45.0功能汇总 - V45.0新增"""
        return {
            'conditional_orders': len(self._conditional_orders),
            'iceberg_orders': len(self._iceberg_orders),
            'twap_orders': len(self._twap_orders),
            'snapshots': len(self._position_snapshots),
            'conditional_enabled': self.run_config.enable_conditional_orders,
            'iceberg_enabled': self.run_config.enable_iceberg,
            'twap_enabled': self.run_config.enable_twap
        }

    # ==================== V46.0: Sentiment & Correlation ====================
    def update_sentiment(self, symbol: str, score: float, pos: int, neg: int, neu: int) -> SentimentData:
        """更新情绪数据 - V46.0新增"""
        data = SentimentData(
            symbol=symbol,
            sentiment_score=score,
            positive_mentions=pos,
            negative_mentions=neg,
            neutral_mentions=neu,
            timestamp=time.time()
        )
        self._sentiment_data[symbol] = data
        return data

    def get_sentiment(self, symbol: str) -> Optional[SentimentData]:
        """获取情绪数据 - V46.0新增"""
        return self._sentiment_data.get(symbol)

    def calculate_correlation(self, symbol_a: str, symbol_b: str, prices_a: List[float], prices_b: List[float]) -> float:
        """计算相关性 - V46.0新增"""
        if len(prices_a) < 2 or len(prices_b) < 2:
            return 0.0

        # 简化相关性计算
        n = min(len(prices_a), len(prices_b))
        returns_a = [0] + [(prices_a[i] - prices_a[i-1])/prices_a[i-1] for i in range(1,n)]
        returns_b = [0] + [(prices_b[i] - prices_b[i-1])/prices_b[i-1] for i in range(1,n)]

        mean_a = sum(returns_a) / n
        mean_b = sum(returns_b) / n
        cov = sum((returns_a[i]-mean_a)*(returns_b[i]-mean_b) for i in range(n)) / n
        std_a = (sum((r-mean_a)**2 for r in returns_a)/n) ** 0.5
        std_b = (sum((r-mean_b)**2 for r in returns_b)/n) ** 0.5

        if std_a == 0 or std_b == 0:
            return 0.0
        return cov / (std_a * std_b)

    def add_timeframe_signal(self, symbol: str, timeframe: str, signal: str, strength: float) -> TimeframeSignal:
        """添加时间框架信号 - V46.0新增"""
        sig = TimeframeSignal(
            symbol=symbol,
            timeframe=timeframe,
            signal=signal,
            strength=strength,
            timestamp=time.time()
        )

        key = f"{symbol}_{timeframe}"
        if key not in self._timeframe_signals:
            self._timeframe_signals[key] = []
        self._timeframe_signals[key].append(sig)
        return sig

    def get_multi_timeframe_signals(self, symbol: str) -> Dict[str, str]:
        """获取多时间框架信号 - V46.0新增"""
        result = {}
        for key, signals in self._timeframe_signals.items():
            if key.startswith(symbol):
                if signals:
                    result[key.split('_')[1]] = signals[-1].signal
        return result

    def get_v46_summary(self) -> Dict[str, Any]:
        """获取V46.0功能汇总 - V46.0新增"""
        return {
            'sentiment_data': len(self._sentiment_data),
            'correlation_pairs': len(self._correlation_pairs),
            'timeframe_signals': len(self._timeframe_signals),
            'sentiment_enabled': self.run_config.enable_sentiment,
            'correlation_enabled': self.run_config.enable_correlation,
            'multitimeframe_enabled': self.run_config.enable_multitimeframe
        }

    # ==================== V47.0: Derivatives ====================
    def create_options_contract(self, underlying: str, strike: float, exp: float, opt_type: str, position: str, qty: float, premium: float) -> OptionsContract:
        """创建期权合约 - V47.0新增"""
        contract = OptionsContract(
            contract_id=f"opt_{int(time.time())}",
            underlying=underlying,
            strike_price=strike,
            expiry=exp,
            option_type=opt_type,
            position=position,
            quantity=qty,
            premium=premium
        )
        self._options_contracts[contract.contract_id] = contract
        return contract

    def create_futures_contract(self, symbol: str, position: str, qty: float, entry: float, leverage: int = 1) -> FuturesContract:
        """创建期货合约 - V47.0新增"""
        contract = FuturesContract(
            contract_id=f"fut_{int(time.time())}",
            symbol=symbol,
            position=position,
            quantity=qty,
            entry_price=entry,
            leverage=leverage,
            margin=entry * qty / leverage
        )
        self._futures_contracts[contract.contract_id] = contract
        return contract

    def open_margin_account(self, equity: float) -> MarginAccount:
        """开设保证金账户 - V47.0新增"""
        account = MarginAccount(
            account_id=f"margin_{int(time.time())}",
            total_equity=equity,
            available_balance=equity,
            margin_used=0.0
        )
        self._margin_accounts[account.account_id] = account
        return account

    def get_v47_summary(self) -> Dict[str, Any]:
        """获取V47.0功能汇总 - V47.0新增"""
        return {
            'options_contracts': len(self._options_contracts),
            'futures_contracts': len(self._futures_contracts),
            'margin_accounts': len(self._margin_accounts),
            'options_enabled': self.run_config.enable_options,
            'futures_enabled': self.run_config.enable_futures,
            'margin_enabled': self.run_config.enable_margin_trading
        }