# V54.0 Phase 2 — 版本快照归档影响清单

## 元信息
- **版本**: V54.0 Phase 2（只读分析）
- **日期**: 2026-05-10 11:47
- **触发**: superpowers 定时无人值守触发（连续第三轮）
- **状态**: 完成（纯只读，无文件改动）
- **前置文档**: [V54_0_PHASE1_AUDIT_REPORT.md](./V54_0_PHASE1_AUDIT_REPORT.md)

---

## 1. 本轮目标

回答用户下次可能问的问题："归档这 5 个版本快照会不会断掉什么东西？"

通过全仓库 grep 扫描，精确量化每个快照文件的**被 import 次数**和**import 来源分类**。

---

## 2. 五个版本快照的依赖影响矩阵

### 2.1 `auto_knowledge_accumulator_v5_2.py`

| 维度 | 数据 |
|---|---|
| 被直接 import 次数 | **2**（仅测试文件） |
| 被 import 的文件 | `tests/test_v5_2_simple.py`, `tests/test_v5_2_integration.py` |
| 被主线代码 import | ❌ 无 |
| 被 agents import | ❌ 无 |
| 被 strategies import | ❌ 无 |
| 当前活跃替代 | `auto_knowledge_accumulator.py`（无版本后缀） |

**影响评估**: 🟢 **零风险归档**
- 仅两个历史测试文件引用，且这两个测试本身就是 V5.2 时代的遗留
- 主线 `backend/api.py` 引用的是无后缀版 `auto_knowledge_accumulator`
- `strategies/strategy_manager.py` 引用的是无后缀版

---

### 2.2 `deep_memo0_integration_v5_8.py`

| 维度 | 数据 |
|---|---|
| 被直接 import 次数 | **2** |
| 被 import 的文件 | `storage/deep_memo0_integration_v5_9.py`, `tests/test_v5_8_modules.py` |
| 被主线代码 import | ⚠️ 被 v5_9 继承 |
| 被 agents import | ❌ 无 |
| 被 strategies import | ❌ 无 |
| 当前活跃替代 | `deep_memo0_integration_v5_9.py`（已继承并超越） |

**影响评估**: 🟡 **低风险，需确认继承链**
- v5_9 第 41 行 `from storage.deep_memo0_integration_v5_8 import DeepMemo0IntegrationV58`
- 这是**版本递进继承关系**（v5_8 → v5_9），属于正常演进
- 若归档 v5_8，v5_9 的 import 会断 → **但 v5_9 本身也是待归档目标**
- 建议：v5_8 和 v5_9 **一起归档**，或先让 v5_9 解除对 v5_8 的继承

---

### 2.3 `deep_memo0_integration_v5_9.py`

| 维度 | 数据 |
|---|---|
| 被直接 import 次数 | **11** |
| 被 agents import | `main_agent_v5_9.py`, `main_agent_v5_10.py` |
| 被 strategies import | `enhanced_low_risk_arbitrage_engine_v5_9.py`, `enhanced_low_risk_arbitrage_v15_6.py` |
| 被 storage 内部 import | `enhanced_memo0_v15_7.py`（第 40 行）, `__init__.py`（第 44 行） |
| 被 tests import | `test_v5_9_integration.py`, `test_v5_9_phase2_integration.py` 等 |
| 被诊断脚本 import | `diagnose_system.py`（第 19 行） |
| 当前活跃替代 | `mem0_storage.py` + `UnifiedStorage`（V15.3 当前版） |

**影响评估**: 🔴 **高风险，不可直接归档**
- 这是 5 个快照中**被依赖最多**的文件（11 处 import）
- `storage/__init__.py` 仍将其作为**官方导出接口**
- `main_agent_v5_10.py`（当前最新 agent）仍直接 import 它
- `enhanced_memo0_v15_7.py` 继承自它
- **必须先迁移引用方**，才能归档

---

### 2.4 `enhanced_memo0_v15_7.py`

| 维度 | 数据 |
|---|---|
| 被直接 import 次数 | **2** |
| 被 import 的文件 | `knowledge/graph_driven_decision_engine_v15_8.py`, `test_v15_7_enhancements.py` |
| 被主线代码 import | ⚠️ `graph_driven_decision_engine_v15_8.py`（知识模块） |
| 被 agents import | ❌ 无 |
| 被 strategies import | ❌ 无 |
| 当前活跃替代 | `mem0_storage.py` + `UnifiedStorage`（V15.3 当前版） |

