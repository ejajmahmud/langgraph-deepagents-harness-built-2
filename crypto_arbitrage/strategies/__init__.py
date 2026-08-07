"""策略模块初始化 V50.0 - 高级交易功能

V50.0重大更新：
- AdvancedOptionsStrategy: 高级期权交易策略（Delta中性、波动率套利、铁鹰策略）
- PerpetualFuturesArbitrage: 永续期货套利（资金费率、基差交易）
- SignalFusionEngine: AI信号融合引擎
- PortfolioRebalancer: 高级投资组合再平衡器

V36.0历史功能：
- GridTradingStrategy: 网格交易策略
- DCABot: DCA定时定额投资机器人
- GridBacktester: 网格交易回测引擎

核心策略:
- BaseStrategy: 所有策略的基类
- StrategyManager: 策略管理器
"""

from strategies.base import BaseStrategy, StrategyState
from strategies.cross_exchange import (
    CrossExchangeArbitrageStrategy,
    LowRiskArbitrageFilter
)
from strategies.triangular_arbitrage import (
    TriangularArbitrageStrategy
)
from strategies.basis_trading import (
    BasisTradingStrategy
)
from strategies.funding_rate import (
    FundingRateArbitrageStrategy
)
from strategies.statistical_arbitrage import (
    StatisticalArbitrageStrategy
)
from strategies.strategy_manager import (
    StrategyManager
)
from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import (
    EnhancedLowRiskArbitrageEngineV59,
    IntelligentArbitrageContext,
    AdaptiveRiskParameters,
    AsyncAnalysisContext,
    AsyncDecisionResult,
    create_enhanced_low_risk_engine_v5_9
)

# V15.3: 统一的策略接口（保持向后兼容性）
LowRiskArbitrageEngine = EnhancedLowRiskArbitrageEngineV59

from strategies.grid_trading import (
    GridOrderType,
    GridStatus,
    DCAMode,
    GridLevel,
    GridPosition,
    DCAPlan,
    GridBacktestResult,
    GridTradingStrategy,
    DCABot,
    GridBacktester,
    create_grid_trading_strategy,
    create_dca_bot,
    create_grid_backtester
)

# V36.0: 网格交易系统
GridTrading = GridTradingStrategy
DCABotV36 = DCABot
GridBacktest = GridBacktester

# V50.0: 高级交易功能
from strategies.advanced_options_strategy import (
    AdvancedOptionsStrategy,
    BlackScholesModel,
    OptionType,
    OptionStyle,
    PositionSide,
    StrategyMode,
    OptionGreeks,
    OptionContract,
    OptionPosition,
    OptionsStrategyResult,
    create_options_strategy
)

from strategies.perpetual_futures_arbitrage import (
    PerpetualFuturesArbitrage,
    FundingRateCalculator,
    PerpetualContract,
    FundingPeriod,
    FundingPrediction,
    PerpetualArbitrageOpportunity,
    PerpTradingSignal,
    create_perpetual_arbitrage
)

from strategies.ai_signal_fusion import (
    SignalFusionEngine,
    SignalSource,
    SignalDirection,
    SignalQuality,
    TradingSignal,
    SignalAggregation,
    FusedSignal,
    create_signal_fusion_engine
)

from strategies.advanced_portfolio_rebalancer import (
    PortfolioRebalancer,
    RebalanceMethod,
    RebalanceTrigger,
    AssetClass,
    PortfolioAsset,
    Portfolio,
    RebalanceResult,
    RiskBudget,
    create_portfolio_rebalancer,
    create_portfolio
)

# V65.0: 跨链交易执行器
from strategies.cross_chain_execution import (
    BridgeProtocol,
    CrossChainOrderStatus,
    OnChainTxType,
    ChainAddress,
    CrossChainOrder,
    BridgeQuote,
    ChainConfig,
    BridgeIntegration,
    CrossChainTransactionBuilder,
    ChainWalletManager,
    get_bridge_integration,
    initialize_bridge_integration,
    get_transaction_builder,
    initialize_transaction_builder,
    get_wallet_manager,
    initialize_wallet_manager,
)

