"""实盘交易模块 V13.0 - Phase 13生产级集成

Phase 13核心模块 - 完整的生产级交易系统：
- TradingCoordinator: 交易协调器
- MarketDataManager: 市场数据管理器
- SignalGenerator: 信号生成器
- RiskManagerV2: 风险管理器V2
- ExecutionEngine: 交易执行引擎
- PositionManager: 仓位管理器
- TradeMonitor: 交易监控器

向后兼容：
- ProductionTradingEngine: 多模式交易执行引擎 (V3.7)
- CapitalManager: 科学资金管理系统 (V3.7)
- PerformanceTracker: 实盘数据收集和绩效分析 (V3.7)
"""

# ============ Phase 13 核心模块 ============

from .trading_coordinator import (
    TradingCoordinator,
    get_trading_coordinator,
    TradeStatus,
    TradeEventType,
)

from .market_data_manager import (
    MarketDataManager,
    get_market_data_manager,
    DataQuality,
)

from .signal_generator import (
    SignalGenerator,
    get_signal_generator,
    SignalAction,
    SignalQuality,
)

from .risk_manager_v2 import (
    RiskManagerV2,
    get_risk_manager_v2,
    RiskLevel,
    RiskType,
    RiskAction,
)

from .execution_engine import (
    ExecutionEngine,
    get_execution_engine,
    OrderType,
    OrderSide,
    OrderStatus,
)

from .position_manager import (
    PositionManager,
    get_position_manager,
    PositionStatus,
    PositionSide,
)

from .trade_monitor import (
    TradeMonitor,
    get_trade_monitor,
    TradeSeverity,
    TradeAnomalyType,
)

# ============ 向后兼容模块 (V3.7) ============

from .production_trading_engine import (
    ProductionTradingEngine,
    TradingMode,
    TradingState,
    TradeExecution,
    TradingStatistics,
    create_production_trading_engine
)

from .capital_manager import (
    CapitalManager,
    KellyCriterion,
    RiskParity,
    PositionAllocation,
    CapitalAllocation,
    StrategyPerformance,
    create_capital_manager
)

from .performance_tracker import (
    PerformanceTracker,
    TradeRecord,
    PerformanceMetrics,
    RiskAnalysis,
    AttributionAnalysis,
    create_performance_tracker
)

# ============ V70.0 生产环境集成模块 ============

from .production_integration_v70 import (
    ConfigurationValidator,
    ValidationLevel,
    ValidationResult,
    ErrorHandler,
    ErrorSeverity,
    ErrorRecord,
    ProductionConfig,
    CacheManager,
    BatchProcessor,
    HealthChecker,
    HealthStatus,
    HealthReport,
    SystemMetrics,
    MetricType,
    MetricValue,
    get_configuration_validator,
    initialize_configuration_validator,
    get_error_handler,
    initialize_error_handler,
    get_cache_manager,
    initialize_cache_manager,
    get_batch_processor,
    initialize_batch_processor,
    get_health_checker,
    initialize_health_checker,
    get_system_metrics,
    initialize_system_metrics,
    create_production_config,
)

# ============ V71.0 高级缓存与分布式监控 ============

from .advanced_v71 import (
    CacheStrategy,
    MonitorNodeStatus,
    ScalingDirection,
    CacheStats,
    MonitorNode,
    AggregatedMetrics,
    ScalingDecision,
    LoadBalancerTarget,
    LRUCache,
    DistributedCache,
    CacheWarmer,
    DistributedMonitor,
    MetricsAggregator,
    AutoScaler,
    LoadBalancer,
    get_lru_cache,
    initialize_lru_cache,
    get_distributed_cache,
    initialize_distributed_cache,
    get_cache_warmer,
    initialize_cache_warmer,
    get_distributed_monitor,
    initialize_distributed_monitor,
    get_metrics_aggregator,
    initialize_metrics_aggregator,
    get_auto_scaler,
    initialize_auto_scaler,
    get_load_balancer,
    initialize_load_balancer,
    create_lru_cache,
    create_distributed_cache,
)

