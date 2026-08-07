# 系统架构知识库

## 系统概述

### 设计理念
数字货币套利交易系统基于 DeepAgents 框架构建，采用模块化、可扩展的架构设计，实现了从市场分析、机会识别、风险控制到交易执行的完整自动化流程。

### 核心特性
- **AI驱动**: 利用大语言模型进行智能决策和优化
- **多策略支持**: 同时运行多种套利策略
- **风险管理**: 完善的风险控制和实时监控
- **知识积累**: 自动记录和分析交易经验
- **持续进化**: 基于反馈不断优化系统

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                  用户界面层                       │
│  (Web界面 / CLI / API)                          │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  DeepAgents 层                  │
│  - 智能决策引擎                                 │
│  - 工具调用管理                                  │
│  - 上下文管理                                   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  应用逻辑层                      │
│  ├── 策略管理模块                              │
│  ├── 风险管理模块                              │
│  ├── 交易执行模块                              │
│  └── 监控告警模块                              │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌▼──────────┐
│ 策略引擎    │ │交易所集成 │ │存储系统   │
│ - 跨交易所  │ │- 多交易所 │ │- 知识库  │
│ - 三角套利  │ │- API统一  │ │- 交易记录 │
│ - 基差套利  │ │- 连接池   │ │- 性能数据 │
│ - 统计套利  │ │- 错误处理 │ │- 项目进度 │
│ - 资金费率  │ │           │ │           │
└──────────────┘ └───────────┘ └───────────┘
        │
┌───────▼──────┐
│  外部服务    │
│ - 市场数据   │
│ - 价格API    │
│ - 通知服务   │
└──────────────┘
```

---

## 核心模块

### 1. DeepAgents 智能体

#### 功能
- 统一的决策引擎
- 工具调用管理
- 上下文理解
- 多步骤任务规划

#### 技术栈
- **框架**: DeepAgents (基于 LangGraph)
- **模型**: Claude Sonnet 4.5 / GPT-4o / Gemini 3
- **提示工程**: 结构化提示模板

#### 核心工具
- `scan_arbitrage_opportunities`: 扫描套利机会
- `execute_arbitrage`: 执行套利交易
- `get_risk_status`: 获取风险状态
- `get_performance_stats`: 获取性能统计
- `analyze_market_conditions`: 分析市场条件
- `record_knowledge`: 记录知识

---

### 2. 策略引擎

#### 策略类型

**跨交易所套利** (`strategies/cross_exchange.py`)
- 功能: 利用不同交易所间价差
- 核心类: `CrossExchangeArbitrageStrategy`
- 主要方法:
  - `scan_opportunities()`: 扫描机会
  - `execute_arbitrage()`: 执行交易
  - `get_performance_stats()`: 性能统计

**三角套利** (`strategies/triangular_arbitrage.py`)
- 功能: 利用三种货币间价差
- 核心类: `TriangularArbitrageStrategy`
- 主要方法:
  - `scan_opportunities()`: 扫描机会
  - `execute_arbitrage()`: 执行交易
  - `get_performance_stats()`: 性能统计

**基差套利** (`strategies/basis_trading.py`)
- 功能: 利用现货期货价差
- 核心类: `BasisTradingStrategy`
- 主要方法:
  - `scan_opportunities()`: 扫描机会
  - `execute_arbitrage()`: 执行交易

**统计套利** (`strategies/statistical_arbitrage.py`)
- 功能: 基于统计关系的套利
- 核心类: `StatisticalArbitrageStrategy`
- 主要方法:
  - `scan_opportunities()`: 扫描机会
  - `execute_arbitrage()`: 执行交易

**资金费率套利** (`strategies/funding_rate.py`)
- 功能: 利用永续合约资金费率
- 核心类: `FundingRateStrategy`
- 主要方法:
  - `scan_opportunities()`: 扫描机会
  - `execute_arbitrage()`: 执行交易

#### 策略管理
- 策略注册和初始化
- 参数配置和热更新
- 性能监控和评估
- 自动启用/禁用

---

### 3. 交易所集成

#### 核心类
**ExchangeManager** (`tools/exchange_api.py`)
- 功能: 统一管理多个交易所
- 支持交易所:
  - Binance
  - OKX
  - Huobi
  - Coinbase
  - Kraken
  - 等其他支持 ccxt 的交易所

#### 主要方法
- `get_ticker()`: 获取行情
- `get_order_book()`: 获取订单簿
- `get_balance()`: 获取余额
- `place_order()`: 下单
- `cancel_order()`: 取消订单
- `get_trading_fees()`: 获取手续费

#### 技术特性
- 异步 I/O 支持
- 连接池管理
- 错误重试机制
- 限流控制

---

### 4. 风险管理

#### 核心组件

**RiskManager** (`tools/risk_management.py`)
- 功能: 实时风险监控和控制
- 主要方法:
  - `check_position_risk()`: 检查仓位风险
  - `update_exposure()`: 更新敞口
  - `record_trade_result()`: 记录交易结果
  - `check_drawdown()`: 检查回撤
  - `get_risk_summary()`: 获取风险摘要

**IntelligentStopLoss**
- 功能: 智能止损和止盈
- 主要方法:
  - `calculate_stop_loss()`: 计算止损价格
  - `calculate_take_profit()`: 计算止盈价格
  - `update_trailing_stop()`: 更新追踪止损

**MarketConditionAnalyzer**
- 功能: 市场条件分析
- 主要方法:
  - `analyze_market_conditions()`: 分析市场条件
  - `get_trading_recommendation()`: 获取交易建议

---

### 5. 存储系统

#### 知识库

**KnowledgeBase** (`storage/knowledge_base.py`)
- 功能: 存储和管理交易知识
- 数据表:
  - `strategies`: 策略知识
  - `market_patterns`: 市场模式
  - `risk_events`: 风险事件
  - `trades`: 交易记录
  - `performance_metrics`: 性能指标
  - `project_progress`: 项目进度
  - `knowledge_entries`: 通用知识

#### 项目追踪

**ProjectTracker** (`storage/project_tracker.py`)
- 功能: 记录项目进度和迭代历史
- 主要方法:
  - `record_iteration()`: 记录迭代
  - `get_iteration_history()`: 获取历史
  - `generate_progress_report()`: 生成报告
  - `analyze_progress()`: 分析进度

---

### 6. 监控告警

#### 监控指标
- 实时风险指标
- 策略性能指标
- 系统健康指标
- 交易所连接状态

#### 告警系统
- 多级别告警 (信息/警告/严重/紧急)
- 多渠道通知 (邮件/Telegram/微信)
- 告警抑制和聚合
- 告警历史记录

---

## 数据流

### 交易执行流程

```
1. 市场数据采集
   ├─ 交易所 API
   ├─ 价格数据
   └─ 订单簿数据

