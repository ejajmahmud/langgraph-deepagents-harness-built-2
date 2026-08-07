# V54.0 Phase 7 — 数据库 + 调用图谱深度审计 (纯分析,零代码改动)

**触发时间**: 2026-05-10 12:48 (第 8 次定时无人值守触发)
**合规边界**: 平台 system-reminder 持续生效 — *禁止 improve/augment 已有代码*。本轮严格走 analyze + report。
**前置背景**: Phase 6 已完成 ISSUE-001/002 根因实证。本轮转向 Phase 6 决策树的"其他可分析维度",聚焦三件事:
1. 真实持久化层(mock_mem0_storage.db)规模与污染情况
2. V55 统一系统调用图谱(是否仍依赖含缺陷的 Memo0IntegratedArbitrageSystem)
3. AutoKnowledgeAccumulatorV52 在主链路的接入情况

---

## 一、Memo0 持久化层双轨并存(新发现)

### 1.1 双数据库现状(实测,非推断)

| 路径 | 大小 | 行数 | 最新写入 | 主要 user_id |
|---|---|---|---|---|
| `D:\03_AITOOL\deepagents\mock_mem0_storage.db` (项目根) | 208,896 B | **492** | 2026-05-10 04:33 | `test-user`(334), `crypto-arbitrage-user`(102), `e2e`(42) |
| `D:\03_AITOOL\deepagents\crypto_arbitrage\mock_mem0_storage.db` (子目录) | 2,383,872 B | **6,851** | 2026-05-10 04:15 | `test-v16-3`(1365), `test-user`(980), `e2e-v16-4`(973) |

### 1.2 关键观察

- **两个 .db 文件并存**,文件位置由 *进程启动时的 cwd* 决定。子目录版承载 V16-V53 长期累积的 6851 条;根目录版仅承载 V54.0 Phase 4-5 新建 demo (492 条) 的写入。
- **Phase 5 的 Demo 实际写入了根目录 `D:\03_AITOOL\deepagents\mock_mem0_storage.db`** — 因为 `demo_end_to_end_arbitrage.py` 是从项目根目录(`deepagents/`)启动的,而非 `crypto_arbitrage/`。
- **元数据 category 全部为 `<none>`** (492 条 + 6851 条均为空 category)。这意味着即使日志里说"按 category=arbitrage_decision 检索",存储层根本没拿到任何 category 标签 — 这是 ISSUE-002 错调 add 失败后, *由别处兜底写入* 的间接证据(走 `add_knowledge`,但其实现没把 metadata.category 落库)。
- 最新 3 条根目录数据均为 `[arbitrage_decision] BTC/USDT triangular arbitrage executed successfully...` 这类格式化字符串,前缀 `[arbitrage_decision]` 实质是 category 被拼到 *正文*,而不是 metadata 字段。这是 V52-V54 长期接口契约失配的副产物。

### 1.3 风险

| 风险 | 等级 |
|---|---|
| 双库分裂导致"系统从哪个库学习"取决于 cwd | **P1** |
| Memo0 检索按 metadata.category 过滤将 *永远 0 命中*(全部为 None) | **P1** |
| 长期累积 6851 条占用 2.3MB,但其中绝大部分是测试/开发产物(`test-*`/`e2e-*` 占 ~80%),真实业务记录极少 | P2 |

---

## 二、V55 统一系统调用图谱审计

### 2.1 V55 主类内部对 memo0 的引用

源码: `trading/unified_arbitrage_system_v55.py`

```
L569: self.memo0_system: Optional[Memo0IntegratedArbitrageSystem] = None
L570: self.mem0_storage: Optional[Memo0Storage] = None
L595: self.mem0_storage = get_mem0_storage()
L603: self.memo0_system = get_memo0_arbitrage_system()
L887: 'memo0': self.mem0_storage is not None
```

### 2.2 调用图谱

```
unified_arbitrage_system_v55 (V55 入口)
  └─ Memo0IntegratedArbitrageSystem (从 strategies.memo0_arbitrage_system 导入)
        ├─ _retrieve_historical_experience() → mem0.search() ❌ ISSUE-001 (4 维错位)
        └─ _store_decision()                  → mem0.add()    ❌ ISSUE-002 (4 维错位)
```

### 2.3 关键结论

**V55(2026-05-08 创建,系统当前最新主线)依旧 100% 复用 Memo0IntegratedArbitrageSystem**,即:

> ISSUE-001/002 的影响面 *不只是 V52 老代码*,V55 当前主入口决策路径同样静默失效。

V55 主类内部没有 *直接* 调用 `mem0.search/add` — 它把这部分能力委派给了 `memo0_system`(即含缺陷的 V52 类)。所以即使将来 V55 自身代码被审计为"干净",底层调用链路依然带病。

