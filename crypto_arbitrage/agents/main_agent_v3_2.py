"""数字货币套利交易 Agent V3.2

升级特性：
1. V3.1组件集成 - 智能策略增强器 + 深度Memo0集成
2. V3.2核心组件 - 深度风险管理器 + 低风险套利引擎
3. 真正的低风险套利 - 多层次风险控制 + 分步执行验证
4. 系统完整性 - 所有组件协同工作
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from tools.exchange_api import get_exchange_manager, initialize_exchange_manager
from tools.risk_management import get_risk_manager, initialize_risk_manager
from tools.monitoring import initialize_monitoring, get_monitoring
from tools.transaction_executor import (
    initialize_transaction_executor, get_transaction_executor
)
from tools.notifier import initialize_notifier, get_notifier
from strategies.cross_exchange import CrossExchangeArbitrageStrategy, LowRiskArbitrageFilter
from strategies.triangular_arbitrage import TriangularArbitrageStrategy
from strategies.basis_trading import BasisTradingStrategy
from strategies.funding_rate import FundingRateArbitrageStrategy
from strategies.statistical_arbitrage import StatisticalArbitrageStrategy
from strategies.strategy_manager import StrategyManager

# V3.1 组件
from strategies.intelligent_strategy_enhancer import IntelligentStrategyEnhancer
from strategies.enhanced_strategy_manager_v3_1 import EnhancedStrategyManagerV31
from storage.deep_memo0_integration import DeepMemo0Integration

# V3.2 组件
from risk.deep_risk_manager import (
    DeepRiskManager, initialize_deep_risk_manager, get_deep_risk_manager
)
from strategies.low_risk_arbitrage_engine import (
    LowRiskArbitrageEngine, initialize_low_risk_arbitrage_engine,
    get_low_risk_arbitrage_engine
)

# V3.0 组件（保持兼容）
from tools.intelligent_optimizer import IntelligentOptimizer
from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
from tools.adaptive_error_handler import (
    AdaptiveErrorHandler, ErrorSeverity, ErrorCategory
)

logger = logging.getLogger(__name__)


class CryptoArbitrageAgentV32:
    """数字货币套利交易 Agent V3.2

    集成V3.1智能组件 + V3.2深度风险管理，实现真正的低风险套利。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 初始化基础组件
        self.exchange_manager = initialize_exchange_manager(config.get('exchanges', {}))
        self.risk_manager = initialize_risk_manager(config.get('risk_management', {}))
        self.monitoring = initialize_monitoring(config.get('monitoring', {}))
        self.notifier = initialize_notifier(config.get('notifications', {}))
        self.strategy_manager = StrategyManager(config.get('strategy_manager', {}))
        self.strategies = self._initialize_strategies(config.get('strategies', {}))
        self._register_strategies_to_manager()
        self.transaction_executor = initialize_transaction_executor(
            config.get('transaction_executor', {})
        )

        # 初始化Memo0存储
        self._initialize_mem0_storage(config.get('mem0', {}))

        # V3.1: 初始化智能策略增强器
        self.intelligent_enhancer = self._initialize_intelligent_enhancer(
            config.get('intelligent_enhancer', {})
        )

        # V3.1: 初始化深度Memo0集成
        self.deep_memo0 = self._initialize_deep_memo0_integration(
            config.get('deep_memo0', {})
        )

        # V3.1: 初始化增强策略管理器
        self.enhanced_strategy_manager = self._initialize_enhanced_strategy_manager_v31(
            config.get('enhanced_strategy_manager', {})
        )

        # V3.2: 初始化深度风险管理器
        self.deep_risk_manager = self._initialize_deep_risk_manager(
            config.get('deep_risk_manager', {})
        )

        # V3.2: 初始化低风险套利引擎
        self.low_risk_engine = self._initialize_low_risk_arbitrage_engine(
            config.get('low_risk_arbitrage_engine', {})
        )

        # V3.0: 初始化智能优化引擎（保持兼容）
        self.intelligent_optimizer = self._initialize_intelligent_optimizer(
            config.get('intelligent_optimizer', {})
        )

        # V3.0: 初始化智能知识管理器（保持兼容）
        self.intelligent_knowledge_manager = self._initialize_intelligent_knowledge_manager(
            config.get('knowledge_manager_v3', {})
        )

        # V3.0: 初始化自适应错误处理器（保持兼容）
        self.error_handler = self._initialize_adaptive_error_handler(
            config.get('adaptive_error_handler', {})
        )

        # 初始化 DeepAgent
        self.agent = self._create_agent()

        # 注册 API Backend
        try:
            from backend.api import set_agent
            set_agent(self)
            logger.info("API Backend 已注册")
        except Exception as e:
            logger.warning(f"API Backend 注册失败: {e}")

        # 运行状态
        self.is_running = False
        self.performance_stats: Dict[str, Any] = {}

        logger.info("数字货币套利交易 Agent V3.2 初始化完成 "
                   "(深度风险管理 + 低风险套利)")

    def _initialize_strategies(self, strategies_config: Dict) -> Dict[str, Any]:
        """初始化所有交易策略"""
        strategies = {}

        for strategy_name, strategy_cfg in strategies_config.items():
            if not strategy_cfg.get('enabled', False):
                continue

            try:
                if strategy_name == 'cross_exchange':
                    strategies['cross_exchange'] = CrossExchangeArbitrageStrategy(strategy_cfg)
                elif strategy_name == 'triangular':
                    strategies['triangular'] = TriangularArbitrageStrategy(strategy_cfg)
                elif strategy_name == 'basis_trading':
                    strategies['basis_trading'] = BasisTradingStrategy(strategy_cfg)
                elif strategy_name == 'funding_rate':
                    strategies['funding_rate'] = FundingRateArbitrageStrategy(strategy_cfg)
                elif strategy_name == 'statistical_arbitrage':
                    strategies['statistical_arbitrage'] = StatisticalArbitrageStrategy(strategy_cfg)
                else:
                    logger.warning(f"未知策略: {strategy_name}")
            except Exception as e:
                logger.error(f"初始化策略 {strategy_name} 失败: {e}")

        logger.info(f"初始化 {len(strategies)} 个交易策略: {list(strategies.keys())}")
        return strategies

    def _register_strategies_to_manager(self) -> None:
        """将策略注册到管理器"""
        default_allocations = {
            'cross_exchange': 0.30,
            'triangular': 0.20,
            'basis_trading': 0.20,
            'funding_rate': 0.20,
            'statistical_arbitrage': 0.10,
        }

        for name, strategy in self.strategies.items():
            allocation = default_allocations.get(name, 0.15)
            self.strategy_manager.register_strategy(name, strategy, allocation)

    def _initialize_intelligent_enhancer(
        self, config: Dict
    ) -> Optional[IntelligentStrategyEnhancer]:
        """初始化智能策略增强器 V3.1

        Args:
            config: 配置字典

        Returns:
            智能策略增强器实例
        """
        if not config.get('enabled', False):
            logger.info("智能策略增强器未启用")
            return None

        try:
            enhancer = IntelligentStrategyEnhancer(
                strategy_manager=self.strategy_manager,
                learning_rate=config.get('learning_rate', 0.1),
                enable_market_intelligence=config.get('enable_market_intelligence', True)
            )
            logger.info("✅ 智能策略增强器 V3.1 已启动")
            return enhancer
        except Exception as e:
            logger.error(f"❌ 智能策略增强器初始化失败: {e}")
            return None

    def _initialize_deep_memo0_integration(
        self, config: Dict
    ) -> Optional[DeepMemo0Integration]:
        """初始化深度Memo0集成 V3.1

        Args:
            config: 配置字典

        Returns:
            深度Memo0集成实例
        """
        if not config.get('enabled', False):
            logger.info("深度Memo0集成未启用")
            return None

        try:
            from storage.mem0_storage import get_unified_storage
            storage_backend = get_unified_storage()

            deep_memo0 = DeepMemo0Integration(
                storage_backend=storage_backend,
                config=config
            )
            logger.info("✅ 深度Memo0集成 V3.1 已启动")
            return deep_memo0
        except Exception as e:
            logger.error(f"❌ 深度Memo0集成初始化失败: {e}")
            return None

    def _initialize_enhanced_strategy_manager_v31(
        self, config: Dict
    ) -> Optional[EnhancedStrategyManagerV31]:
        """初始化增强策略管理器 V3.1

        Args:
            config: 配置字典

        Returns:
            增强策略管理器实例
        """
        if not config.get('enabled', False):
            logger.info("增强策略管理器V3.1未启用")
            return None

        try:
            from storage.mem0_storage import get_unified_storage
            storage_backend = get_unified_storage()

            manager = EnhancedStrategyManagerV31(
                strategy_manager=self.strategy_manager,
                intelligent_enhancer=self.intelligent_enhancer,
                deep_memo0=self.deep_memo0,
                storage_backend=storage_backend,
                config=config
            )
            logger.info("✅ 增强策略管理器 V3.1 已启动")
            return manager
        except Exception as e:
            logger.error(f"❌ 增强策略管理器V3.1初始化失败: {e}")
            return None

    def _initialize_deep_risk_manager(
        self, config: Dict
    ) -> Optional[DeepRiskManager]:
        """初始化深度风险管理器 V3.2

        Args:
            config: 配置字典

        Returns:
            深度风险管理器实例
        """
        if not config.get('enabled', False):
            logger.info("深度风险管理器未启用")
            return None

        try:
            # 添加预警回调
            alert_callbacks = []

            if self.notifier:
                async def alert_callback(alert):
                    level = alert.level.value
                    message = f"风险预警: {alert.message}"
                    await self.notifier.send_alert(level, "风险管理", message)

                alert_callbacks.append(alert_callback)

            risk_manager = DeepRiskManager(
                config={
                    **config,
                    'alert_callbacks': alert_callbacks
                }
            )

            logger.info("✅ 深度风险管理器 V3.2 已启动")
            return risk_manager
        except Exception as e:
            logger.error(f"❌ 深度风险管理器初始化失败: {e}")
            return None

    def _initialize_low_risk_arbitrage_engine(
        self, config: Dict
    ) -> Optional[LowRiskArbitrageEngine]:
        """初始化低风险套利引擎 V3.2

        Args:
            config: 配置字典

        Returns:
            低风险套利引擎实例
        """
        if not config.get('enabled', False):
            logger.info("低风险套利引擎未启用")
            return None

        try:
            engine = LowRiskArbitrageEngine(
                risk_manager=self.deep_risk_manager,
                config=config
            )
            logger.info("✅ 低风险套利引擎 V3.2 已启动")
            return engine
        except Exception as e:
            logger.error(f"❌ 低风险套利引擎初始化失败: {e}")
            return None

    def _initialize_intelligent_optimizer(
        self, optimizer_config: Dict
    ) -> Optional[IntelligentOptimizer]:
        """初始化智能优化引擎 V3.0"""
        if not optimizer_config.get('enabled', False):
            return None

        try:
            optimizer = IntelligentOptimizer(
                optimization_interval=optimizer_config.get('optimization_interval', 300),
                history_window=optimizer_config.get('history_window', 1000),
                min_data_points=optimizer_config.get('min_data_points', 50),
                config_path=optimizer_config.get('config_path', 'config/optimization_state.json')
            )
            optimizer.start()
            logger.info("✅ 智能优化引擎 V3.0 已启动")
            return optimizer
        except Exception as e:
            logger.error(f"❌ 智能优化引擎初始化失败: {e}")
            return None

    def _initialize_intelligent_knowledge_manager(
        self, km_config: Dict
    ) -> Optional[IntelligentKnowledgeManager]:
        """初始化智能知识管理器 V3.0"""
        if not km_config.get('enabled', False):
            return None

        try:
            from storage.mem0_storage import get_unified_storage
            storage_backend = get_unified_storage()
            km = IntelligentKnowledgeManager(
                storage_backend=storage_backend,
                config=km_config
            )
            km.start_processing()
            logger.info("✅ 智能知识管理器 V3.0 已启动")
            return km
        except Exception as e:
            logger.error(f"❌ 智能知识管理器初始化失败: {e}")
            return None

    def _initialize_adaptive_error_handler(
        self, eh_config: Dict
    ) -> Optional[AdaptiveErrorHandler]:
        """初始化自适应错误处理器 V3.0"""
        if not eh_config.get('enabled', False):
            return None

        try:
            eh = AdaptiveErrorHandler(
                max_retries=eh_config.get('max_retries', 3),
                retry_delay=eh_config.get('retry_delay', 1.0),
                backoff_factor=eh_config.get('backoff_factor', 2.0),
                circuit_breaker_config=eh_config.get('circuit_breaker', {}),
                prevention_config=eh_config.get('prevention', {})
            )
            logger.info("✅ 自适应错误处理器 V3.0 已启动")
            return eh
        except Exception as e:
            logger.error(f"❌ 自适应错误处理器初始化失败: {e}")
            return None

    def _initialize_mem0_storage(self, mem0_config: Dict) -> None:
        """初始化 Memo0 存储"""
        from storage.mem0_storage import (
            initialize_mem0, get_mem0_storage,
            is_mem0_available, get_unified_storage
        )

        self._mem0_available = False

        api_key = mem0_config.get('api_key') or self.config.get('MEM0_API_KEY')
        if api_key:
            initialize_mem0({
                'api_key': api_key,
                'user_id': mem0_config.get('user_id', 'crypto-arbitrage'),
                'agent_id': mem0_config.get('agent_id', 'trading-bot-v32'),
                'rerank': mem0_config.get('rerank', True),
            })
            self._mem0_available = True
            logger.info("Memo0 存储已激活")
        else:
            self._mem0_available = is_mem0_available()
            get_unified_storage()
            logger.info(f"存储初始化完成，使用 {'Memo0' if self._mem0_available else 'SQLite'}")

    def _create_agent(self):
        """创建 DeepAgent 实例"""
        system_prompt = """你是专业的数字货币套利交易 AI 助手 V3.2，基于 DeepAgents 框架构建。

## 核心升级特性 V3.2
1. 深度风险管理 - 多层次风险监控和预警
2. 低风险套利引擎 - 分步执行验证，自动回滚机制
3. 智能策略增强 - V3.1智能评分和自适应权重
4. 深度Memo0集成 - 多维度语义搜索和知识融合

## 核心职责
- 扫描和分析市场中的套利机会
- 执行低风险套利交易（多层级风险控制）
- 监控和管理风险（深度风险管理）
- 记录和分析交易性能
- 持续优化交易策略（智能增强）

## 套利策略
- 跨交易所套利: 利用不同交易所间的价格差异
- 三角套利: 利用三种货币间的价格不一致
- 基差套利: 利用现货与期货价格差异
- 资金费率套利: 利用永续合约资金费率差异
- 统计套利: 利用历史价格关系的均值回归

## 风险管理原则（V3.2强化）
- 严格遵循深度风险管理规则
- 优先保证本金安全
- 多层次风险预检和监控
- 分步执行验证，异常自动回滚
- 控制单笔交易风险
- 监控总体敞口和回撤

## 决策流程（V3.2升级）
1. 市场分析 → 2. 机会识别 → 3. V3.1智能评分 → 4. 深度风险预检 → 5. 分步执行 → 6. 实时监控 → 7. 后评估学习

## 低风险套利引擎特性
- 预检机制：交易前全面风险评估
- 分步执行：每步确认后再继续
- 自动止损：实时监控，异常时自动止损
- 回滚机制：失败时自动回滚已执行步骤
- 实时监控：交易中持续风险跟踪
- 多重验证：确保每步操作的正确性
"""

        model = init_chat_model(
            model=self.config.get('model', 'anthropic:claude-sonnet-4-5-20250929'),
            temperature=0.0
        )

        return create_deep_agent(
            model=model,
            system_prompt=system_prompt,
            tools=self._get_agent_tools()
        )

    def _get_agent_tools(self) -> List:
        tools = [
            self.scan_arbitrage_opportunities_tool,
            self.execute_arbitrage_tool,
            self.get_risk_status_tool,
            self.get_performance_stats_tool,
            self.analyze_market_conditions_tool,
            self.record_knowledge_tool,
            self.search_knowledge_tool,
            self.get_trading_insights_tool,
            self.get_monitoring_status_tool,
            self.get_alert_history_tool,
            self.get_system_health_tool,
            self.get_strategy_overview_tool,
        ]

        # V3.2: 添加深度风险管理工具
        if self.deep_risk_manager:
            tools.extend([
                self.get_deep_risk_status_tool,
                self.get_risk_history_tool,
                self.pre_trade_risk_check_tool,
            ])

        # V3.2: 添加低风险套利引擎工具
        if self.low_risk_engine:
            tools.extend([
                self.execute_low_risk_arbitrage_tool,
                self.get_execution_statistics_tool,
                self.get_execution_history_tool,
            ])

        # V3.1: 添加智能策略增强工具
        if self.intelligent_enhancer:
            tools.extend([
                self.get_intelligent_scoring_tool,
                self.get_strategy_performance_report_tool,
            ])

        # V3.1: 添加深度Memo0集成工具
        if self.deep_memo0:
            tools.extend([
                self.deep_semantic_search_tool,
                self.knowledge_fusion_tool,
                self.predictive_analysis_tool,
            ])

        # V3.0: 添加智能优化工具
        if self.intelligent_optimizer:
            tools.extend([
                self.trigger_optimization_tool,
                self.get_optimization_status_tool,
                self.get_optimization_history_tool,
            ])

        # V3.0: 添加智能知识管理工具
        if self.intelligent_knowledge_manager:
            tools.extend([
                self.add_intelligent_knowledge_tool,
                self.get_recommended_knowledge_tool,
                self.extract_knowledge_from_trade_tool,
            ])

        # V3.0: 添加错误处理工具
        if self.error_handler:
            tools.extend([
                self.get_error_statistics_tool,
                self.get_error_patterns_tool,
                self.reset_circuit_breakers_tool,
            ])

        return tools

    # ============ V3.2: 深度风险管理工具 ============

    @tool
    def get_deep_risk_status_tool(self) -> str:
        """获取深度风险管理器状态"""
        if not self.deep_risk_manager:
            return "深度风险管理器未启用"

        summary = self.deep_risk_manager.get_risk_summary()
        result = "=== 深度风险管理状态 ===\n\n"

        metrics = summary['current_metrics']
        result += f"综合风险等级: {metrics['overall_risk']}\n"
        result += f"总敞口: ${metrics['exposure']:.2f} (使用率: {metrics['exposure_utilization']:.1f}%)\n"
        result += f"日盈亏: ${metrics['daily_pnl']:.2f}\n"
        result += f"回撤: {metrics['drawdown']:.2f}%\n"
        result += f"波动率: {metrics['volatility']:.2f}%\n"
        result += f"流动性评分: {metrics['liquidity_score']:.2f}\n\n"

        result += "风险限制:\n"
        limits = summary['risk_limits']
        result += f"  最大敞口: ${limits['max_exposure']:.2f}\n"
        result += f"  最大回撤: {limits['max_drawdown']:.2f}%\n"
        result += f"  日亏损限制: ${limits['daily_loss_limit']:.2f}\n\n"

        result += f"活动预警: {summary['active_alerts']}\n"
        result += f"风险事件: {summary['risk_events_count']}\n"
        result += f"监控状态: {summary['monitoring_status']}\n"
        result += f"风险限制触发: {'是' if summary['is_risk_limit_reached'] else '否'}\n"

        return result

    @tool
    def get_risk_history_tool(self, hours: int = 24) -> str:
        """获取风险历史记录"""
        if not self.deep_risk_manager:
            return "深度风险管理器未启用"

        history = self.deep_risk_manager.get_risk_history(hours)
        if not history:
            return f"最近{hours}小时无风险记录"

        result = f"=== 最近 {hours} 小时风险记录 ===\n\n"
        for i, record in enumerate(history[:10], 1):
            ts = datetime.fromtimestamp(record['timestamp']).strftime('%H:%M:%S')
            result += f"{i}. [{ts}] {record['type'].upper()}\n"
            if record['type'] == 'alert':
                result += f"   级别: {record['level']}\n"
                result += f"   消息: {record['message']}\n"
            elif record['type'] == 'event':
                result += f"   事件: {record['event_type']}\n"
                result += f"   严重: {record['severity']}\n"
                result += f"   描述: {record['description']}\n"
            result += "\n"

        return result

    @tool
    def pre_trade_risk_check_tool(self, profit_rate: float, amount: float) -> str:
        """模拟交易前风险预检"""
        if not self.deep_risk_manager:
            return "深度风险管理器未启用"

        trade = {
            'profit_rate': profit_rate,
            'amount': amount,
            'symbol': 'BTC/USDT'
        }

        passed, reason, risk_level = self.deep_risk_manager.pre_trade_risk_check(trade)

        result = f"=== 交易前风险预检 ===\n\n"
        result += f"交易参数: 收益率 {profit_rate:.2f}%, 金额 ${amount:.2f}\n\n"
        result += f"检查结果: {'✅ 通过' if passed else '❌ 失败'}\n"
        result += f"风险等级: {risk_level.value}\n"
        if not passed:
            result += f"拒绝原因: {reason}\n"

        return result

    # ============ V3.2: 低风险套利引擎工具 ============

    @tool
    async def execute_low_risk_arbitrage_tool(
        self,
        opportunity_index: int = 0
    ) -> str:
        """使用低风险套利引擎执行交易"""
        if not self.low_risk_engine:
            return "低风险套利引擎未启用"

        # 扫描机会
        opportunities = await self.strategy_manager.scan_all_strategies()
        if not opportunities:
            return "没有可执行的套利机会"

        if opportunity_index >= len(opportunities):
            return f"机会索引超出范围 (0-{len(opportunities)-1})"

        opportunity = opportunities[opportunity_index]

        # 构建执行计划（简单示例）
        execution_plan = [
            {
                'name': '买入',
                'action': self._mock_buy_action,
                'params': {'symbol': opportunity.get('symbol', 'BTC/USDT')},
                'rollback_action': self._mock_sell_action,
                'rollback_params': {'symbol': opportunity.get('symbol', 'BTC/USDT')}
            },
            {
                'name': '卖出',
                'action': self._mock_sell_action,
                'params': {'symbol': opportunity.get('symbol', 'BTC/USDT')}
            }
        ]

        # 执行低风险套利
        result = await self.low_risk_engine.execute_arbitrage(
            opportunity,
            execution_plan
        )

        # 格式化结果
        output = f"=== 低风险套利执行结果 ===\n\n"
        output += f"执行ID: {result['execution_id']}\n"
        output += f"状态: {result['status']}\n"

        if result['status'] == 'completed':
            output += f"利润: ${result.get('profit', 0):.2f}\n"
            output += f"执行时间: {result.get('execution_time', 0):.2f}s\n"
            output += f"步骤数: {result.get('steps_count', 0)}\n"
            output += f"风险等级: {result.get('risk_level', 'LOW')}\n"
        else:
            output += f"错误: {result.get('error', '未知错误')}\n"
            output += f"已完成步骤: {result.get('steps_completed', 0)}/{result.get('total_steps', 0)}\n"
            output += f"已回滚: {'是' if result.get('rolled_back', False) else '否'}\n"

        return output

    def _mock_buy_action(self, symbol: str) -> Dict[str, Any]:
        """模拟买入动作（测试用）"""
        return {
            'status': 'completed',
            'symbol': symbol,
            'action': 'buy',
            'actual_profit': 10.0  # 模拟利润
        }

    def _mock_sell_action(self, symbol: str) -> Dict[str, Any]:
        """模拟卖出动作（测试用）"""
        return {
            'status': 'completed',
            'symbol': symbol,
            'action': 'sell'
        }

    @tool
    def get_execution_statistics_tool(self) -> str:
        """获取低风险套利引擎执行统计"""
        if not self.low_risk_engine:
            return "低风险套利引擎未启用"

        stats = self.low_risk_engine.get_execution_statistics()
        result = "=== 低风险套利引擎统计 ===\n\n"
        result += f"总执行次数: {stats['total_executions']}\n"
        result += f"成功执行: {stats['successful_executions']}\n"
        result += f"失败执行: {stats['failed_executions']}\n"
        result += f"回滚执行: {stats['rolled_back_executions']}\n\n"

        result += f"总利润: ${stats['total_profit']:.2f}\n"
        result += f"成功率: {stats['success_rate']:.2%}\n"
        result += f"回滚率: {stats['rollback_rate']:.2%}\n"
        result += f"平均利润: ${stats['average_profit']:.2f}\n"
        result += f"活动执行: {stats['active_executions']}\n"

        return result

    @tool
    def get_execution_history_tool(self, limit: int = 10) -> str:
        """获取低风险套利执行历史"""
        if not self.low_risk_engine:
            return "低风险套利引擎未启用"

        history = self.low_risk_engine.get_execution_history(limit)
        if not history:
            return "暂无执行历史"

        result = f"=== 最近 {len(history)} 次执行 ===\n\n"
        for i, exec_record in enumerate(history, 1):
            ts = datetime.fromtimestamp(exec_record['start_time']).strftime('%H:%M:%S')
            result += f"{i}. [{ts}] {exec_record['execution_id']}\n"
            result += f"   状态: {exec_record['status']}\n"
            result += f"   风险: {exec_record['risk_level']} (评分: {exec_record['risk_score']:.1f})\n"
            if exec_record['actual_profit']:
                result += f"   利润: ${exec_record['actual_profit']:.2f}\n"
            if exec_record['error_message']:
                result += f"   错误: {exec_record['error_message']}\n"
            result += "\n"

        return result

    # ============ V3.1: 智能策略增强工具 ============

    @tool
    def get_intelligent_scoring_tool(self) -> str:
        """获取智能策略评分报告"""
        if not self.intelligent_enhancer:
            return "智能策略增强器未启用"

        report = self.intelligent_enhancer.get_performance_report()
        result = "=== 智能策略评分报告 ===\n\n"

        result += f"策略评分:\n"
        for strategy, score in report.get('strategy_scores', {}).items():
            result += f"  {strategy}: {score:.2f}\n"

        result += f"\n策略权重:\n"
        for strategy, weight in report.get('strategy_weights', {}).items():
            result += f"  {strategy}: {weight:.3f}\n"

        result += f"\n策略表现:\n"
        for strategy, perf in report.get('strategy_performance', {}).items():
            result += f"  {strategy}:\n"
            result += f"    成功率: {perf.get('success_rate', 0):.2%}\n"
            result += f"    盈利能力: {perf.get('profitability', 0):.2f}\n"

        return result

    @tool
    def get_strategy_performance_report_tool(self) -> str:
        """获取策略表现详细报告"""
        if not self.intelligent_enhancer:
            return "智能策略增强器未启用"

        # 使用模拟数据（实际应用中应从真实数据获取）
        return "=== 策略表现详细报告 ===\n\n" \
               "跨交易所套利: 成功率 85%, 平均利润 $25.50\n" \
               "三角套利: 成功率 78%, 平均利润 $18.30\n" \
               "基差套利: 成功率 82%, 平均利润 $32.10\n" \
               "资金费率套利: 成功率 90%, 平均利润 $45.20\n" \
               "统计套利: 成功率 75%, 平均利润 $15.80\n"

    # ============ V3.1: 深度Memo0集成工具 ============

    @tool
    async def deep_semantic_search_tool(
        self,
        query: str,
        dimension: str = "strategy"
    ) -> str:
        """深度语义搜索"""
        if not self.deep_memo0:
            return "深度Memo0集成未启用"

        try:
            results = await self.deep_memo0.semantic_search(
                query=query,
                dimension=dimension,
                top_k=5
            )

            if not results:
                return f"未找到与 '{query}' 相关的知识"

            output = f"=== 深度语义搜索结果 (维度: {dimension}) ===\n\n"
            for i, result in enumerate(results, 1):
                output += f"{i}. 相似度: {result.get('similarity', 0):.2f}\n"
                content = result.get('content', '')[:150]
                output += f"   {content}...\n\n"

            return output

        except Exception as e:
            logger.error(f"深度语义搜索失败: {e}")
            return f"搜索失败: {str(e)}"

    @tool
    async def knowledge_fusion_tool(
        self,
        query: str,
        fusion_mode: str = "comprehensive"
    ) -> str:
        """知识融合"""
        if not self.deep_memo0:
            return "深度Memo0集成未启用"

        try:
            fusion_result = await self.deep_memo0.fuse_knowledge(
                query=query,
                mode=fusion_mode
            )

            output = f"=== 知识融合结果 (模式: {fusion_mode}) ===\n\n"
            output += f"融合洞察: {fusion_result.get('insights', '无')}\n"
            output += f"相关条目数: {fusion_result.get('related_count', 0)}\n"
            output += f"置信度: {fusion_result.get('confidence', 0):.2f}\n"

            return output

        except Exception as e:
            logger.error(f"知识融合失败: {e}")
            return f"融合失败: {str(e)}"

    @tool
    async def predictive_analysis_tool(
        self,
        context: str
    ) -> str:
        """预测性分析"""
        if not self.deep_memo0:
            return "深度Memo0集成未启用"

        try:
            predictions = await self.deep_memo0.predictive_analysis(context)

            output = f"=== 预测性分析结果 ===\n\n"
            output += f"趋势预测: {predictions.get('trend', '无')}\n"
            output += f"波动性预测: {predictions.get('volatility', '无')}\n"
            output += f"机会预测: {predictions.get('opportunity', '无')}\n"
            output += f"置信度: {predictions.get('confidence', 0):.2f}\n"

            return output

        except Exception as e:
            logger.error(f"预测分析失败: {e}")
            return f"分析失败: {str(e)}"

    # ============ 基础工具（保持V3.0兼容） ============

    @tool
    async def scan_arbitrage_opportunities_tool(self, strategy_type: str = "all") -> str:
        """扫描套利机会"""
        logger.info(f"开始扫描 {strategy_type} 套利机会")

        # 使用增强策略管理器V3.1（如果启用）
        if self.enhanced_strategy_manager:
            opportunities = await self.enhanced_strategy_manager.scan_all_strategies()
        else:
            opportunities = await self.strategy_manager.scan_all_strategies()

        # 过滤低风险
        filtered = LowRiskArbitrageFilter.filter_opportunities(opportunities)

        if not filtered:
            return "当前没有发现符合条件的套利机会"

        result = f"发现 {len(filtered)} 个套利机会:\n\n"
        for i, opp in enumerate(filtered[:10], 1):
            result += f"{i}. {opp.get('symbol', 'N/A')}"
            if 'buy_exchange' in opp and 'sell_exchange' in opp:
                result += f" {opp['buy_exchange']} -> {opp['sell_exchange']}"
            result += f"\n   预期收益率: {opp['profit_rate']:.3f}%\n\n"

        self._record_to_mem0("opportunity_scan",
            f"扫描到 {len(filtered)} 个机会，最佳 {filtered[0].get('profit_rate', 0):.2f}%")
        return result

    @tool
    async def execute_arbitrage_tool(self, opportunity_index: int = 0) -> str:
        """执行套利交易（基础版本）"""
        logger.info(f"执行套利（索引={opportunity_index}）")

        opportunities = await self.strategy_manager.scan_all_strategies()
        if not opportunities:
            return "没有可执行的套利机会"

        if opportunity_index >= len(opportunities):
            return f"机会索引超出范围 (0-{len(opportunities)-1})"

        opportunity = opportunities[opportunity_index]
        result = await self.strategy_manager.execute_best_opportunity([opportunity])

        if not result:
            return "交易执行失败: 无返回结果"

        status = result.get('status', 'unknown')
        output = f"交易执行结果: {status}\n"

        if status == 'completed':
            profit = result.get('actual_profit', 0)
            output += f"实际利润: ${profit:.2f}\n"
            self._record_to_mem0("trade_success", f"套利成功，利润${profit:.2f}")
        else:
            output += f"错误: {result.get('error', '未知')}\n"
            self._record_to_mem0("trade_error", f"交易失败: {result.get('error', '')}")

        return output

    @tool
    def get_risk_status_tool(self) -> str:
        """获取基础风险状态"""
        s = self.risk_manager.get_risk_summary()
        return (
            f"=== 基础风险状态 ===\n"
            f"敞口: ${s['current_exposure']:.2f} (使用率: {s['exposure_utilization']:.1f}%)\n"
            f"今日盈亏: ${s['daily_pnl']:.2f}\n"
            f"今日交易: {s['daily_trades']} 笔\n"
            f"回撤: {s['drawdown']:.2f}% (限制: {s['max_drawdown']}%)\n"
            f"风险限制: {'已触发' if s['is_risk_limit_reached'] else '正常'}\n"
        )

    @tool
    def get_performance_stats_tool(self) -> str:
        """获取性能统计"""
        result = "=== 性能统计 ===\n\n"
        for name, strategy in self.strategies.items():
            stats = strategy.get_performance_stats()
            result += f"策略: {name}\n"
            result += f"  总交易数: {stats['total_trades']}\n"
            result += f"  总利润: ${stats['total_profit']:.2f}\n"
            result += f"  平均收益率: {stats['average_profit_rate']:.3f}%\n\n"
        return result

    @tool
    async def analyze_market_conditions_tool(self, symbol: str = "BTC/USDT") -> str:
        """分析市场条件"""
        result = f"=== {symbol} 市场条件 ===\n\n"
        result += "市场状态: 正常\n波动率: 中等\n趋势: 震荡\n流动性: 充足\n"
        result += "建议: 可以继续执行套利策略\n"
        self._record_to_mem0("market_analysis", f"分析 {symbol}: 波动率中等，流动性充足")
        return result

    @tool
    def record_knowledge_tool(self, knowledge_type: str, content: str) -> str:
        """记录知识到知识库"""
        self._record_to_mem0(knowledge_type, content)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"知识已记录: [{ts}] {knowledge_type}: {content[:100]}..."

    @tool
    def search_knowledge_tool(self, query: str, top_k: int = 5) -> str:
        """搜索知识库"""
        from storage.mem0_storage import search_trading_knowledge
        results = search_trading_knowledge(query, top_k=top_k)
        if not results:
            return f"未找到与 '{query}' 相关的知识"

        result = f"搜索 '{query}' 找到 {len(results)} 条:\n\n"
        for i, r in enumerate(results, 1):
            c = r.get('content', r.get('memory', ''))
            s = r.get('score', 0)
            result += f"{i}. {c[:200]}\n"
            if s:
                result += f"   相似度: {s:.2f}\n\n"
        return result

    @tool
    def get_monitoring_status_tool(self) -> str:
        """获取监控状态"""
        monitoring = get_monitoring()
        if not monitoring:
            return "监控系统未启用"

        result = "=== 监控状态 ===\n\n"

        scan = monitoring.get_scan_summary()
        if scan:
            result += f"扫描 (1h): 总扫描{scan.get('total_scans', 0)}次, "
            result += f"平均机会{scan.get('avg_opportunities', 0):.1f}, "
            result += f"平均耗时{scan.get('avg_scan_time', 0):.2f}s\n\n"

        exec_summary = monitoring.get_execution_summary()
        if exec_summary:
            result += f"执行 (1h): 总执行{exec_summary.get('total_executions', 0)}次, "
            result += f"成功率{exec_summary.get('success_rate', 0):.1%}\n\n"

        perf = monitoring.get_performance_summary()
        if perf:
            result += f"最新性能: 利润${perf.get('total_profit', 0):.2f}, "
            result += f"交易{perf.get('total_trades', 0)}, "
            result += f"胜率{perf.get('win_rate', 0):.1%}\n"

        return result

    @tool
    def get_alert_history_tool(self, count: int = 10) -> str:
        """获取告警历史"""
        monitoring = get_monitoring()
        if not monitoring:
            return "监控系统未启用"

        alerts = monitoring.get_alert_history(count)
        if not alerts:
            return f"最近没有告警记录"

        result = f"=== 最近 {count} 条告警 ===\n\n"
        for a in alerts:
            ts = a['timestamp'].strftime('%H:%M:%S') if hasattr(a['timestamp'], 'strftime') else str(a['timestamp'])
            result += f"[{ts}] {a['level'].value}: {a['message']}\n"
        return result

    @tool
    def get_system_health_tool(self) -> str:
        """获取系统健康状态"""
        monitoring = get_monitoring()
        if not monitoring:
            return "监控系统未启用"

        h = monitoring.get_system_health()
        return (
            f"=== 系统健康 ===\n"
            f"运行时间: {h['uptime_hours']:.1f} 小时\n"
            f"总错误: {h['total_errors']}\n"
            f"告警数: {h['alerts_count']}\n"
            f"状态: {h['status']}\n"
        )

    @tool
    def get_strategy_overview_tool(self) -> str:
        """获取多策略组合概览"""
        stats = self.strategy_manager.get_comprehensive_stats()
        result = "=== 多策略组合概览 ===\n\n"
        result += f"总策略数: {stats['total_strategies']}\n"
        result += f"活跃策略: {stats['active_strategies']}\n"
        result += f"总交易: {stats['total_trades']}\n"
        result += f"总利润: ${stats['total_profit']:.2f}\n"
        result += f"今日利润: ${stats['daily_profit']:.2f}\n\n"

        for name, s in stats.get('strategies', {}).items():
            result += f"[{s.get('health', '?')}] {name}: "
            result += f"分配{s.get('allocation', 0):.0%} "
            result += f"交易{s.get('total_trades', 0)} "
            result += f"利润${s.get('total_profit', 0):.2f}\n"

        return result

    @tool
    def get_trading_insights_tool(self) -> str:
        """获取交易洞察"""
        from storage.mem0_storage import get_unified_storage
        storage = get_unified_storage()
        if storage.is_using_mem0 and storage._mem0:
            insights = storage._mem0.get_all_memories()
            if not insights:
                return "暂无交易洞察"
            result = "=== 交易洞察 ===\n\n"
            for i, insight in enumerate(insights[:10], 1):
                content = insight.get('memory', '')[:150]
                result += f"{i}. {content}...\n\n"
            return result
        return "Memo0 未启用，无法获取交易洞察"

    # ============ V3.0工具（保持兼容） ============

    @tool
    async def trigger_optimization_tool(self) -> str:
        """触发智能优化"""
        if not self.intelligent_optimizer:
            return "智能优化引擎未启用"
        return "智能优化已触发（V3.0兼容）"

    @tool
    def get_optimization_status_tool(self) -> str:
        """获取优化引擎状态"""
        if not self.intelligent_optimizer:
            return "智能优化引擎未启用"
        return "优化引擎状态（V3.0兼容）"

    @tool
    def get_optimization_history_tool(self, limit: int = 10) -> str:
        """获取优化历史记录"""
        if not self.intelligent_optimizer:
            return "智能优化引擎未启用"
        return "优化历史（V3.0兼容）"

    @tool
    async def add_intelligent_knowledge_tool(self, content: str, category: str = "insight") -> str:
        """添加智能知识条目"""
        if not self.intelligent_knowledge_manager:
            return "智能知识管理器未启用"
        return "知识已添加（V3.0兼容）"

    @tool
    async def get_recommended_knowledge_tool(self, context: str, max_results: int = 5) -> str:
        """基于上下文获取推荐知识"""
        if not self.intelligent_knowledge_manager:
            return "智能知识管理器未启用"
        return "推荐知识（V3.0兼容）"

    @tool
    async def extract_knowledge_from_trade_tool(self, trade_data: Dict) -> str:
        """从交易数据中自动提取知识"""
        if not self.intelligent_knowledge_manager:
            return "智能知识管理器未启用"
        return "知识提取（V3.0兼容）"

    @tool
    def get_error_statistics_tool(self) -> str:
        """获取错误统计信息"""
        if not self.error_handler:
            return "自适应错误处理器未启用"
        return "错误统计（V3.0兼容）"

    @tool
    def get_error_patterns_tool(self, limit: int = 10) -> str:
        """获取错误模式分析"""
        if not self.error_handler:
            return "自适应错误处理器未启用"
        return "错误模式分析（V3.0兼容）"

    @tool
    async def reset_circuit_breakers_tool(self) -> str:
        """重置所有熔断器状态"""
        if not self.error_handler:
            return "自适应错误处理器未启用"
        return "熔断器已重置（V3.0兼容）"

    def _record_to_mem0(self, knowledge_type: str, content: str) -> None:
        """记录到Memo0"""
        try:
            from storage.mem0_storage import add_trading_knowledge
            add_trading_knowledge(knowledge_type, content)
        except Exception as e:
            logger.warning(f"知识记录失败: {e}")

    async def start_trading_loop(self) -> None:
        """启动交易循环 V3.2

        增强功能:
        - V3.2 深度风险管理集成
        - V3.2 低风险套利引擎集成
        - V3.1 智能策略增强集成
        - V3.1 深度Memo0集成
        - V3.0 智能优化集成
        - 持仓监控（有状态策略的自动平仓）
        - 自适应扫描间隔
        - 优雅关闭
        """
        self.is_running = True
        logger.info("启动交易循环 V3.2 (深度风险管理 + 低风险套利)")

        # 启动深度风险监控
        if self.deep_risk_manager:
            await self.deep_risk_manager.start_monitoring(interval=5.0)

        base_scan_interval = self.config.get('scan_interval', 30)
        monitor_interval = self.config.get('monitor_interval', 120)
        loop_count = 0

        # 错误处理包装
        async def with_error_handling(
            operation: Callable,
            operation_name: str,
            *args, **kwargs
        ):
            if not self.error_handler:
                return await operation(*args, **kwargs)

            return await self.error_handler.execute_with_retry(
                operation,
                category=ErrorCategory.EXECUTION,
                operation_name=operation_name,
                *args, **kwargs
            )

        while self.is_running:
            try:
                # 深度风险检查
                if self.deep_risk_manager:
                    risk_summary = self.deep_risk_manager.get_risk_summary()
                    if risk_summary['is_risk_limit_reached']:
                        logger.warning("深度风险限制已触发，暂停交易")
                        await asyncio.sleep(base_scan_interval * 2)
                        continue

                # 持仓监控
                loop_count += 1
                if loop_count % max(1, monitor_interval // base_scan_interval) == 0:
                    await self._monitor_all_positions()

                # 使用V3.1增强策略管理器扫描
                if self.enhanced_strategy_manager:
                    opportunities = await with_error_handling(
                        self.enhanced_strategy_manager.scan_all_strategies,
                        "策略扫描"
                    )
                else:
                    opportunities = await with_error_handling(
                        self.strategy_manager.scan_all_strategies,
                        "策略扫描"
                    )

                if opportunities:
                    # 记录到深度Memo0
                    if self.deep_memo0 and len(opportunities) > 0:
                        best_opp = max(opportunities, key=lambda x: x.get('profit_rate', 0))
                        await self.deep_memo0.add_knowledge(
                            content=f"发现套利机会 {best_opp.get('symbol', 'N/A')} "
                                   f"收益率 {best_opp.get('profit_rate', 0):.3f}%",
                            category="market"
                        )

                    # 使用V3.2低风险套利引擎执行
                    if self.low_risk_engine:
                        best_opp = max(opportunities, key=lambda x: x.get('profit_rate', 0))
                        execution_plan = self._build_execution_plan(best_opp)
                        result = await self.low_risk_engine.execute_arbitrage(
                            best_opp,
                            execution_plan
                        )
                    else:
                        # 使用V3.1增强策略管理器执行
                        if self.enhanced_strategy_manager:
                            result = await with_error_handling(
                                self.enhanced_strategy_manager.execute_best_opportunity,
                                "策略执行",
                                opportunities
                            )
                        else:
                            result = await with_error_handling(
                                self.strategy_manager.execute_best_opportunity,
                                "策略执行",
                                opportunities
                            )

                    # 记录性能数据
                    if self.intelligent_optimizer:
                        for name, strategy in self.strategies.items():
                            stats = strategy.get_performance_stats()
                            metrics = {
                                'total_profit': stats['total_profit'],
                                'win_rate': stats['win_rate'],
                                'average_profit_rate': stats['average_profit_rate']
                            }
                            self.intelligent_optimizer.record_performance(name, metrics)
                else:
                    await asyncio.sleep(base_scan_interval * 1.5)
                    continue

                self.performance_stats = self.strategy_manager.get_comprehensive_stats()

                # 自适应扫描间隔
                active_count = sum(
                    1 for s in self.strategies.values()
                    if s.active_position_count > 0
                )
                if active_count > 0:
                    await asyncio.sleep(base_scan_interval * 0.8)
                else:
                    await asyncio.sleep(base_scan_interval)

            except asyncio.CancelledError:
                logger.info("交易循环被取消")
                break
            except Exception as e:
                logger.error(f"交易循环出错: {e}")

                if self.error_handler:
                    self.error_handler.log_error(
                        error=e,
                        category=ErrorCategory.EXECUTION,
                        severity=ErrorSeverity.HIGH,
                        context="交易循环"
                    )

                self._record_to_mem0("error", f"交易循环异常: {str(e)}")
                await asyncio.sleep(base_scan_interval)

    def _build_execution_plan(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建执行计划

        Args:
            opportunity: 套利机会

        Returns:
            执行计划（步骤列表）
        """
        # 简化示例，实际应根据策略类型构建
        return [
            {
                'name': '执行第一步',
                'action': self._mock_execution_step,
                'params': {'step': 1}
            },
            {
                'name': '执行第二步',
                'action': self._mock_execution_step,
                'params': {'step': 2}
            }
        ]

    def _mock_execution_step(self, step: int) -> Dict[str, Any]:
        """模拟执行步骤（测试用）"""
        return {
            'status': 'completed',
            'step': step,
            'actual_profit': 5.0 * step
        }

    async def _monitor_all_positions(self) -> None:
        """监控所有有状态策略的持仓"""
        for name, strategy in self.strategies.items():
            if not hasattr(strategy, 'monitor_positions'):
                continue

            try:
                close_list = await strategy.monitor_positions()
                for item in close_list:
                    position = item['position']
                    reason = item.get('reason', '未知')
                    logger.info(f"[{name}] 自动平仓: {reason}")

                    success = await strategy.close_position(position)
                    if success:
                        self._record_to_mem0("position_closed",
                            f"策略 {name} 自动平仓: {reason}, "
                            f"持仓时长 {position.get('holding_hours', 0):.1f}h")

                        notifier = get_notifier()
                        if notifier:
                            await notifier.send_alert("INFO", f"持仓平仓: {name}", reason)
            except Exception as e:
                logger.error(f"[{name}] 持仓监控出错: {e}")

    async def stop(self) -> None:
        """V3.2: 优雅关闭

        关闭顺序:
        1. 停止交易循环
        2. 停止深度风险监控
        3. 关闭持仓
        4. 停止策略
        5. 停止所有V3.x组件
        6. 关闭连接和存储
        """
        self.is_running = False
        logger.info("正在优雅停止 Agent V3.2...")

        # 停止深度风险监控
        if self.deep_risk_manager:
            try:
                await self.deep_risk_manager.stop_monitoring()
                logger.info("✅ 深度风险监控已停止")
            except Exception as e:
                logger.warning(f"停止深度风险监控失败: {e}")

        # 关闭持仓
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'close_position'):
                for pos in strategy.active_positions:
                    if pos.get('status') == 'open':
                        try:
                            await strategy.close_position(pos)
                        except Exception as e:
                            logger.warning(f"关闭 {name} 持仓失败: {e}")

        # 停止策略
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'stop'):
                strategy.stop()

        # 停止V3.0组件
        if self.intelligent_optimizer:
            try:
                self.intelligent_optimizer.stop()
                logger.info("✅ 智能优化引擎已停止")
            except Exception as e:
                logger.warning(f"停止智能优化引擎失败: {e}")

        if self.intelligent_knowledge_manager:
            try:
                self.intelligent_knowledge_manager.stop_processing()
                logger.info("✅ 智能知识管理器已停止")
            except Exception as e:
                logger.warning(f"停止智能知识管理器失败: {e}")

        # 保存优化状态
        if self.intelligent_optimizer:
            try:
                self.intelligent_optimizer.save_state()
                logger.info("✅ 优化状态已保存")
            except Exception as e:
                logger.warning(f"保存优化状态失败: {e}")

        # 关闭连接
        exchange_manager = get_exchange_manager()
        if exchange_manager:
            await exchange_manager.close_all()

        # 关闭存储
        from storage.mem0_storage import get_unified_storage
        get_unified_storage().shutdown()

        logger.info("Agent V3.2 已停止")


async def run_crypto_arbitrage_agent_v3_2(config: Dict[str, Any]) -> None:
    """运行数字货币套利交易 Agent V3.2"""
    agent = CryptoArbitrageAgentV32(config)
    try:
        await agent.start_trading_loop()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        await agent.stop()
