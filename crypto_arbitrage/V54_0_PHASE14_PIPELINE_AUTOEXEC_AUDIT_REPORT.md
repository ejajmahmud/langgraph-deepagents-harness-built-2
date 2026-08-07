# Phase 14 审计报告：trading/ 生产链路 + 版本号通胀

> **触发**：第 16 次定时迭代（2026-05-10 16:13）
> **路径**：Phase 13 决策树 B（trading/ arbitrage_pipeline + auto_execution_engine + 版本号 v75-v105 抽样）
> **模式**：纯只读审计（system-reminder 全程 5 次合规约束生效，禁止 improve/augment 已有源码）
> **交付**：本报告 + user memory（零代码改动）

---

## 0. 范围界定

| 文件 | 行数 | 备注 |
|---|---:|---|
| `trading/arbitrage_pipeline.py` | 1535 | 回路 C 编排器（V16.6 标称） |
| `trading/auto_execution_engine.py` | 7349 | 标称 V47.0 / 64 大功能 |
| `trading/execution_engine.py` | 701 | Phase 13 注入点 |
| `trading/__init__.py` | 1080 | 暴露 v75-v94 全量 API surface |
| `trading/v75.py` 抽样 | 410 | 跨链套利+清算+AI |
| `trading/v95.py` 抽样 | 669 | （仅行数核证） |
| `trading/v100_production.py` 抽样 | 471 | 生产部署+高级订单 |
| `trading/v105_smart_routing.py` 抽样 | 293 | 组合再平衡+智能路由 |
| **审计总计** | **~10 200 行**（仅核心二件 + 抽样四件 + `__init__`） | |

> trading/ 目录共计 105+ 文件（v75-v105 共 31 个版本号文件），本轮以核心管道+抽样代表性样本展开，不重复 Phase 12 已覆盖的 v5_2/v5_9/v15_6/v30 等老引擎。

---

## 1. 关键新发现（5 项 ISSUE）

### ISSUE-031（P0，致命）：`auto_execution_engine._scan_with_pipeline` 丢弃管道结果，注入硬编码伪机会

**位置**：`trading/auto_execution_engine.py` L3403-3428

**证据**：
```python
async def _scan_with_pipeline(self) -> List[ScannedOpportunity]:
    opportunities = []
    try:
        result = await self.arbitrage_pipeline.run_once()
        # 转换结果
        if result and result.opportunities_executed > 0:
            opportunities.append(ScannedOpportunity(
                opportunity_id=f"opp_{int(time.time())}",
                symbol="BTC/USDT",          # ← 硬编码！
                action="buy",                # ← 硬编码！
                entry_price=50000.0,         # ← 硬编码！
                target_price=55000.0,
                stop_loss=48000.0,
                score=75.0,                  # ← 硬编码！
                confidence=0.7,
                recommendation="execute"
            ))
    except Exception as e:
        logger.error(f"❌ 管道扫描错误: {e}")
    return opportunities
```

**结构性问题（4 重）**：
1. `result.opportunities_executed > 0` 仅作 bool 触发——**真正的 `result.all_opportunities`/`scan_result` 列表全部被丢弃**
2. 无论管道返回什么（XRP/USDT 0.005% 利润、ETH/USDT 跨所、SOL 三角），都生成 BTC/USDT @ 50000 的同一伪样本
3. `score=75.0` / `confidence=0.7` 硬编码，使下游 `_evaluate_and_execute` 的 `min_score_threshold` / `min_confidence` 闸门**100% 形同虚设**（始终通过）
4. 调用的方法名 `run_once()` 与 `arbitrage_pipeline.py` 实际方法 `run_pipeline()` / `run_pipeline_async()` 不匹配——**配置 pipeline 后必然进入 except 分支返回空列表**，再无机会被生成（既然 except 也只是日志，整条上游路径死亡）

**影响**：回路 C 实际生产链路两端都断——
- **配置 pipeline → `run_once` 不存在 → 异常 → 空列表 → 后续 `_simulate_scan` 也不会再调用**（因 try/except 不通向 else 分支），整条扫描静默失败
- **未配置 pipeline → 走 `_simulate_scan` → 30% 概率随机 BTC/ETH/SOL/DOGE 假机会 → `_execute_opportunity` 走 L3578 显式注释「5. 执行（模拟）」**

> **回路 C 实际状态：从 KnowledgeDrivenArbitrageScanner 到 auto_execution_engine 之间不存在任何真实数据流**——这是 Phase 7-13 一直被推断、本轮被实证的「伪集成」。

---

