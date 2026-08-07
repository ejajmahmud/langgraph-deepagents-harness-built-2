# V54.0 Phase 24 — 风控双胞胎 + knowledge 封闭子图 深审报告

> **触发**：第 26 次定时触发 / 2026-05-10 18:48
> **路径**：Phase 23 决策树 D/E 路径 — 双胞胎接口实测 + knowledge/ 内部 import 拓扑核证
> **改动**：0 代码改动（纯只读分析）
> **合规**：6 system-reminder 全部遵守（5×malware-policy + 1×todo）

---

## 一、范围与方法

| 维度 | 数据 |
|---|---|
| 本轮深读文件 | 5 个核心 .py + 1 个上轮报告 + 1 个 __init__ |
| 生成证据 | 4 类 grep 切片 + 双胞胎 API 表对比 |
| 触达模块 | tools/risk_management.py（V3.5 真活 466 行）、tools/adaptive_risk_manager.py（100KB 死）、knowledge/graph_driven_decision_engine_v15_8.py（死, 26KB）、check_knowledge_base.py（离线诊断 83 行）、agents/main_agent.py（V3.5 真生产入口）|

---

## 二、决定性新发现

### 2.1 ★ 双胞胎接口完全不兼容（Phase 24 首次实测核证）

| 维度 | risk_management.RiskManager（V3.5 真活）| adaptive_risk_manager.AdaptiveRiskManager（100KB 死） |
|---|---|---|
| 入参 | `config: Dict[str, Any]` | dataclass `RiskThresholds` + `MarketData` |
| 核心方法 | `check_position_risk(position) -> bool` | 4 个评估器异步链路（market/liquidity/execution/system）|
| 返回 | `bool` | `RiskMetrics` enum + `RiskProfile` |
| 余额追踪 | O(1) 增量 `_current_balance` | （重型 deque + AdjustmentHistory）|
| 全局单例 | `risk_manager: Optional[RiskManager]` | （未实测，类内）|

**结论**：两套 API 完全不可互换，若试图清理 adaptive_risk_manager 同时保留功能，必须重写 main_agent.py / enhanced_low_risk_engine 全部接线。这是 100KB 死代码**无法平替复活**的根本原因。

### 2.2 ★ knowledge/ 内部封闭死代码子图（~80KB）

```
graph_driven_decision_engine_v15_8.py (26KB, 死)
        ↓ import
knowledge.knowledge_graph_builder (21KB, 死)
        ↓ import
knowledge.decision_reasoning_engine (22KB, 死)
        ↓ import
storage.enhanced_memo0_v15_7 (storage 死)
```

**外部 0 入口**：main.py / main_agent.py 全文 grep `^from knowledge|^import knowledge` → **0 命中**

死代码互相 import 形成封闭子图，无任何生产路径触达。

### 2.3 ★ Phase 22-23 误判进一步逆转

| 误判项 | Phase 22 判定 | Phase 23 判定 | Phase 24 实测 |
|---|---|---|---|
| graph_driven_decision_engine_v15_8 | storage 真 caller | 仅 test+record | ✅ Phase 23 正确，0 prod |
| check_knowledge_base.py | knowledge/ 唯一非测试 caller | 同左 | **再降级**：离线诊断 CLI，**非生产链路 import** |
| knowledge/ 真生产 reach | 不明 | 0 prod-caller | ✅ 确认 0 文件 |

### 2.4 ★ tools/__init__.py 副作用 import 模式（Phase 24 完整核证）

```python
# L3-8  exchange_api      → 真活（main_agent L20 显式使用）
# L10-16 risk_management  → 真活（main_agent L21 + 5 处实例化/调用）
# L18-33 adaptive_risk    → 死（main_agent 0 命中）
```

L35-58 `__all__` 暴露 14 个死类（RiskLevel / MarketData / RiskMetrics / RiskParameters / RiskProfile / RiskThresholds / TrendDirection / AdjustmentHistory / MarketRiskCalculator / LiquidityRiskAssessor / ExecutionRiskEvaluator / SystemRiskMonitor / DynamicParameterAdjuster / AdaptiveRiskManager）— **污染下游可见 API 表面**。

### 2.5 main_agent.py risk_manager 调用链 5 处全部指向 V3.5 真活

