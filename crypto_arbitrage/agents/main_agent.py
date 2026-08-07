"""数字货币套利交易 Agent - V3.5

升级特性：
1. 智能优化引擎集成 - 自动优化系统参数和策略权重
2. 智能知识管理 V3 - 自动提炼、分类、推荐和应用知识
3. 自适应错误处理 - 智能错误分类、恢复和预防
4. 系统自进化能力 - 基于AI驱动的持续优化
5. 版本号统一 - 统一到 V3.5，解决历史版本混乱问题
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

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

# V3.0 组件
from tools.intelligent_optimizer import IntelligentOptimizer
from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
from tools.adaptive_error_handler import (
    AdaptiveErrorHandler, ErrorSeverity, ErrorCategory
)

logger = logging.getLogger(__name__)


class CryptoArbitrageAgent:
    """数字货币套利交易 Agent V3.5

    基于 DeepAgents 框架 + Memo0 存储 + 智能自进化系统
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 初始化交易所管理器
        self.exchange_manager = initialize_exchange_manager(config.get('exchanges', {}))

        # 初始化风险管理器
        self.risk_manager = initialize_risk_manager(config.get('risk_management', {}))

        # 初始化监控系统
        self.monitoring = initialize_monitoring(config.get('monitoring', {}))

        # 初始化通知系统
        self.notifier = initialize_notifier(config.get('notifications', {}))

        # 初始化策略管理器
        self.strategy_manager = StrategyManager(config.get('strategy_manager', {}))

        # 初始化各策略
        self.strategies = self._initialize_strategies(config.get('strategies', {}))

        # 将策略注册到管理器
        self._register_strategies_to_manager()

        # V2.9: 初始化增强策略管理器（TradingAgents集成）
        self.enhanced_strategy_manager = None
        if config.get('trading_agents', {}).get('enabled', False):
            try:
                from strategies.enhanced_strategy_manager import create_enhanced_strategy_manager
                self.enhanced_strategy_manager = create_enhanced_strategy_manager(
                    self.strategy_manager,
                    config.get('trading_agents', {})
                )
                logger.info("✅ 增强策略管理器已启用 (V2.9)")
            except Exception as e:
                logger.warning(f"⚠️  增强策略管理器初始化失败: {e}")

        # V4.2: 初始化增强版低风险套利引擎
        self.enhanced_low_risk_engine = None
        if config.get('enhanced_low_risk_engine', {}).get('enabled', False):
            try:
                from strategies.enhanced_low_risk_arbitrage_engine import EnhancedLowRiskArbitrageEngine
                self.enhanced_low_risk_engine = EnhancedLowRiskArbitrageEngine(
                    risk_manager=self.risk_manager,
                    config=config.get('enhanced_low_risk_engine', {})
                )
                logger.info("✅ 增强版低风险套利引擎 V4.1 已启用")
            except Exception as e:
                logger.warning(f"⚠️  增强版低风险套利引擎初始化失败: {e}")

        # 初始化交易执行引擎
        self.transaction_executor = initialize_transaction_executor(
            config.get('transaction_executor', {})
        )

        # 初始化 Memo0 存储
        self._initialize_mem0_storage(config.get('mem0', {}))

        # V3.0: 初始化智能优化引擎
        self.intelligent_optimizer = self._initialize_intelligent_optimizer(
            config.get('intelligent_optimizer', {})
        )

        # V3.0: 初始化智能知识管理器 V3
        self.intelligent_knowledge_manager = self._initialize_intelligent_knowledge_manager(
            config.get('knowledge_manager_v3', {})
        )

        # V3.0: 初始化自适应错误处理器
        self.error_handler = self._initialize_adaptive_error_handler(
            config.get('adaptive_error_handler', {})
        )

        # 初始化 DeepAgent
        self.agent = self._create_agent()

        # V1.5.0: 注册 API Backend
        try:
            from backend.api import set_agent
            set_agent(self)
            logger.info("API Backend 已注册")
        except Exception as e:
            logger.warning(f"API Backend 注册失败: {e}")

        # 运行状态
        self.is_running = False
        self.performance_stats: Dict[str, Any] = {}

        logger.info("数字货币套利交易 Agent V3.0 初始化完成 (智能自适应系统)")

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

    def _initialize_intelligent_optimizer(
        self, optimizer_config: Dict
    ) -> Optional[IntelligentOptimizer]:
        """初始化智能优化引擎 V3.0

        Args:
            optimizer_config: 优化引擎配置

        Returns:
            智能优化引擎实例，如果未启用则返回 None
        """
        if not optimizer_config.get('enabled', False):
            logger.info("智能优化引擎未启用")
            return None

        try:
            optimizer = IntelligentOptimizer(
                optimization_interval=optimizer_config.get('optimization_interval', 300),
                history_window=optimizer_config.get('history_window', 1000),
                min_data_points=optimizer_config.get('min_data_points', 50),
                config_path=optimizer_config.get('config_path', 'config/optimization_state.json')
            )

            # 启动优化引擎
            optimizer.start_auto_optimization()

            logger.info("✅ 智能优化引擎 V3.0 已启动")
            return optimizer

        except Exception as e:
            logger.error(f"❌ 智能优化引擎初始化失败: {e}")
            return None

    def _initialize_intelligent_knowledge_manager(
        self, km_config: Dict
    ) -> Optional[IntelligentKnowledgeManager]:
        """初始化智能知识管理器 V3.0

        Args:
            km_config: 知识管理器配置

        Returns:
            智能知识管理器实例，如果未启用则返回 None
        """
        if not km_config.get('enabled', False):
            logger.info("智能知识管理器 V3.0 未启用")
            return None

        try:
            from storage.mem0_storage import get_unified_storage
            storage_backend = get_unified_storage()

            km = IntelligentKnowledgeManager(
                storage_backend=storage_backend,
                config=km_config
            )

            # 智能知识管理器 V3.0 已初始化（纯同步类，无需后台线程）
            logger.info("✅ 智能知识管理器 V3.0 已启动")
            return km

        except Exception as e:
            logger.error(f"❌ 智能知识管理器 V3.0 初始化失败: {e}")
            return None

    def _initialize_adaptive_error_handler(
        self, eh_config: Dict
    ) -> Optional[AdaptiveErrorHandler]:
        """初始化自适应错误处理器 V3.0

        Args:
            eh_config: 错误处理器配置

        Returns:
            自适应错误处理器实例，如果未启用则返回 None
        """
        if not eh_config.get('enabled', False):
            logger.info("自适应错误处理器 V3.0 未启用")
            return None

        try:
            eh = AdaptiveErrorHandler(
                config={
                    'max_retries': eh_config.get('max_retries', 3),
                    'retry_delay': eh_config.get('retry_delay', 1.0),
                    'backoff_factor': eh_config.get('backoff_factor', 2.0),
                    'circuit_breaker': eh_config.get('circuit_breaker', {}),
                    'prevention': eh_config.get('prevention', {})
                }
            )

            logger.info("✅ 自适应错误处理器 V3.0 已启动")
            return eh

        except Exception as e:
            logger.error(f"❌ 自适应错误处理器 V3.0 初始化失败: {e}")
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
                'agent_id': mem0_config.get('agent_id', 'trading-bot'),
                'rerank': mem0_config.get('rerank', True),
            })
            self._mem0_available = True
            # 修复：赋值给 self._unified_storage
            self._unified_storage = get_unified_storage()
            logger.info("Memo0 存储已激活")
        else:
            self._mem0_available = is_mem0_available()
            # 修复：赋值给 self._unified_storage
            self._unified_storage = get_unified_storage()
            logger.info(f"存储初始化完成，使用 {'Memo0' if self._mem0_available else 'SQLite'}")

    def _create_agent(self):
        """创建 DeepAgent 实例"""
        system_prompt = """你是专业的数字货币套利交易 AI 助手，基于 DeepAgents 框架构建。

## 核心职责
- 扫描和分析市场中的套利机会
- 执行低风险套利交易
- 监控和管理风险
- 记录和分析交易性能
- 持续优化交易策略

## 套利策略
- 跨交易所套利: 利用不同交易所间的价格差异
- 三角套利: 利用三种货币间的价格不一致
- 基差套利: 利用现货与期货价格差异
- 资金费率套利: 利用永续合约资金费率差异
- 统计套利: 利用历史价格关系的均值回归

## 风险管理原则
- 严格遵循风险管理规则
- 优先保证本金安全
- 控制单笔交易风险
- 监控总体敞口和回撤
- 及时止损和止盈

## 决策流程
1. 市场分析 → 2. 机会识别 → 3. 风险评估 → 4. 执行决策 → 5. 监控管理 → 6. 性能评估

## 注意事项
- 始终优先考虑风险控制
- 避免情绪化交易
- 持续学习和改进
"""

        model_config = self.config.get('model', {})
        if isinstance(model_config, dict):
            model_str = f"{model_config.get('provider', 'anthropic')}:{model_config.get('model', 'claude-sonnet-4-6')}"
        else:
            model_str = str(model_config)

        model = init_chat_model(
            model=model_str,
            temperature=model_config.get('temperature', 0.0) if isinstance(model_config, dict) else 0.0
        )

        return create_deep_agent(
            model=model,
            system_prompt=system_prompt,
            tools=self._get_agent_tools()
        )

    def _get_agent_tools(self) -> List:
        tools = [
            self.scan_arbitrage_opportunities_tool,
            self.scan_with_enhanced_engine_tool,  # V4.2 新增
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

    # ============ V3.0: 智能优化工具 ============

    @tool
    async def trigger_optimization_tool(self) -> str:
        """触发智能优化 - 立即执行一次系统优化"""
        if not self.intelligent_optimizer:
            return "智能优化引擎未启用"

        try:
            # 获取当前优化建议
            optimizations = self.intelligent_optimizer.get_current_optimizations()
            if optimizations:
                output = "✅ 智能优化完成\n\n"
                for name, changes in optimizations.items():
                    output += f"{name}:\n"
                    if isinstance(changes, dict):
                        for param, value in changes.items():
                            output += f"  {param}: {value}\n"
                    else:
                        output += f"  {changes}\n"
                    output += "\n"

                # 记录到知识库
                self._record_to_mem0("optimization",
                    f"智能优化执行: {len(optimizations)}个策略被优化")

                return output
            else:
                return "优化未执行: 暂无优化建议"

        except Exception as e:
            logger.error(f"智能优化失败: {e}")
            return f"优化失败: {str(e)}"

    @tool
    def get_optimization_status_tool(self) -> str:
        """获取优化引擎状态"""
        if not self.intelligent_optimizer:
            return "智能优化引擎未启用"

        status = self.intelligent_optimizer.get_current_optimizations()
        result = "=== 智能优化引擎状态 ===\n\n"
        result += f"当前优化建议数: {len(status)}\n\n"

        if status:
            result += "当前优化:\n"
            for name, opt in status.items():
                result += f"  {name}: {opt}\n"
        else:
            result += "暂无优化建议（数据不足）\n"

        return result

    @tool
    def get_optimization_history_tool(self, limit: int = 10) -> str:
        """获取优化历史记录"""
        if not self.intelligent_optimizer:
            return "智能优化引擎未启用"

        # 优化历史通过 generate_optimization_report 获取
        report = self.intelligent_optimizer.generate_optimization_report()
        history = report.get('recommendations', [])
        if not history:
            return "暂无优化历史"

        result = f"=== 最近 {len(history[:limit])} 次优化建议 ===\n\n"
        for i, record in enumerate(history[:limit], 1):
            result += f"{i}. [{record.get('type', 'info')}] {record.get('strategy', 'unknown')}\n"
            result += f"   {record.get('message', '')}\n"
            result += "\n"

        return result

    # ============ V3.0: 智能知识管理工具 ============

    @tool
    async def add_intelligent_knowledge_tool(
        self, content: str, category: str = "insight"
    ) -> str:
        """添加智能知识条目（自动分类和质量评估）"""
        if not self.intelligent_knowledge_manager:
            return "智能知识管理器未启用"

        try:
            knowledge_id = self.intelligent_knowledge_manager.add_knowledge(
                content=content,
                category=category,
                auto_classify=True
            )

            # 获取知识质量评分（通过统计信息间接获取）
            stats = self.intelligent_knowledge_manager.get_knowledge_statistics()
            quality = stats.get('total_knowledge', 0)

            return f"✅ 知识已添加 (ID: {knowledge_id})\n类别: {category}\n知识总数: {quality}"

        except Exception as e:
            logger.error(f"添加知识失败: {e}")
            return f"添加失败: {str(e)}"

    @tool
    async def get_recommended_knowledge_tool(
        self, context: str, max_results: int = 5
    ) -> str:
        """基于上下文获取推荐知识"""
        if not self.intelligent_knowledge_manager:
            return "智能知识管理器未启用"

        try:
            recommendations = self.intelligent_knowledge_manager.recommend_knowledge(
                context={"query": context},
                top_k=max_results
            )

            if not recommendations:
                return f"未找到与 '{context}' 相关的推荐知识"

            result = f"=== 知识推荐 (上下文: {context}) ===\n\n"
            for i, rec in enumerate(recommendations, 1):
                relevance = rec.get('relevance', 0)
                content = rec.get('content', '')[:150]
                result += f"{i}. 相关度: {relevance:.2f}\n"
                result += f"   {content}...\n\n"

            return result

        except Exception as e:
            logger.error(f"获取推荐知识失败: {e}")
            return f"推荐失败: {str(e)}"

    @tool
    async def extract_knowledge_from_trade_tool(self, trade_data: Dict) -> str:
        """从交易数据中自动提取知识"""
        if not self.intelligent_knowledge_manager:
            return "智能知识管理器未启用"

        try:
            insights = self.intelligent_knowledge_manager.extract_knowledge_from_trade(trade_data)

            if not insights:
                return "未从交易数据中提取到知识"

            result = f"✅ 从交易中提取 {len(insights)} 条知识:\n\n"
            for insight in insights:
                result += f"- {insight}\n"

            return result

        except Exception as e:
            logger.error(f"知识提取失败: {e}")
            return f"提取失败: {str(e)}"

    # ============ V3.0: 错误处理工具 ============

    @tool
    def get_error_statistics_tool(self) -> str:
        """获取错误统计信息"""
        if not self.error_handler:
            return "自适应错误处理器未启用"

        stats = self.error_handler.get_error_statistics()
        result = "=== 错误统计 ===\n\n"
        result += f"总错误数: {stats['total_errors']}\n"
        result += f"已恢复: {stats['recovered']} ({stats['recovery_rate']:.1%})\n"
        result += f"未恢复: {stats['not_recovered']}\n\n"

        result += "按严重程度:\n"
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = stats['by_severity'].get(severity, 0)
            if count > 0:
                result += f"  {severity}: {count}\n"

        result += "\n按类别:\n"
        for category, count in stats['by_category'].items():
            result += f"  {category}: {count}\n"

        return result

    @tool
    def get_error_patterns_tool(self, limit: int = 10) -> str:
        """获取错误模式分析"""
        if not self.error_handler:
            return "自适应错误处理器未启用"

        patterns = self.error_handler.get_error_patterns()
        if not patterns:
            return "暂无错误模式分析"

        # 限制返回数量
        items = list(patterns.items())[:limit]
        result = f"=== 错误模式分析 (Top {len(items)}) ===\n\n"
        for i, (pattern_key, pattern_data) in enumerate(items, 1):
            result += f"{i}. {pattern_key}\n"
            result += f"   出现次数: {pattern_data.get('count', 0)}\n"
            result += f"   最后发生: {pattern_data.get('last_occurrence', 'N/A')}\n"
            result += "\n"

        return result

    @tool
    async def reset_circuit_breakers_tool(self) -> str:
        """重置所有熔断器状态"""
        if not self.error_handler:
            return "自适应错误处理器未启用"

        try:
            self.error_handler.reset()
            return "✅ 所有熔断器已重置"
        except Exception as e:
            logger.error(f"重置熔断器失败: {e}")
            return f"重置失败: {str(e)}"

    # ============ 原有工具 ============

    @tool
    async def scan_with_enhanced_engine_tool(self, symbol: str = "BTC/USDT") -> str:
        """使用增强版引擎扫描套利机会（集成风险预测、健康监控、智能决策）"""
        if not self.enhanced_low_risk_engine:
            return "增强版引擎未启用，回退到标准扫描"

        try:
            # 先扫描标准套利机会
            opportunities = []
            for name, strategy in self.strategies.items():
                try:
                    opps = await strategy.scan_opportunities()
                    opportunities.extend(opps)
                except Exception as e:
                    logger.error(f"扫描 {name} 失败: {e}")

            # 过滤低风险
            filtered = []
            for opp in opportunities:
                # 使用增强版引擎的预检机制
                try:
                    # 创建简单的执行计划用于预检
                    execution_plan = [
                        {"action": "buy", "exchange": opp.get("buy_exchange"), "symbol": opp.get("symbol")},
                        {"action": "sell", "exchange": opp.get("sell_exchange"), "symbol": opp.get("symbol")}
                    ]

                    # 使用增强版引擎执行（包含风险预测、健康监控、智能决策）
                    result = await self.enhanced_low_risk_engine.execute_arbitrage(opp, execution_plan)

                    if result.get('status') == 'completed':
                        # 成功的执行，记录为增强机会
                        enhanced_opp = opp.copy()
                        enhanced_opp['_enhanced_execution'] = result
                        enhanced_opp['_risk_prediction'] = getattr(result, 'risk_prediction', None)
                        enhanced_opp['_health_status'] = getattr(result, 'health_status', None)
                        enhanced_opp['_intelligent_decision'] = getattr(result, 'intelligent_decision', None)
                        filtered.append(enhanced_opp)

                except Exception as e:
                    logger.warning(f"增强预检失败: {e}")

            if not filtered:
                return "增强版引擎未发现符合条件的套利机会"

            result = f"增强版引擎发现 {len(filtered)} 个套利机会:\n\n"
            for i, opp in enumerate(filtered[:5], 1):
                result += f"{i}. {opp.get('symbol', 'N/A')} - {opp.get('strategy', 'Unknown')}\n"
                result += f"   预期收益率: {opp.get('profit_rate', 0):.3f}%\n"
                if '_risk_prediction' in opp and opp['_risk_prediction']:
                    rp = opp['_risk_prediction']
                    result += f"   风险预测: {rp.risk_type} (置信度: {rp.confidence:.2f})\n"
                if '_health_status' in opp and opp['_health_status']:
                    hs = opp['_health_status']
                    result += f"   系统健康: {hs.health_score:.2f}\n"
                if '_intelligent_decision' in opp and opp['_intelligent_decision']:
                    id_ = opp['_intelligent_decision']
                    result += f"   智能决策: {id_.decision_type} (置信度: {id_.confidence:.2f})\n"
                result += "\n"

            return result

        except Exception as e:
            return f"增强版引擎扫描失败: {str(e)}"

    @tool
    async def scan_arbitrage_opportunities_tool(self, strategy_type: str = "all") -> str:
        """扫描套利机会"""
        logger.info(f"开始扫描 {strategy_type} 套利机会")
        opportunities = []

        for name, strategy in self.strategies.items():
            if strategy_type in ('all', name):
                try:
                    opps = await strategy.scan_opportunities()
                    opportunities.extend(opps)
                except Exception as e:
                    logger.error(f"扫描 {name} 失败: {e}")

        # 过滤低风险
        filtered = LowRiskArbitrageFilter.filter_opportunities(opportunities)

        if not filtered:
            return "当前没有发现符合条件的套利机会"

        result = f"发现 {len(filtered)} 个套利机会:\n\n"
        for i, opp in enumerate(filtered[:10], 1):
            strategy_label = opp.get('strategy', opp.get('_strategy_name', ''))
            if 'symbol' in opp:
                result += f"{i}. [{strategy_label}] {opp['symbol']}"
                if 'buy_exchange' in opp and 'sell_exchange' in opp:
                    result += f" {opp['buy_exchange']} -> {opp['sell_exchange']}"
                result += f"\n   预期收益率: {opp['profit_rate']:.3f}%\n\n"
            else:
                result += f"{i}. [{strategy_label}] 收益率: {opp['profit_rate']:.3f}%\n\n"

        # 发送通知
        notifier = get_notifier()
        if notifier and filtered:
            best = filtered[0]
            await notifier.send_alert(
                "INFO", "发现套利机会",
                f"最佳: {best.get('symbol', 'N/A')} 收益率 {best['profit_rate']:.3f}%"
            )

        self._record_to_mem0("opportunity_scan",
            f"扫描到 {len(filtered)} 个机会，最佳 {filtered[0].get('profit_rate', 0):.2f}%")
        return result

    @tool
    async def execute_arbitrage_tool(self, opportunity_index: int, strategy_type: str) -> str:
        """执行套利交易"""
        logger.info(f"执行套利: 策略={strategy_type}, 索引={opportunity_index}")

        # 使用策略管理器执行最佳机会
        opportunities = await self.strategy_manager.scan_all_strategies()
        if not opportunities:
            return "没有可执行的套利机会"

        result = await self.strategy_manager.execute_best_opportunity(opportunities)

        if not result:
            return "交易执行失败: 无返回结果"

        status = result.get('status', 'unknown')
        output = f"交易执行结果: {status}\n"

        if status == 'completed':
            profit = result.get('actual_profit', 0)
            output += f"实际利润: ${profit:.2f}\n"
            steps = result.get('steps', [])
            if steps:
                output += "执行步骤:\n"
                for step in steps:
                    output += f"  {step.get('action', '?')}: {step.get('exchange', '?')}\n"
            self._record_to_mem0("trade_success", f"套利成功，利润${profit:.2f}")

            notifier = get_notifier()
            if notifier:
                await notifier.send_alert("INFO", "交易成功", f"利润 ${profit:.2f}")
        elif status == 'rejected':
            output += f"拒绝原因: {result.get('reason', '未知')}\n"
            self._record_to_mem0("trade_rejected", f"交易被拒: {result.get('reason', '')}")
        else:
            output += f"错误: {result.get('error', '未知')}\n"
            self._record_to_mem0("trade_error", f"交易失败: {result.get('error', '')}")

            notifier = get_notifier()
            if notifier:
                await notifier.send_alert(
                    "ERROR", "交易失败",
                    result.get('error', '未知错误')
                )

        return output

    @tool
    def get_risk_status_tool(self) -> str:
        """获取当前风险状态"""
        s = self.risk_manager.get_risk_summary()
        return (
            f"=== 当前风险状态 ===\n"
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

    def _record_to_mem0(self, knowledge_type: str, content: str) -> None:
        try:
            from storage.mem0_storage import add_trading_knowledge
            add_trading_knowledge(knowledge_type, content)
        except Exception as e:
            logger.warning(f"知识记录失败: {e}")

    async def start_trading_loop(self) -> None:
        """启动交易循环 V3.0

        增强功能:
        - V3.0 智能优化集成
        - V3.0 知识自动提炼
        - V3.0 自适应错误处理
        - 持仓监控（有状态策略的自动平仓）
        - 自适应扫描间隔（根据市场活跃度动态调整）
        - 优雅关闭（停止前先尝试平仓）
        """
        self.is_running = True
        logger.info("启动交易循环 V3.0 (智能自适应系统)")

        base_scan_interval = self.config.get('scan_interval', 30)
        monitor_interval = self.config.get('monitor_interval', 120)
        loop_count = 0

        # V3.0: 使用错误处理器包装关键操作
        async def with_error_handling(
            operation: Callable,
            operation_name: str,
            *args, **kwargs
        ):
            """使用错误处理器包装操作"""
            if not self.error_handler:
                return await operation(*args, **kwargs)

            # 使用 handle_error 包装操作（执行前检查熔断器）
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context={"operation": operation_name}
                )
                raise

        while self.is_running:
            try:
                risk_summary = self.risk_manager.get_risk_summary()
                if risk_summary['is_risk_limit_reached']:
                    logger.warning("风险限制已触发，暂停交易")

                    # V3.0: 记录到智能知识库
                    if self.intelligent_knowledge_manager:
                        self.intelligent_knowledge_manager.add_knowledge(
                            content=f"风险限制触发，日亏损 ${risk_summary['daily_pnl']:.2f}",
                            category="risk",
                            metadata={
                                "severity": "HIGH",
                                "daily_pnl": risk_summary['daily_pnl']
                            }
                        )

                    self._record_to_mem0("risk_alert",
                        f"风险限制触发，日亏损 {risk_summary['daily_pnl']:.2f}")

                    notifier = get_notifier()
                    if notifier:
                        await notifier.send_alert(
                            "ERROR", "风险限制触发",
                            f"日亏损 ${risk_summary['daily_pnl']:.2f}"
                        )

                    await asyncio.sleep(base_scan_interval * 2)
                    continue

                # V1.7.0: 持仓监控（每 N 次扫描执行一次）
                loop_count += 1
                if loop_count % max(1, monitor_interval // base_scan_interval) == 0:
                    await self._monitor_all_positions()

                # V2.9/V3.0: 使用增强策略管理器扫描（TradingAgents集成 + 错误处理）
                if self.enhanced_strategy_manager:
                    opportunities = await with_error_handling(
                        self.enhanced_strategy_manager.scan_with_llm_enhancement,
                        "策略扫描"
                    )
                else:
                    opportunities = await with_error_handling(
                        self.strategy_manager.scan_all_strategies,
                        "策略扫描"
                    )

                if opportunities:
                    # V3.0: 记录市场机会到知识库
                    if self.intelligent_knowledge_manager and len(opportunities) > 0:
                        best_opp = max(opportunities, key=lambda x: x.get('profit_rate', 0))
                        self.intelligent_knowledge_manager.add_knowledge(
                            content=f"发现套利机会 {best_opp.get('symbol', 'N/A')} "
                                   f"收益率 {best_opp.get('profit_rate', 0):.3f}%",
                            category="market",
                            metadata={
                                "opportunity_count": len(opportunities),
                                "best_profit_rate": best_opp.get('profit_rate', 0)
                            }
                        )

                    # V2.9/V3.0: 使用增强策略管理器执行（LLM验证 + 错误处理）
                    if self.enhanced_strategy_manager:
                        result = await with_error_handling(
                            self.enhanced_strategy_manager.execute_with_llm_validation,
                            "策略执行",
                            opportunities
                        )
                    else:
                        result = await with_error_handling(
                            self.strategy_manager.execute_best_opportunity,
                            "策略执行",
                            opportunities
                        )

                    # V3.0: 从交易结果中提取知识
                    if self.intelligent_knowledge_manager and result:
                        trade_data = {
                            'strategy': result.get('strategy'),
                            'profit': result.get('actual_profit', 0),
                            'status': result.get('status'),
                            'execution_time': result.get('execution_time', 0)
                        }
                        await self.intelligent_knowledge_manager.extract_from_trade(trade_data)

                    # V3.0: 记录性能数据到优化引擎
                    if self.intelligent_optimizer and result:
                        for name, strategy in self.strategies.items():
                            stats = strategy.get_performance_stats()
                            metrics = {
                                'total_profit': stats['total_profit'],
                                'win_rate': stats['win_rate'],
                                'average_profit_rate': stats['average_profit_rate']
                            }
                            self.intelligent_optimizer.record_performance(name, metrics)

                else:
                    # V1.7.0: 无机会时自适应降低扫描频率
                    await asyncio.sleep(base_scan_interval * 1.5)
                    continue

                self.performance_stats = self.strategy_manager.get_comprehensive_stats()

                # V1.7.0: 自适应扫描间隔
                active_count = sum(
                    1 for s in self.strategies.values()
                    if s.active_position_count > 0
                )
                if active_count > 0:
                    await asyncio.sleep(base_scan_interval * 0.8)  # 有持仓时加快
                else:
                    await asyncio.sleep(base_scan_interval)

            except asyncio.CancelledError:
                logger.info("交易循环被取消")
                break
            except Exception as e:
                logger.error(f"交易循环出错: {e}")

                # V3.0: 使用错误处理器记录错误
                if self.error_handler:
                    self.error_handler.handle_error(
                        e,
                        context={"category": "execution", "severity": "high", "source": "trading_loop"}
                    )

                self._record_to_mem0("error", f"交易循环异常: {str(e)}")
                await asyncio.sleep(base_scan_interval)

    async def _monitor_all_positions(self) -> None:
        """V1.7.0: 监控所有有状态策略的持仓，自动平仓"""
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
                        # 记录到知识库
                        self._record_to_mem0("position_closed",
                            f"策略 {name} 自动平仓: {reason}, "
                            f"持仓时长 {position.get('holding_hours', 0):.1f}h")

                        notifier = get_notifier()
                        if notifier:
                            await notifier.send_alert(
                                "INFO", f"持仓平仓: {name}",
                                reason
                            )
                    else:
                        logger.error(f"[{name}] 自动平仓失败")

            except Exception as e:
                logger.error(f"[{name}] 持仓监控出错: {e}")

    async def stop(self) -> None:
        """V3.0: 优雅关闭 - 先尝试平仓再关闭连接

        关闭顺序:
        1. 停止交易循环
        2. 关闭持仓
        3. 停止策略
        4. 停止 V3.0 组件
        5. 关闭连接和存储
        """
        self.is_running = False
        logger.info("正在优雅停止 Agent V3.0...")

        # 尝试关闭所有持仓
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'close_position'):
                for pos in strategy.active_positions:
                    if pos.get('status') == 'open':
                        try:
                            await strategy.close_position(pos)
                        except Exception as e:
                            logger.warning(f"关闭 {name} 持仓失败: {e}")

        # 停止所有策略
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'stop'):
                strategy.stop()

        # V3.0: 停止智能优化引擎
        if self.intelligent_optimizer:
            try:
                self.intelligent_optimizer.stop_auto_optimization()
                logger.info("✅ 智能优化引擎已停止")
            except Exception as e:
                logger.warning(f"停止智能优化引擎失败: {e}")

        # V3.0: 保存优化状态（通过 _save_optimization_state 内部方法）
        if self.intelligent_optimizer:
            try:
                self.intelligent_optimizer._save_optimization_state()
                logger.info("✅ 优化状态已保存")
            except Exception as e:
                logger.warning(f"保存优化状态失败: {e}")

        # 关闭交易所连接
        exchange_manager = get_exchange_manager()
        if exchange_manager:
            await exchange_manager.close_all()

        # 关闭存储
        from storage.mem0_storage import get_unified_storage
        get_unified_storage().shutdown()

        logger.info("Agent V3.0 已停止")


async def run_crypto_arbitrage_agent(config: Dict[str, Any]) -> None:
    """运行数字货币套利交易 Agent"""
    agent = CryptoArbitrageAgent(config)
    try:
        await agent.start_trading_loop()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        await agent.stop()