### ISSUE-032（P0）：`auto_execution_engine` 7349 行零真实交易所对接

**证据**（grep 跨整文件统计）：
- `ccxt|binance.*api|create_order|fetch_balance` 真实 API 调用：**0 处**
- `binance/bybit/okx` 仅作字符串配置出现（L730/969/989/1007/1041/1228/1248/1266/1300/4251/5015/7120）
- `random.|simulate|asyncio.sleep`（模拟特征）：**18 处**
- L3578 显式注释：`# 5. 执行（模拟）`
- L3612 显式注释：`# V25.8: 更新连盈/连亏 (假设模拟盈利)`
- L3582-3591 即使 `self.execution_engine` 为真，也只是同进程内 mock 对象的 `await execute_order(...)`——返回 `{'price', 'size'}` dict，无任何链上/交易所证据

**与 V25.1 文档头声明对比**：
> "更新时间：2026-05-06 06:10 (V25.8) — 添加Memo0集成 / 执行质量追踪 / 最大暴露限制 / 连亏熔断器"

文档承诺「Memo0 集成」「执行质量追踪」是真实的（确实有 stats/质量函数），但「执行」是**纯随机数 + 全模拟通道**——文档形成了「真实集成」的暗示，与代码事实背离。

---

### ISSUE-033（P0）：`arbitrage_pipeline._live_execution` 是空壳

**位置**：`trading/arbitrage_pipeline.py` L1113-1124

**证据**：
```python
def _live_execution(self, opp) -> Dict[str, Any]:
    """实盘执行套利（预留接口）"""
    # 实盘模式需要对接真实交易所 API
    logger.warning("实盘模式尚未对接真实交易所，降级为模拟执行")
    return self._simulate_execution(opp)
```

**结构性问题**：
- 配置文件可写 `mode: "live"`，PipelineMode 枚举有 `LIVE = "live"`
- `_execute_single_opportunity` (L1046-1049) 真实分支 `if SIMULATION ... else _live_execution`
- 但 `_live_execution` 内部直接 `return self._simulate_execution(opp)` —— **配置「实盘」与「模拟」的实际行为完全等价**
- 与 ISSUE-032 的 `auto_execution_engine` 形成双重欺骗：上层 PipelineMode=LIVE / 下层 ExecutionMode=FULL_AUTO，但中间无真实交易所链路

---

### ISSUE-034（P0，规模灾难）：trading/ 版本号文件通胀 = 31 个匿名 v* 文件 + 24 个生产 0 引用

**事实清单**：

| 区段 | 文件 | 行数 | 生产/测试引用 |
|---|---|---:|---|
| v75-v98 | 24 个文件 | 大约 ~12 000 行 | **生产 0 / 测试 0**（grep `from .*v(7[5-9]\|8\|9[0-8]) import` = 0 hit；`__init__.py` 暴露但 `__init__` 自身亦非生产入口） |
| v99-v105 | 7 个文件 | 大约 ~3 200 行 | 仅 `tests/test_v99..v105.py` 引用（**6 个测试文件 + 1 v100 由 v99 间接 import**），生产代码（agents/ + main_*）= **0 hit** |
| 累计 | 31 个匿名版本号文件 | ~15 200 行 | **31 文件 0 生产引用** |

**抽样行为剖面**（v75/v100/v105 头 80-100 行均同型）：
- 全部 `import random`（无 `import ccxt` / `import requests` / 任何外部 IO）
- 全部独立的 Enum + Dataclass（无继承、无 import 同包姊妹模块）
- 命名空间冲突：v82 自定义 `BridgeQuote`、v75 也自定义 `BridgeQuote`、v77 又有 `CrossChainRoute` 与 strategies/cross_chain_arbitrage.py 同义不同型
- 文档头标注 "数字货币交易系统 V100.0 / V105.0"，但**互不引用、互无依赖**

**根因**：明显的「LLM 生成式版本通胀」遗留——每轮迭代生成 v(N+1)，**从未删除前版**，且 v75-v98 连测试都不存在，**仅 `__init__.py` 一处广义 `from .vN import *` 风格全量暴露**，使 import trading 触发 24 个无意义文件加载。

**进一步推论**：`__init__.py` 内 `OptimizationResult` (L106 v70) / `OptimizationResult` (L287 v76) / `OptimizationResult` (L755 v94) 三同名类被覆盖式 import——**最终 `trading.OptimizationResult` 是 v94 版本，前两个被静默吞没**。`PerformanceMetrics` / `BridgeQuote` / `EnterpriseFeatures` / `ExecutionStatus` / `RegionStatus` 同型重复，形成「沉默符号污染」。

