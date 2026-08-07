# V54.0 Phase 10 — API 端点真伪 + 测试覆盖度审计

**触发**：第 11 次定时触发 (2026-05-10 13:27:23)
**模式**：纯只读分析（合规边界：禁止 improve/augment）
**审计目标**：`backend/api.py` (1333 行) + `tests/` (116 文件)
**前置 Phase**：Phase 5~8 决策→风控→执行→存储；Phase 9 ML+实时数据+桥费输入端

---

## 一、本轮 5 项新 ISSUE

| ID | 等级 | 模块 | 摘要 |
|---|---|---|---|
| **ISSUE-017** | **P0** | backend/api.py L1057-1138 | `/api/v55/signals`、`/api/v55/positions` 返回**完全硬编码**的 mock 数组（BTC=51250 死值、200USD/-100USD 持仓硬编码），注释明写「实际需要连接 V55」但**从未连接** |
| **ISSUE-018** | **P0** | backend/api.py L1161-1196 | `/api/v55/exchanges/status`、`/api/v55/risk/status`、`/api/v55/execute` 三端点**全部返回硬编码字典**，与 `LiveExchangeConnector`、`AdvancedRiskManager`、引擎 execute 路径**零调用** |
| **ISSUE-019** | P1 | backend/api.py L461-475 | `/api/trading/status` 注释「实际应从 engine 获取」，**实际仍硬编码** `mode="simulation"`、`state="idle"`、计数 0 |
| **ISSUE-020** | P1 | tests/test_v55_system.py L172-210 | `bridge_fee_pct=0.1` 与 `expected_profit=2.0` 测试时单位**默认一致**（pct vs USD 未区分），无法捕获 ISSUE-006/016 量纲错位 |
| **ISSUE-021** | P2 | tests/test_v54__ml_predictor L209 | 仅断言 `prediction > 0`，未校验「文档承诺的 XGBoost/LightGBM」与「实际 SMA 启发式」差异（ISSUE-009 不被任何测试覆盖） |

---

## 二、Phase 9 ISSUE-016 重大修正

**原描述（Phase 9）**：「dataclass 完全没有 `bridge_fee_pct` 字段」——**错误**。

**实证修正**：
- `unified_arbitrage_system_v55.py` L85 `class V55ArbitrageSignal` **有** `bridge_fee_pct: float = 0.0`（L104）
- L486：`min_profit = signal.bridge_fee_pct + 0.01`
- L487：`checks['profit_ok'] = signal.expected_profit > min_profit`
- L691：信号构造时 `bridge_fee_pct=bridge_fee` 注入
- L839/L860：执行结果 `cross_chain_fees = bridge_fee_pct * position_size * price`

**真正问题（ISSUE-006 根因坐实）**：
- `expected_profit` 来自 cross_chain_arbitrage L265：`spread_pct * min(volume, 10000) * 0.9` ⇒ **USD 绝对金额**（量级 1~9000）
- `bridge_fee_pct` 是百分比小数 ⇒ 量级 0.0~1.0
- L487 比较：`USD金额 > 百分比小数 + 0.01` ⇒ 几乎**永真**
- profit_ok 检查**实际失能**，被 risk_score_ok（0.7 阈值）和 confidence_ok（0.6 阈值）实际拦截

---

## 三、API 端点真伪矩阵（共 30 端点抽样）

| 端点 | 接通真实模块 | 备注 |
|---|---|---|
| `/api/health` (L262) | ✅ | agent 真实存在性检查 |
| `/api/strategies` (L335) | ✅ | `agent.strategies` |
| `/api/strategies/{name}/start` (L528) | ✅ | `strategy.start()` |
| `/api/scan` (L601) | ✅ | `agent.strategy_manager.scan_all_strategies()` |
| `/api/execute` (L637) | ✅ | `execute_best_opportunity()` |
| `/api/knowledge/search` (L660) | ✅ | `get_unified_storage().search_knowledge()` |
| `/api/trading/status` (L461) | **❌** | 硬编码 simulation/idle/0 |
| `/api/v55/signals` (L1057) | **❌** | 2 条死信号 |
| `/api/v55/positions` (L1101) | **❌** | 2 条死持仓 |
| `/api/v55/execute` (L1141) | **❌** | 直接返回 status="executed" 不调引擎 |
| `/api/v55/exchanges/status` (L1161) | **❌** | 7 交易所硬编码布尔 |
| `/api/v55/risk/status` (L1182) | **❌** | 5 风险字段硬编码 |
| `/api/v56/live/prices` (L1201) | ✅(部分) | 调 `get_live_data_connector()`，但连接器内部仍 mock（ISSUE-014） |
| `/api/v56/live/orderbook/{symbol}` (L1238) | ✅(部分) | 同上 |
| `/api/v56/exchanges/connector-status` (L1269) | ✅(部分) | 调用真实，数据 mock |

**真伪比例**：6/15 真接通 + 3/15 半接通（连接器自身 mock）+ **6/15 完全硬编码**。其中 V55 命名空间 5 个端点全失能（ISSUE-017/018），与 V55 引擎完全解耦。

---