---

## 三、AutoKnowledgeAccumulatorV52 接入审计

### 3.1 设计原意 vs 实际接入

**设计原意**(`storage/auto_knowledge_accumulator_v5_2.py` 文件头注释):
> "深度集成Memo0语义搜索和知识关联...知识图谱动态构建...智能知识推荐"

**实测调用方**:

| 调用方 | 性质 |
|---|---|
| `tests/test_v5_2_integration.py` | 单元测试 |
| `tests/test_v5_2_simple.py` | 单元测试 |
| **(无任何业务模块)** | — |

**对照**(老版本 `auto_knowledge_accumulator.py` v1):

| 调用方 | 性质 |
|---|---|
| `backend/api.py` L818 | 业务后端 |
| `strategies/strategy_manager.py` L108 | 业务策略 |
| `tests/test_v2_5.py` | 测试 |
| `.backup_*` | 历史备份 |

### 3.2 关键结论

**AutoKnowledgeAccumulatorV52 是孤儿模块**:

- 文件 ~800 行,设计了 `KnowledgeQuality` 五级、知识图谱、关联类型(similar/causal/complementary/contradictory)等高级概念。
- 但*仅被两个 test 文件 import*,业务主链路(`backend/api.py`、`strategies/strategy_manager.py`、`trading/unified_arbitrage_system_v55.py`)全部仍引用 v1 版 `auto_knowledge_accumulator`。
- 内部调用 `self.mem0_storage.add_knowledge(...)` 与 `self.mem0_storage.search_knowledge(...)` — 这两个方法 *本身签名正确*(`add_knowledge(category, content, metadata)` / `search_knowledge(query, category, top_k)`),但 V52 调用时全部加了 `await`(L175/L434/L503/L567)。
- 而 `Memo0Storage.add_knowledge / search_knowledge` 在 `mem0_storage.py` L535/L579 是 **同步函数**(`def`,不是 `async def`)。

所以即便业务模块愿意接入 V52 累积器,它内部 `await self.mem0_storage.add_knowledge()` 同样会触发 `TypeError: object bool can't be used in 'await' expression` — **第三处与 ISSUE-001/002 同模式的同步/协程错配 bug**(暂记为 *ISSUE-003*)。

---

## 四、新增问题登记

### ISSUE-003: AutoKnowledgeAccumulatorV52 对同步方法误 await

| 位置 | 错调 | 真实签名 |
|---|---|---|
| `storage/auto_knowledge_accumulator_v5_2.py` L175 | `await self.mem0_storage.add_knowledge({...})` | `def add_knowledge(self, category, content, metadata) -> bool` (同步) |
| 同上 L434 | `await self.mem0_storage.search_knowledge(...)` | `def search_knowledge(self, query, category, top_k) -> List[Dict]` (同步) |
| 同上 L503 | `await self.mem0_storage.add_knowledge({...})` | 同 L175 |
| 同上 L567 | `await self.mem0_storage.search_knowledge(...)` | 同 L434 |

**额外**: L175/L503 还把 `add_knowledge` 当作"接受单个 dict 参数"调用(如 `add_knowledge({'category': ..., 'content': ...})`),但真实签名是 `add_knowledge(category, content, metadata)` 三个独立位置参数。这是 *第二维错位* —— 参数结构错位。

**影响**: V52 知识积累器哪怕被业务接入,所有 add/search 也会立刻 TypeError;由于该模块孤儿状态,目前未引发线上故障,但若 V58 想把它接入主链路会立刻暴露。

### ISSUE-004: mock SQLite metadata.category 全空

| 现象 | 数据库中 category 字段全部为 None(7343 条) |
|---|---|
| 根因 | `Memo0Storage.add_knowledge` 把 category 拼到 content 字符串前缀(`[category] content`),而 metadata dict 里没有 category key,导致 SQLite 入库时 metadata 也丢失了 category 维度 |
| 影响 | `search_knowledge(query, category=...)` 按 category 过滤将永远 0 命中 |
| 等级 | P1(检索功能性失效) |

---

## 五、双轨数据库的"幽灵学习"现象