2. 机会识别
   ├─ 策略引擎扫描
   ├─ 套利机会计算
   └─ 收益率评估

3. 风险评估
   ├─ 仓位风险检查
   ├─ 市场条件分析
   └─ 风险收益比计算

4. 决策制定
   ├─ DeepAgents 智能决策
   ├─ 策略选择
   └─ 参数优化

5. 交易执行
   ├─ 订单下发
   ├─ 执行监控
   └─ 结果验证

6. 结果记录
   ├─ 交易记录保存
   ├─ 性能指标更新
   └─ 知识库更新
```

### 数据存储流

```
实时数据 → 内存缓冲 → 定期持久化
            │
            ├─ SQLite (交易记录)
            ├─ SQLite (知识库)
            ├─ Log 文件 (系统日志)
            └─ Redis (实时状态)
```

---

## 技术栈

### 后端技术
- **框架**: Python 3.11+
- **AI框架**: DeepAgents, LangGraph
- **Web框架**: FastAPI (可选）
- **异步库**: asyncio, aiohttp

### 数据库
- **关系型**: SQLite
- **缓存**: Redis
- **时序数据**: InfluxDB (可选）

### 交易所集成
- **统一接口**: ccxt
- **WebSocket**: 原生实现
- **REST API**: ccxt 封装

### 监控告警
- **指标收集**: Prometheus
- **可视化**: Grafana
- **日志**: ELK Stack (可选）

---

## 扩展性设计

### 水平扩展
- 多进程/多线程支持
- 分布式任务队列
- 微服务架构预留

### 垂直扩展
- 异步 I/O 优化
- 内存使用优化
- CPU 密集型任务优化

### 功能扩展
- 策略插件机制
- 工具插件机制
- 交易所适配器模式

---

## 安全设计

### API 安全
- API 密钥加密存储
- 权限最小化原则
- 定期轮换密钥

### 数据安全
- 数据传输加密
- 敏感数据脱敏
- 定期备份

### 系统安全
- 访问控制
- 操作日志审计
- 异常行为检测

---

## 性能优化

### 延迟优化
- 网络连接优化
- 数据处理优化
- 异步并行执行

### 吞吐量优化
- 连接池复用
- 批量操作
- 缓存机制

### 资源优化
- 内存管理
- CPU 使用优化
- I/O 效率提升

---

## 未来演进

### 短期目标
- 完善所有套利策略
- 优化风险管理系统
- 增强监控告警功能
- 提升系统稳定性

### 中期目标
- 引入机器学习模型
- 实现自适应参数优化
- 构建 Web 管理界面
- 支持更多交易所

### 长期愿景
- 构建完整的量化交易平台
- 实现多资产类别支持
- 开放平台和生态系统
- 商业化部署

---

## V1.5.0 新增架构组件

### FastAPI REST API 后端 (`backend/api.py`)
- 14 个 RESTful API 端点
- 2 个 WebSocket 端点（价格推送、系统事件）
- CORS 中间件
- 策略管理、风险查询、交易执行、知识库搜索

### 回测框架 (`backtesting/engine.py`)
- 几何布朗运动价格数据生成
- 相关资产对模拟
- 跨交易所套利回测
- 统计套利回测
- 完整绩效指标计算（夏普/索提诺/最大回撤/盈亏比）

### 策略基类 (`strategies/base.py`)
- BaseStrategy 抽象基类
- 统一接口定义
- 通用交易记录和统计方法

---

## V1.6.0 新增架构组件

### 策略基类增强 (`strategies/base.py`)
- `StrategyState` 枚举（INITIALIZED/RUNNING/PAUSED/STOPPED/ERROR）
- 生命周期管理（start/stop/pause/resume + on_start/on_stop 钩子）
- `safe_scan()` / `safe_execute()` 带状态检查和错误处理
- `validate_config()` 配置验证（子类可覆盖）
- `is_healthy` 健康状态属性 + `get_health_report()`
- 连续错误自动暂停
- `_post_process_opportunities()` 统一过滤+排序+策略标识注入

### 策略重构（全部继承 BaseStrategy）
- CrossExchangeArbitrageStrategy: `cross_exchange`
- TriangularArbitrageStrategy: `triangular`
- BasisTradingStrategy: `basis_trading`
- FundingRateArbitrageStrategy: `funding_rate`
- StatisticalArbitrageStrategy: `statistical_arbitrage`
- 消除 ~250 行重复的 `get_performance_stats` 代码
- 修复 `list(exchanges.keys())[0]` 硬编码交易所问题 → `preferred_exchange`

### WebSocket 实时价格流 (`tools/price_stream.py`)
- `PriceTick` 数据类
- `PriceCache` 本地价格缓存（线程安全，支持历史查询、回调订阅）
- `PriceStreamManager`:
  - ccxt WebSocket 连接（watch_ticker）
  - 指数退避自动重连
  - REST 轮询降级
  - 跨交易所价差计算
  - 全局单例管理

### JWT 认证系统 (`backend/auth.py`)
- 纯 Python JWT 实现（无 PyJWT 依赖）
- `UserManager`：注册/登录/刷新/API Key/速率限制
- 角色权限：admin/user/readonly
- FastAPI 依赖注入（`_require_user`/`_require_admin`）
- 默认管理员账户

### FastAPI 后端增强 (`backend/api.py`)
- 认证路由：login/register/refresh/me/api-key
- 策略生命周期端点：start/stop
- 价格流端点：`/api/prices/{symbol}`, `/api/prices/stream/status`
- WebSocket 主题订阅（subscribe/unsubscribe 命令）
- ConnectionManager 主题化（`send_to_topic`）
- 价格桥接后台任务

### StrategyManager 增强 (`strategies/strategy_manager.py`)
- `register_strategy` 验证 `execute_arbitrage` 方法
- `_check_strategy_health` 优先使用 `BaseStrategy.is_healthy`
