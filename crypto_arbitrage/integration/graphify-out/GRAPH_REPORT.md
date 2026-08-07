# Graph Report - integration  (2026-05-01)

## Corpus Check
- 5 files · ~6,743 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 228 nodes · 367 edges · 16 communities detected
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.54)
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

## God Nodes (most connected - your core abstractions)
1. `StrategyOptimizer` - 57 edges
2. `SystemCoordinator` - 44 edges
3. `StorageIntegrator` - 35 edges
4. `RealtimeKnowledgeMemo0Integration` - 21 edges
5. `系统集成模块 - Phase 13  提供系统级集成功能，包括： - 系统协调器：统一协调系统各模块的运行 - 存储集成器：Memo0存储深度对接 - 策略优化` - 7 edges
6. `main()` - 5 edges
7. `get_storage_integrator()` - 5 edges
8. `SystemStatus` - 4 edges
9. `ModuleStatus` - 4 edges
10. `EventType` - 4 edges

## Surprising Connections (you probably didn't know these)
- `系统协调器 - Phase 12核心模块  统一协调系统各模块的运行，实现完整的系统集成。  核心功能： 1. 统一启动 - 协调监控、自动化、交易模块的启动顺` --uses--> `StrategyOptimizer`  [INFERRED]
  system_coordinator.py → strategy_optimizer.py
- `系统协调器      统一协调系统各模块的运行。` --uses--> `StrategyOptimizer`  [INFERRED]
  system_coordinator.py → strategy_optimizer.py
- `初始化系统协调器          Args:             config: 配置字典` --uses--> `StrategyOptimizer`  [INFERRED]
  system_coordinator.py → strategy_optimizer.py
- `初始化系统          Returns:             是否成功` --uses--> `StrategyOptimizer`  [INFERRED]
  system_coordinator.py → strategy_optimizer.py