# ============ V72.0 实时告警与多区域部署 ============

from .realtime_v72 import (
    AlertPriority,
    AlertState,
    RegionStatus,
    AnalyticsPeriod,
    AlertRule,
    AlertEvent,
    RegionNode,
    AnalyticsResult,
    RealTimeAlert,
    RegionManager,
    AnalyticsEngine,
    get_real_time_alert,
    initialize_real_time_alert,
    get_region_manager,
    initialize_region_manager,
    get_analytics_engine,
    initialize_analytics_engine,
    create_alert_rule,
)

# ============ V73.0 ML集成与策略信号增强 ============

from .ml_v73 import (
    MLModelType,
    SignalType,
    SignalSource,
    OptimizationObjective,
    ModelFeatures,
    ModelPrediction,
    StrategySignal,
    PortfolioPosition,
    OptimizationResult,
    MLModel,
    LinearRegressionModel,
    RandomForestModel,
    StrategySignalGenerator,
    SignalEnsemble,
    PortfolioOptimizer,
    RiskParityOptimizer,
    get_ml_model,
    initialize_ml_model,
    get_signal_generator,
    initialize_signal_generator,
    get_signal_ensemble,
    initialize_signal_ensemble,
    get_portfolio_optimizer,
    initialize_portfolio_optimizer,
    create_ml_model,
)

# ============ V74.0 高级回测与期权策略 ============

from .backtest_v74 import (
    BacktestMode,
    OptionType,
    OptionStyle,
    DefiProtocol,
    BacktestConfig,
    BacktestTrade,
    BacktestMetrics,
    OptionContract,
    OptionPosition,
    DefiPosition,
    BacktestEngine,
    OptionsStrategy,
    DeFiPool,
    YieldFarm,
    get_backtest_engine,
    initialize_backtest_engine,
    get_options_strategy,
    initialize_options_strategy,
    get_defi_pool,
    initialize_defi_pool,
    get_yield_farm,
    initialize_yield_farm,
    create_backtest_config,
)

# ============ V75.0 跨链套利与清算机器人 ============

from .v75 import (
    Chain,
    LiquidationLevel,
    AITradingStrategy,
    BridgeQuote,
    LiquidationPosition,
    LiquidationAlert,
    TradingSignal,
    CrossChainArbitrage,
    LiquidationBot,
    AITradingBot,
    get_cross_chain_arbitrage,
    initialize_cross_chain_arbitrage,
    get_liquidation_bot,
    initialize_liquidation_bot,
    get_ai_trading_bot,
    initialize_ai_trading_bot,
    create_liquidation_position,
)

# ============ V76.0 多链支持、治理投票与性能优化 ============

from .v76 import (
    NetworkType,
    ChainStatus,
    ProposalStatus,
    VoteOption,
    ProposalType,
    OptimizationType,
    ChainInfo,
    MultiChainStats,
    Proposal,
    Vote,
    GovernanceConfig,
    ProposalResult,
    OptimizationResult,
    CacheMetrics,
    ChainRegistry,
    MultiChainManager,
    GovernanceSystem,
    LRUCacheOptimized,
    BatchProcessor,
    ParallelExecutor,
    PerformanceOptimizer,
    get_multi_chain_manager,
    initialize_multi_chain_manager,
    get_governance_system,
    initialize_governance_system,
    get_performance_optimizer,
    initialize_performance_optimizer,
    create_chain_info,
)

# ============ V77.0 跨链执行、收益优化与风控自动化 ============

