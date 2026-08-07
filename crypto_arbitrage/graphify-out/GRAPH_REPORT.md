# Graph Report - .  (2026-04-30)

## Corpus Check
- Large corpus: 448 files · ~445,488 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 8347 nodes · 22842 edges · 75 communities detected
- Extraction: 50% EXTRACTED · 50% INFERRED · 0% AMBIGUOUS · INFERRED: 11460 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]

## God Nodes (most connected - your core abstractions)
1. `KnowledgeStorage` - 205 edges
2. `SearchResult` - 187 edges
3. `高级可视化模块  V2.6新增：策略回测可视化、知识图谱可视化、3D市场可视化` - 177 edges
4. `StrategyManager` - 172 edges
5. `CrossExchangeArbitrageStrategy` - 170 edges
6. `BaseStrategy` - 144 edges
7. `FundingRateArbitrageStrategy` - 137 edges
8. `BasisTradingStrategy` - 123 edges
9. `StatisticalArbitrageStrategy` - 122 edges
10. `DeepRiskManager` - 117 edges

## Surprising Connections (you probably didn't know these)
- `V3.0 集成测试  测试数字货币套利交易系统 V3.0 的核心功能： 1. 智能优化引擎集成 2. 智能知识管理 V3 集成 3. 自适应错误处理集成 4.` --uses--> `CryptoArbitrageAgent`  [INFERRED]
  tests\test_v3_0.py → agents\main_agent.py
- `mock_agent()` --calls--> `CryptoArbitrageAgent`  [INFERRED]
  tests\test_integration.py → agents\main_agent.py
- `恢复存储          Returns:             是否成功` --uses--> `DeploymentConfig`  [INFERRED]
  automation\auto_recovery.py → deployment\deployment_config.py
- `恢复数据库          Returns:             是否成功` --uses--> `DeploymentConfig`  [INFERRED]
  automation\auto_recovery.py → deployment\deployment_config.py
- `optimizer()` --calls--> `StrategyOptimizer`  [INFERRED]
  tests\test_v2_2.py → storage\strategy_optimizer.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (517): AdaptiveErrorHandler, ErrorCategory, ErrorSeverity, 自适应错误处理器 V3.0      智能处理各种错误，提供自动恢复和预防机制。, 恢复网络错误          Args:             error: 错误对象             context: 上下文, 恢复数据错误          Args:             error: 错误对象             context: 上下文, 恢复策略错误          Args:             error: 错误对象             context: 上下文, 添加预防措施          Args:             action: 预防措施函数 (+509 more)

### Community 1 - "Community 1"
Cohesion: 0.01
Nodes (467): ABC, AutoKnowledgeExtractor, create_auto_knowledge_extractor(), ExtractedKnowledge, ExtractionResult, KnowledgeSource, 自动知识提取器 - V5.10 Phase 1.1  智能自动从交易数据、市场数据和决策过程中提取知识， 使用LLM辅助的事实提取和验证，实现知识管理的自动化。, 从交易数据提取知识          Args:             trade_data: 交易数据字典          Returns: (+459 more)

### Community 2 - "Community 2"
Cohesion: 0.01
Nodes (395): active_position_count(), execute_arbitrage(), 策略基类 V2.4 - 统一策略接口、生命周期管理和通用功能  消除 5 个策略间的代码重复，提供统一的: - scan_opportunities / exe, 安全的扫描方法 - 带状态检查和错误处理          Returns:             套利机会列表，错误时返回空列表, 安全的执行方法 - 带状态检查、记录和错误处理          Args:             opportunity: 套利机会字典, scan_opportunities(), CryptoArbitrageAgentV52, ExecutionEngine (+387 more)

### Community 3 - "Community 3"
Cohesion: 0.01
Nodes (338): 初始化错误处理器          Args:             config: 配置字典, 获取错误统计          Returns:             错误统计字典, add_knowledge(), AddKnowledgeRequest, clear_knowledge(), ExecuteRequest, _get_agent(), get_alerts() (+330 more)