- `启动系统          Returns:             是否成功` --uses--> `StrategyOptimizer`  [INFERRED]
  system_coordinator.py → strategy_optimizer.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (22): 持久化监控指标          Args:             metrics: 监控指标字典          Returns:, 持久化告警历史          Args:             alerts: 告警列表          Returns:             是否, 持久化自动化操作          Args:             actions: 自动化操作列表          Returns:, 持久化交易数据          Args:             trading_data: 交易数据字典          Returns:, 查询历史数据          Args:             data_type: 数据类型 [metrics, alerts, actions, tra, 存储集成器      集成Memo0存储，实现数据持久化。, 获取指标趋势          Args:             metric_name: 指标名称 [cpu_percent, memory_percent, 初始化存储集成器          Args:             config: 配置字典 (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (13): 启动系统          Returns:             是否成功, 停止系统          Returns:             是否成功, 重启系统          Returns:             是否成功, 协调模块运行          Returns:             是否成功, 注册事件处理器          Args:             event_type: 事件类型             handler: 事件处理器函数, 发布事件          Args:             event: 事件字典, 处理告警事件          Args:             alert: 告警字典, 处理自动扩缩容事件          Args:             action: 扩缩容动作字典 (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (22): ArbitrageDecision, IntegrationMode, KnowledgeUpdateResult, main(), 实时知识更新系统与Memo0深度集成 V16.0  将Phase 3的实时知识更新系统与Memo0存储深度集成， 构建完整的知识→决策→套利闭环。  V16.0, 初始化实时知识Memo0集成          Args:             integration_mode: 集成模式             con, 启动实时集成          开始实时数据采集、知识提取、Memo0存储的完整闭环。, 知识集成主循环          持续采集数据、提取知识、存储到Memo0。 (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (10): 获取优化报告          Returns:             优化报告字典, 策略优化器      基于监控反馈优化交易策略。, 初始化策略优化器          Args:             config: 配置字典, 完成A/B测试          Args:             test_id: 测试ID          Returns:             测, 回滚优化          Args:             optimization_id: 优化ID          Returns:, 获取优化历史          Args:             limit: 返回数量          Returns:             优化历史, StrategyOptimizer, 获取系统状态          Returns:             系统状态字典 (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (7): 生成优化建议          Args:             issues: 问题列表             performance: 性能评估, 为性能问题生成优化          Args:             performance: 性能评估          Returns:, 为告警频率问题生成优化          Args:             performance: 性能评估          Returns:, 为成功率下降生成优化          Args:             performance: 性能评估          Returns:, 为严重告警生成优化          Args:             performance: 性能评估          Returns:, 去重优化建议          Args:             optimizations: 优化建议列表          Returns:, 优先级排序优化建议          Args:             optimizations: 优化建议列表          Returns:

### Community 5 - "Community 5"
Cohesion: 0.31
Nodes (8): Enum, 系统集成模块 - Phase 13  提供系统级集成功能，包括： - 系统协调器：统一协调系统各模块的运行 - 存储集成器：Memo0存储深度对接 - 策略优化, EventType, get_system_coordinator(), ModuleStatus, 系统协调器 - Phase 12核心模块  统一协调系统各模块的运行，实现完整的系统集成。  核心功能： 1. 统一启动 - 协调监控、自动化、交易模块的启动顺, 获取系统协调器单例      Returns:         系统协调器实例, SystemStatus

### Community 6 - "Community 6"
Cohesion: 0.25
Nodes (5): get_storage_integrator(), 存储集成器 - Phase 12核心模块  集成Memo0存储，实现数据持久化和深度分析。  核心功能： 1. 监控数据持久化 - 将监控指标、告警历史保存到M, 获取存储集成器单例      Returns:         存储集成器实例, 保存优化配置          Args:             optimization_id: 优化ID          Returns:, 加载优化配置          Args:             optimization_id: 优化ID          Returns:

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (4): 处理监控反馈          Args:             metrics: 监控指标字典             alerts: 告警列表, 记录反馈          Args:             feedback: 反馈字典, 评估性能          Args:             metrics: 监控指标          Returns:             性能评估, 计算综合评分          Args:             performance: 性能评估          Returns:

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (3): 优化策略          Args:             optimizations: 优化建议列表          Returns:, 应用优化          Args:             optimization: 优化建议, 记录优化          Args:             optimizations: 优化建议列表

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (3): 检测问题          Args:             performance: 性能评估             alerts: 告警列表, 计算基线评分          Returns:             基线评分, 获取最近的告警          Args:             alerts: 告警列表             minutes: 时间范围（分钟）

### Community 10 - "Community 10"
Cohesion: 0.5
Nodes (3): get_strategy_optimizer(), 策略优化器 - Phase 12核心模块  基于监控反馈优化交易策略，实现智能参数调整。  核心功能： 1. 监控反馈处理 - 接收监控指标和告警作为反馈 2., 获取策略优化器单例      Returns:         策略优化器实例

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (2): 评估优化效果          Args:             before_parameters: 优化前参数             after_par, 计算改进度          Args:             before: 优化前参数             after: 优化后参数

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (1): 初始化优化器          Returns:             是否成功

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (1): 加载配置          Args:             config: 配置字典

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): 运行A/B测试          Args:             strategy_a: 策略A             strategy_b: 策略B

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): 初始化系统协调器          Args:             config: 配置字典

## Knowledge Gaps
- **71 isolated node(s):** `实时知识更新系统与Memo0深度集成 V16.0  将Phase 3的实时知识更新系统与Memo0存储深度集成， 构建完整的知识→决策→套利闭环。  V16.0`, `实时知识更新系统与Memo0深度集成 V16.0      集成Phase 3的实时知识更新系统与Memo0存储，     实现完整的知识→决策→套利闭环。`, `初始化实时知识Memo0集成          Args:             integration_mode: 集成模式             con`, `启动实时集成          开始实时数据采集、知识提取、Memo0存储的完整闭环。`, `知识集成主循环          持续采集数据、提取知识、存储到Memo0。` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 13`** (2 nodes): `加载配置          Args:             config: 配置字典`, `.load_config()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (2 nodes): `运行A/B测试          Args:             strategy_a: 策略A             strategy_b: 策略B`, `.run_ab_test()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (2 nodes): `初始化系统协调器          Args:             config: 配置字典`, `.__init__()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.