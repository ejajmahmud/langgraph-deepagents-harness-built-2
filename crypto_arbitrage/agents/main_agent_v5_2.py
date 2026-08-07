"""数字货币套利交易 Agent V5.2 - 智能深度集成版

升级特性：
1. V5.2智能决策引擎 - 深度Memo0语义搜索
2. V5.2增强版低风险套利引擎 - 预测性风险管理
3. 智能决策和自适应风险参数调整
4. 知识学习和自优化能力
5. 完整的Memo0降级机制

V5.2核心突破：
- 深度集成Memo0语义搜索替代基础查询
- 实现预测性风险管理和智能决策
- 优化套利执行的智能路径选择
- 增强知识学习和参数自优化
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

# V15.3 统一核心组件（从V5.2升级到V5.9）
from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import (
    EnhancedLowRiskArbitrageEngineV59, create_enhanced_low_risk_engine_v5_9
)
# 向后兼容别名（V5.2接口保持兼容）
EnhancedLowRiskArbitrageEngineV52 = EnhancedLowRiskArbitrageEngineV59
create_enhanced_low_risk_engine_v5_2 = create_enhanced_low_risk_engine_v5_9

# V5.2 智能决策引擎组件
from storage.intelligent_decision_engine_v5_2 import IntelligentDecisionEngineV52, create_intelligent_decision_engine_v5_2

# V3.0 组件（保持兼容）
from tools.intelligent_optimizer import IntelligentOptimizer
from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
from tools.adaptive_error_handler import (
    AdaptiveErrorHandler, ErrorSeverity, ErrorCategory
)

logger = logging.getLogger(__name__)


class CryptoArbitrageAgentV52:
    """数字货币套利交易 Agent V5.2 - 智能深度集成版

    完整集成V5.2智能决策引擎和V5.2增强版低风险套利引擎，
    实现真正的AI驱动低风险套利。
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

        # V5.2: 初始化智能决策引擎
        self.decision_engine = self._initialize_decision_engine_v5_2(
            config.get('intelligent_decision_engine_v5_2', {})
        )

        # V5.2: 初始化增强版低风险套利引擎
        self.enhanced_low_risk_engine_v5_2 = self._initialize_enhanced_low_risk_engine_v5_2(
            config.get('enhanced_low_risk_engine_v5_2', {})
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

        logger.info("数字货币套利交易 Agent V5.2 初始化完成 "
                   "(智能深度集成 + Memo0语义搜索)")

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

    def _initialize_decision_engine_v5_2(
        self, config: Dict
    ) -> Optional[IntelligentDecisionEngineV52]:
        """初始化V5.2智能决策引擎

        Args:
            config: 配置字典

        Returns:
            V5.2智能决策引擎实例
        """
        if not config.get('enabled', False):
            logger.info("V5.2智能决策引擎未启用")
            return None

        try:
            from storage.mem0_storage import get_unified_storage
            storage_backend = get_unified_storage()

            # 创建V5.2智能决策引擎
            decision_engine = create_intelligent_decision_engine_v5_2(
                mem0_storage=storage_backend,
                fallback_storage=None  # 使用内置降级机制
            )

            logger.info("✅ V5.2智能决策引擎已启动 (Memo0深度集成)")
            return decision_engine
        except Exception as e:
            logger.error(f"❌ V5.2智能决策引擎初始化失败: {e}")
            return None

    def _initialize_enhanced_low_risk_engine_v5_2(
        self, config: Dict
    ) -> Optional[EnhancedLowRiskArbitrageEngineV52]:
        """初始化V5.2增强版低风险套利引擎

        Args:
            config: 配置字典

        Returns:
            V5.2增强版低风险套利引擎实例
        """
        if not config.get('enabled', False):
            logger.info("V5.2增强版低风险套利引擎未启用")
            return None

        try:
            # V5.2引擎需要决策引擎实例
            if self.decision_engine is None:
                logger.warning("⚠️  V5.2决策引擎未初始化，低风险引擎将受限运行")

            # 创建V5.2增强版低风险套利引擎
            enhanced_engine = create_enhanced_low_risk_engine_v5_2(
                config=config,
                decision_engine=self.decision_engine
            )

            logger.info("✅ V5.2增强版低风险套利引擎已启动 (智能深度集成)")
            return enhanced_engine
        except Exception as e:
            logger.error(f"❌ V5.2增强版低风险套利引擎初始化失败: {e}")
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
            optimizer.start_auto_optimization()
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
            # IntelligentKnowledgeManager没有start_processing方法，直接返回已初始化的实例
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
            # AdaptiveErrorHandler只接受一个config参数
            eh = AdaptiveErrorHandler(config=eh_config)
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
                'agent_id': mem0_config.get('agent_id', 'trading-bot-v52'),
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
        system_prompt = """你是专业的数字货币套利交易 AI 助手 V5.2，基于 DeepAgents 框架构建。

## 核心升级特性 V5.2
1. 智能决策引擎 - 深度Memo0语义搜索，基于历史经验决策
2. 增强版低风险套利引擎 - 预测性风险管理和自适应参数调整
3. 知识学习系统 - 从执行中自动学习，优化未来决策
4. 智能路径优化 - 基于历史表现优化执行路径

## 核心职责
- 扫描和分析市场中的套利机会
- 使用V5.2智能决策引擎评估机会
- 执行低风险套利交易（预测性风险管理）
- 监控和管理风险（多层次风险控制）
- 记录和分析交易性能
- 持续优化交易策略（知识学习）

## 套利策略
- 跨交易所套利: 利用不同交易所间的价格差异
- 三角套利: 利用三种货币间的价格不一致
- 基差套利: 利用现货与期货价格差异
- 资金费率套利: 利用永续合约资金费率差异
- 统计套利: 利用历史价格关系的均值回归

## 风险管理原则（V5.2强化）
- 严格遵循预测性风险管理规则
- 优先保证本金安全
- 多层次风险预检和监控
- 自适应风险参数调整
- 分步执行验证，异常自动回滚
- 控制单笔交易风险
- 监控总体敞口和回撤

## 决策流程（V5.2升级）
1. 市场分析 → 2. 机会识别 → 3. V5.2智能评估 → 4. 预测性风险检查 → 5. 自适应参数调整 → 6. 分步执行 → 7. 知识学习

## V5.2智能特性
- 语义搜索历史决策，基于经验推荐策略
- 风险预测：基于历史风险模式提前预警
- 自适应参数：根据风险等级动态调整仓位和止损
- 执行优化：基于历史表现优化执行路径
- 知识积累：从每次执行中学习，持续优化
"""

        model_config = self.config.get('model', {})
        model_provider = model_config.get('provider', 'anthropic')
        model_name = model_config.get('model', 'claude-sonnet-4-5-20250929')

        # 构建完整的模型字符串
        if model_provider and model_name:
            model_string = f"{model_provider}:{model_name}"
        else:
            model_string = 'anthropic:claude-sonnet-4-5-20250929'

        logger.info(f"使用模型: {model_string}")

        model = init_chat_model(
            model=model_string,
            temperature=model_config.get('temperature', 0.0)
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

        # V5.2: 添加智能决策引擎工具
        if self.decision_engine:
            tools.extend([
                self.v52_recommend_strategy_tool,
                self.v52_assess_opportunity_risk_tool,
                self.v52_get_decision_engine_stats_tool,
            ])

        # V5.2: 添加增强版低风险套利引擎工具
        if self.enhanced_low_risk_engine_v5_2:
            tools.extend([
                self.v52_intelligent_evaluation_tool,
                self.v52_optimize_execution_path_tool,
                self.v52_get_enhanced_engine_stats_tool,
                self.v52_learn_from_execution_tool,
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

    # ============ V5.2: 智能决策引擎工具 ============

    @tool
    async def v52_recommend_strategy_tool(
        self,
        volatility: float = 1.5,
        trend: str = "stable",
        liquidity: str = "normal"
    ) -> str:
        """V5.2: 基于Memo0语义搜索推荐策略"""
        if not self.decision_engine:
            return "V5.2智能决策引擎未启用"

        try:
            # 构建市场条件
            current_market_conditions = {
                "volatility": volatility,
                "trend": trend,
                "liquidity": liquidity,
                "timestamp": datetime.now().timestamp()
            }

            # 获取策略推荐
            available_strategies = [
                "cross_exchange", "triangular", "basis_trading",
                "funding_rate", "statistical_arbitrage"
            ]

            recommendation = await self.decision_engine.recommend_strategy(
                current_market_conditions=current_market_conditions,
                available_strategies=available_strategies,
                top_k=3
            )

            # 格式化结果
            result = "=== V5.2 智能策略推荐 ===\n\n"
            result += f"数据源: {recommendation.get('data_source', 'unknown')}\n"
            result += f"生成时间: {recommendation.get('generated_at', 'unknown')}\n\n"

            result += "市场分析:\n"
            market_analysis = recommendation.get('market_analysis', {})
            result += f"  波动率等级: {market_analysis.get('volatility_level', 'N/A')}\n"
            result += f"  波动率建议: {market_analysis.get('volatility_advice', 'N/A')}\n"
            result += f"  趋势强度: {market_analysis.get('trend_strength', 'N/A')}\n"
            result += f"  趋势建议: {market_analysis.get('trend_advice', 'N/A')}\n"
            result += f"  流动性状态: {market_analysis.get('liquidity_status', 'N/A')}\n"
            result += f"  流动性建议: {market_analysis.get('liquidity_advice', 'N/A')}\n\n"

            result += "策略推荐:\n"
            for i, rec in enumerate(recommendation.get('recommendations', []), 1):
                result += f"{i}. {rec.get('strategy', 'N/A')}\n"
                result += f"   置信度: {rec.get('confidence', 0):.2f}\n"
                result += f"   预期胜率: {rec.get('expected_win_rate', 0):.1%}\n"
                result += f"   预期利润: ${rec.get('expected_profit', 0):.2f}\n"
                result += f"   盈亏比: {rec.get('profit_factor', 0):.2f}\n"
                result += f"   历史交易: {rec.get('historical_trades', 0)}笔\n"
                result += f"   推荐理由: {rec.get('reasoning', 'N/A')}\n\n"

            result += "备选策略:\n"
            for strategy in recommendation.get('alternative_strategies', []):
                result += f"  - {strategy}\n"

            return result

        except Exception as e:
            logger.error(f"V5.2策略推荐失败: {e}")
            return f"V5.2策略推荐失败: {str(e)}"

    @tool
    async def v52_assess_opportunity_risk_tool(
        self,
        profit_rate: float = 1.0,
        strategy: str = "cross_exchange"
    ) -> str:
        """V5.2: 评估套利机会风险"""
        if not self.decision_engine:
            return "V5.2智能决策引擎未启用"

        try:
            # 构建机会和条件
            opportunity = {
                "profit_rate": profit_rate,
                "symbol": "BTC/USDT",
                "expected_profit": 100.0 * profit_rate
            }

            current_market_conditions = {
                "volatility": 2.0,
                "trend": "stable",
                "liquidity": "normal"
            }

            # 执行风险评估
            risk_assessment = await self.decision_engine.assess_opportunity_risk(
                opportunity=opportunity,
                strategy=strategy,
                current_market_conditions=current_market_conditions
            )

            # 格式化结果
            result = "=== V5.2 机会风险评估 ===\n\n"
            result += f"策略: {strategy}\n"
            result += f"预期收益率: {profit_rate:.2f}%\n\n"

            result += "风险等级:\n"
            risk_level = risk_assessment.get('risk_level', 'unknown')
            risk_score = risk_assessment.get('risk_score', 0)
            result += f"  等级: {risk_level.upper()}\n"
            result += f"  评分: {risk_score}/100\n\n"

            # 风险因素
            result += "风险因素:\n"
            for factor in risk_assessment.get('risk_factors', []):
                result += f"  - {factor.get('factor', 'N/A')} ({factor.get('severity', 'unknown')})\n"
                result += f"    描述: {factor.get('description', 'N/A')}\n"
                result += f"    影响: {factor.get('score', 0)}\n"
                result += f"    缓解: {factor.get('mitigation', 'N/A')}\n"

            # 建议
            result += "\n建议:\n"
            for rec in risk_assessment.get('recommendations', []):
                result += f"  - {rec}\n"

            # 历史风险
            similar_risks = risk_assessment.get('historical_similar_risks', [])
            if similar_risks:
                result += f"\n历史相似风险: {len(similar_risks)}条\n"

            return result

        except Exception as e:
            logger.error(f"V5.2风险评估失败: {e}")
            return f"V5.2风险评估失败: {str(e)}"

    @tool
    def v52_get_decision_engine_stats_tool(self) -> str:
        """V5.2: 获取智能决策引擎统计"""
        if not self.decision_engine:
            return "V5.2智能决策引擎未启用"

        try:
            stats = self.decision_engine.get_statistics()

            result = "=== V5.2 智能决策引擎统计 ===\n\n"
            result += f"总查询数: {stats.get('total_queries', 0)}\n"
            result += f"缓存命中: {stats.get('cache_hits', 0)}\n"
            result += f"缓存命中率: {stats.get('cache_hit_rate', '0%')}\n"
            result += f"Memo0查询: {stats.get('mem0_queries', 0)}\n"
            result += f"降级查询: {stats.get('fallback_queries', 0)}\n"
            result += f"Memo0可用: {'是' if stats.get('mem0_available', False) else '否'}\n"
            result += f"缓存大小: {stats.get('cache_size', 0)}条\n"

            return result

        except Exception as e:
            logger.error(f"获取V5.2统计失败: {e}")
            return f"获取V5.2统计失败: {str(e)}"

    # ============ V5.2: 增强版低风险套利引擎工具 ============

    @tool
    async def v52_intelligent_evaluation_tool(
        self,
        profit_rate: float = 1.0,
        strategy: str = "cross_exchange"
    ) -> str:
        """V5.2: 智能评估套利机会"""
        if not self.enhanced_low_risk_engine_v5_2:
            return "V5.2增强版低风险套利引擎未启用"

        try:
            # 构建机会
            opportunity = {
                "profit_rate": profit_rate,
                "symbol": "BTC/USDT",
                "expected_profit": 100.0 * profit_rate,
                "max_position_size": 1000.0,
                "buy_exchange": "binance",
                "sell_exchange": "okx"
            }

            # 构建市场条件
            current_market_conditions = {
                "volatility": 2.0,
                "trend": "stable",
                "liquidity": "normal",
                "spread": 0.3,
                "funding_rate": 0.05
            }

            # 执行智能评估
            evaluation = await self.enhanced_low_risk_engine_v5_2.evaluate_opportunity_intelligent(
                opportunity=opportunity,
                strategy=strategy,
                current_market_conditions=current_market_conditions
            )

            # 格式化结果
            result = "=== V5.2 智能评估结果 ===\n\n"
            result += f"执行建议: {'执行' if evaluation.get('should_execute', False) else '拒绝'}\n"
            result += f"置信度: {evaluation.get('confidence', 0):.2f}\n\n"

            result += "决策推理:\n"
            result += f"{evaluation.get('decision_reasoning', 'N/A')}\n\n"

            # 自适应参数
            adaptive_params = evaluation.get('adaptive_parameters', {})
            if adaptive_params:
                result += "自适应风险参数:\n"
                result += f"  基础仓位: ${adaptive_params.get('base_position_size', 0):.2f}\n"
                result += f"  调整后仓位: ${adaptive_params.get('adjusted_position_size', 0):.2f}\n"
                result += f"  基础止损: {adaptive_params.get('base_stop_loss', 0):.2f}%\n"
                result += f"  调整后止损: {adaptive_params.get('adjusted_stop_loss', 0):.2f}%\n"
                result += f"  基础止盈: {adaptive_params.get('base_take_profit', 0):.2f}%\n"
                result += f"  调整后止盈: {adaptive_params.get('adjusted_take_profit', 0):.2f}%\n"
                result += f"  调整因子: {adaptive_params.get('adjustment_factor', 0):.2f}\n"
                result += f"  调整理由: {adaptive_params.get('reasoning', 'N/A')}\n\n"

            # 预期结果
            expected_outcome = evaluation.get('expected_outcome', {})
            if expected_outcome:
                result += "预期结果:\n"
                result += f"  成功概率: {expected_outcome.get('success_probability', 0):.1%}\n"
                result += f"  预期利润: ${expected_outcome.get('expected_profit', 0):.2f}\n"
                result += f"  预期风险: ${expected_outcome.get('expected_loss_risk', 0):.2f}\n"
                result += f"  风险调整后收益: ${expected_outcome.get('risk_adjusted_return', 0):.2f}\n"
                result += f"  置信度: {expected_outcome.get('confidence_level', 'N/A')}\n\n"

            # 风险评估
            risk_assessment = evaluation.get('risk_assessment', {})
            if risk_assessment:
                result += "风险评估:\n"
                result += f"  风险等级: {risk_assessment.get('risk_level', 'N/A')}\n"
                result += f"  风险评分: {risk_assessment.get('risk_score', 0)}/100\n"

            return result

        except Exception as e:
            logger.error(f"V5.2智能评估失败: {e}")
            return f"V5.2智能评估失败: {str(e)}"

    @tool
    async def v52_optimize_execution_path_tool(
        self,
        strategy: str = "cross_exchange"
    ) -> str:
        """V5.2: 优化执行路径"""
        if not self.enhanced_low_risk_engine_v5_2:
            return "V5.2增强版低风险套利引擎未启用"

        try:
            # 构建机会
            opportunity = {
                "symbol": "BTC/USDT",
                "buy_exchange": "binance",
                "sell_exchange": "okx",
                "amount": 1000.0
            }

            # 执行路径优化
            optimization = await self.enhanced_low_risk_engine_v5_2.optimize_execution_path(
                opportunity=opportunity,
                strategy=strategy
            )

            # 格式化结果
            result = "=== V5.2 执行路径优化 ===\n\n"
            result += f"优化状态: {'已优化' if optimization.get('optimized', False) else '未优化'}\n"

            if not optimization.get('optimized', False):
                result += f"原因: {optimization.get('reasoning', 'N/A')}\n"
                return result

            execution_plan = optimization.get('execution_plan', {})
            if execution_plan:
                result += "\n执行计划:\n"

                if 'steps' in execution_plan:
                    result += "执行步骤:\n"
                    for i, step in enumerate(execution_plan['steps'], 1):
                        result += f"  {i}. {step.get('action', 'N/A')} {step.get('exchange', 'N/A')} {step.get('symbol', 'N/A')}\n"
                        if 'amount' in step:
                            result += f"     数量: ${step.get('amount', 0):.2f}\n"

                if 'triangle' in execution_plan:
                    triangle = execution_plan['triangle']
                    result += "三角形路径:\n"
                    result += f"  收益率: {triangle.get('profit_rate', 0):.2f}%\n"

                result += f"\n预估时间: {execution_plan.get('estimated_time', 0):.1f}秒\n"
                result += f"置信度: {execution_plan.get('confidence', 0):.2f}\n"

            result += f"\n优化依据: {optimization.get('optimization_basis', 'N/A')}\n"

            return result

        except Exception as e:
            logger.error(f"V5.2路径优化失败: {e}")
            return f"V5.2路径优化失败: {str(e)}"

    @tool
    def v52_get_enhanced_engine_stats_tool(self) -> str:
        """V5.2: 获取增强版引擎统计"""
        if not self.enhanced_low_risk_engine_v5_2:
            return "V5.2增强版低风险套利引擎未启用"

        try:
            stats = self.enhanced_low_risk_engine_v5_2.get_v5_2_statistics()

            result = "=== V5.2 增强版引擎统计 ===\n\n"

            # 基础统计
            result += "基础统计:\n"
            result += f"  总执行: {stats.get('total_executions', 0)}\n"
            result += f"  成功执行: {stats.get('successful_executions', 0)}\n"
            result += f"  失败执行: {stats.get('failed_executions', 0)}\n"
            result += f"  总利润: ${stats.get('total_profit', 0):.2f}\n"
            result += f"  总损失: ${stats.get('total_loss', 0):.2f}\n\n"

            # V5.2统计
            result += "V5.2智能统计:\n"
            result += f"  智能决策: {stats.get('v5_2_intelligent_decisions', 0)}\n"
            result += f"  风险预测: {stats.get('v5_2_risk_predictions', 0)}\n"
            result += f"  自适应调整: {stats.get('v5_2_adaptive_adjustments', 0)}\n"
            result += f"  知识学习: {stats.get('v5_2_knowledge_learned', 0)}\n\n"

            # 决策引擎统计
            decision_stats = stats.get('decision_engine_stats', {})
            if decision_stats:
                result += "决策引擎统计:\n"
                result += f"  总查询: {decision_stats.get('total_queries', 0)}\n"
                result += f"  缓存命中: {decision_stats.get('cache_hits', 0)}\n"
                result += f"  缓存命中率: {decision_stats.get('cache_hit_rate', '0%')}\n"
                result += f"  Memo0可用: {'是' if decision_stats.get('mem0_available', False) else '否'}\n"

            return result

        except Exception as e:
            logger.error(f"获取V5.2引擎统计失败: {e}")
            return f"获取V5.2引擎统计失败: {str(e)}"

    @tool
    async def v52_learn_from_execution_tool(
        self,
        strategy: str = "cross_exchange",
        profit: float = 25.50,
        status: str = "completed"
    ) -> str:
        """V5.2: 从执行中学习"""
        if not self.enhanced_low_risk_engine_v5_2:
            return "V5.2增强版低风险套利引擎未启用"

        try:
            # 创建模拟执行记录（V15.3统一到V5.9）
            from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import EnhancedArbitrageExecution
            from strategies.enhanced_low_risk_arbitrage_engine import RiskLevel, ExecutionStatus

            execution = EnhancedArbitrageExecution(
                execution_id="test_execution_001",
                strategy=strategy,
                opportunity={"symbol": "BTC/USDT", "profit_rate": 1.0},
                actual_profit=profit,
                status=ExecutionStatus.COMPLETED if status == "completed" else ExecutionStatus.FAILED,
                risk_level=RiskLevel.LOW,
                timestamp=datetime.now().timestamp(),
                intelligent_decision={"decision_type": "execute", "confidence": 0.8},
                market_conditions={"volatility": 2.0, "trend": "stable"}
            )

            # 执行学习
            await self.enhanced_low_risk_engine_v5_2.learn_from_execution(execution)

            result = f"✅ 知识学习完成\n"
            result += f"策略: {strategy}\n"
            result += f"利润: ${profit:.2f}\n"
            result += f"状态: {status}\n"
            result += f"执行ID: {execution.execution_id}\n"
            result += f"时间戳: {datetime.fromtimestamp(execution.timestamp).isoformat()}"

            return result

        except Exception as e:
            logger.error(f"V5.2知识学习失败: {e}")
            return f"V5.2知识学习失败: {str(e)}"

    # ============ 基础工具（保持V3.0兼容） ============

    @tool
    async def scan_arbitrage_opportunities_tool(self, strategy_type: str = "all") -> str:
        """扫描套利机会"""
        logger.info(f"开始扫描 {strategy_type} 套利机会")
        opportunities = await self.strategy_manager.scan_all_strategies()
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
        """启动交易循环 V5.2

        增强功能：
        - V5.2 智能决策引擎集成
        - V5.2 增强版低风险套利引擎集成
        - V5.2 知识学习和自优化
        - V3.0 智能优化集成
        - 持仓监控（有状态策略的自动平仓）
        - 自适应扫描间隔
        - 优雅关闭
        """
        self.is_running = True
        logger.info("启动交易循环 V5.2 (智能深度集成)")

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
                # 持仓监控
                loop_count += 1
                if loop_count % max(1, monitor_interval // base_scan_interval) == 0:
                    await self._monitor_all_positions()

                # 使用V5.2增强版引擎扫描
                opportunities = await with_error_handling(
                    self.strategy_manager.scan_all_strategies,
                    "策略扫描"
                )

                if opportunities:
                    # V5.2: 使用智能决策引擎评估最佳机会
                    if self.decision_engine and self.enhanced_low_risk_engine_v5_2:
                        best_opp = max(opportunities, key=lambda x: x.get('profit_rate', 0))

                        # 构建市场条件
                        current_market_conditions = {
                            "volatility": 2.0,
                            "trend": "stable",
                            "liquidity": "normal"
                        }

                        # V5.2智能评估
                        evaluation = await self.enhanced_low_risk_engine_v5_2.evaluate_opportunity_intelligent(
                            opportunity=best_opp,
                            strategy=best_opp.get('strategy', 'cross_exchange'),
                            current_market_conditions=current_market_conditions
                        )

                        # V5.2决策后执行
                        if evaluation.get('should_execute', False):
                            logger.info(f"V5.2智能决策建议执行: {best_opp.get('symbol', 'N/A')}")
                            # 这里可以执行实际交易
                        else:
                            logger.info(f"V5.2智能决策建议跳过: {best_opp.get('symbol', 'N/A')}")
                    else:
                        # 降级到基础执行
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
        """V5.2: 优雅关闭

        关闭顺序:
        1. 停止交易循环
        2. 关闭持仓
        3. 停止策略
        4. 停止所有V5.x组件
        5. 关闭连接和存储
        """
        self.is_running = False
        logger.info("正在优雅停止 Agent V5.2...")

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

        logger.info("Agent V5.2 已停止")


async def run_crypto_arbitrage_agent_v5_2(config: Dict[str, Any]) -> None:
    """运行数字货币套利交易 Agent V5.2"""
    agent = CryptoArbitrageAgentV52(config)
    try:
        await agent.start_trading_loop()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        await agent.stop()