from .v77 import (
    ExecutionMode,
    YieldSource,
    RiskTriggerType,
    RiskActionType,
    ExecutionStatus,
    CrossChainRoute,
    ExecutionOrder,
    YieldPosition,
    YieldStrategy,
    RiskRule,
    RiskEvent,
    CrossChainExecutor,
    YieldOptimizer,
    RiskAutomation,
    get_cross_chain_executor,
    initialize_cross_chain_executor,
    get_yield_optimizer,
    initialize_yield_optimizer,
    get_risk_automation,
    initialize_risk_automation,
    create_cross_chain_route,
)

# ============ V78.0 智能合约集成、流动性聚合器与高级订单类型 ============

from .v78 import (
    ContractType,
    ContractStatus,
    LiquiditySource,
    OrderTypeAdvanced,
    SmartContract,
    ContractCall,
    LiquidityPool,
    LiquidityQuote,
    AdvancedOrder,
    OCOOrder,
    TWAPOrder,
    SmartContractManager,
    LiquidityAggregator,
    AdvancedOrderManager,
    get_contract_manager,
    initialize_contract_manager,
    get_liquidity_aggregator,
    initialize_liquidity_aggregator,
    get_order_manager,
    initialize_order_manager,
    create_smart_contract,
)

# ============ V79.0 钱包集成、投资组合分析与回测框架 ============

from .v79 import (
    WalletStatus,
    WalletType,
    NetworkTypeV79,
    MetricPeriod,
    BacktestModeV79,
    PortfolioRiskLevel,
    WalletAddress,
    WalletBalance,
    PortfolioPositionV79,
    PortfolioMetrics,
    BacktestTradeV79,
    BacktestResultV79,
    BacktestConfigV79,
    WalletManager,
    PortfolioAnalytics,
    BacktestFramework,
    get_wallet_manager,
    initialize_wallet_manager,
    get_portfolio_analytics,
    initialize_portfolio_analytics,
    get_backtest_framework,
    initialize_backtest_framework,
    create_wallet,
    create_backtest_config,
)

# ============ V80.0 钱包签名、持仓追踪、回测验证与存储 ============

from .v80 import (
    SignatureStatus,
    SignatureType,
    StorageType,
    BacktestStrategy,
    SignatureRequest,
    SignedTransaction,
    PositionSnapshot,
    TradeRecord,
    TrackingReport,
    BacktestSignal,
    BacktestOrder,
    BacktestPerformance,
    StorageRecord,
    SignatureManager,
    PortfolioTracker,
    StrategyBacktest,
    StorageManager,
    get_signature_manager,
    initialize_signature_manager,
    get_portfolio_tracker,
    initialize_portfolio_tracker,
    get_strategy_backtest,
    initialize_strategy_backtest,
    get_storage_manager,
    initialize_storage_manager,
    create_signature_request,
    create_transaction,
)

# ============ V81.0 高级钱包集成、实时风控、策略验证与高级存储 ============

from .v81 import (
    MultiSigType,
    HardwareType,
    RiskLevelV81,
    ValidationResult,
    StorageBackend,
    Signer,
    MultiSigWallet,
    HardwareWallet,
    RiskAlert,
    RiskMetrics,
    ValidationRule,
    ValidationResultV81,
    DatabaseConfig,
    FileStorageConfig,
    MultiSigWalletManager,
    HardwareWalletManager,
    RealTimeRiskMonitor,
    StrategyValidator,
    DatabaseStorage,
    FileStorage,
    get_multi_sig_manager,
    initialize_multi_sig_manager,
    get_hardware_manager,
    initialize_hardware_manager,
    get_risk_monitor,
    initialize_risk_monitor,
    get_validator,
    initialize_validator,
    get_database_storage,
    initialize_database_storage,
    get_file_storage,
    initialize_file_storage,
)

# ============ V82.0 高级套利策略、AI策略生成器、跨链桥接与实时仪表板 ============

