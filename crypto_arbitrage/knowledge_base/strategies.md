# 套利策略知识库

## 跨交易所套利策略

### 策略描述
跨交易所套利利用同一资产在不同交易所间的价格差异进行无风险或低风险套利。

### 工作原理
1. 监控多个交易所的实时价格
2. 计算买入价（最低价）和卖出价（最高价）
3. 扣除交易手续费后计算预期收益
4. 如果收益率为正，执行套利交易

### 关键参数
- **最小收益率**: 默认 0.5%
- **最大仓位大小**: 默认 $1000
- **风险容忍度**: 默认 10%
- **监控交易对**: BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT

### 优势
- 风险相对较低
- 执行逻辑简单
- 不依赖复杂的市场预测

### 风险
- 价格变动风险（滑点）
- 交易所流动性不足
- 转账时间成本
- API 限流和连接问题

### 优化方向
- 减少订单执行时间
- 优化交易所选择策略
- 实现智能价格预测
- 增加更多交易所支持

---

## 三角套利策略

### 策略描述
三角套利利用三种货币间的价格不一致进行套利，通常在同一交易所内进行。

### 工作原理
1. 找到一个三角套利路径，如 USDT → BTC → ETH → USDT
2. 计算每步的汇率和手续费
3. 确定最终是否能回到初始货币并获利
4. 如果收益率为正，按顺序执行三笔交易

### 关键参数
- **最小收益率**: 默认 0.3%
- **最大仓位大小**: 默认 $500
- **常用三角路径**:
  - USDT → BTC → ETH → USDT
  - USDT → BTC → BNB → USDT
  - USDT → ETH → BNB → USDT

### 优势
- 不需要跨交易所转账
- 执行速度快
- 可以频繁交易

### 风险
- 需要连续执行三笔交易
- 中间任何一步失败都会导致损失
- 市场波动风险
- 交易手续费累积

### 优化方向
- 优化交易执行顺序
- 减少交易延迟
- 实现并发执行
- 增加更多三角路径

---

## 基差套利策略

### 策略描述
基差套利利用现货和期货价格之间的差异进行套利。

### 工作原理
1. 监控现货和期货价格
2. 当期货价格显著高于现货时，买入现货，卖出期货
3. 等待价格收敛，平仓获利

### 关键参数
- **最小收益率**: 默认 0.8%
- **最大仓位大小**: 默认 $2000
- **监控交易对**: BTC/USDT, ETH/USDT

### 优势
- 风险较低（价格最终会收敛）
- 可以锁定收益
- 适合大资金

### 风险
- 资金占用时间长
- 可能需要追加保证金
- 期货手续费较高
- 价格收敛时间不确定

### 注意事项
- 需要同时开通现货和期货账户
- 注意期货合约到期时间
- 关注资金费率影响

---

## 统计套利策略

### 策略描述
统计套利基于历史统计关系，当价格偏离统计规律时进行反向操作。

### 工作原理
1. 收集历史价格数据
2. 计算两种资产之间的统计关系（如相关性、协整关系）
3. 当价格偏离历史关系时，构建套利组合
4. 等待价格回归正常范围后平仓

### 关键参数
- **最小收益率**: 默认 0.4%
- **最大仓位大小**: 默认 $800
- **回溯期**: 默认 30 天
- **Z分数阈值**: 默认 2.0

### 优势
- 基于统计规律，相对客观
- 可以同时监控多个资产对
- 适合量化分析

### 风险
- 历史关系可能失效
- 价格可能持续偏离
- 需要大量历史数据
- 模型过拟合风险

### 优化方向
- 使用机器学习优化模型
- 增加更多技术指标
- 实现在线学习
- 结合市场情绪分析

---

## 资金费率套利策略

### 策略描述
资金费率套利利用永续合约的资金费率差异进行套利。

### 工作原理
1. 监控永续合约的资金费率
2. 当资金费率为正时，买入现货，做空合约
3. 当资金费率为负时，卖出现货，做多合约
4. 收取资金费率，价格变动相互抵消

