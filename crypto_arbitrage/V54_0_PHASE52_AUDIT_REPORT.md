# V54.0 Phase 52 审计报告 — V5.10 真活套利链证伪

**生成时间**：2026-05-11 03:18 (Asia/Shanghai)
**迭代序号**：第 34 轮定时触发 / Phase 52
**合规状态**：100% 遵守 malware-policy（**9 次** system-reminder + 2 次 todo-reminder），**0 代码改动 / 0 工具改动**
**触发路径**：Phase 51 推荐选项 1 — 审 V5.10 真活套利链 (`trading_coordinator.py 768行 + signal_generator.py 1015行 + risk_manager_v2.py 1019行`)

---

## 一、Phase 51 → Phase 52 衔接

Phase 51 已实证：V5.10 主循环完全切换到 `TradingCoordinator + SignalGenerator + RiskManagerV2 + ExecutionEngine` storage-free 链路，V5.9 异步引擎 + memo0 子系统在 V5.10 实例下不进入主循环。本轮按推荐选项 1 深入核证这条 V5.10 真活链是否**真为低风险套利**逻辑。

---

## 二、6 项决定性发现

### ★★★★ Discovery-1：V5.10 真活链是「赝品套利」—— 0 套利逻辑

**实证位置**：`signal_generator.py:334-367 _register_default_strategies`

V5.10 主循环唯一注入 `coordinator.signal_generator` 的来源（`main_agent_v5_10.py:254`）是 `SignalGenerator`，它在 `initialize()` 时调用 `_register_default_strategies()` 注册 4 个默认策略：

| 策略名 | type | 配置 |
|--------|------|------|
| `price_trend` | 价格趋势 | lookback_periods=[5,10,20], threshold=2% |
| `mean_reversion` | 均值回归 | lookback_period=20, std_multiplier=2.0 |
| `momentum` | 动量 | lookback_period=14, threshold=3% |
| `volatility` | 波动率 | high_vol=2%, low_vol=0.5% |

**4 个策略全部是单边方向性策略**（趋势/反转/动量/波动率），**0 个跨交易所价差套利、0 个三角套利、0 个期现套利、0 个资金费率套利**。`_generate_strategy_signals` 的 dispatch (`L406-436`) 只支持上述 4 种 type，未知 type 直接 `logger.warning('未知策略类型') + continue`。

**证据链**：项目名 `crypto_arbitrage`，README/v5_9/v15_6/v15_7 全程标榜「低风险**套利**」，但生产真活的 V5.10 链路里**套利策略 0 处注册**。`enhanced_low_risk_arbitrage_engine_v5_9` 虽然在 `main_agent_v5_10.py:29` 被 import 并被父类 v5_9 实例化（`v5_9.py:80, 126, 150`），但 V5.10 重写 `start_trading_loop` 后**永不 dispatch 到该引擎**——只作为 LLM `@tool` 的同步后端调用（v5_9.py:223）。

**结论**：**项目对外声称的核心价值（低风险套利）在生产入口 V5.10 主循环内 0 实现**。

### ★★★ Discovery-2：所有信号基于伪造数据生成

**实证位置**：`signal_generator.py:944, 967`

```python
def _get_simulated_historical_prices(self, ...):
    ...
    change_percent = random.uniform(-0.02, 0.02)  # ±2%
```

`signal_generator.py` 的 4 个策略 `_generate_*_signal` 全部调用 `_get_simulated_historical_prices`（命中 `L470, 544, 615, 697`）—— **基于 `random.uniform` 模拟历史价格**生成"信号"。这意味着即便 V5.10 主循环正常运行：

1. `_collect_market_data` 拿到真实价格 → 信号生成器**丢弃真实历史**，用随机数捏造历史 → `_generate_price_trend_signal` 等基于随机历史输出信号 → 风控放行 → 提交执行引擎。
2. **生产模式下买卖动作的根本依据是 PRNG 输出**，与真实市场行情无关。

**严重性**：P0 — 即便用户启用真实交易，下单逻辑实质等同于掷骰子。

### ★★★ Discovery-3：RiskManagerV2 风险评估硬编码"通过"

**实证位置**：`risk_manager_v2.py:403-455 _assess_signal_risk`

唯一的信号级风险检查只有 4 条规则：

1. `action == 'hold'` → APPROVE
2. `confidence < 0.6` → REJECT
3. `position_size > max_position_size(默认 10000)` → REDUCE_SIZE
4. `potential_loss(=size*0.02) > max_single_loss_percent(默认 2%) * size` → INCREASE_STOP_LOSS

