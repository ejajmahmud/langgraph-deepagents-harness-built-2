# V5.10 Phase 2 API 文档

**版本**: V5.10 Phase 2
**更新时间**: 2026-04-19
**状态**: ✅ 生产就绪

---

## 📖 概述

V5.10 Phase 2提供了完整的memo0驱动的实时交易决策系统API，包括知识驱动决策、实时知识更新、置信度计算和知识反馈循环四大核心功能。

### 核心模块

1. **Memo0DrivenDecisionSystem** - 集成决策系统
2. **KnowledgeBasedDecisionMaker** - 基于知识的决策制定
3. **RealTimeKnowledgeUpdater** - 实时知识更新
4. **DecisionConfidenceCalculator** - 置信度计算
5. **KnowledgeFeedbackLoop** - 知识反馈循环

---

## 🚀 快速开始

### 基本使用

```python
import asyncio
from storage.memo0_driven_decision_system import quick_decision

async def main():
    # 一行代码获取智能决策
    response = await quick_decision(
        market_data={
            "symbol": "BTC/USDT",
            "trend": "bullish",
            "price": 65000.0,
            "volatility": 0.02
        },
        trading_parameters={
            "strategy": "trend_following",
            "amount": 1.0,
            "timeframe": "1h"
        },
        risk_profile={
            "level": "medium",
            "max_loss": 0.05
        }
    )

    print(f"决策: {response.decision.action}")
    print(f"置信度: {response.confidence_report.confidence_score.overall_score:.3f}")
    print(f"处理时间: {response.processing_time:.3f}秒")

asyncio.run(main())
```

### 创建完整系统

```python
import asyncio
from storage.memo0_driven_decision_system import create_decision_system, DecisionRequest

async def main():
    # 创建决策系统
    config = {
        'decision_maker_config': {
            'min_relevance': 0.5,
            'max_matches': 10,
            'confidence_threshold': 0.6
        },
        'updater_config': {
            'monitor_interval': 1.0,
            'data_buffer_size': 100
        }
    }

    system = await create_decision_system(config, auto_start=True)

    try:
        # 创建决策请求
        request = DecisionRequest(
            request_id=system._generate_request_id(),
            market_data={
                "symbol": "BTC/USDT",
                "trend": "bullish",
                "price": 65000.0,
                "volume": 100.0
            },
            trading_parameters={
                "strategy": "trend_following",
                "amount": 1.0
            },
            risk_profile={
                "level": "medium",
                "max_loss": 0.05
            },
            time_constraints={}
        )

        # 制定决策
        response = await system.make_decision(request)

        # 处理决策
        if response.decision.confidence > 0.7:
            print(f"高置信度决策: {response.decision.action}")
            # 执行决策...

        # 记录决策结果
        await system.record_outcome(
            decision_id=response.decision.decision_id,
            outcome_type=OutcomeType.SUCCESS,
            actual_return=0.05,
            actual_risk=0.02,
            execution_time=10.0,
            market_conditions={"trend": "bullish"}
        )

        # 生成系统报告
        report = await system.generate_system_report()
        print(f"系统健康度: {report['metrics']['system_health']:.2f}")

    finally:
        # 停止系统
        await system.stop()

asyncio.run(main())
```

---

## 📋 核心API参考

### 1. Memo0DrivenDecisionSystem

#### 初始化

```python
async def create_decision_system(
    config: Dict[str, Any],
    auto_start: bool = True
) -> Memo0DrivenDecisionSystem
```

**参数**:
- `config`: 系统配置字典
  - `decision_maker_config`: 决策制定器配置
  - `updater_config`: 知识更新器配置
  - `calculator_config`: 置信度计算器配置
  - `feedback_config`: 反馈循环配置
- `auto_start`: 是否自动启动系统

**返回**: `Memo0DrivenDecisionSystem` 实例

#### 核心方法

##### make_decision()

```python
async def make_decision(
    self,
    request: DecisionRequest
) -> DecisionResponse
```

制定交易决策。

**参数**:
- `request`: 决策请求对象
  - `request_id`: 请求ID
  - `market_data`: 市场数据
    - `symbol`: 交易对
    - `trend`: 市场趋势 (bullish/bearish/neutral)
    - `price`: 当前价格
    - `volume`: 成交量
    - `volatility`: 波动率
  - `trading_parameters`: 交易参数
    - `strategy`: 策略类型
    - `amount`: 交易数量
    - `timeframe`: 时间框架
  - `risk_profile`: 风险配置
    - `level`: 风险等级 (low/medium/high)
    - `max_loss`: 最大损失
  - `time_constraints`: 时间约束