### 关键参数
- **最小资金费率**: 默认 0.05%
- **最大仓位大小**: 默认 $1500
- **监控交易对**: BTC/USDT:USDT, ETH/USDT:USDT

### 优势
- 风险较低（价格风险对冲）
- 资金费率收益稳定
- 可以长期持有

### 风险
- 价格大幅波动可能导致强平
- 需要同时管理现货和合约仓位
- 资金费率可能突然变化
- 交易所风险

### 注意事项
- 密切监控资金费率变化
- 设置合理的止损位置
- 注意交易所强平规则
- 控制杠杆比例

---

## 策略组合建议

### 保守型组合
- 跨交易所套利: 60%
- 资金费率套利: 40%

### 平衡型组合
- 跨交易所套利: 40%
- 三角套利: 30%
- 资金费率套利: 30%

### 激进型组合
- 跨交易所套利: 30%
- 三角套利: 30%
- 统计套利: 20%
- 资金费率套利: 20%

---

## 策略优化框架

### 数据收集
- 收集所有策略的历史表现数据
- 记录市场条件和策略成功率的对应关系
- 分析不同时间段的表现差异

### 参数优化
- 使用网格搜索优化关键参数
- 实现自适应参数调整
- 基于市场波动率动态调整

### 风险控制
- 设置单策略最大损失限制
- 实现策略组合相关性分析
- 建立策略熔断机制

### 性能监控
- 实时监控各策略表现
- 定期回顾和评估
- 及时淘汰表现差的策略

---

## V1.5.0 策略基类

### BaseStrategy 抽象基类 (`strategies/base.py`)
V1.5.0 引入了统一的策略抽象基类，所有策略应继承此类：

**核心方法**:
- `scan_opportunities()`: 扫描套利机会（抽象方法）
- `execute_arbitrage()`: 执行套利交易（抽象方法）
- `get_performance_stats()`: 获取性能统计（通用实现）
- `_record_trade()`: 记录交易（通用方法）
- `_sort_opportunities()`: 按指定键排序（通用方法）
- `_filter_by_threshold()`: 收益率过滤（通用方法）

**策略元数据**:
- `STRATEGY_NAME`: 策略名称标识
- `STRATEGY_DESCRIPTION`: 策略描述

### V1.6.0 策略重构（已完成）
所有 5 个策略已重构为继承 BaseStrategy：
- CrossExchangeArbitrageStrategy → BaseStrategy (STRATEGY_NAME="cross_exchange")
- TriangularArbitrageStrategy → BaseStrategy (STRATEGY_NAME="triangular")
- BasisTradingStrategy → BaseStrategy (STRATEGY_NAME="basis_trading")
- FundingRateArbitrageStrategy → BaseStrategy (STRATEGY_NAME="funding_rate")
- StatisticalArbitrageStrategy → BaseStrategy (STRATEGY_NAME="statistical_arbitrage")

重构后所有策略自动获得：
- 生命周期管理（start/stop/pause/resume）
- 配置验证（validate_config）
- 安全执行（safe_scan/safe_execute）
- 健康检查（is_healthy/get_health_report）
- 统一交易记录（_record_trade）
- 统一性能统计（get_performance_stats）

### V1.7.0 关键修复（已完成）
V1.6.0 迭代记录声称 3 个策略已重构继承 BaseStrategy，但实际代码未修改。
V1.7.0 彻底完成了以下修复：

**策略重构（真正完成）**:
- BasisTradingStrategy: 修复初始化顺序（子类属性先赋值），新增 validate_config
- FundingRateArbitrageStrategy: 修复初始化顺序，消除3处硬编码交易所
- StatisticalArbitrageStrategy: 修复初始化顺序，消除3处硬编码交易所，移除 `* 0.8` 魔术数字

**双重记录修复**:
- CrossExchangeArbitrageStrategy.execute_arbitrage: 移除直接 _record_trade 调用
- TriangularArbitrageStrategy.execute_arbitrage: 移除直接 _record_trade 调用