## 四、测试覆盖度黑洞

**已覆盖**：
- V55 风险检查通过/失败两路径（test_v55_5）
- V54 ML 预测器初始化、价格预测>0（test_v54__ml_predictor）
- V56.1 交易所枚举、连接器构造（test_v56_1_*）
- bridge_fee 离线值检查（test_v55_3 L93-106）

**未覆盖（13 项 ISSUE）**：

| ISSUE | 是否有测试 | 理由 |
|---|---|---|
| ISSUE-001/002 await 同步 | ❌ | 无 mem0 错调 await 用例 |
| ISSUE-005 风控只 3 项 bool | ❌ | test_v55_5 反而验证「3 项通过」 |
| ISSUE-006 量纲错位 | ❌ | test_v55_5 假设单位一致 |
| ISSUE-009 假 ML | ❌ | test_v54__ml_predictor 仅 `>0` |
| ISSUE-013 live_data 与 V55 解耦 | ❌ | 无 live→V55 集成用例 |
| ISSUE-014 RealTimeDataConnector mock | ❌ | 无真实 ccxt 接入测试 |
| ISSUE-016 桥费率 dataclass 缺失 | ✅(已修正为不存在) | — |
| ISSUE-017 V55 API 端点硬编码 | ❌ | 无 backend/api.py 集成测试 |
| ISSUE-018 V55 risk/exchange API 硬编码 | ❌ | 同上 |

**测试覆盖率结论**：116 个测试文件中，约 30+ 个是版本化历史快照（test_v1.5 ~ V69 共 60+ 单测），**无一覆盖跨层数据流真实性验证**——单测全过却产生不了可信信号。

---

## 五、系统现状再校核（含 Phase 9 修正）

```
              [API 层]
              ┌──────────────────────┐
              │ /api/v55/* 五端硬编码  │  ← ISSUE-017/018
              │ /api/v56/* 半接通       │  ← ISSUE-013/014
              └──────────────────────┘
                       ↓ 不调
              [V55 主引擎]
   ┌─────────────────────────────────┐
   │ ① mock 价 (live_data 死值)         │ ← ISSUE-014
   │ ② mock 桥费 (BridgeFeeMonitor 离线) │ ← Phase 9 ISSUE-016 已修正
   │ ③ 假 ML (numpy SMA)               │ ← ISSUE-009
   │ ④ profit_ok 量纲错位失能           │ ← ISSUE-006/016 根因
   │ ⑤ await 同步 mem0 (无效写入)       │ ← ISSUE-001/002
   └─────────────────────────────────┘
                       ↓ 写入但被 await 阻塞
              [Mock SQLite 存储]
```

---

## 六、累积问题矩阵（Phase 5~10 共 21 项）

| 等级 | 数量 | ID 列表 |
|---|---|---|
| **P0** | **8** | 001, 002, 006, 013, 014, **017, 018** |
| **P1** | 7 | 003, 005, 009, 015, **019, 020** |
| P2 | 4 | 010, 011, **021** |
| P3 | 2 | 004, 012 |

**Phase 10 P0 计数 +2、P1 +2、P2 +1**。

---

## 七、Phase 11 决策树

| 选项 | 解读 |
|---|---|
| **A** "授权批量修复 8 项 P0" | 解除合规限制；预估 ~150 行 diff，跨 6 文件 |
| **B** 续 Phase 11 只读 | 转向 `agents/` 主体（auto_knowledge_accumulator/main_agent_v5_10）逻辑闭环审计 |
| **C** "授权归档孤儿" | 60+ 历史版本测试 + 5 个孤儿快照集中归档 |
| **D** "输出 V57 真实接入蓝图" | 设计文档：ccxt + LI.FI + XGBoost + 量纲规约 |
| **E** "仅修 ISSUE-006/016 量纲" | ~10 行 diff，引入 `bridge_fee_usd` 字段 |
| **F** "Phase 10 双修：API 接通 + 量纲" | ~50 行 diff，将 5 个 V55 mock 端点改为调用真实引擎 |

---

## 八、本轮交付物

| 文件 | 性质 |
|---|---|
| [V54_0_PHASE10_API_TEST_AUDIT_REPORT.md](file:///D:/03_AITOOL/deepagents/crypto_arbitrage/V54_0_PHASE10_API_TEST_AUDIT_REPORT.md) | 纯分析报告 |

**已有源码改动**：0 处 | **新增代码文件**：0 个 | **删除/移动**：0 处

---

## 九、Phase 9 失误自省

Phase 9 ISSUE-016 描述与实际不符，根因：未读 V55 主线 dataclass 定义即以 cross_chain_arbitrage 推断。本轮通过 grep `bridge_fee_pct` 跨文件回查在 unified_arbitrage_system_v55.py 5 处使用，实证修正。

**经验**：跨模块字段断言必须 grep 全文件再下结论，prevent 单文件视角失真。

---

**报告作者**：LobsterAI (定时第 11 次触发)
**生成时间**：2026-05-10 13:27:34 (Asia/Shanghai)
**合规状态**：✅ 零代码变更、零文件移动、纯只读分析