---

### ISSUE-035（P1）：`ArbitragePipeline.AdaptiveRiskGate` 的 win_rate 启发式存在严重判定缺陷

**位置**：`trading/arbitrage_pipeline.py` L156-232

**证据**（L180-189 wins/losses 判定）：
```python
wins = sum(
    1 for r in all_results
    if "profitable" in r.get("memory", "").lower() or
       "profit" in r.get("memory", "").lower()
)
losses = sum(
    1 for r in all_results
    if "loss" in r.get("memory", "").lower() and
       "profitable" not in r.get("memory", "").lower()
)
```

**4 重缺陷**：
1. `"profit" in memory` 关键词命中过于宽松——任何包含 `expected_profit_pct: -0.5%`（亏损但字段含 `profit`）的记忆都被计入 wins
2. 同时 `"profit" in` 与 `"profitable" in` 双词命中，**亏损记录被计为 win**（因 PipelineResult 模板含 `"expected_profit"` 字段）
3. losses 用 `"loss" in ... and "profitable" not in` 但忽略 `"stop_loss"`（含 loss 子串）的非交易结果记录会被错算亏损
4. 与 Phase 13 ISSUE-030 的 scanner 关键词污染同型——这是**项目内"模糊关键词作为统计语义"的系统性反模式**

**联动放大效应**：
- 该 win_rate 错算结果直接驱动 `current_confidence` / `current_profit` / `current_max_positions` 的自动调整
- L196-200 win_rate>0.7 → 放宽到 confidence=0.4 / profit=0.02
- 因 wins 被高估，系统会**长期处于"放宽"档**（confidence 阈值降低），与 ISSUE-030 scanner 自我加强污染叠加 → 决策门槛系统性低估风险

---

## 2. 回路 C 重构后的实证状态（修正 Phase 11/13 推断）

```
旧推断（Phase 11/13）:
trading/auto_execution_engine → arbitrage_pipeline → KnowledgeDrivenArbitrageScanner

实证（Phase 14）:
trading/auto_execution_engine
  ├── _scan_with_pipeline (L3403)
  │     └── arbitrage_pipeline.run_once()  ← 方法名错误，必抛异常
  │     └── 即使成功也注入硬编码 BTC/USDT @50000  ← ISSUE-031
  └── _simulate_scan (L3430)
        └── random.choice(["BTC/USDT","ETH/USDT","SOL/USDT","DOGE/USDT"])
        └── _execute_opportunity → "执行（模拟）"  ← ISSUE-032
                └── execution_engine.execute_order()  [若注入 mock 对象]
                └── 否则 executed_price = opportunity.entry_price  [零滑点]

trading/arbitrage_pipeline (独立调用方)
  ├── run_pipeline / run_pipeline_async
  ├── _stage_scan → KnowledgeDrivenArbitrageScanner.full_scan() [真实存在]
  ├── 但 scanner 自身全 random 模拟（Phase 13 ISSUE-030）
  └── _live_execution → 直接 fallback _simulate_execution  ← ISSUE-033
```

**回路 C 真实状态**：
- arbitrage_pipeline 与 auto_execution_engine **不存在双向数据流**
- arbitrage_pipeline 自身能从 scanner 取数据，但 scanner 是 random（ISSUE-030）
- auto_execution_engine 的 pipeline 入口因方法名错误必失败，必走 `_simulate_scan`
- 模拟 + 模拟 + 模拟 = **所有"成功"统计均来自随机数**

---

## 3. 累计 ISSUE 汇总（截至 Phase 14）