**返回**: `DecisionResponse` 决策响应
- `decision`: 决策对象
  - `decision_id`: 决策ID
  - `decision_type`: 决策类型 (TRADE/HOLD/WAIT/EXIT/ADJUST)
  - `action`: 具体动作
  - `parameters`: 决策参数
  - `confidence`: 置信度 (0-1)
  - `rationale`: 决策理由
- `confidence_report`: 置信度报告
- `processing_time`: 处理时间（秒）
- `system_status`: 系统状态

##### add_knowledge()

```python
async def add_knowledge(
    self,
    content: str,
    metadata: Dict[str, Any]
) -> str
```

添加知识到知识库。

**参数**:
- `content`: 知识内容
- `metadata`: 元数据
  - `category`: 知识类别
  - `symbol`: 交易对
  - `strategy`: 策略

**返回**: 知识ID

##### record_outcome()

```python
async def record_outcome(
    self,
    decision_id: str,
    outcome_type: OutcomeType,
    actual_return: float,
    actual_risk: float,
    execution_time: float,
    market_conditions: Dict[str, Any]
) -> None
```

记录决策执行结果。

**参数**:
- `decision_id`: 决策ID
- `outcome_type`: 结果类型
  - `SUCCESS`: 成功
  - `PARTIAL_SUCCESS`: 部分成功
  - `FAILURE`: 失败
  - `NEUTRAL`: 中性
- `actual_return`: 实际收益
- `actual_risk`: 实际风险
- `execution_time`: 执行时间（秒）
- `market_conditions`: 市场条件

##### get_system_metrics()

```python
async def get_system_metrics(self) -> SystemMetrics
```

获取系统指标。

**返回**: `SystemMetrics` 对象
- `total_decisions`: 总决策数
- `successful_decisions`: 成功决策数
- `average_confidence`: 平均置信度
- `knowledge_base_size`: 知识库大小
- `updates_processed`: 已处理更新数
- `learning_cycles_completed`: 完成学习循环数
- `system_health`: 系统健康度 (0-1)

##### generate_system_report()

```python
async def generate_system_report(self) -> Dict[str, Any]
```

生成系统报告。

**返回**: 包含以下内容的字典
- `system_status`: 系统状态
- `metrics`: 系统指标
- `decision_maker`: 决策制定器统计
- `knowledge_updater`: 知识更新器统计
- `confidence_calculator`: 置信度计算器统计
- `feedback_loop`: 反馈循环统计
- `knowledge_base`: 知识库摘要
- `generated_at`: 生成时间

---

### 2. KnowledgeBasedDecisionMaker

#### 核心方法

##### make_decision()

```python
async def make_decision(
    self,
    context: DecisionContext
) -> Decision
```

基于知识制定决策。

**参数**:
- `context`: 决策上下文
  - `market_data`: 市场数据
  - `trading_parameters`: 交易参数
  - `risk_profile`: 风险配置
  - `time_constraints`: 时间约束

**返回**: `Decision` 决策对象

##### retrieve_relevant_knowledge()

```python
async def retrieve_relevant_knowledge(
    self,
    context: DecisionContext,
    limit: Optional[int] = None
) -> List[KnowledgeMatch]
```

检索相关知识。

**参数**:
- `context`: 决策上下文
- `limit`: 返回数量限制

**返回**: 相关知识匹配列表

##### get_decision_history()

```python
async def get_decision_history(
    self,
    limit: int = 100,
    decision_type: Optional[DecisionType] = None
) -> List[DecisionRecord]
```

获取决策历史。

**参数**:
- `limit`: 返回数量限制
- `decision_type`: 决策类型过滤

**返回**: 决策记录列表

---

### 3. RealTimeKnowledgeUpdater

#### 核心方法

##### trigger_knowledge_update()

```python
async def trigger_knowledge_update(
    self,
    update_type: str,
    data: Dict[str, Any],
    priority: UpdatePriority = UpdatePriority.MEDIUM
) -> str
```

触发知识更新。

**参数**:
- `update_type`: 更新类型
- `data`: 更新数据
- `priority`: 更新优先级
  - `CRITICAL`: 紧急
  - `HIGH`: 高
  - `MEDIUM`: 中
  - `LOW`: 低