**影响评估**: 🟡 **中低风险**
- 仅被知识图谱决策引擎和测试引用
- `graph_driven_decision_engine_v15_8.py` 是 V15.8 知识模块，可能仍在演进
- 需确认该知识模块是否活跃使用

---

### 2.5 `intelligent_decision_engine_v5_2.py`

| 维度 | 数据 |
|---|---|
| 被直接 import 次数 | **8** |
| 被 agents import | `main_agent_v5_2.py`, `main_agent_v5_9.py`, `main_agent_v5_10.py` |
| 被 strategies import | `enhanced_low_risk_arbitrage_engine_v5_2.py` |
| 被 .graphify_core import | `main_agent_v5_2.py`, `enhanced_low_risk_arbitrage_engine_v5_2.py` |
| 被 tests import | `test_v5_2_simple.py`, `test_v5_2_integration.py`, `test_v5_9_phase2_integration.py` |
| 当前活跃替代 | `intelligent_decision_engine.py`（无版本后缀，V2.2+） |

**影响评估**: 🔴 **高风险，不可直接归档**
- 被 3 个 agent 版本引用（v5_2, v5_9, v5_10）
- `main_agent_v5_10.py`（当前最新 agent）仍直接 import 它
- 但 `storage/__init__.py` 当前导出的是无后缀版 `IntelligentDecisionEngine`
- **矛盾点**：官方接口已切到新类，但 agent 代码仍 import 旧类

---

## 3. 综合风险评估

### 3.1 直接归档风险等级

| 快照文件 | 风险等级 | 被依赖数 | 关键依赖方 | 能否直接归档 |
|---|---|---|---|---|
| `auto_knowledge_accumulator_v5_2.py` | 🟢 低 | 2 | 仅测试 | ✅ 可以 |
| `deep_memo0_integration_v5_8.py` | 🟡 中 | 2 | v5_9 继承 | ⚠️ 需和 v5_9 一起处理 |
| `deep_memo0_integration_v5_9.py` | 🔴 高 | 11 | agent_v5_10, storage/__init__ | ❌ 不可 |
| `enhanced_memo0_v15_7.py` | 🟡 中 | 2 | graph_decision_engine_v15_8 | ⚠️ 需确认 |
| `intelligent_decision_engine_v5_2.py` | 🔴 高 | 8 | agent_v5_10, 多 agent | ❌ 不可 |

### 3.2 真正零风险可归档的（单文件）

仅 **`auto_knowledge_accumulator_v5_2.py`** 一个文件可以**单独安全归档**。

其余 4 个都有活跃的跨文件依赖链。

---

## 4. 若用户批准"路线 A + C"合并执行的推荐顺序

基于依赖分析，推荐**分波次归档**，避免一次性破坏：

### Wave 1（零风险，可立即执行）
1. `auto_knowledge_accumulator_v5_2.py` → `archive/snapshots/`
2. 同步移动其测试文件 `tests/test_v5_2_simple.py`, `tests/test_v5_2_integration.py`

### Wave 2（需先修改引用方）
前置工作：把 `main_agent_v5_10.py` 中的旧 import 切到当前版
- `from storage.deep_memo0_integration_v5_9 import ...` → `from storage import DeepMemo0IntegrationV59, ...`
- `from storage.intelligent_decision_engine_v5_2 import ...` → `from storage import IntelligentDecisionEngine, ...`

然后可归档：
- `deep_memo0_integration_v5_9.py`
- `intelligent_decision_engine_v5_2.py`
- `deep_memo0_integration_v5_8.py`（v5_9 已归档，继承链自然解除）

### Wave 3（最后处理）
- `enhanced_memo0_v15_7.py` — 需先确认 `graph_driven_decision_engine_v15_8.py` 是否仍在活跃使用

---

## 5. 意外发现：当前代码存在"双脚手架"问题

`storage/__init__.py` 导出的是无后缀新版：
```python
from storage.intelligent_decision_engine import IntelligentDecisionEngine
```

但 `agents/main_agent_v5_10.py`（号称"当前最新 agent"）却 import 旧版：
```python
from storage.intelligent_decision_engine_v5_2 import IntelligentDecisionEngineV52
```

**这意味着**：官方接口和实际使用代码之间存在**版本漂移**。这是 V54.0 之前某轮迭代切接口时，agent 代码未同步迁移的遗留问题。

---

## 6. 给用户的决策数据