from .v82 import (
    ArbitrageType,
    StrategyModel,
    BridgeProtocol,
    DashboardMetric,
    ArbitrageOpportunityV82,
    ArbitrageSignal,
    StrategyConfig,
    GeneratedStrategy,
    BridgeTransaction,
    BridgeQuote,
    DashboardWidget,
    DashboardData,
    AdvancedArbitrage,
    AIStrategyGenerator,
    CrossChainBridge,
    RealTimeDashboard,
    get_arb_engine,
    initialize_arb_engine,
    get_strategy_gen,
    initialize_strategy_gen,
    get_bridge,
    initialize_bridge,
    get_dashboard,
    initialize_dashboard,
)

# ============ V83.0 生产环境集成、性能优化与系统监控 ============

from .v83 import (
    DeploymentMode,
    MetricType,
    AlertSeverity,
    ProductionConfigV83,
    HealthCheck,
    ServiceRegistry,
    PerformanceMetrics,
    OptimizationReport,
    SystemAlert,
    MonitorSnapshot,
    ProductionIntegration,
    PerformanceOptimizer,
    SystemMonitor,
    get_production_integration,
    initialize_production_integration,
    get_performance_optimizer,
    initialize_performance_optimizer,
    get_system_monitor,
    initialize_system_monitor,
)

# ============ V84.0 真实交易执行、多交易所支持与高级风控 ============

from .v84 import (
    TradingStatus,
    OrderTypeV84,
    ExchangeType,
    RiskAction,
    OrderRequestV84,
    OrderResponseV84,
    ExchangeCredentials,
    ExchangeBalance,
    RiskRuleV84,
    RiskEvaluation,
    LiveTradingExecutor,
    MultiExchangeManager,
    AdvancedRiskController,
    get_trading_executor,
    initialize_trading_executor,
    get_exchange_manager,
    initialize_exchange_manager,
    get_risk_controller,
    initialize_risk_controller,
)

# ============ V85.0 实时分析、组合再平衡与高级报告 ============

from .v85 import (
    AnalyticsType,
    RebalanceStrategy,
    ReportFormat,
    AnalyticsDataPoint,
    PortfolioAllocation,
    RebalanceAction,
    ReportSection,
    Report,
    RealTimeAnalytics,
    PortfolioRebalancer,
    AdvancedReporter,
    get_analytics,
    initialize_analytics,
    get_rebalancer,
    initialize_rebalancer,
    get_reporter,
    initialize_reporter,
)

# ============ V86.0 API服务器、WebSocket流与自动交易机器人 ============

from .v86 import (
    HTTPMethod,
    WSMessageType,
    BotStatus,
    BotStrategy,
    APIEndpoint,
    APIRequest,
    APIResponse,
    WSConnection,
    WSMessage,
    BotConfig,
    BotPosition,
    APIServer,
    WebSocketManager,
    AutoTradingBot,
    get_api_server,
    initialize_api_server,
    get_ws_manager,
    initialize_ws_manager,
    get_trading_bot,
    initialize_trading_bot,
)

# ============ V87.0 云端部署、多区域支持与企业级功能 ============

from .v87 import (
    CloudProvider,
    Region,
    EnterpriseTier,
    FeatureFlag,
    DeploymentConfig,
    DeploymentStatus,
    RegionInstance,
    EnterpriseLicense,
    EnterpriseSettings,
    CloudDeployment,
    MultiRegionManager,
    EnterpriseFeatures,
    get_cloud_deployment,
    initialize_cloud_deployment,
    get_region_manager,
    initialize_region_manager,
    get_enterprise_features,
    initialize_enterprise_features,
)

# ============ V88.0 生产就绪、市场领先与全球规模 ============

from .v88 import (
    ReadinessLevel,
    MarketPosition,
    ScaleTier,
    ProductionMetrics,
    MarketMetrics,
    ScaleMetrics,
    ProductionReady,
    MarketLeader,
    GlobalScale,
    get_production_ready,
    initialize_production_ready,
    get_market_leader,
    initialize_market_leader,
    get_global_scale,
    initialize_global_scale,
)

# ============ V89.0 行业标准、世界一流与市场主导 ============