**初始化顺序修复（所有5个策略）**:
- 统一为先赋值子类属性，最后调用 super().__init__(config)
- 避免 validate_config 引用未赋值的属性

**Memo0 集成**:
- BaseStrategy._record_trade_to_memory: 交易自动记录到知识库
- 成功/失败交易分别记录到不同类别

**交易循环增强**:
- 持仓监控: 定期检查有状态策略持仓
- 自适应扫描: 根据持仓状态调整扫描频率
- 优雅关闭: 停止前先平仓

### V1.8.0 性能优化（已完成）

**并发价格获取**:
- ExchangeManager.get_tickers_batch: 并发获取多个交易对行情
- 支持超时控制和部分失败处理

**并发策略扫描**:
- StrategyManager.scan_all_strategies: 改为 asyncio.gather 并发执行
- 单策略失败不影响其他策略
- 策略错误自动记录到 Memo0

### V1.9.0 性能优化（已完成）

**RiskManager O(1) 优化**:
- `_get_current_balance()` 从 O(n) 优化为 O(1)
- 新增 `self._current_balance` 增量追踪属性
- 每次交易后增量更新，避免遍历整个 pnl_history

**测试覆盖**:
- 新增 test_v1_9_0.py 测试套件 (7 个测试)
- 覆盖版本号验证、O(1) 性能、并发稳定性

### V2.0 市场条件分析（已完成）

**市场条件分析器集成**:
- StrategyManager 初始化 MarketConditionAnalyzer
- scan_all_strategies() 新增 price_data 参数
- 根据市场波动率、趋势、流动性动态调整交易评分

**配置参数**:
- enable_market_analysis: True (默认启用)

**评分调整逻辑**:
- highly_favorable: 1.5x 仓位乘数
- favorable: 1.2x 仓位乘数
- normal: 1.0x 仓位乘数
- cautious: 0.7x 仓位乘数
- avoid: 0.3x 仓位乘数

### V2.1 智能止损（已完成）

**IntelligentStopLoss 集成**:
- StrategyManager 自动初始化智能止损系统
- 在交易执行时自动计算止损/止盈价格
- 支持根据市场波动率动态调整止损距离
- 提供追踪止损功能

**核心功能**:
- `calculate_stop_loss()`: 计算止损价格（考虑波动率）
- `calculate_take_profit()`: 计算止盈价格（基于风险回报比）
- `update_trailing_stop()`: 更新追踪止损价格

**配置参数**:
- enable_intelligent_stop_loss: True (默认启用)
- base_stop_loss: 2.0% (基础止损比例)
- base_take_profit: 1.0% (基础止盈比例)
- trailing_stop: 0.5% (追踪止损比例)
- risk_reward_ratio: 2.0 (风险回报比)

### V2.1 回测引擎集成（已完成）

**StrategyManager 回测功能**:
- `backtest_strategy()`: 单策略回测
- `backtest_all_strategies()`: 全策略回测
- `_generate_backtest_summary()`: 生成回测汇总报告
- `get_backtest_recommendations()`: 提供策略建议

**回测类型**:
- simple: 简单套利回测（基于收益率阈值）
- statistical: 统计套利回测（基于 Z-score）
- cross_exchange: 跨交易所套利回测

**回测指标**:
- total_return: 总收益率
- annualized_return: 年化收益率
- max_drawdown: 最大回撤
- sharpe_ratio: 夏普比率
- sortino_ratio: 索提诺比率
- win_rate: 胜率
- profit_factor: 盈亏比
- max_consecutive_losses: 最大连续亏损

**策略评估标准**:
- 优秀策略：夏普 > 2.0，回撤 < 5%，胜率 > 60%
- 可用策略：夏普 > 1.0，回撤 < 10%，胜率 > 50%
- 不推荐：其他情况

### V2.1 资金费率预测（已完成）

**FundingRatePredictor 类**:
- 基于历史数据预测未来资金费率
- 使用多种预测方法（移动平均、线性回归、加权预测）
- 支持趋势分析（上升/下降/稳定）
- 提供预测置信度

