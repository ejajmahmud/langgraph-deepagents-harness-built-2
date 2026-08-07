# Crypto Arbitrage V15.0 配置使用指南

## 🎯 V15.0 核心改进

V15.0版本主要针对以下方面进行了深度优化：

1. **混合存储系统** - 云端Memo0 + 本地向量 + 内存缓存的多层架构
2. **Memo0云存储完善** - 增强的API配置、熔断器、重试机制
3. **测试覆盖率提升** - 目标从78%提升到90%
4. **性能基准建立** - 明确的响应时间和吞吐量目标
5. **低风险套利增强** - 预检机制、执行优化、风险控制增强

---

## 🔧 Memo0 云存储配置

### 方式1：环境变量配置（推荐）

在项目根目录创建 `.env` 文件：

```bash
# Memo0 API 配置
MEM0_API_KEY=your_mem0_api_key_here
MEM0_USER_ID=crypto-arbitrage-v15-user
MEM0_AGENT_ID=trading-bot-v15
```

**获取API Key**：
1. 访问 [Memo0 Platform](https://platform.mem0.ai)
2. 注册/登录账户
3. 创建新的API Key
4. 复制API Key到 `.env` 文件

### 方式2：配置文件配置

在 `config/config_v15_0.yaml` 中配置：

```yaml
mem0:
  api_key: "your_mem0_api_key_here"
  user_id: "crypto-arbitrage-v15-user"
  agent_id: "trading-bot-v15"

  # 高级配置
  timeout: 30
  search:
    top_k: 20
    score_threshold: 0.6
  cache:
    enabled: true
    ttl: 300
```

---

## 🏗️ 混合存储系统配置

### 存储层级说明

V15.0实现了四层存储架构：

1. **热缓存 (HOT_CACHE)** - 内存缓存，最快访问
2. **本地快速存储 (LOCAL_FAST)** - SQLite，中等速度
3. **云端主存储 (CLOUD_PRIMARY)** - Memo0，持久化
4. **云端备份存储 (CLOUD_BACKUP)** - S3/Azure/GCS，灾难恢复

### 智能路由配置

```yaml
hybrid_storage_v15:
  intelligent_routing:
    enabled: true
    read_preference: "hot_cache_first"  # 读取优先级
    write_preference: "async_cloud"     # 写入策略
    search_strategy: "hybrid"            # 搜索策略
```

**读取优先级选项**：
- `hot_cache_first` - 优先使用缓存（最快）
- `cloud_first` - 优先使用云端（最新数据）
- `balanced` - 智能平衡（推荐）

**写入策略选项**：
- `immediate` - 立即同步到云端
- `async_cloud` - 异步同步（性能最佳）
- `local_only` - 仅本地存储（离线模式）

### 故障切换配置

```yaml
hybrid_storage_v15:
  failover:
    enabled: true
    auto_switch: true
    health_check_interval: 60
    max_failures_before_switch: 3
```

系统会自动检测云端存储健康状态，失败时自动切换到本地存储。

---

## 🧪 测试优化配置

### 覆盖率目标设定

```yaml
testing_v15:
  enabled: true
  coverage:
    target_overall: 0.90    # 总体目标90%
    target_critical: 0.95   # 关键模块95%
    target_strategies: 0.90  # 策略模块90%
```

### 运行测试套件

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_strategies_comprehensive.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### Mock配置

```yaml
testing_v15:
  mocking:
    external_apis: true
    database_operations: true
    exchange_connections: true
```

这确保测试不依赖外部服务，提高稳定性和执行速度。

---

## ⚡ 性能基准配置

### 响应时间目标

```yaml
performance_benchmarks:
  latency_targets:
    api_calls: 100        # API调用 < 100ms
    search_operations: 200  # 搜索操作 < 200ms
    trade_execution: 1000   # 交易执行 < 1s
    risk_assessment: 500   # 风险评估 < 500ms
```

### 吞吐量目标

```yaml
performance_benchmarks:
  throughput_targets:
    trades_per_minute: 10
    api_calls_per_second: 100
    search_queries_per_second: 50
```

### 运行性能基准测试

```bash
# 运行基准测试
python scripts/benchmark_performance.py

# 查看性能报告
cat reports/performance_benchmark_report.json
```

---

## 🎯 低风险套利引擎配置

### 预检机制

```yaml
low_risk_arbitrage_engine_v15:
  pre_check:
    enabled: true
    risk_assessment: true
    liquidity_check: true
    volatility_analysis: true
    correlation_check: true
```

### 执行优化

```yaml
low_risk_arbitrage_engine_v15:
  execution:
    step_verification: true
    auto_rollback: true
    max_execution_time: 30
    parallel_steps: false
```

### 风险控制增强

```yaml
low_risk_arbitrage_engine_v15:
  risk_control:
    dynamic_stop_loss: true
    trailing_stop_enabled: true
    position_sizing: "kelly"
    max_correlation_exposure: 0.7
```

---

## 🚀 快速开始

### 1. 基础配置

```bash
# 复制配置文件
cp config/config_v15_0.yaml config/config.yaml

# 编辑配置文件
nano config/config.yaml
```

### 2. 设置API密钥

```bash
# 创建环境变量文件
cat > .env << EOF
MEM0_API_KEY=your_api_key_here
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret
EOF
```

### 3. 验证配置

```bash
# 运行配置验证
python scripts/validate_config_v15.py

# 检查Memo0连接
python scripts/test_memo0_connection.py
```

### 4. 启动系统

```bash
# 仿真模式
python main.py --mode simulation

# 模拟交易模式
python main.py --mode paper_trading

# 实盘交易模式（谨慎！）
python main.py --mode live_trading
```

---

## 📊 监控和调试

### 查看系统状态

```bash
# 查看存储系统健康状态
python scripts/check_storage_health.py

# 查看性能指标
python scripts/monitor_performance.py

# 查看测试覆盖率
python scripts/generate_coverage_report.py
```

### 日志查看

```bash
# 实时查看日志
tail -f logs/crypto_arbitrage.log

# 查看错误日志
grep ERROR logs/crypto_arbitrage.log

# 查看性能日志
tail -f logs/performance.log
```

---

## 🔧 常见问题解决

### Memo0连接失败

**问题**：`Memo0 API Key 未配置`

**解决方案**：
1. 检查 `.env` 文件是否存在
2. 确认 `MEM0_API_KEY` 已设置
3. 验证API Key格式正确

### 测试覆盖率低

**问题**：测试覆盖率低于目标

**解决方案**：
1. 运行完整测试套件：`pytest tests/ --cov=.`
2. 查看未覆盖代码：`open htmlcov/index.html`
3. 为未覆盖代码添加测试用例

### 性能不达标

**问题**：响应时间或吞吐量低于目标

**解决方案**：
1. 检查缓存配置是否启用
2. 优化数据库查询和索引
3. 考虑增加异步工作线程数

---

## 📈 性能优化建议

### 1. 缓存优化

- 启用热缓存（推荐大小：1000-2000）
- 配置合适的TTL（推荐：300-600秒）
- 启用预取功能

### 2. 数据库优化

- 为常用查询创建索引
- 使用连接池（推荐大小：10-20）
- 定期清理过期数据

### 3. API调用优化

- 启用请求缓存
- 使用批量操作
- 实现熔断器防止雪崩

### 4. 异步处理

- 启用异步操作
- 合理设置工作线程数（推荐：4-8）
- 使用队列管理任务

---

## 🎓 最佳实践

### 开发环境

```yaml
system:
  mode: "simulation"  # 使用仿真模式

testing_v15:
  enabled: true
  mocking:
    external_apis: true  # Mock外部API
```

### 测试环境

```yaml
system:
  mode: "paper_trading"  # 使用模拟交易

performance_benchmarks:
  enabled: true  # 启用性能监控
```

### 生产环境

```yaml
system:
  mode: "live_trading"  # 谨慎使用实盘模式

hybrid_storage_v15:
  failover:
    enabled: true  # 启用故障切换
```

---

## 🔐 安全建议

1. **API密钥保护**
   - 永远不要将API密钥提交到版本控制
   - 使用 `.env` 文件或密钥管理服务
   - 定期轮换API密钥

2. **权限控制**
   - 使用最小权限原则
   - 为不同环境使用不同的API密钥
   - 限制API密钥的IP访问

3. **数据备份**
   - 定期备份本地数据库
   - 验证云端数据同步
   - 测试灾难恢复流程

---

## 📞 获取帮助

- **文档**：查看项目 `docs/` 目录
- **示例**：查看 `examples/` 目录
- **问题反馈**：提交GitHub Issue
- **社区支持**：加入Discord/Slack社区

---

**配置版本**：V15.0
**最后更新**：2026-04-29
**维护状态**：✅ 活跃维护