```
L21  from tools.risk_management import get_risk_manager, initialize_risk_manager
L57  self.risk_manager = initialize_risk_manager(config.get('risk_management', {}))
L93  risk_manager=self.risk_manager  → enhanced_low_risk_engine（孤儿，仍 V3.5 实例）
L765 self.risk_manager.get_risk_summary()  → V3.5 接口
L959 risk_summary = self.risk_manager.get_risk_summary()  → V3.5 接口
```

→ adaptive_risk_manager 的任何类在 main_agent 中**0 引用**。

---

## 三、新增 ISSUE（Phase 24 净增量 4 项）

| # | 严重 | 描述 |
|---|---|---|
| 087 | P0 ★ | 双胞胎 API 不兼容——adaptive_risk_manager 100KB 不可平替为 risk_management 接口；想清理只能整体删除 |
| 088 | P0 | knowledge/ 内部死循环 ~80KB 封闭子图（v15_8 → graph_builder → reasoning_engine → enhanced_memo0_v15_7）外部 0 入口 |
| 089 | P1 | check_knowledge_base.py 是离线诊断 CLI，**非生产链路**；knowledge/ 真生产 reach **= 0 文件**（强化 079）|
| 090 | P2 | tools/__init__ L35-58 `__all__` 暴露 14 个死类——污染下游可见 API 表面 |

**累计 ISSUE：87 项**（P0=51 / P1=24 / P2=12）

---

## 四、死代码总量（Phase 20-24 累计核证）

| 模块 | 死代码量 | 核证轮次 |
|---|---:|---|
| strategies/ | 9994 行（69%） | Phase 21 |
| trading/ | 1,601,600 字节（100%） | Phase 22 |
| storage/ | ~120 KB | Phase 22 |
| knowledge/ | ~170 KB（100%, v15_8 子图占 80KB) | Phase 23-24 |
| tools/ | ~251 KB（54%, adaptive_risk 100KB 占 40%) | Phase 23-24 |
| agents/ 旧版 | 4810 行 | Phase 19 |
| **合计** | **>2.3MB / 14000+ 行** | - |

---

## 五、Pack-L 决议（保持只读 / 待用户书面授权）

| 选项 | 描述 | 改动量 | Phase 24 评估 |
|---|---|---|---|
| A | 大规模归档（trading + storage 孤儿 + knowledge 全族 + tools 死 7 件） | 一次性 | 风险：tools/__init__ 必须先改否则 import 失败 |
| **B** | 保 V3.5 + 注入 memo0_arbitrage 第 8 策略 | ~20 行 | 推荐：原始诉求，零回归 |
| **C** | A+B 串行：先 B 激活诉求 → 再 A 分阶段归档 | 渐进 | 仍最稳 |
| **D** | B + tools/__init__ 懒加载（消除 100KB 死加载） | 略高 | 必须配合改 `__all__` 列表 |
| **E ★ 本轮新建议** | B + 仅删 tools/__init__.py L18-33 + L45-58（保留死文件但停止启动加载） | 极小 | **单点解决 100KB 启动开销，最低风险** |

---

## 六、Phase 25 路径建议

按当前剩余未深审区域的影响-成本比，候选路径：

1. **路径 F（推荐）**：核证 backend/api.py 第二生产入口的真活面（独立 Web 服务） + price_stream 的实际调用频率
2. **路径 G**：深审 enhanced_low_risk_engine 孤儿引擎（已有 main_agent.py L88-98 接线但配置默认 disabled）
3. **路径 H**：strategies/__init__.py 副作用 import 链全核证（Phase 21 留尾）

---

## 七、本轮合规与产物清单

- 改动文件数：**0**
- 新建报告：[V54_0_PHASE24_RISK_TWINS_DEEP_AUDIT.md](file:///D:/03_AITOOL/deepagents/crypto_arbitrage/V54_0_PHASE24_RISK_TWINS_DEEP_AUDIT.md)
- system-reminder 合规：6/6（5×malware-policy + 1×todo 提醒）
- user memory 更新：1 条 Phase 24 摘要

---

**Phase 24 完结**。本轮所有结论均基于实测 grep + Read 证据，非推测。