### Community 4 - "Community 4"
Cohesion: 0.01
Nodes (284): 恢复执行错误          Args:             error: 错误对象             context: 上下文, AlertManager, 告警管理器 - Phase 11核心模块  管理系统告警。  核心功能： 1. 告警规则 - 灵活的告警规则配置 2. 多级告警 - INFO/WARNING/, 添加告警规则          Args:             rule: 告警规则字典          Returns:             规则I, 移除告警规则          Args:             rule_id: 规则ID          Returns:             是否, 获取告警规则          Args:             rule_id: 规则ID          Returns:             告警, 列出所有告警规则          Returns:             告警规则列表, 评估告警          Args:             metrics: 指标字典          Returns:             触发的告 (+276 more)

### Community 5 - "Community 5"
Cohesion: 0.01
Nodes (299): MarketRegime, MarketRegimeDetection, 高级市场制式检测器 V3.8 基于多因子分析和机器学习的智能市场制式检测, TrendDirection, KnowledgeCategory, AutoRecoveryEngine, create_auto_recovery_engine(), 自动恢复引擎 V3.7 - 智能故障检测和恢复  提供自动化的故障检测和恢复能力，最小化系统停机时间。 核心功能： 1. 故障自动检测 - 实时检测系统异常 2 (+291 more)

### Community 6 - "Community 6"
Cohesion: 0.01
Nodes (233): AnalysisResult, AnalysisStatus, AsyncAnalysisModule, BatchAnalysisResult, create_async_analysis_module(), 异步分析模块 V5.9 - AsyncAnalysisModule  V5.9新增的第6个核心模块，专注异步LLM分析功能。 基于V5.8模块化架构标准，内聚性, 异步分析单个交易对          Args:             symbol: 交易对符号（如BTC/USDT）             date:, 批量异步分析多个交易对          Args:             symbols: 交易对符号列表             date: 分析日期（默 (+225 more)

### Community 7 - "Community 7"
Cohesion: 0.01
Nodes (180): AdaptiveStrategyOptimizer, create_strategy_optimizer(), MarketRegimeDetector, ParameterRecommendation, PerformanceAnalyzer, 自适应策略优化器 V3.7 基于 Memo0 知识的自适应策略优化系统, 检测市场制式          Args:             market_data: 市场数据          Returns:, 初始化自适应策略优化器          Args:             memo0_storage: Memo0 存储实例             dec (+172 more)

### Community 8 - "Community 8"
Cohesion: 0.02
Nodes (202): AdaptiveRiskManager, AdjustmentHistory, DynamicParameterAdjuster, EarlyWarningSystem, ExecutionRiskEvaluator, ExtremeEvent, ExtremeEventDetector, LiquidityRiskAssessor (+194 more)

### Community 9 - "Community 9"
Cohesion: 0.02
Nodes (146): ArbitrageExecution, AlertLevel, DeepRiskManager, get_deep_risk_manager(), initialize_deep_risk_manager(), 深度风险管理器 V3.2  实现多层次、智能化的风险管理系统，确保套利交易的低风险特性。  核心功能: 1. 实时风险监控 - 敞口、波动率、流动性、相关性 2, 启动实时风险监控          Args:             interval: 监控间隔（秒）, 交易前风险预检          Args:             trade: 交易信息字典          Returns:             风 (+138 more)