**核心功能**:
- `add_observation()`: 添加历史资金费率数据
- `predict_next_rate()`: 预测未来资金费率
- `get_prediction_summary()`: 生成预测摘要

**预测方法**:
1. 移动平均（短期和长期）
2. 线性回归（趋势分析）
3. 加权预测（综合方法）

**预测输出**:
- predicted_rate: 预测的资金费率
- current_rate: 当前资金费率
- trend: 趋势方向（rising/falling/stable）
- confidence: 预测置信度 (0-1)
- method: 预测方法（hybrid）

**FundingRateArbitrageStrategy 集成**:
- 自动记录资金费率历史数据
- 每次扫描时更新预测器
- 在机会数据中包含预测信息
- 提供查询预测的公共方法

### V2.4 Web UI可视化界面（已完成）

**Web UI技术栈**:
- React 18 + TypeScript：现代化前端框架，类型安全
- Ant Design 5：企业级UI组件库
- Zustand：轻量级全局状态管理
- Vite：快速开发服务器，HMR支持
- Recharts：React原生图表库
- Axios：HTTP客户端，自动Token管理

**核心页面（7个）**:

#### 1. 仪表盘（Dashboard）
- 系统状态概览（在线状态/运行时间/连接数）
- 实时性能指标（当日盈亏/胜率/总交易数）
- 活跃策略状态卡片
- 最近交易列表
- 风险指标仪表盘

#### 2. 实时行情（RealtimeMarket）
- 多交易对实时价格卡片（BTC/USDT, ETH/USDT等）
- K线价格图表（可交互）
- WebSocket实时价格推送
- 24H涨跌幅和交易量显示

#### 3. 策略管理（StrategyManagement）
- 策略列表展示（5种套利策略）
- 启用/禁用策略（Switch组件）
- 策略配置编辑（最小收益率/最大仓位）
- 策略性能统计（交易数/利润/胜率）
- 暂停/启动策略按钮

#### 4. 交易历史（TradeHistory）
- 完整交易记录表格
- 高级筛选（日期/策略/状态）
- 搜索功能（交易ID/策略/交易对）
- 交易详情查看模态框
- 导出CSV功能

#### 5. 风险管理（RiskManagement）
- 当前风险状态展示（错误数/损失限制/持仓限制）
- 风险参数配置表单
- 参数：每日最大损失/最大持仓/总敞口/回撤/止损/止盈/风险回报比
- 保存和重置功能

#### 6. 监控告警（MonitoringAlerts）
- 告警列表展示（信息/警告/错误/严重）
- 未读/全部过滤
- 告警确认功能
- 批量全部已读
- 未读告警徽章

#### 7. 系统设置（Settings）
- 用户信息展示
- 系统配置表单（启用通知/自动交易/日志级别）
- 保存设置功能
- 自动交易风险警告

**API集成（9个模块）**:
- authAPI: 登录/注册/刷新Token
- systemAPI: 系统状态/性能指标
- strategyAPI: 策略管理/扫描/推荐/优化
- tradeAPI: 交易执行/历史/导出
- marketAPI: 价格/历史/机会
- riskAPI: 风险配置/健康/建议
- monitoringAPI: 监控指标/告警/健康
- backtestAPI: 回测运行/结果
- intelligentAPI: 智能推荐/风险评估/异常检测/优化建议

**WebSocket实时通信**:
- WebSocketService服务类
- 自动重连机制（最多5次）
- 消息类型处理（system_status/price_update/opportunity/trade_update/alert/performance_update）
- 订阅主题管理
- 状态同步（系统/市场/交易/告警/监控）

**核心功能**:
- 实时数据推送：价格/交易/告警实时更新
- 路由保护：未登录自动重定向到登录页
- 统一错误处理：拦截器自动处理401错误
- 响应式布局：支持桌面端和移动端
- 类型安全：100% TypeScript覆盖

**测试套件**:
- test_v2_4.py（16个测试）
- 前端目录结构验证
- 配置文件完整性验证
- 组件和页面存在性验证
- API和Store验证
- 版本号一致性验证
- 测试结果：16/16通过（100%）