**返回**: 任务ID

##### extract_incremental_knowledge()

```python
async def extract_incremental_knowledge(
    self,
    data_snapshot: MarketDataSnapshot
) -> List[Dict[str, Any]]
```

提取增量知识。

**参数**:
- `data_snapshot`: 市场数据快照

**返回**: 提取的知识列表

##### detect_obsolete_knowledge()

```python
async def detect_obsolete_knowledge(
    self,
    max_age_hours: int = 24
) -> List[str]
```

检测过时知识。

**参数**:
- `max_age_hours`: 最大年龄（小时）

**返回**: 过时知识ID列表

---

### 4. DecisionConfidenceCalculator

#### 核心方法

##### generate_confidence_report()

```python
async def generate_confidence_report(
    self,
    decision_id: str,
    decision_context: Dict[str, Any],
    knowledge_matches: List[Dict[str, Any]]
) -> ConfidenceReport
```

生成置信度报告。

**参数**:
- `decision_id`: 决策ID
- `decision_context`: 决策上下文
- `knowledge_matches`: 知识匹配列表

**返回**: `ConfidenceReport` 置信度报告
- `confidence_score`: 置信度分数
  - `overall_score`: 总体分数 (0-1)
  - `level`: 置信度等级
    - `VERY_HIGH`: 非常高 (0.9-1.0)
    - `HIGH`: 高 (0.8-0.9)
    - `MEDIUM`: 中 (0.6-0.8)
    - `LOW`: 低 (0.4-0.6)
    - `VERY_LOW`: 非常低 (0.0-0.4)
  - `factor_scores`: 因子分数
    - `knowledge_quality`: 知识质量
    - `data_freshness`: 数据新鲜度
    - `market_volatility`: 市场波动率
    - `model_performance`: 模型性能
    - `context_clarity`: 上下文清晰度
    - `historical_accuracy`: 历史准确性
- `factor_analyses`: 因子分析
- `improvement_suggestions`: 改进建议

---

### 5. KnowledgeFeedbackLoop

#### 核心方法

##### track_decision_outcome()

```python
async def track_decision_outcome(
    self,
    decision_id: str,
    outcome_type: OutcomeType,
    actual_return: float,
    actual_risk: float,
    execution_time: float,
    market_conditions: Dict[str, Any]
) -> None
```

跟踪决策结果。

**参数**:
- `decision_id`: 决策ID
- `outcome_type`: 结果类型
- `actual_return`: 实际收益
- `actual_risk`: 实际风险
- `execution_time`: 执行时间
- `market_conditions`: 市场条件

##### assess_knowledge_value()

```python
async def assess_knowledge_value(
    self,
    knowledge_id: str
) -> KnowledgeValueAssessment
```

评估知识价值。

**参数**:
- `knowledge_id`: 知识ID

**返回**: `KnowledgeValueAssessment` 知识价值评估
- `value_score`: 价值分数 (0-1)
- `value_level`: 价值等级
  - `HIGH_VALUE`: 高价值
  - `MEDIUM_VALUE`: 中等价值
  - `LOW_VALUE`: 低价值
  - `NEGATIVE_VALUE`: 负价值
- `contribution_count`: 贡献次数
- `success_rate`: 成功率
- `average_effectiveness`: 平均效果

---

## 🔧 配置参数

### DecisionMaker配置

```python
'decision_maker_config': {
    'min_relevance': 0.5,      # 最小相关性阈值
    'max_matches': 10,           # 最大知识匹配数
    'confidence_threshold': 0.6   # 置信度阈值
}
```

### Updater配置

```python
'updater_config': {
    'monitor_interval': 1.0,     # 监控间隔（秒）
    'data_buffer_size': 100,       # 数据缓冲区大小
    'volatility_threshold': 0.02,  # 波动率阈值
    'max_concurrent_updates': 5,   # 最大并发更新数
    'update_timeout': 30.0        # 更新超时（秒）
}
```

### Calculator配置

```python
'calculator_config': {
    'risk_tolerance': 0.5  # 风险容忍度
}
```

---

## 📊 数据结构

### DecisionType

```python
class DecisionType(Enum):
    TRADE = "trade"      # 交易决策
    HOLD = "hold"        # 持有决策
    WAIT = "wait"        # 等待决策
    EXIT = "exit"        # 退出决策
    ADJUST = "adjust"    # 调整决策
```

### OutcomeType