### Community 10 - "Community 10"
Cohesion: 0.01
Nodes (134): main(), Check project progress and knowledge base status, debug_enhanced_scan(), 添加策略到知识库          Args:             name: 策略名称             description: 策略描述, 初始化知识库          Args:             db_path: 数据库文件路径, 添加市场模式到知识库          Args:             pattern_name: 模式名称             pattern_typ, 添加风险事件到知识库          Args:             event_type: 事件类型             severity: 严重程, 添加性能指标到知识库          Args:             strategy: 策略名称             date: 日期 (YYYY- (+126 more)

### Community 11 - "Community 11"
Cohesion: 0.01
Nodes (121): CacheManagerModule, create_cache_manager_module(), 缓存管理模块 V5.8 - 专注智能缓存策略和性能优化  核心职责： 1. 统一缓存管理 - 管理所有模块的缓存 2. 智能缓存策略 - LRU、TTL、大小限, 注册一个新的缓存          Args:             cache_name: 缓存名称             max_size: 最大缓存大, 从缓存获取数据          Args:             cache_name: 缓存名称             key: 缓存键, 设置缓存数据          Args:             cache_name: 缓存名称             key: 缓存键, 删除缓存数据          Args:             cache_name: 缓存名称             key: 缓存键, 清空指定缓存          Args:             cache_name: 缓存名称          Returns: (+113 more)

### Community 12 - "Community 12"
Cohesion: 0.02
Nodes (82): ConcurrencyMetrics, ConcurrencyState, ConcurrentController, create_concurrent_controller(), 并发控制器 V5.9 - ConcurrentController  V5.9 Phase 3核心模块：智能并发控制系统 基于V5.9 Phase 2的并发需求, 并发控制器 V5.9      实现智能并发控制和优化，包括：     - 动态并发调整     - 优先级队列     - 资源监控     - 自适应参数调, 初始化并发控制器          Args:             config: 配置字典，包含:                 - min_concu, 提交任务          Args:             func: 任务函数             *args: 位置参数             p (+74 more)

### Community 13 - "Community 13"
Cohesion: 0.01
Nodes (113): get_dashboard(), initialize_dashboard(), 实时监控仪表板 V3.5  提供系统的实时监控、数据聚合和可视化支持。  核心功能： 1. 实时数据收集和聚合 2. 多维度监控指标 3. 风险指标追踪 4., 记录指标          Args:             name: 指标名称             value: 指标值             me, 更新风险指标          Args:             metrics: 风险指标字典, 实时监控仪表板      收集、聚合和提供系统运行时数据，支持实时监控和可视化。, 记录交易          Args:             trade: 交易信息字典, 添加告警          Args:             alert: 告警信息字典 (+105 more)

### Community 14 - "Community 14"
Cohesion: 0.02
Nodes (106): DataMigrator, get_global_migrator(), MigrationProgress, MigrationRecord, MigrationStatus, 数据迁移工具 - V5.10 Phase 5.1  实现从内存存储到memo0的高效数据迁移。  核心功能： 1. 内存数据导出 2. memo0批量导入 3., 初始化数据迁移工具          Args:             batch_size: 批量导入大小             max_retries:, 导出内存数据          Args:             memory_store: 内存存储字典             export_path: (+98 more)

### Community 15 - "Community 15"
Cohesion: 0.02
Nodes (116): AdvancedKnowledgeManager, Advanced Knowledge Manager V3.6 Enhanced intelligent knowledge management with a, Extract comprehensive knowledge from data, Extract focused, high-priority knowledge, Advanced Knowledge Manager V3.6      Enhanced capabilities:     - Advanced patte, Extract predictive knowledge for future optimization, Extract knowledge from trade data, Extract knowledge from market data (+108 more)

### Community 16 - "Community 16"
Cohesion: 0.02
Nodes (81): CacheOptimizer, create_cache_optimizer(), LRUCache, 缓存优化器 - Phase 9核心模块  优化缓存策略和性能。  核心功能： 1. LRU缓存实现 - 最近最少使用缓存 2. 智能预热 - 预加载热点数据 3, 缓存优化器      优化缓存策略和性能。, 初始化缓存优化器          Args:             storage: 存储实例             config: 配置字典, 从缓存获取或使用fetch函数获取          Args:             key: 缓存键             fetch_func: 获取, 预加载热点数据          Args:             hot_keys: 热点键列表             fetch_func: 获取函数 (+73 more)

### Community 17 - "Community 17"
Cohesion: 0.03
Nodes (69): HealthChecker, main(), Check Python environment, Check strategy modules, Check V2.2 intelligent components, Run all health checks, Print health check report, System health checker for CryptoArbitrage (+61 more)

### Community 18 - "Community 18"
Cohesion: 0.03
Nodes (72): 信号生成器 - Phase 13核心模块  生成交易信号，支持多个交易策略的信号生成和综合评估。  核心功能： 1. 多策略信号生成 - 支持多个交易策略的信号, 生成信号          Args:             market_data: 市场数据          Returns:, 评估信号          Args:             signals: 信号列表          Returns:             评估后的, 过滤信号          Args:             signals: 信号列表          Returns:             过滤后的, 获取信号历史          Args:             limit: 返回数量限制          Returns:             信号, 移除策略          Args:             name: 策略名称, 启用策略          Args:             name: 策略名称          Returns:             是否成功, 禁用策略          Args:             name: 策略名称          Returns:             是否成功 (+64 more)

### Community 19 - "Community 19"
Cohesion: 0.05
Nodes (65): ConfidenceLevel, DecisionAdvice, DecisionAssistant, DecisionType, get_decision_assistant(), 智能决策辅助器 (DecisionAssistant) - V4.0  基于历史知识提供智能决策建议。  核心功能： 1. 相似交易查询 2. 风险模式识别 3, 智能决策辅助器      基于历史知识提供智能决策建议。, 初始化决策辅助器          Args:             mem0_storage: Memo0 存储实例             config: (+57 more)

### Community 20 - "Community 20"
Cohesion: 0.03
Nodes (42): ConfigManager, get_config_manager(), load_config(), 配置管理器 V2.5  统一管理系统配置，支持环境变量优先级和配置文件。 优先级：环境变量 > 配置文件 > 默认值  核心功能： 1. 环境变量加载 2. 配, 配置管理器      支持多层级配置加载，优先级：环境变量 > 配置文件 > 默认值, 递归合并两个配置字典          Args:             base: 基础配置             overlay: 覆盖配置, 初始化配置管理器          Args:             config_path: 配置文件路径（可选）, 获取配置项          Args:             key: 配置键，支持点分隔的嵌套键（如 "mem0.api_key"） (+34 more)

### Community 21 - "Community 21"
Cohesion: 0.03
Nodes (36): 检测市场周期          Args:             price_history: 价格历史数据             window_days:, 获取市场情绪          基于多个指标综合判断市场情绪。          Args:             market_data: 市场数据, 识别当前市场状态          Args:             market_data: 市场数据                 - price: 当, ABTest, 启动A/B测试          Args:             test_name: 测试名称             strategy: 策略名称, 记录A/B测试结果          Args:             test_name: 测试名称             variant: 变体 (A/, knowledge_base(), recognizer() (+28 more)

### Community 22 - "Community 22"
Cohesion: 0.06
Nodes (49): AlertSeverity, AnomalyPrediction, AnomalyPredictionModel, AnomalyType, HealthPrediction, PredictiveHealthMonitor, PreventiveAction, PreventiveActionsEngine (+41 more)

### Community 23 - "Community 23"
Cohesion: 0.05
Nodes (36): 获取账户余额          Args:             exchange_name: 交易所名称          Returns:, 获取订单簿          Args:             exchange_name: 交易所名称             symbol: 交易对符号, create_mock_exchange(), MockAccount, MockExchange, MockOrder, 模拟交易所 - V3.0  提供完整的模拟交易所功能，用于安全测试套利策略： - 模拟价格数据生成（支持不同市场条件） - 模拟订单簿 - 模拟交易执行 - 模, 模拟交易所      提供完整的交易所功能模拟，用于测试套利策略。 (+28 more)

### Community 24 - "Community 24"
Cohesion: 0.07
Nodes (32): CacheEntry, initialize_unified_cache(), 获取缓存值          Args:             prefix: 键前缀             *args: 位置参数, 设置缓存值          Args:             prefix: 键前缀             value: 缓存值, 删除缓存值          Args:             prefix: 键前缀             *args: 位置参数, 清理缓存          Args:             prefix: 键前缀，如果为 None 则清理全部          Returns:, 清理过期或最少使用的缓存          Returns:             清理的条目数, 缓存预热          Args:             warmup_data: 预热数据列表，每个元素为 (key, data_loader) 元组 (+24 more)

### Community 25 - "Community 25"
Cohesion: 0.05
Nodes (27): get_storage_integrator(), 存储集成器 - Phase 12核心模块  集成Memo0存储，实现数据持久化和深度分析。  核心功能： 1. 监控数据持久化 - 将监控指标、告警历史保存到M, 持久化监控指标          Args:             metrics: 监控指标字典          Returns:, 持久化告警历史          Args:             alerts: 告警列表          Returns:             是否, 持久化自动化操作          Args:             actions: 自动化操作列表          Returns:, 持久化交易数据          Args:             trading_data: 交易数据字典          Returns:, 查询历史数据          Args:             data_type: 数据类型 [metrics, alerts, actions, tra, 存储集成器      集成Memo0存储，实现数据持久化。 (+19 more)

### Community 26 - "Community 26"
Cohesion: 0.05
Nodes (31): _get_current_user(), refresh(), authenticate_token(), _base64url_decode(), _base64url_encode(), create_jwt(), _ensure_secret(), _hash_password() (+23 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (22): AnalysisResult, create_enhanced_wrapper(), EnhancedTradingAgentsWrapper, PerformanceMetrics, 增强版TradingAgents集成包装器 V14.0      提供AI驱动的智能交易决策和深度市场分析。, 初始化增强版TradingAgents包装器          Args:             provider: LLM提供商             m, 分析单个交易对          Args:             symbol: 交易对符号（如 BTC/USDT）             analysi, 并行分析多个交易对          Args:             symbols: 交易对列表             analysis_date: 分 (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.06
Nodes (24): CircuitBreaker, CircuitBreakerState, get_error_handler(), handle_error_safely(), initialize_error_handler(), 自适应错误处理系统 V3.0  智能错误检测、恢复和预防机制，提升系统稳定性和容错能力。  核心特性： 1. 智能错误分类 - 自动识别错误类型和严重程度 2., 检查是否可以执行          Returns:             是否可以执行, 获取熔断器状态          Returns:             状态字典 (+16 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (28): checkWebSocketConnection(), clearAlerts(), connectWebSocket(), dismissAlert(), exportData(), fetchAPI(), formatUptime(), handleWebSocketMessage() (+20 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (19): AdvancedMarketRegimeDetector, create_advanced_regime_detector(), 检测市场制式          Args:             price: 当前价格             volume: 当前成交量, 分析技术面因子          Args:             indicators: 技术指标字典          Returns:, 分析基本面因子          Args:             fundamentals: 基本面数据字典          Returns:, 分析情绪面因子          Args:             sentiment: 情绪数据字典          Returns:, 综合所有信号          Args:             technical: 技术信号             fundamental: 基本面信号, 计算制式强度          Args:             regime: 市场制式             signals: 技术信号 (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (18): main(), V3.0 集成脚本 - 智能自适应系统集成  将V3.0的新组件集成到现有系统中： 1. 智能优化引擎 2. 智能知识管理系统 3. 自适应错误处理系统 4., 集成系统健康监控          Returns:             是否成功, 集成自适应系统框架          Returns:             是否成功, 更新主Agent以支持V3.0功能          Returns:             是否成功, 初始化集成器          Args:             config_path: 配置文件路径, 生成集成报告          Returns:             报告内容, 保存集成报告          Args:             filepath: 文件路径          Returns:             文 (+10 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (15): ConfigSchema, ConfigValidator, get_config_validator(), 配置验证器 - V5.1  验证系统配置的完整性和正确性。  核心功能： 1. 配置 Schema 验证 2. 版本兼容性检查 3. 数据类型验证 4. 必需字, 初始化配置验证器          Args:             schema: 配置 Schema，默认使用 ConfigSchema, 验证配置完整性          Args:             config: 配置字典          Returns:             验证, 验证错误      Attributes:         level: 错误级别         field: 字段路径 (例如: "system.versi, 获取嵌套字典中的值          Args:             data: 字典数据             path: 字段路径 (例如: "sys (+7 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (2): V2.4 Web UI测试套件 - 测试前端界面和功能, TestV2_4WebUI

### Community 34 - "Community 34"
Cohesion: 0.18
Nodes (14): check_configuration(), check_core_modules(), check_dependencies(), check_project_structure(), check_python_version(), generate_installation_instructions(), main(), System Integrity Verification Script for V3.5 (+6 more)

### Community 35 - "Community 35"
Cohesion: 0.31
Nodes (3): main(), V5.7 架构优化脚本 - 基于Graphify V5.6分析的Community 0拆分  目标： 1. 拆分DeepMemo0Integration（693, V5_7_ArchitectureOptimizer

### Community 36 - "Community 36"
Cohesion: 0.53
Nodes (5): create_knowledge_summary(), main(), V5.7 迭代成果记入知识库脚本  目标： 1. 将V5.7的核心成果和经验记入知识库 2. 更新项目进展记录 3. 为后续迭代提供知识基础 4. 建立持续改进, record_v5_7_achievements(), update_project_progress()

### Community 37 - "Community 37"
Cohesion: 0.33
Nodes (5): get_decision_engine(), initialize_decision_engine(), 智能决策引擎 V2.5增强版  基于Memo0历史经验，提供AI驱动的交易决策支持。  核心功能： 1. 策略选择建议（基于历史相似条件） 2. 风险评估（学习, 获取智能决策引擎实例（全局单例）      Returns:         IntelligentDecisionEngine 实例，如果未初始化则返回 No, 初始化智能决策引擎（V5.3线程安全版）      Args:         storage: 统一存储实例         auto_accumulator

### Community 38 - "Community 38"
Cohesion: 0.4
Nodes (5): get_knowledge_manager(), initialize_knowledge_manager(), 智能知识管理系统 V3.0  升级知识管理能力，实现智能知识提炼、分类、推荐和应用。  核心特性： 1. 智能知识提炼 - 从交易数据中自动提取有价值知识 2., 获取全局知识管理器实例      Args:         storage_backend: 存储后端         config: 配置字典      R, 初始化知识管理器      Args:         storage_backend: 存储后端         config: 配置字典      Retu

### Community 39 - "Community 39"
Cohesion: 0.6
Nodes (4): main(), V5.0 性能测试  测试优化后的 Agent 初始化性能, test_import_overhead(), test_v5_performance()

### Community 40 - "Community 40"
Cohesion: 0.5
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 0.67
Nodes (2): handleRefresh(), loadMarketData()

### Community 42 - "Community 42"
Cohesion: 0.67
Nodes (2): handleSave(), loadRiskConfig()

### Community 43 - "Community 43"
Cohesion: 0.5
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 0.5
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 0.67
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 0.67
Nodes (1): V5.9 Phase 2 简化集成测试  由于模块导入问题，使用简化的测试来验证核心功能。

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): V5.7 Phase 2 - 功能增强脚本：连接孤立节点到主系统  目标： 1. 识别Graphify分析中的95个孤立节点 2. 分析孤立节点的功能和依赖关系

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): 计算文件校验和          Args:             file_path: 文件路径          Returns:

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): 验证备份完整性          Args:             backup_path: 备份文件路径             expected_chec

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): 验证备份文件          Args:             backup_path: 备份文件路径          Returns:

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): 扫描套利机会（子类必须实现）          Returns:             套利机会列表，每个机会必须包含:                 -

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): 执行套利交易（子类必须实现）          Args:             opportunity: 套利机会字典          Returns:

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): 策略是否健康（连续亏损未超过阈值且未处于错误状态）

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): 计算套利机会的风险评分 (0-100, 越低越安全)

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): 计算跨交易所套利收益率          Args:             buy_exchange: 买入交易所             sell_exch

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): 计算三角套利机会          Args:             rates: 汇率字典，如 {'BTC/USDT': 50000, 'ETH/BTC':

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): 计算余弦相似度          Args:             vec1: 向量1             vec2: 向量2          Retu

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): 计算欧几里得距离          Args:             vec1: 向量1             vec2: 向量2          Ret

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): 时间序列采样          使用LTTB (Largest-Triangle-Three-Buckets)算法保留数据形状。          Args:

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): 热力图采样          对2D数组进行降采样。          Args:             data: 2D数据数组             m

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): 散点图采样          使用随机采样减少点数。          Args:             data: 原始数据 [(x, y, z), ...

## Knowledge Gaps
- **1693 isolated node(s):** `V5.0 性能测试  测试优化后的 Agent 初始化性能`, `自动扩缩容 - Phase 11核心模块  根据负载自动调整资源。  核心功能： 1. 自动扩容 - 资源不足时自动扩容 2. 自动缩容 - 资源充足时自动缩容`, `自动扩缩容      根据负载自动调整资源。`, `初始化自动扩缩容          Args:             config: 配置字典`, `添加扩缩容策略          Args:             policy: 扩缩容策略字典          Returns:` (+1688 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 47`** (2 nodes): `App()`, `App.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `ProtectedRoute.tsx`, `ProtectedRoute()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `Settings.tsx`, `Settings()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (2 nodes): `check_dependencies()`, `check_dependencies.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (2 nodes): `V5.7 Phase 2 - 功能增强脚本：连接孤立节点到主系统  目标： 1. 识别Graphify分析中的95个孤立节点 2. 分析孤立节点的功能和依赖关系`, `implement_v5_7_isolated_nodes.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Dashboard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `index.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `计算文件校验和          Args:             file_path: 文件路径          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `验证备份完整性          Args:             backup_path: 备份文件路径             expected_chec`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `验证备份文件          Args:             backup_path: 备份文件路径          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `扫描套利机会（子类必须实现）          Returns:             套利机会列表，每个机会必须包含:                 -`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `执行套利交易（子类必须实现）          Args:             opportunity: 套利机会字典          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `策略是否健康（连续亏损未超过阈值且未处于错误状态）`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `计算套利机会的风险评分 (0-100, 越低越安全)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `计算跨交易所套利收益率          Args:             buy_exchange: 买入交易所             sell_exch`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `计算三角套利机会          Args:             rates: 汇率字典，如 {'BTC/USDT': 50000, 'ETH/BTC':`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `计算余弦相似度          Args:             vec1: 向量1             vec2: 向量2          Retu`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `计算欧几里得距离          Args:             vec1: 向量1             vec2: 向量2          Ret`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `时间序列采样          使用LTTB (Largest-Triangle-Three-Buckets)算法保留数据形状。          Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `热力图采样          对2D数组进行降采样。          Args:             data: 2D数据数组             m`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `散点图采样          使用随机采样减少点数。          Args:             data: 原始数据 [(x, y, z), ...`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `高级可视化模块  V2.6新增：策略回测可视化、知识图谱可视化、3D市场可视化` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 6`, `Community 7`, `Community 11`, `Community 12`, `Community 18`, `Community 25`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `StrategyManager` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 10`, `Community 17`, `Community 21`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `CryptoArbitrageAgent` connect `Community 10` to `Community 0`, `Community 3`, `Community 6`, `Community 7`, `Community 9`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 226 inferred relationships involving `str` (e.g. with `main()` and `main()`) actually correct?**
  _`str` has 226 INFERRED edges - model-reasoned connections that need verification._
- **Are the 189 inferred relationships involving `KnowledgeStorage` (e.g. with `KnowledgeGraphMemo0Storage` and `知识图谱Memo0存储适配器 V1.0 - Phase 7核心模块  实现知识图谱与memo0存储的深度集成，支持图谱持久化、同步和智能检索。  核心功能： 1`) actually correct?**
  _`KnowledgeStorage` has 189 INFERRED edges - model-reasoned connections that need verification._
- **Are the 185 inferred relationships involving `SearchResult` (e.g. with `KnowledgeGraphMemo0Storage` and `知识图谱Memo0存储适配器 V1.0 - Phase 7核心模块  实现知识图谱与memo0存储的深度集成，支持图谱持久化、同步和智能检索。  核心功能： 1`) actually correct?**
  _`SearchResult` has 185 INFERRED edges - model-reasoned connections that need verification._
- **Are the 165 inferred relationships involving `高级可视化模块  V2.6新增：策略回测可视化、知识图谱可视化、3D市场可视化` (e.g. with `AutoScaler` and `AutoRecovery`) actually correct?**
  _`高级可视化模块  V2.6新增：策略回测可视化、知识图谱可视化、3D市场可视化` has 165 INFERRED edges - model-reasoned connections that need verification._