| 方案 | 可归档文件数 | 需前置修改 | 预计时间 | 风险 |
|---|---|---|---|---|
| **保守**：只归档 `auto_knowledge_accumulator_v5_2.py` | 1 | 无 | 2 分钟 | 零 |
| **中等**：Wave 1 + Wave 2（先改 import 再归档） | 4 | 改 2 个 agent 文件的 import | 15 分钟 | 低 |
| **激进**：全部 5 个 + 清理相关测试 | 5 | 改 import + 确认 graph_decision_engine | 30 分钟 | 中 |

---

## 7. 本轮工作产出清单（无破坏性）

| 类型 | 文件 | 行数级 |
|---|---|---|
| 新增报告 | `V54_0_PHASE2_SNAPSHOT_IMPACT_REPORT.md` | ~200 行（本文件） |
| 修改源码 | 无 | 0 |
| 删除文件 | 无 | 0 |
| 移动文件 | 无 | 0 |

---

## 8. 给下一轮 Agent 的精确交接

### 8.1 已知数据（可直接复用）

```yaml
snapshot_dependencies:
  auto_knowledge_accumulator_v5_2:
    risk: low
    imports: 2
    all_from_tests: true
    can_archive_solo: true
  deep_memo0_integration_v5_8:
    risk: medium
    imports: 2
    inherited_by: v5_9
    can_archive_solo: false
  deep_memo0_integration_v5_9:
    risk: high
    imports: 11
    imported_by: [agent_v5_9, agent_v5_10, strategies_v5_9, storage_init, tests]
    can_archive_solo: false
  enhanced_memo0_v15_7:
    risk: medium
    imports: 2
    imported_by: [graph_decision_engine_v15_8, tests]
    can_archive_solo: maybe
  intelligent_decision_engine_v5_2:
    risk: high
    imports: 8
    imported_by: [agent_v5_2, agent_v5_9, agent_v5_10, strategies_v5_2, tests]
    can_archive_solo: false
    drift_noted: "storage/__init__ exports new class, but agents still import old"
```

### 8.2 决策树

```
1. 读 V54_0_PHASE2_SNAPSHOT_IMPACT_REPORT.md（本文件）
2. 用户是否在线？
   ├─ 是 → 用 §6 数据让用户选保守/中等/激进方案
   └─ 否 → 跳到 3
3. MEM0_API_KEY 是否已配置？
   ├─ 是 → 可启动路线 B（但路线 A 仍推荐优先做）
   └─ 否 → 路线 B 不可执行
4. 本轮可做的非破坏性子任务：
   - 检查 `agents/main_agent_v5_10.py` 当前是否真的是"最新活跃 agent"
     （对比 V53/V56 的 agent 版本，确认 v5_10 是否已被 newer 版本超越）
   - 若 v5_10 也已是历史版本，则整个 Wave 2 的风险进一步降低
   - 这是只读分析，不改不动文件
5. 不要发 V55，仍按 V54_0_PHASE<N>_REPORT.md 命名
```

### 8.3 严禁动作

- ❌ 不要"代用户决策"擅自归档/删除/移动文件
- ❌ 不要在 `MEM0_API_KEY=NOT_SET` 时跑 Memo0 真实测试并写"PASS"
- ❌ 不要修改已有源码（包括 agent import 语句）
- ❌ 不要写新的策略代码

---

## 9. 知识库登记字段

```yaml
version: V54.0_Phase2
type: read_only_impact_analysis
date: 2026-05-10T11:47:00+08:00
trigger: scheduled_unattended
predecessor: V54.0_Phase1
successor: V54.0_Phase3 (TBD - awaiting user decision)
deliverables:
  - V54_0_PHASE2_SNAPSHOT_IMPACT_REPORT.md (本文件)
work_done:
  - 全仓库 grep 扫描 5 个版本快照的 import 依赖关系
  - 量化每个快照的被依赖次数和来源分类
  - 评估直接归档风险等级（2个🔴高/2个🟡中/1个🟢低）
  - 发现 agent 代码与 storage/__init__ 之间的版本漂移问题
  - 给出分波次归档的推荐顺序（Wave 1/2/3）
  - 给出保守/中等/激进三种方案的代价数据
no_code_changed: true
no_files_deleted: true
no_files_moved: true
follow_up_required:
  - 用户决策归档方案（保守/中等/激进）
  - 若选中等/激进：需明文授权修改 agent import + 归档操作
  - 若选路线 B：提供 MEM0_API_KEY
```

---

**报告生成时间**: 2026-05-10 11:47:10
**迭代负责人**: AI Assistant (V54.0 Phase 2)
**项目状态**: ✅ Phase 2 只读影响分析完成，等待用户决策