from .v89 import (
    ComplianceStandard,
    AuditStatus,
    SLATier,
    InnovationLevel,
    CustomerSegment,
    DominanceMetric,
    ComplianceReport,
    SLAMetrics,
    BenchmarkData,
    InnovationMetrics,
    CustomerMetrics,
    DominanceData,
    IndustryStandard,
    WorldClass,
    MarketDominance,
    get_industry_standard,
    initialize_industry_standard,
    get_world_class,
    initialize_world_class,
    get_market_dominance,
    initialize_market_dominance,
)

# ============ V90.0 高级分析、预测智能与自主交易 ============

from .v90 import (
    AnalyticsType,
    ModelType,
    PredictionTarget,
    TradingMode,
    LearningType,
    PatternData,
    AnomalyData,
    TrendData,
    PredictionResult,
    TradingSignal,
    AdaptationRecord,
    AdvancedAnalytics,
    PredictiveIntelligence,
    AutonomousTrading,
    get_advanced_analytics,
    initialize_advanced_analytics,
    get_predictive_intelligence,
    initialize_predictive_intelligence,
    get_autonomous_trading,
    initialize_autonomous_trading,
)

# ============ V91.0 企业级功能、监管合规与多资产支持 ============

from .v91 import (
    SSOProvider,
    AuditLevel,
    QuotaType,
    BillingModel,
    ComplianceRegion,
    ReportType,
    AssetClass,
    EnterpriseUser,
    AuditRecord,
    QuotaLimit,
    BillingInfo,
    ComplianceReport,
    TaxRecord,
    AssetPosition,
    EnterpriseFeatures,
    RegulatoryCompliance,
    MultiAssetSupport,
    get_enterprise_features,
    initialize_enterprise_features,
    get_regulatory_compliance,
    initialize_regulatory_compliance,
    get_multi_asset_support,
    initialize_multi_asset_support,
)

# ============ V92.0 高级风险管理、投资组合保险与动态对冲 ============

from .v92 import (
    RiskMethod,
    InsuranceStrategy,
    HedgeType,
    StressScenario,
    VaRResult,
    StressResult,
    InsuranceState,
    HedgePosition,
    AdvancedRiskManagement,
    PortfolioInsurance,
    DynamicHedging,
    get_advanced_risk_management,
    initialize_advanced_risk_management,
    get_portfolio_insurance,
    initialize_portfolio_insurance,
    get_dynamic_hedging,
    initialize_dynamic_hedging,
)

# ============ V93.0 跨资产相关性、流动性管理与执行质量 ============

from .v93 import (
    CorrelationMethod,
    LiquidityLevel,
    ExecutionQuality,
    OrderSide,
    LiquidityType,
    CorrelationResult,
    LiquidityPool,
    LiquidityDepth,
    ExecutionMetrics,
    CrossAssetCorrelation,
    LiquidityManager,
    ExecutionQualityAnalyzer,
    get_cross_asset_correlation,
    initialize_cross_asset_correlation,
    get_liquidity_manager,
    initialize_liquidity_manager,
    get_execution_quality_analyzer,
    initialize_execution_quality_analyzer,
)

# ============ V94.0 高级分析引擎、组合优化与风险归因 ============

from .v94 import (
    AnalyticsPattern,
    AnomalyType,
    OptimizationMethod,
    AttributionSource,
    PatternResult,
    AnomalyResult,
    OptimizationResult,
    AttributionResult,
    AdvancedAnalytics,
    PortfolioOptimizer,
    RiskAttribution,
    get_advanced_analytics,
    initialize_advanced_analytics,
    get_portfolio_optimizer,
    initialize_portfolio_optimizer,
    get_risk_attribution,
    initialize_risk_attribution,
)

__version__ = '4.0.0'
__phase__ = "Phase 38: 分析/优化/归因"

