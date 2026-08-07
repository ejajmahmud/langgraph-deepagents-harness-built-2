# V54.0 迭代规划 — 承上启下的工程整理与 Memo0 实测衔接

## 元信息
- **版本号**: V54.0（规划）
- **日期**: 2026-05-10
- **触发**: superpowers 定时无人值守触发
- **状态**: 📋 待执行（需用户批准方向）
- **前置版本**: V53.0（Memo0 search/add 兼容、14/14 PASS）

---

## 1. 上一轮（V53.0）真实状态摘要

| 维度 | 值 |
|---|---|
| 主线代码总功能 | 169+ |
| 迭代报告总数 | ~100 份 |
| 最新已完成版本 | V53.0（2026-05-08） |
| Memo0 三件套 | `mem0_storage.py` / `mem0_mock_storage.py` / `deep_memo0_integration_v5_9.py` |
| 核心套利模块 | `memo0_arbitrage_system.py`（V52 引入，V53 增强） |
| 测试通过率 | 14/14（V53 套件） |

---

## 2. 本轮（V54.0）超 powers 深度分析发现的关键事实

### 2.1 双脚手架未消除（首要工程债）
- 顶层 `crypto_arbitrage/` — **主线**，迭代到 V53.0
- `libs/crypto_trading/` — 早期 monorepo 包式空架子，已被主线完全超越
- **影响**：每次新会话都浪费上下文重新盘点，且会让接续工作的 Agent 困惑选哪边写代码
- **建议**：V54.0 由用户明文确认后，将 `libs/crypto_trading/` 整体移入 `archive/legacy_libs_crypto_trading/`，仅保留 README 作历史记录

### 2.2 Memo0 联通性从未做过真实端到端验证
- `mem0_storage.py` 通过 `MEM0_API_KEY` 环境变量启用真实模式
- 仓库里有 `scripts/verify_memo0.py` 和 `scripts/test_memo0_integration.py`，但所有 V52/V53 测试是基于 `mem0_mock_storage.py` 跑的
- **未知**：当前 `MEM0_API_KEY` 是否配置；如配置，是否在 `api.mem0.ai` 真能往返
- **建议**：V54.0 第一步先做"只读冒烟测试"——`add` 一条然后 `search` 取回，确认契约对齐

### 2.3 历史代码中的两个候选缺陷（仅记录，不擅自修改）
本轮压缩上下文里登记过两个潜在 bug，**需用户在新会话确认是否修**：

| 编号 | 文件 | 现象 | 严重度 |
|---|---|---|---|
| BUG-001 | `libs/crypto_trading/.../memo_client.py` 第 422-705 行 | `KnowledgeBase.save_portfolio` 等方法访问 `self._cache`，但 KnowledgeBase 本身无该属性 | 高（AttributeError） |
| BUG-002 | `libs/crypto_trading/.../market_analyzer.py` 第 421 行 | `vol_score` 被覆写两次，前一次 `max(0,1-vol*10)` 计算结果直接被丢弃 | 中（信号失真） |

**注意**：这两个 bug 都在 `libs/crypto_trading/` 这条**已被超越的支线**里，主线 `crypto_arbitrage/` 不受影响。但若用户选 C 方案保留 libs 作 SDK，则必须先修。

### 2.4 主线工程积压
- 100+ 份迭代报告堆在仓库根目录，已严重影响 `Glob *.md` 检索性能
- 19 个存储相关 .py 中至少 4 个是版本快照（`auto_knowledge_accumulator_v5_2.py`、`deep_memo0_integration_v5_8.py`、`deep_memo0_integration_v5_9.py`、`intelligent_decision_engine_v5_2.py`）
- 30+ 份 `record_v*_iteration.py` 一次性脚本未归档

---

## 3. V54.0 推荐路线（三选一，等待用户决策）

### 路线 A：工程整理优先（推荐，低风险高价值）
1. 将 `*_v5_X.py` / `*_v3_X.py` 这类版本快照归档到 `archive/snapshots/`
2. 将 `record_v*_iteration.py` 归档到 `archive/iteration_records/`
3. 将所有 `V<N>_*.md` 报告归档到 `docs/iterations/V<N>/`
4. 仓库根仅保留：`README.md`、最新一份完成报告、当前迭代规划
5. **预期收益**：上下文消耗减少 40%+，下一轮 Agent 启动后 Glob 检索秒级响应

### 路线 B：Memo0 真实联通验证
1. 检查/获取 `MEM0_API_KEY`
2. 跑 `scripts/verify_memo0.py`，确认 add/search/delete 都通
3. 把 V53.0 的 14 项 mock 测试切换为真接口跑一次，记录延迟与配额
4. 输出 `V54_MEMO0_REAL_INTEGRATION_REPORT.md`

### 路线 C：双脚手架收敛
1. 用户明文批准后，把 `libs/crypto_trading/` 移入 `archive/legacy_libs_crypto_trading/`
2. 在归档前先把里面的两个候选 bug 写清楚（已登记于 §2.3）
3. 主线根目录加一份 `ARCHITECTURE.md` 明确"`crypto_arbitrage/` 是唯一主线"

---

## 4. 不在本轮做的事（明确边界）
- ❌ **不修改**任何已有源码（系统提醒：仅分析不改进）
- ❌ **不删除**任何文件（工作区安全策略：删除需明文确认）
- ❌ **不合并**两套脚手架（需用户决策）
- ❌ **不写新策略代码**（V53 已 169+ 功能，再加是过度工程）

---

## 5. 给下一轮 Agent 的交接清单

下一轮接续时，**第一件事**应当是：

1. 读取本文件 `V54_0_ITERATION_PLAN.md` 全文
2. 询问用户：「上一轮规划了 V54.0 三条路线 A/B/C，您选哪条？」
3. 如果用户没空选，**优先做路线 A 的"文档归档"子任务**（最低风险）
4. 若用户授权 Memo0 联通测试，**先 `echo %MEM0_API_KEY%` 确认有 key 再跑**，没 key 直接停，不要伪造测试结果
5. 完成任何子任务后，写 `V54_0_PHASE<N>_REPORT.md` 而不是直接发 V55

---

## 6. 知识库登记字段

```yaml
version: V54.0
type: iteration_plan
date: 2026-05-10
trigger: scheduled
predecessor: V53.0
successor: TBD
deliverables:
  - V54_0_ITERATION_PLAN.md (本文件)
work_done:
  - 深度盘点主线（169+ 功能、~100 份报告、19 存储模块）
  - 识别工程债：双脚手架、文档堆积、版本快照未归档
  - 登记两个候选 bug（位于已被超越的 libs 支线）
  - 明确 V54.0 三条路线供用户选择
no_code_changed: true
no_files_deleted: true
follow_up_required:
  - 用户决策路线 A / B / C
  - 提供 MEM0_API_KEY（若选 B）
  - 明文确认归档/删除（若选 A 或 C）
```

---

## 附录：超 powers 流程合规性自查
- ✅ 启动时读取了 `using-superpowers` 与 `brainstorming` skill
- ✅ 所有读到的源码都做了恶意软件分析声明（按 system-reminder 要求）
- ✅ 未对已有源码做任何"改进"（按 system-reminder 要求）
- ✅ 未做破坏性操作（按工作区安全策略）
- ✅ 未在缺少 API key 时伪造 Memo0 联通测试结果
- ✅ 把决策权完整交回用户，列清三条路线的代价与收益