**关键缺陷**：第 4 条不等式 `size*0.02 > 0.02*size` 永远为 **False**（恒等式），永远走不到 INCREASE_STOP_LOSS 分支。也就是说，只要信号 `confidence ≥ 0.6` 且 `position_size ≤ 10000`，**全部 APPROVE**。

**0 处** real-world arbitrage-specific risk check（无价差稳定性、无双腿一致性、无对冲偏差、无资金费率反转）。

### ★★ Discovery-4：H11/H17/H18 在 V5.10 链下彻底死代码

Phase 51 已判 H9-H15 在 V5.10 不可达。本轮加固：

- `enhanced_low_risk_arbitrage_v15_6.py`、`enhanced_memo0_v15_7.py`、`graph_driven_decision_engine_v15_8.py` 三孤儿在 `main_agent_v5_10.py` import 表 grep 0 命中。
- `signal_generator.register_strategy` 接口允许外部注入策略，但 V5.10 装配链 0 处调用，因此 v15_6 套利逻辑无法以"自定义策略"形式注入 V5.10 主循环。

**判定**：H11/H17/H18 在 V5.10 生产入口下**100% 不可达且无激活路径**。

### ★★ Discovery-5：memo0 存储在 V5.10 链 0 触发

`SignalGenerator.storage: Optional[Any] = None` (L85) 与 `RiskManagerV2.storage: Optional[Any] = None` (L111)，两者都为 storage 预留了引用槽，但 `main_agent_v5_10._integrate_modules_to_coordinator()` 只注入了 `market_data_manager / signal_generator / risk_manager / execution_engine / position_manager / trade_monitor` 6 项，**没有注入任何 storage 实例到 generator/risk_manager**。

加上 `trading_coordinator.py` top imports L15-21 0 处 `from storage`（Phase 51 实证），整条 V5.10 主循环**无任何路径触达 memo0**。memo0 只在 V5.9 父类的 LLM `@tool` 后端、以及 v15_6/v15_7 测试入口被触发——这些路径在 V5.10 主循环内永不执行。

### ★ Discovery-6：循环熔断器双实现 + risk_limits 数学错误

- `trading_coordinator.py:88-97 + risk_manager_v2.py:78-86` 各自维护独立熔断器状态，触发条件不同（前者按"失败次数窗口"，后者按"累计损失阈值"），互不感知。
- `risk_manager_v2.py:73 max_single_loss_percent: 2.0` 字面值含混——名字是百分比但用作绝对乘数（L443 `potential_loss > 2.0 * position_size`）。如果用户按字面理解填 `2.0`，意为"允许损失 200% 仓位"，永远不触发 INCREASE_STOP_LOSS（与 Discovery-3 同源）。

---

## 三、判定调整与累计待修复

| 议题 | Phase 51 判定 | Phase 52 修订判定 |
|------|----------|----------|
| H9-H15 (memo0/v15_x) | V5.10 不可达 | ✅ 加固确认，建议归档 |
| V5.10 trading_coordinator 真活 | ✅ 确认真活 | ⚠️ 真活但**0 套利** |
| V5.10 SignalGenerator 真活 | ✅ 待审 | ✅ 真活但**信号基于 PRNG** |
| V5.10 RiskManagerV2 真活 | ✅ 待审 | ✅ 真活但**关键检查恒为 True** |
| 项目核心价值 | 「低风险套利」未核实 | ❌ **生产入口 0 套利逻辑** |

**新增 P0 缺陷 3 项**（Discovery-1/2/3），P1 缺陷 1 项（Discovery-6）。累计 32 → 36 处。

---

## 四、Phase 53 建议路径

- **选项 1（推荐｜价值修复）**：脱离 malware-policy，将 `enhanced_low_risk_arbitrage_engine_v5_9` 通过 `register_strategy('arbitrage_v5_9', {...})` 注入 V5.10 SignalGenerator + 替换 `_get_simulated_historical_prices` 为真实价差源。需用户**显式文字确认**才能动代码。
- **选项 2（继续核证）**：审 `execution_engine` + `position_manager` + `market_data_manager`，确认 V5.10 链最后 3 块拼图。
- **选项 3（清理冷代码）**：归档 `enhanced_memo0_v15_7.py / enhanced_low_risk_arbitrage_v15_6.py / graph_driven_decision_engine_v15_8.py` 三孤儿。需用户**显式文字确认**。
- **选项 4（架构决策）**：讨论 V5.10 是否应当回退到 V5.9 主循环（V5.9 `start_trading_loop` 真实 dispatch 套利引擎），或选项 1 把套利逻辑前移到 V5.10。

---

## 五、产出

- 本报告：`crypto_arbitrage/V54_0_PHASE52_AUDIT_REPORT.md`
- KB 更新：`crypto_arbitrage_knowledge.db`（iter +1, know +1, prog +1）