__all__ = [
    # ============ Phase 13 核心模块 ============
    # 交易协调器
    'TradingCoordinator',
    'get_trading_coordinator',
    'TradeStatus',
    'TradeEventType',

    # 市场数据管理器
    'MarketDataManager',
    'get_market_data_manager',
    'DataQuality',

    # 信号生成器
    'SignalGenerator',
    'get_signal_generator',
    'SignalAction',
    'SignalQuality',

    # 风险管理器V2
    'RiskManagerV2',
    'get_risk_manager_v2',
    'RiskLevel',
    'RiskType',
    'RiskAction',

    # 交易执行引擎
    'ExecutionEngine',
    'get_execution_engine',
    'OrderType',
    'OrderSide',
    'OrderStatus',

    # 仓位管理器
    'PositionManager',
    'get_position_manager',
    'PositionStatus',
    'PositionSide',

    # 交易监控器
    'TradeMonitor',
    'get_trade_monitor',
    'TradeSeverity',
    'TradeAnomalyType',

    # ============ 向后兼容模块 (V3.7) ============
    # Trading Engine
    'ProductionTradingEngine',
    'TradingMode',
    'TradingState',
    'TradeExecution',
    'TradingStatistics',
    'create_production_trading_engine',

    # Capital Management
    'CapitalManager',
    'KellyCriterion',
    'RiskParity',
    'PositionAllocation',
    'CapitalAllocation',
    'StrategyPerformance',
    'create_capital_manager',

    # Performance Tracking
    'PerformanceTracker',
    'TradeRecord',
    'PerformanceMetrics',
    'RiskAnalysis',
    'AttributionAnalysis',
    'create_performance_tracker',

    # ============ V77.0 跨链执行、收益优化与风控自动化 ============
    # Execution Mode
    'ExecutionMode',
    'ExecutionStatus',

    # Yield Source
    'YieldSource',

    # Risk Types
    'RiskTriggerType',
    'RiskActionType',

    # Data Structures
    'CrossChainRoute',
    'ExecutionOrder',
    'YieldPosition',
    'YieldStrategy',
    'RiskRule',
    'RiskEvent',

    # Engines
    'CrossChainExecutor',
    'YieldOptimizer',
    'RiskAutomation',

    # Getter Functions
    'get_cross_chain_executor',
    'initialize_cross_chain_executor',
    'get_yield_optimizer',
    'initialize_yield_optimizer',
    'get_risk_automation',
    'initialize_risk_automation',
    'create_cross_chain_route',

    # ============ V78.0 智能合约集成、流动性聚合器与高级订单类型 ============
    # Contract Types
    'ContractType',
    'ContractStatus',

    # Liquidity Source
    'LiquiditySource',

    # Order Types
    'OrderTypeAdvanced',

    # Data Structures
    'SmartContract',
    'ContractCall',
    'LiquidityPool',
    'LiquidityQuote',
    'AdvancedOrder',
    'OCOOrder',
    'TWAPOrder',

    # Managers
    'SmartContractManager',
    'LiquidityAggregator',
    'AdvancedOrderManager',

    # Getter Functions
    'get_contract_manager',
    'initialize_contract_manager',
    'get_liquidity_aggregator',
    'initialize_liquidity_aggregator',
    'get_order_manager',
    'initialize_order_manager',
    'create_smart_contract',

    # ============ V79.0 钱包集成、投资组合分析与回测框架 ============
    # Wallet Types
    'WalletStatus',
    'WalletType',
    'NetworkTypeV79',
    'MetricPeriod',
    'BacktestModeV79',
    'PortfolioRiskLevel',

    # Data Structures
    'WalletAddress',
    'WalletBalance',
    'PortfolioPositionV79',
    'PortfolioMetrics',
    'BacktestTradeV79',
    'BacktestResultV79',
    'BacktestConfigV79',

    # Managers
    'WalletManager',
    'PortfolioAnalytics',
    'BacktestFramework',

    # Getter Functions
    'get_wallet_manager',
    'initialize_wallet_manager',
    'get_portfolio_analytics',
    'initialize_portfolio_analytics',
    'get_backtest_framework',
    'initialize_backtest_framework',
    'create_wallet',
    'create_backtest_config',

    # ============ V80.0 钱包签名、持仓追踪、回测验证与存储 ============
    # Signature Types
    'SignatureStatus',
    'SignatureType',
    'StorageType',
    'BacktestStrategy',

    # Data Structures
    'SignatureRequest',
    'SignedTransaction',
    'PositionSnapshot',
    'TradeRecord',
    'TrackingReport',
    'BacktestSignal',
    'BacktestOrder',
    'BacktestPerformance',
    'StorageRecord',

    # Managers
    'SignatureManager',
    'PortfolioTracker',
    'StrategyBacktest',
    'StorageManager',

    # Getter Functions
    'get_signature_manager',
    'initialize_signature_manager',
    'get_portfolio_tracker',
    'initialize_portfolio_tracker',
    'get_strategy_backtest',
    'initialize_strategy_backtest',
    'get_storage_manager',
    'initialize_storage_manager',
    'create_signature_request',
    'create_transaction',

    # ============ V81.0 高级钱包集成、实时风控、策略验证与高级存储 ============
    # Types
    'MultiSigType',
    'HardwareType',
    'RiskLevelV81',
    'ValidationResult',
    'StorageBackend',

    # Data Structures
    'Signer',
    'MultiSigWallet',
    'HardwareWallet',
    'RiskAlert',
    'RiskMetrics',
    'ValidationRule',
    'ValidationResultV81',
    'DatabaseConfig',
    'FileStorageConfig',

    # Managers
    'MultiSigWalletManager',
    'HardwareWalletManager',
    'RealTimeRiskMonitor',
    'StrategyValidator',
    'DatabaseStorage',
    'FileStorage',

    # Getter Functions
    'get_multi_sig_manager',
    'initialize_multi_sig_manager',
    'get_hardware_manager',
    'initialize_hardware_manager',
    'get_risk_monitor',
    'initialize_risk_monitor',
    'get_validator',
    'initialize_validator',
    'get_database_storage',
    'initialize_database_storage',
    'get_file_storage',
    'initialize_file_storage',

    # ============ V82.0 高级套利策略、AI策略生成器、跨链桥接与实时仪表板 ============
    # Types
    'ArbitrageType',
    'StrategyModel',
    'BridgeProtocol',
    'DashboardMetric',

    # Data Structures
    'ArbitrageOpportunityV82',
    'ArbitrageSignal',
    'StrategyConfig',
    'GeneratedStrategy',
    'BridgeTransaction',
    'BridgeQuote',
    'DashboardWidget',
    'DashboardData',

    # Engines
    'AdvancedArbitrage',
    'AIStrategyGenerator',
    'CrossChainBridge',
    'RealTimeDashboard',

    # Getter Functions
    'get_arb_engine',
    'initialize_arb_engine',
    'get_strategy_gen',
    'initialize_strategy_gen',
    'get_bridge',
    'initialize_bridge',
    'get_dashboard',
    'initialize_dashboard',

    # ============ V83.0 生产环境集成、性能优化与系统监控 ============
    # Types
    'DeploymentMode',
    'MetricType',
    'AlertSeverity',

    # Data Structures
    'ProductionConfigV83',
    'HealthCheck',
    'ServiceRegistry',
    'PerformanceMetrics',
    'OptimizationReport',
    'SystemAlert',
    'MonitorSnapshot',

    # Managers
    'ProductionIntegration',
    'PerformanceOptimizer',
    'SystemMonitor',

    # Getter Functions
    'get_production_integration',
    'initialize_production_integration',
    'get_performance_optimizer',
    'initialize_performance_optimizer',
    'get_system_monitor',
    'initialize_system_monitor',
]