| ID | 严重 | 位置 | 主旨 |
|---|---|---|---|
| 001 | P0 | memo0_arbitrage_system | search L417 / add L453 接口错调 |
| 002 | P0 | memo0_arbitrage_system | mem0 SDK 误 await 同步方法 |
| 003 | P0 | auto_knowledge_accumulator_v5_2 | add/search 全错调 + 双 mock_mem0_storage.db 分裂 |
| 004 | P0 | unified_arbitrage_system_v55 | expected_profit 量纲错位 |
| 005 | P1 | risk_manager | 仅 3 项 bool 检查 |
| 006 | P0 | unified_arbitrage_system_v55 | 量纲错位（细化） |
| 007 | P2 | live_data_connector_v56 | 数据通道孤儿 |
| 008 | P3 | misc | （略） |
| 009 | P1 | strategies/ml_predictor | 标称 XGBoost 实为 numpy |
| 010 | P2 | ml_predictor.predict_price | 加法+乘法外推叠加 |
| 011 | P2 | ml_predictor | 训练样本不足 |
| 012 | P2 | ml_predictor | 启发式置信度 |
| 013 | P2 | bridge_fee_aware | 桥费率硬编码 |
| 014 | P1 | bridge_fee_aware | 模拟数据通道 |
| 015 | P3 | misc | （略） |
| 016 | P3 | misc | （略） |
| 017 | P0 | backend/api.py /api/v55/signals | mock 数组 BTC=51250 |
| 018 | P0 | backend/api.py /api/v55/risk + execute | 全硬编码 |
| 019 | P3 | misc | （略） |
| 020 | P3 | misc | （略） |
| 021 | P3 | misc | （略） |
| 022 | P0 | agents/ 7 文件 | 0 import V55 → 三孤岛 |
| 023 | P0 | main_agent_v5_10 | Phase 13 独立模块栈 |
| 024 | P0 | engines/ 6 文件 3754 行 | 引擎版本漂移 |
| 025 | P1 | strategies/ 31 文件 | （略） |
| 026 | P2 | strategies/ | （略） |
| 027 | P0 | strategies/cross_chain_execution 948 行 | 整模块孤儿 + 假签名 |
| 028 | P0 | strategies/smart_order_router | 90% 硬编码成交率 + UTF-8 污染 |
| 029 | P1 | strategies/cross_chain_arbitrage | 类型注解谎报 + 利润系数硬扣 |
| 030 | P0 | strategies/knowledge_driven_arbitrage_scanner | random 价格 + 三角套利结构性永不触发 |
| **031** | **P0** | **auto_execution_engine L3403-3428** | **`_scan_with_pipeline` 丢弃 pipeline 结果 + 硬编码伪机会 + 方法名 run_once 不存在** |
| **032** | **P0** | **auto_execution_engine 全文 7349 行** | **零 ccxt 调用 + 18 处 random/simulate + L3578 「执行（模拟）」+ L3612 「假设模拟盈利」** |
| **033** | **P0** | **arbitrage_pipeline L1113-1124** | **`_live_execution` 直接 fallback 到 `_simulate_execution`，LIVE 模式即 SIMULATION** |
| **034** | **P0** | **trading/ v75-v105 + `__init__.py`** | **31 匿名版本号文件 ~15 200 行 + 24 文件 0 生产引用 + `__init__.py` 同名 import 沉默覆盖** |
| **035** | **P1** | **arbitrage_pipeline.AdaptiveRiskGate L156-232** | **win_rate 关键词命中错算 + 与 scanner ISSUE-030 自我加强污染** |

**累计**：35 项（P0=15 / P1=8 / P2=9 / P3=3）

---

## 4. 决策树（下轮 Phase 15）

| 选项 | 范围 | 收益 | 风险 |
|---|---|---|---|
| **A** | data_collection/ 全栈 + ccxt_price_feed（**回路 D 起点实证**） | 验证唯一可能的真实数据源是否真接入交易所 | 中 |
| **B**（推荐） | 五孤岛桥接「设计文档」（合规边界内仅产文档，不动代码） | 形成可执行重构蓝图，归并 35 项 ISSUE 成 5-7 个原子重构包 | 低 |
| C | trading/v75-v98 24 文件深度孤儿确认 + `__init__.py` 沉默覆盖语义影响清单 | 完成 ISSUE-034 闭环 | 低 |
| D | strategies/ 剩 17 个非引擎策略文件深审 | 持续覆盖盲区 | 中 |

**建议路径**：B → A，本轮已证明执行链全是模拟，下轮**应建立重构蓝图把"已确诊 35 项 ISSUE"归并成可一次落地的合并方案**，而不是继续无差别审计累积 ISSUE。

---

## 5. 合规元数据

- 触发：第 16 次定时迭代 / 2026-05-10 16:13:23
- system-reminder（"禁 improve/augment 已有源码"）触发：**5 次（100% 遵守）**
- 代码改动：**0 处**
- 新文件：本报告 1 个（路径：`crypto_arbitrage/V54_0_PHASE14_PIPELINE_AUTOEXEC_AUDIT_REPORT.md`）
- 删除：无
- user memory 写入：1 条 Phase 14 摘要

---

> 编制：自动化审计代理 / Phase 14
> 锚定文件：`trading/arbitrage_pipeline.py`、`trading/auto_execution_engine.py`、`trading/__init__.py`、`trading/v75.py`、`trading/v100_production.py`、`trading/v105_smart_routing.py`、Phase 13 报告