# V66.0: AI策略优化器
from strategies.ai_strategy_optimizer import (
    MarketRegime,
    StrategyType,
    OptimizationGoal,
    StrategyMetrics,
    StrategyPerformance,
    ParameterSet,
    OptimizationResult,
    StrategyRecommendation,
    StrategyPerformanceAnalyzer,
    AdaptiveParameterOptimizer,
    MarketRegimeDetector,
    StrategyRecommendationEngine,
    get_performance_analyzer,
    initialize_performance_analyzer,
    get_parameter_optimizer,
    initialize_parameter_optimizer,
    get_recommendation_engine,
    initialize_recommendation_engine,
)

__all__ = [
    # 基础类
    'BaseStrategy',
    'StrategyState',
    # 核心套利策略
    'CrossExchangeArbitrageStrategy',
    'LowRiskArbitrageFilter',
    'TriangularArbitrageStrategy',
    'BasisTradingStrategy',
    'FundingRateArbitrageStrategy',
    'StatisticalArbitrageStrategy',
    # 策略管理
    'StrategyManager',
    # V5.9增强版低风险套利引擎
    'EnhancedLowRiskArbitrageEngineV59',
    'IntelligentArbitrageContext',
    'AdaptiveRiskParameters',
    'AsyncAnalysisContext',
    'AsyncDecisionResult',
    'create_enhanced_low_risk_engine_v5_9',
    # V15.3: 向后兼容别名
    'LowRiskArbitrageEngine',
    # V36.0: 网格交易系统
    'GridOrderType',
    'GridStatus',
    'DCAMode',
    'GridLevel',
    'GridPosition',
    'DCAPlan',
    'GridBacktestResult',
    'GridTradingStrategy',
    'DCABot',
    'GridBacktester',
    'create_grid_trading_strategy',
    'create_dca_bot',
    'create_grid_backtester',
    # V36.0: 向后兼容别名
    'GridTrading',
    'DCABotV36',
    'GridBacktest',
    # V50.0: 高级交易功能
    'AdvancedOptionsStrategy',
    'BlackScholesModel',
    'OptionType',
    'OptionStyle',
    'PositionSide',
    'StrategyMode',
    'OptionGreeks',
    'OptionContract',
    'OptionPosition',
    'OptionsStrategyResult',
    'create_options_strategy',
    'PerpetualFuturesArbitrage',
    'FundingRateCalculator',
    'PerpetualContract',
    'FundingPeriod',
    'FundingPrediction',
    'PerpetualArbitrageOpportunity',
    'PerpTradingSignal',
    'create_perpetual_arbitrage',
    'SignalFusionEngine',
    'SignalSource',
    'SignalDirection',
    'SignalQuality',
    'TradingSignal',
    'SignalAggregation',
    'FusedSignal',
    'create_signal_fusion_engine',
    'PortfolioRebalancer',
    'RebalanceMethod',
    'RebalanceTrigger',
    'AssetClass',
    'PortfolioAsset',
    'Portfolio',
    'RebalanceResult',
    'RiskBudget',
    'create_portfolio_rebalancer',
    'create_portfolio',
    # V65.0: 跨链交易执行器
    'BridgeProtocol',
    'CrossChainOrderStatus',
    'OnChainTxType',
    'ChainAddress',
    'CrossChainOrder',
    'BridgeQuote',
    'ChainConfig',
    'BridgeIntegration',
    'CrossChainTransactionBuilder',
    'ChainWalletManager',
    'get_bridge_integration',
    'initialize_bridge_integration',
    'get_transaction_builder',
    'initialize_transaction_builder',
    'get_wallet_manager',
    'initialize_wallet_manager',
    # V66.0: AI策略优化器
    'MarketRegime',
    'StrategyType',
    'OptimizationGoal',
    'StrategyMetrics',
    'StrategyPerformance',
    'ParameterSet',
    'OptimizationResult',
    'StrategyRecommendation',
    'StrategyPerformanceAnalyzer',
    'AdaptiveParameterOptimizer',
    'MarketRegimeDetector',
    'StrategyRecommendationEngine',
    'get_performance_analyzer',
    'initialize_performance_analyzer',
    'get_parameter_optimizer',
    'initialize_parameter_optimizer',
    'get_recommendation_engine',
    'initialize_recommendation_engine',
]