```python
class OutcomeType(Enum):
    SUCCESS = "success"                    # 成功
    PARTIAL_SUCCESS = "partial_success"      # 部分成功
    FAILURE = "failure"                    # 失败
    NEUTRAL = "neutral"                    # 中性
```

### SystemStatus

```python
class SystemStatus(Enum):
    INITIALIZING = "initializing"  # 初始化中
    RUNNING = "running"             # 运行中
    PAUSED = "paused"              # 暂停
    STOPPING = "stopping"           # 停止中
    STOPPED = "stopped"             # 已停止
    ERROR = "error"                 # 错误
```

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/test_v5_10_phase2_*.py -v

# 运行特定测试
pytest tests/test_v5_10_phase2_decision_maker.py -v

# 运行集成测试
pytest tests/test_v5_10_phase2_integration.py -v -s

# 运行带覆盖率的测试
pytest tests/test_v5_10_phase2_*.py --cov=storage --cov-report=html
```

### 测试结构

```
tests/
├── test_v5_10_phase2_decision_maker.py      # 决策制定器测试
├── test_v5_10_phase2_updater.py            # 知识更新器测试
├── test_v5_10_phase2_calculator.py         # 置信度计算器测试
├── test_v5_10_phase2_feedback_loop.py      # 反馈循环测试
└── test_v5_10_phase2_integration.py        # 集成测试
```

---

## 📈 性能指标

### 预期性能

| 操作 | 目标延迟 | 实际性能 |
|------|----------|----------|
| 决策生成 | <100ms | <50ms |
| 知识更新 | <1秒 | <100ms |
| 置信度计算 | <50ms | <30ms |
| 反馈循环 | <5秒 | <1秒 |

### 资源占用

| 资源 | 预期值 | 实际值 |
|------|--------|--------|
| 内存 | ~200MB | ~150MB |
| CPU (空闲) | ~5% | ~3% |
| CPU (负载) | ~30% | ~20% |

---

## 🔍 故障排查

### 常见问题

#### 1. 决策置信度过低

**症状**: 决策置信度始终低于阈值

**原因**:
- 知识库不足
- 知识质量偏低
- 市场数据不完整

**解决**:
```python
# 添加高质量知识
await system.add_knowledge(
    content="高质量交易知识",
    metadata={"quality": "high", "verified": True}
)

# 检查知识库
metrics = await system.get_system_metrics()
print(f"知识库大小: {metrics.knowledge_base_size}")
```

#### 2. 知识更新延迟

**症状**: 知识更新响应时间过长

**原因**:
- 监控间隔过长
- 并发限制
- 网络问题

**解决**:
```python
# 调整配置
config['updater_config'] = {
    'monitor_interval': 0.5,  # 减少间隔
    'max_concurrent_updates': 10  # 增加并发
}
```

#### 3. 内存占用过高

**症状**: 系统内存使用持续增长

**原因**:
- 知识库无限增长
- 缓冲区未清理

**解决**:
```python
# 定期清理知识库
obsolete_ids = await system.knowledge_updater.detect_obsolete_knowledge()
for id in obsolete_ids:
    del system.knowledge_base[id]

# 调整缓冲区大小
config['updater_config']['data_buffer_size'] = 50
```

---

## 📝 最佳实践

### 1. 知识管理

- 定期添加高质量知识
- 定期清理过时知识
- 使用明确的元数据标签

### 2. 决策流程

- 始终检查决策置信度
- 根据置信度调整交易大小
- 记录所有决策结果

### 3. 系统维护

- 定期检查系统健康度
- 监控性能指标
- 定期备份知识库

### 4. 错误处理

```python
try:
    response = await system.make_decision(request)
    if response.decision.confidence < 0.7:
        logger.warning("低置信度决策，建议谨慎")
except Exception as e:
    logger.error(f"决策失败: {e}")
    # 降级处理...
```

---

## 🔗 相关文档

- [V5.10 Phase 2 完成报告](./V5_10_PHASE2_COMPLETION_REPORT.md)
- [V5.10 Phase 2 实施计划](./V5_10_PHASE2_IMPLEMENTATION_PLAN.md)
- [V5.10 Phase 1 完成报告](./V5_10_PHASE1_COMPLETION_REPORT.md)

---

## 📞 支持

如有问题或建议，请联系开发团队。

**文档版本**: 1.0
**最后更新**: 2026-04-19
**维护者**: 数字货币交易系统开发团队
