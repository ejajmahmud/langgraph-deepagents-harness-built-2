# Memo0 配置指南

**适用版本**: V3.5+
**更新日期**: 2026-04-17

---

## 目录

1. [Memo0 简介](#memo0-简介)
2. [获取 API Key](#获取-api-key)
3. [配置方法](#配置方法)
4. [验证配置](#验证配置)
5. [常见问题](#常见问题)
6. [降级模式](#降级模式)

---

## Memo0 简介

### 什么是 Memo0？

Memo0 是一个 AI 驱动的智能记忆平台，为您的交易系统提供：

- **语义搜索**: 基于AI的智能知识检索
- **自动分类**: 自动整理和分类交易知识
- **智能推荐**: 基于历史经验提供决策建议
- **持续学习**: 从每次交易中自动学习和优化

### 为什么需要 Memo0？

在本系统中，Memo0 提供：

1. **智能决策支持**: 基于历史交易经验推荐最佳策略
2. **知识自动积累**: 自动记录重要决策和结果
3. **模式识别**: 识别市场模式和交易机会
4. **性能优化**: 基于历史表现自动调优参数

### 降级模式

如果未配置 Memo0，系统会自动降级到 SQLite 本地存储模式：
- ✅ 基础功能正常工作
- ⚠️ AI 智能功能受限
- ⚠️ 语义搜索不可用
- ⚠️ 智能推荐不可用

---

## 获取 API Key

### 步骤 1: 注册 Memo0 账户

1. 访问 [Memo0 平台](https://platform.mem0.ai)
2. 点击 "Sign Up" 注册账户
3. 完成邮箱验证

### 步骤 2: 创建 API Key

1. 登录后进入 Dashboard
2. 导航到 "API Keys" 页面
3. 点击 "Create New API Key"
4. 输入 Key 名称（例如：`crypto-arbitrage-bot`）
5. 选择合适的权限（建议选择 `Read & Write`）
6. 点击 "Generate"

### 步骤 3: 保存 API Key

⚠️ **重要提示**:
- API Key 只会显示一次，请立即复制并妥善保存
- 不要将 API Key 提交到版本控制系统
- 建议使用环境变量存储 API Key

### 步骤 4: 获取 User ID 和 Agent ID（可选）

如果需要使用多用户或多 Agent 功能：

1. 在 Dashboard 中创建新的 User
2. 记录 User ID（格式：`user_xxxxxxxx`）
3. 创建新的 Agent
4. 记录 Agent ID（格式：`agent_xxxxxxxx`）

**默认值**（如果不配置）：
- User ID: `crypto-arbitrage-user`
- Agent ID: `trading-bot`

---

## 配置方法

### 方法 1: 使用环境变量（推荐）

#### 1. 创建 `.env` 文件

在项目根目录创建 `.env` 文件：

```bash
# Memo0 配置
MEM0_API_KEY=your_actual_api_key_here
MEM0_USER_ID=crypto-arbitrage-user
MEM0_AGENT_ID=trading-bot
```

#### 2. 确保 `.env` 文件安全

将 `.env` 添加到 `.gitignore`：

```gitignore
# 环境变量
.env
.env.local
.env.production
```

#### 3. 验证环境变量加载

系统会在启动时自动加载 `.env` 文件中的环境变量。

### 方法 2: 直接修改配置文件

#### 1. 编辑 `config/config.yaml`

```yaml
# Memo0 配置
mem0:
  api_key: "your_actual_api_key_here"  # 替换为真实的 API Key
  user_id: "crypto-arbitrage-user"
  agent_id: "trading-bot"
  rerank: true
  keyword_search: false
```

#### 2. 保存配置文件

⚠️ **安全提示**:
- 如果使用配置文件，请确保不将其提交到公开仓库
- 建议使用 `config.yaml.local` 并添加到 `.gitignore`

### 方法 3: 系统环境变量

#### Windows (PowerShell)

```powershell
$env:MEM0_API_KEY="your_actual_api_key_here"
$env:MEM0_USER_ID="crypto-arbitrage-user"
$env:MEM0_AGENT_ID="trading-bot"
```

#### Linux/macOS (Bash)

```bash
export MEM0_API_KEY="your_actual_api_key_here"
export MEM0_USER_ID="crypto-arbitrage-user"
export MEM0_AGENT_ID="trading-bot"
```

---

## 验证配置

### 自动验证

系统启动时会自动验证 Memo0 配置：

```bash
python main.py
```

**成功输出**：
```
✅ Memo0 API Key 已配置，AI 智能功能已启用
```

**降级模式输出**：
```
⚠️  Memo0 API Key 未配置
AI 智能功能将不可用，系统将使用 SQLite 降级模式
请设置环境变量 MEM0_API_KEY 或在 config.yaml 中配置
获取 API Key: https://platform.mem0.ai
```

### 手动验证脚本

创建验证脚本 `scripts/verify_memo0.py`：

```python
"""Memo0 配置验证脚本"""

import os
import sys
from dotenv import load_dotenv

def verify_memo0_config():
    """验证 Memo0 配置"""
    load_dotenv()

    print("=" * 60)
    print("Memo0 配置验证")
    print("=" * 60)

    # 检查 API Key
    api_key = os.getenv('MEM0_API_KEY', '')
    if api_key:
        print(f"✅ MEM0_API_KEY: 已配置 ({len(api_key)} 字符)")
    else:
        print("❌ MEM0_API_KEY: 未配置")

    # 检查 User ID
    user_id = os.getenv('MEM0_USER_ID', 'crypto-arbitrage-user')
    print(f"✅ MEM0_USER_ID: {user_id}")

    # 检查 Agent ID
    agent_id = os.getenv('MEM0_AGENT_ID', 'trading-bot')
    print(f"✅ MEM0_AGENT_ID: {agent_id}")

    # 尝试导入 Memo0
    try:
        from storage.memo0 import Memo0Storage
        print("✅ Memo0 模块: 可用")

        # 尝试初始化
        if api_key:
            try:
                storage = Memo0Storage(
                    api_key=api_key,
                    user_id=user_id,
                    agent_id=agent_id
                )
                print("✅ Memo0 初始化: 成功")

                # 测试连接
                health = storage.check_health()
                if health.get('healthy'):
                    print("✅ Memo0 连接: 正常")
                else:
                    print(f"⚠️  Memo0 连接: {health.get('message', '异常')}")

            except Exception as e:
                print(f"❌ Memo0 初始化: 失败 - {e}")
        else:
            print("⚠️  Memo0 初始化: 跳过（无 API Key）")

    except ImportError as e:
        print(f"❌ Memo0 模块: 不可用 - {e}")

    print("=" * 60)

    # 返回状态
    return bool(api_key)

if __name__ == "__main__":
    success = verify_memo0_config()
    sys.exit(0 if success else 1)
```

**运行验证脚本**：
```bash
python scripts/verify_memo0.py
```

---

## 常见问题

### Q1: API Key 配置后仍然显示降级模式？

**可能原因**：
1. 环境变量未正确加载
2. 配置文件路径错误
3. API Key 格式不正确

**解决方法**：
1. 确认 `.env` 文件在项目根目录
2. 检查 API Key 是否有引号或空格
3. 重启系统
4. 运行验证脚本检查

### Q2: Memo0 连接超时或失败？

**可能原因**：
1. 网络连接问题
2. API Key 无效或过期
3. Memo0 服务暂时不可用

**解决方法**：
1. 检查网络连接
2. 重新生成 API Key
3. 查看 Memo0 平台状态
4. 系统会自动降级到 SQLite 模式

### Q3: 如何测试 Memo0 功能？

**测试方法**：
1. 运行系统模拟交易
2. 检查知识库是否有自动记录
3. 尝试语义搜索功能
4. 查看智能推荐是否生效

### Q4: Memo0 是否免费？

**定价信息**：
- 免费套餐：有限的 API 调用次数
- 付费套餐：更多调用次数和高级功能

**建议**：
- 开发测试：使用免费套餐
- 生产环境：根据使用量选择合适套餐
- 查看 [Memo0 定价页面](https://platform.mem0.ai/pricing) 获取最新信息

### Q5: 数据安全性和隐私？

**安全措施**：
1. 所有数据通过 HTTPS 加密传输
2. API Key 不要硬编码在代码中
3. 敏感数据可以考虑本地存储
4. 定期检查 Memo0 的隐私政策

**最佳实践**：
- 使用环境变量存储 API Key
- 定期轮换 API Key
- 限制 API Key 权限
- 监控 API 使用情况

---

## 降级模式

### 降级模式特性

当 Memo0 不可用时，系统会自动降级到 SQLite 模式：

**可用功能**：
- ✅ 基础套利策略
- ✅ 风险管理
- ✅ 交易执行
- ✅ 性能监控
- ✅ 基础知识存储

**不可用功能**：
- ❌ AI 语义搜索
- ❌ 智能知识推荐
- ❌ 自动模式识别
- ❌ 高级决策优化

### 切换回完整模式

配置 Memo0 API Key 后，重启系统即可自动切换回完整模式：

```bash
# 配置 API Key
# 编辑 .env 文件，添加 MEM0_API_KEY

# 重启系统
python main.py
```

### 监控降级状态

系统会持续监控 Memo0 连接状态：
- 连续失败 5 次（120秒内）会触发熔断
- 熔断后会暂时停止尝试连接
- 熔断会在一段时间后自动恢复

---

## 下一步

配置完成后，建议：

1. ✅ 验证配置是否成功
2. ✅ 运行模拟交易测试
3. ✅ 检查知识库自动记录功能
4. ✅ 测试智能推荐功能
5. ✅ 根据需要调整参数

## 技术支持

- **Memo0 官方文档**: [https://docs.mem0.ai](https://docs.mem0.ai)
- **Memo0 平台**: [https://platform.mem0.ai](https://platform.mem0.ai)
- **问题反馈**: 通过项目 GitHub Issues 提交

---

**最后更新**: 2026-04-17
**文档版本**: V1.0
**适用系统版本**: V3.5+
