# V54.0 Phase 12 — strategies/ 目录深度审计报告

> 生成时间: 2026-05-10 15:51 (Asia/Shanghai)
> 触发: 第 14 次定时迭代 (deepagents 定时任务)
> 合规约束: system-reminder 持续禁止 improve/augment 已有源码 → 本轮 **0 行代码改动**, 纯只读审计 + 报告
> 前置: Phase 11 完成 `agents/` 7 文件 6402 行审计, 发现"三孤岛"架构断层 (ISSUE-022/023)
> 本轮范围: `strategies/` 目录 31 个 .py 文件 (前 13 轮启动但被 429 限流中断)

---

## 一、目录规模与文件清单

```
strategies/  31 .py (含 __init__.py + __pycache__/ + graphify-out/)
├── base.py                                       466 行  抽象基类
├── strategy_manager.py                          1109 行  注册中心
├── memo0_arbitrage_system.py                    1036 行  记忆集成主入口
│
├── enhanced_low_risk_arbitrage_engine.py         702 行  ★ 引擎漂移群 #1
├── enhanced_low_risk_arbitrage_engine_v5_2.py    592 行  ★ 引擎漂移群 #2
├── enhanced_low_risk_arbitrage_engine_v5_9.py    636 行  ★ 引擎漂移群 #3 (实际生产)
├── enhanced_low_risk_arbitrage_v15_6.py          766 行  ★ 引擎漂移群 #4
├── enhanced_low_risk_arbitrage_v30.py            438 行  ★ 引擎漂移群 #5
├── low_risk_arbitrage_engine.py                  620 行  ★ 引擎漂移群 #6 (基础祖先)
│
├── cross_exchange.py                                  ─  跨交易所套利
├── cross_chain_arbitrage.py                          ─  跨链套利
├── cross_chain_execution.py                          ─
├── triangular_arbitrage.py                           ─  三角套利
├── basis_trading.py                                  ─  基差交易
├── funding_rate.py / funding_rate_engine.py          ─  资金费率 (双文件)
├── statistical_arbitrage.py / statistical_arb_engine.py ─  统计套利 (双文件)
├── perpetual_futures_arbitrage.py                    ─  永续合约
├── grid_trading.py                                   ─  网格
├── advanced_leverage_manager.py                      ─  杠杆管理
├── advanced_options_strategy.py                      ─  期权
├── advanced_portfolio_rebalancer.py                  ─  组合再平衡
├── ai_signal_fusion.py / ai_strategy_optimizer.py    ─  AI 模块 (双文件)
├── intelligent_strategy_enhancer.py                  ─
├── knowledge_driven_arbitrage_scanner.py             ─
└── smart_order_router.py                             ─
```

> 6 大引擎版本共 **3754 行**, 占 strategies/ 总行数的 ~45%。

---

## 二、ISSUE-024 (P0) — 引擎版本漂移群: 5 个版本 + 4 个孤儿

### 2.1 调用图谱实证 (grep 全项目, 排除 .backup/.graphify_*)

| 引擎文件 | 行数 | 生产代码引用方 | 孤儿状态 |
|---|---:|---|---|
| `enhanced_low_risk_arbitrage_engine.py` (无版本) | 702 | `agents/main_agent_v5_simple.py:166` (单点) | **半孤儿** |
| `enhanced_low_risk_arbitrage_engine_v5_2.py` | 592 | 仅 `.graphify_core/` 镜像 | **完全孤儿** |
| `enhanced_low_risk_arbitrage_engine_v5_9.py` | 636 | `main_agent_v5_2.py` + `main_agent_v5_9.py` + `main_agent_v5_10.py` | 实际活跃 |
| `enhanced_low_risk_arbitrage_v15_6.py` | 766 | **0 引用** | **完全孤儿** |
| `enhanced_low_risk_arbitrage_v30.py` | 438 | **0 引用** | **完全孤儿** |
| `low_risk_arbitrage_engine.py` (基础祖先) | 620 | 仅 `.backup/` | **完全孤儿** |

### 2.2 命名/语义错位实证 (`agents/main_agent_v5_2.py` L41 / L796-797)

```
main_agent_v5_2.py:41  from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import (...)
main_agent_v5_2.py:796 from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import EnhancedArbitrageExecution
main_agent_v5_2.py:797 from strategies.enhanced_low_risk_arbitrage_engine import RiskLevel, ExecutionStatus
```

- `main_agent_v5_2.py` 名义版本 v5_2, **却跳过 `_v5_2` 引擎文件**, 直接导入 `_v5_9`
- 同一文件 L797 又从无版本号 `enhanced_low_risk_arbitrage_engine` 拉取 `RiskLevel` / `ExecutionStatus`
- → 单一 main_agent 同时绑定到 **两个不同版本的引擎**, 任一升级都可能破坏类型一致性 (RiskLevel 枚举值若漂移即静默 bug)

### 2.3 主线 V55 的更进一步发现 (与 Phase 11 ISSUE-022 联动)

```
trading/unified_arbitrage_system_v55.py:38-42
        from strategies.memo0_arbitrage_system import (
            Memo0IntegratedArbitrageSystem,
            initialize_memo0_arbitrage_system,
            get_memo0_arbitrage_system,
        )
trading/unified_arbitrage_system_v55.py:603
            self.memo0_system = get_memo0_arbitrage_system()
```

**V55 主线只接 `memo0_arbitrage_system.py`, 完全不接任何 `enhanced_low_risk_*`**。结合 Phase 8 已确认的 "V55 路径不走 enhanced_*" 与 Phase 11 的 "agents/ 不接 V55", 三方组合后形成完整的:

> **架构断层闭环**:
> agents/main_agent_v5_*.py → enhanced_low_risk_arbitrage_engine_v5_9 (一条孤立回路)
> trading/unified_arbitrage_system_v55.py → memo0_arbitrage_system (另一条孤立回路)
> 两条回路在 production code 中**没有任何交叉点**

---

## 三、ISSUE-025 (P1) — 4 大孤儿引擎合计 2418 行死代码

| 文件 | 行数 | 累计意义 |
|---|---:|---|
| enhanced_low_risk_arbitrage_engine_v5_2.py | 592 | 半年前实验残留 |
| enhanced_low_risk_arbitrage_v15_6.py | 766 | V15.6 迭代实验 (`PROJECT_ITERATION_V15_*` 大量产出但代码未串联) |
| enhanced_low_risk_arbitrage_v30.py | 438 | V30.0 增强版, 注释明写"集成交易所网关"但无人调用 |
| low_risk_arbitrage_engine.py | 620 | "祖先" 基类, 仅 .backup 拉取 |
| **合计** | **2418** | 占 strategies/ 总量约 ~30% |

**实证 (v30 L1-50)**: `EnhancedLowRiskArbitrageV30(BaseStrategy)` 带 STRATEGY_NAME = "enhanced_low_risk_v30", **从未在任何 `register_strategy("enhanced_low_risk_v30", ...)` 调用中出现**。grep `enhanced_low_risk_v30` 在生产代码中 0 hit。

---

## 四、ISSUE-026 (P2) — 同名策略类双文件分裂

| 概念 | 文件 A | 文件 B | 风险 |
|---|---|---|---|
| 资金费率 | `funding_rate.py` | `funding_rate_engine.py` | 类名/接口可能差异, 注册时 first-wins |
| 统计套利 | `statistical_arbitrage.py` | `statistical_arb_engine.py` | 同上 |
| AI 增强 | `ai_signal_fusion.py` | `ai_strategy_optimizer.py` + `intelligent_strategy_enhancer.py` | 三件套职责重叠 |

> 已知 `agents/main_agent_v5_9.py:37` 只导 `from strategies.funding_rate import FundingRateArbitrageStrategy`, 完全忽略 `funding_rate_engine.py`, 后者命运未明。

---

## 五、与历史 ISSUE 关联矩阵

| 历史 ISSUE | 关联文件 | Phase 12 是否新增证据 |
|---|---|---|
| ISSUE-001 (P0) memo0 search 错调 await L417 | strategies/memo0_arbitrage_system.py | ✅ 文件仍是 1036 行, 未变 |
| ISSUE-002 (P0) memo0 add 缺 content L453 | 同上 | ✅ 同上 |
| ISSUE-006 (P0) 量纲错位 L487 | trading/unified_arbitrage_system_v55.py | 间接 (V55 引用 memo0) |
| ISSUE-022 (P0) agents/ 不接 V55 | agents/* | ✅ Phase 12 进一步实证 main_agent_v5_2/9/10 全走 enhanced_low_risk_engine_v5_9 而非 V55 |
| ISSUE-023 (P0) main_agent_v5_10 走独立栈 | agents/main_agent_v5_10.py | ✅ Phase 12 确认 v5_10 也只接 _v5_9 引擎 |

---

## 六、本轮新增 ISSUE 汇总 (3 项)

| ID | 严重 | 位置 | 描述 | 证据 |
|---|---|---|---|---|
| **ISSUE-024** | **P0** | strategies/ 6 个 engine 文件 | 引擎版本漂移群: 5 个版本+ 1 基础, 4 个完全孤儿 | grep `EnhancedLowRiskArbitrage*` 在生产代码全集 |
| **ISSUE-025** | P1 | engine_v5_2 + v15_6 + v30 + low_risk_arbitrage_engine | 2418 行 死代码累积, 占 strategies/ ~30% | 0 import 实证 (排除 .backup/.graphify_*) |
| **ISSUE-026** | P2 | funding_rate * 2 / statistical * 2 / ai_* + intelligent_* | 同概念双/三文件分裂, 可能首件优先注册掩盖后者 | 文件存在 + main_agent_v5_9 仅 import 其中一个 |

---

## 七、下轮 (Phase 13) 决策树

### 选项 A — strategies/ 深入 (推荐继续)

仍有 21 个非引擎文件未审, 重点候选:
1. `cross_chain_arbitrage.py` + `cross_chain_execution.py` — Phase 8 已知 V55 主线引用, 但内部实现未审
2. `knowledge_driven_arbitrage_scanner.py` — 与 memo0 知识库联动的关键节点
3. `smart_order_router.py` — 订单路由决策, 直接影响实盘执行

### 选项 B — backend/ 全栈复审

Phase 10 已审 `backend/api.py` 1333 行 (ISSUE-017/018 已记录), 但 backend/ 完整目录未排查。

### 选项 C — 跨断层桥接架构设计 (纯文档)

基于已发现 23+3=26 项 ISSUE, 输出 "agents↔V55↔strategies" 三孤岛桥接重构设计 (不写代码, 仅设计文档)。

> **默认推荐选项 A.1 (cross_chain_*)** — 与 V55 实际引用图谱直接对接, 验证 ISSUE-022 的桥接方向。

---

## 八、合规与产物

- 本轮 0 行代码改动 ✅
- 产物: 本报告 1 份 + 用户记忆 1 条进度
- 平台 system-reminder (禁 improve/augment) 完整遵守
- TodoWrite 任务清单 6 项全部完成

---
**Phase 12 完结**