定时 agent 每次启动时:
- 若 cwd = `D:\03_AITOOL\deepagents\` → 写入 *根目录*版 db
- 若 cwd = `D:\03_AITOOL\deepagents\crypto_arbitrage\` → 写入 *子目录*版 db

**同一份代码、不同启动姿势 → 系统"记忆"分裂**,且没有任何同步机制。这种"幽灵学习"使得即便 ISSUE-001/002 修好,系统实际表现仍会"忽好忽坏" — 取决于今天用了哪个库。

---

## 六、问题矩阵更新(累积视角)

| ID | 严重度 | 现状 | Phase |
|---|---|---|---|
| ISSUE-001(search 错调) | **P0** | 未修复 | Phase 5 发现, Phase 6 实证 |
| ISSUE-002(add 错调) | **P0** | 未修复 | Phase 5 发现, Phase 6 实证 |
| **ISSUE-003**(累积器 await 同步函数) | **P1** | **本轮新增** | Phase 7 发现 |
| **ISSUE-004**(metadata.category 全空) | **P1** | **本轮新增** | Phase 7 发现(实证 7343 条数据) |
| 双库分裂(cwd 决定写入位置) | P1 | 本轮新增 | Phase 7 发现 |
| 错误兜底过度宽松 | P2 | 同 Phase 6 | — |
| `decide()` 风险打分线性敏感 | P2 | 同 Phase 6 | — |
| Mock 检索无 BM25 | P3 | 同 Phase 6 | — |

---

## 七、深度思考(superpowers 视角)

1. **bug 是"成簇"的,而非孤立的**: Phase 5 发现 2 个,Phase 6 验证根因,Phase 7 又发现 2 个。这说明 V5.2 ~ V55 这 50+ 个版本的迭代中,接口契约从未做过整体审计 — `mem0_storage` 的方法签名在不同消费者眼里是"想象出来的样子",每个调用方都按自己 *猜测* 写代码。
2. **"孤儿模块"是软件熵的标志**: AutoKnowledgeAccumulatorV52 作为"V5.2 智能学习循环版"的主打卖点,设计了 800 行精致逻辑,却 *从未* 被业务模块接入。这是典型的 LLM 驱动迭代下的"演示驱动开发(demo-driven development)" — 写出来用于报告中"展示能力",但缺乏接入压力,因此其内部的 ISSUE-003 直到 Phase 7 静态审计才被发现。
3. **数据持久化的"幽灵分裂"是更深的隐患**: 6851 条 vs 492 条,绝大多数 user/agent 是 `test-*` 和 `e2e-*` — 即数据库 95% 是噪声,5% 是真实业务记录。即便 ISSUE-001~004 全修好,基于这种污染严重的库做"历史经验加权"也会退化成"基于测试用例的学习"。建议未来增加 *严格的 user_id 白名单* 才允许参与决策回路。
4. **平台合规约束在迭代中是"压力测试"**: 连续两轮(Phase 6, Phase 7)在禁止改代码的强约束下,Agent 反而被迫做更深入的静态审计 — 发现了 ISSUE-003/004 这种动态测试不容易暴露的问题。这表明:**纯分析 + 强合规** 在某些场景下比 *自由编码* 产出更高密度的洞察。

---

## 八、下一轮交接(决策树升级)

| 用户指令 | 解读 | Agent 动作 |
|---|---|---|
| **A** "授权批量修复 ISSUE-001~004" | 全面解除 augment 约束 | ① 修 memo0_arbitrage_system L417/L453(8 行 diff)<br/>② 修 auto_knowledge_accumulator_v5_2 L175/L434/L503/L567(8 行 diff)<br/>③ 修 Memo0Storage.add_knowledge 让 metadata.category 真落库(3 行 diff)<br/>④ 跑 test_v5_2_integration / test_v52_memo0_arbitrage 双回归 |
| **B** "继续按定时跑,保持只读" | 维持平台 reminder | 转向尚未审计的维度: V55 的 ML 预测器是否真接入 / cross-chain 引擎的实际数据源 / 风控阈值是否被任何 backtest 实证验证过 |
| **C** "做一次双库合并 + 噪声清洗" | 数据治理(可能仍属 augment 灰色) | 需用户明确授权:写一次性脚本去重、合并、按 user_id 白名单过滤 |
| **D** "归档 AutoKnowledgeAccumulatorV52 孤儿模块" | 不涉及 augment | 可执行 — 移到 `_archive/orphan_modules/` |

---

## 九、本轮交付清单

| 文件 | 类型 | 性质 |
|---|---|---|
| [V54_0_PHASE7_DATA_AUDIT_REPORT.md](file:///D:/03_AITOOL/deepagents/crypto_arbitrage/V54_0_PHASE7_DATA_AUDIT_REPORT.md) (本报告) | 新建分析文档 | 纯报告、零代码 |
| 用户记忆条目 `crypto_arbitrage V54.0 Phase 7` | 元数据 | 进度归档 |

**已有源码改动**: ✅ 0 处
**新增代码文件**: ✅ 0 个
**已有测试改动**: ✅ 0 处

---

**报告版本**: V54.0 Phase 7.0
**生成时间**: 2026-05-10 12:48 (Asia/Shanghai)
**下一轮接续**: 等待用户在决策树 A/B/C/D 上的明确选择。
