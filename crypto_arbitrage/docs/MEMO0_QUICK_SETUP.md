# Memo0 快速配置指南

## 🚀 快速开始

### 第一步：获取 Memo0 API Key

1. 访问 Memo0 官网：https://platform.mem0.ai
2. 注册账号（如果还没有）
3. 创建新的 API Key
4. 复制 API Key（格式类似：`mem0-xxxxxxxxxxxxx`）

### 第二步：配置 API Key

#### 方法 1：环境变量配置（推荐）

```bash
# 在 .env 文件中添加
MEM0_API_KEY=your_actual_api_key_here
```

#### 方法 2：配置文件配置

编辑 `config/config.yaml`：

```yaml
mem0:
  api_key: "your_actual_api_key_here"  # 在这里填入你的 API Key
  user_id: "crypto-arbitrage-user"
  agent_id: "trading-bot"
  rerank: true
  keyword_search: false
```

### 第三步：验证配置

运行配置验证：

```bash
cd crypto_arbitrage
python -c "
from config.config_manager import load_config
config = load_config()
api_key = config.get('mem0', {}).get('api_key')
if api_key:
    print('✅ Memo0 API Key 已配置')
    print(f'API Key 长度: {len(api_key)} 字符')
else:
    print('❌ Memo0 API Key 未配置')
"
```

---

## 🔧 高级配置

### 优化 Memo0 性能参数

```yaml
mem0:
  api_key: "your_api_key"
  user_id: "crypto-arbitrage-user"
  agent_id: "trading-bot"

  # 搜索优化
  rerank: true              # 启用结果重排序（提升准确性）
  keyword_search: false      # 禁用关键词搜索（纯语义搜索）
  top_k: 10                # 返回前10个结果
  score_threshold: 0.7      # 相似度阈值（0-1）

  # 性能优化
  cache_ttl: 300           # 缓存5分钟
  max_retries: 3           # 最大重试次数
  timeout: 30              # 请求超时（秒）
```

### 多环境配置

**开发环境**：
```bash
# .env.development
MEM0_API_KEY=dev_api_key
MEM0_USER_ID=crypto-arbitrage-dev
```

**生产环境**：
```bash
# .env.production
MEM0_API_KEY=prod_api_key
MEM0_USER_ID=crypto-arbitrage-prod
```

---

## ✅ 功能验证

### 1. 基础连接测试

```python
import asyncio
from storage.mem0_storage import initialize_mem0, get_mem0_storage

async def test_mem0_connection():
    # 初始化 Memo0
    storage = initialize_mem0()

    if storage is None:
        print("❌ Memo0 初始化失败")
        return False

    print("✅ Memo0 初始化成功")

    # 测试添加知识
    test_knowledge = {
        "content": "这是一条测试知识",
        "metadata": {
            "type": "test",
            "timestamp": "2026-04-18"
        }
    }

    try:
        result = await storage.add_knowledge(test_knowledge)
        print(f"✅ 知识添加成功: {result}")

        # 测试搜索
        search_results = await storage.search_knowledge("测试知识", top_k=1)
        print(f"✅ 搜索成功: 找到 {len(search_results)} 条结果")

        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

# 运行测试
asyncio.run(test_mem0_connection())
```

### 2. 语义搜索测试

```python
import asyncio
from storage.mem0_storage import get_mem0_storage

async def test_semantic_search():
    storage = get_mem0_storage()

    if storage is None:
        print("❌ Memo0 未配置")
        return

    # 添加测试知识
    test_knowledges = [
        {"content": "BTC价格上涨时，跨交易所套利机会增加", "metadata": {"type": "strategy"}},
        {"content": "高波动率环境下，三角套利风险较高", "metadata": {"type": "risk"}},
        {"content": "资金费率为正时，适合做空资金费率套利", "metadata": {"type": "strategy"}},
    ]

    for knowledge in test_knowledges:
        await storage.add_knowledge(knowledge)

    # 测试语义搜索
    queries = [
        "比特币价格上涨时应该用什么策略？",
        "什么时候三角套利风险比较高？",
        "如何利用资金费率赚钱？"
    ]

    for query in queries:
        results = await storage.search_knowledge(query, top_k=2)
        print(f"\n查询: {query}")
        print(f"结果: {len(results)} 条")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('content', 'N/A')[:50]}...")

asyncio.run(test_semantic_search())
```

---

## 🔍 故障排查

### 问题 1：API Key 无效

**症状**：
```
ERROR: Memo0 API Key 验证失败
```

**解决方案**：
1. 检查 API Key 是否正确复制
2. 确认 API Key 没有过期
3. 检查账号是否有足够的配额

### 问题 2：连接超时

**症状**：
```
ERROR: Memo0 请求超时
```

**解决方案**：
```yaml
mem0:
  timeout: 60  # 增加超时时间
  max_retries: 5  # 增加重试次数
```

### 问题 3：搜索结果不准确

**症状**：搜索结果与查询不相关

**解决方案**：
```yaml
mem0:
  rerank: true              # 启用重排序
  score_threshold: 0.8      # 提高相似度阈值
  top_k: 5                 # 减少返回结果数量
```

---

## 📊 性能优化建议

### 1. 查询缓存

```python
from functools import lru_cache
import time

class Memo0StorageWithCache:
    def __init__(self, storage):
        self.storage = storage
        self.cache = {}
        self.cache_ttl = 300  # 5分钟

    @lru_cache(maxsize=100)
    async def search_knowledge(self, query, top_k=10):
        # 检查缓存
        cache_key = f"{query}:{top_k}"
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result

        # 调用实际搜索
        result = await self.storage.search_knowledge(query, top_k)

        # 缓存结果
        self.cache[cache_key] = (result, time.time())

        return result
```

### 2. 批量操作

```python
async def batch_add_knowledge(knowledges):
    """批量添加知识，减少 API 调用"""
    tasks = [storage.add_knowledge(k) for k in knowledges]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 3. 异步查询

```python
async def parallel_search(queries):
    """并行执行多个查询"""
    tasks = [storage.search_knowledge(q, top_k=5) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 🔒 安全建议

### 1. 环境变量保护

确保 `.env` 文件不被提交到版本控制：

```bash
# .gitignore
.env
.env.local
.env.*.local
```

### 2. API Key 轮换

定期更换 API Key，建议每 90 天轮换一次。

### 3. 访问控制

限制 API Key 的使用范围和权限。

---

## 📈 监控和维护

### 监控指标

- **API 调用次数**：避免超出配额
- **响应时间**：目标 < 1秒
- **错误率**：目标 < 1%
- **缓存命中率**：目标 > 80%

### 维护任务

- **每日**：检查 API 调用配额
- **每周**：清理无效知识
- **每月**：评估和优化查询性能
- **每季度**：API Key 轮换

---

## 📞 获取帮助

如果遇到问题：

1. 查看系统日志：`logs/memo0.log`
2. 检查 Memo0 平台状态：https://status.mem0.ai
3. 查阅 Memo0 文档：https://docs.mem0.ai
4. 提交 Issue：项目 GitHub Issues

---

**最后更新**: 2026-04-18
**版本**: V5.2
**维护者**: AI Assistant (CryptoArbitrage Team)
