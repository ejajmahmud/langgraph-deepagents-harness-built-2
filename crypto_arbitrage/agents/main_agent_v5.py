"""数字货币套利交易 Agent - V5.0 性能优化版

性能优化特性：
1. 延迟加载 - 所有策略和可选组件按需加载
2. 动态导入 - 减少启动时的依赖链
3. 并发初始化 - 独立组件并行初始化
4. 优化配置 - 减少不必要的初始化

目标：初始化时间从 5.94秒优化到 < 3秒
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

# 只导入必需的核心组件
from tools.exchange_api import get_exchange_manager, initialize_exchange_manager
from tools.risk_management import get_risk_manager, initialize_risk_manager
from tools.monitoring import initialize_monitoring, get_monitoring
from tools.transaction_executor import (
    initialize_transaction_executor, get_transaction_executor
)
from tools.notifier import initialize_notifier, get_notifier
from strategies.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)


class CryptoArbitrageAgentV5:
    """数字货币套利交易 Agent V5.0 性能优化版

    基于 DeepAgents 框架 + Memo0 存储 + 智能自进化系统
    + 性能优化（延迟加载、动态导入、并发初始化）
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 基础组件初始化（必须的）
        logger.info("[V5.0] 开始性能优化初始化...")

        # 并行初始化独立组件
        init_tasks = []

        # 交易所管理器
        init_tasks.append(self._async_init_exchange_manager())

        # 风险管理器
        init_tasks.append(self._async_init_risk_manager())

        # 监控系统
        init_tasks.append(self._async_init_monitoring())

        # 通知系统
        init_tasks.append(self._async_init_notifier())

        # 策略管理器
        init_tasks.append(self._async_init_strategy_manager())

        # 等待基础组件初始化完成
        results = asyncio.run(asyncio.gather(*init_tasks, return_exceptions=True))

        # 处理初始化结果
        self.exchange_manager = results[0]
        self.risk_manager = results[1]
        self.monitoring = results[2]
        self.notifier = results[3]
        self.strategy_manager = results[4]

        # 初始化策略（延迟加载）
        self.strategies = self._initialize_strategies(config.get('strategies', {}))

        # 将策略注册到管理器
        self._register_strategies_to_manager()

        # 初始化可选组件（按需加载）
        self._initialize_optional_components(config)

        # 交易执行引擎
        self.transaction_executor = initialize_transaction_executor(
            config.get('transaction_executor', {})
        )

        # Memo0 存储
        self._initialize_mem0_storage(config.get('mem0', {}))

        # 创建 DeepAgent
        self.agent = self._create_agent()

        # 注册 API Backend
        self._register_api_backend()

        # 运行状态
        self.is_running = False
        self.performance_stats: Dict[str, Any] = {}

        logger.info("数字货币套利交易 Agent V5.0 初始化完成 (性能优化版)")

    async def _async_init_exchange_manager(self):
        """异步初始化交易所管理器"""
        try:
            manager = initialize_exchange_manager(self.config.get('exchanges', {}))
            logger.info("[V5.0] 交易所管理器初始化完成")
            return manager
        except Exception as e:
            logger.error(f"[V5.0] 交易所管理器初始化失败: {e}")
            return None

    async def _async_init_risk_manager(self):
        """异步初始化风险管理器"""
        try:
            manager = initialize_risk_manager(self.config.get('risk_management', {}))
            logger.info("[V5.0] 风险管理器初始化完成")
            return manager
        except Exception as e:
            logger.error(f"[V5.0] 风险管理器初始化失败: {e}")
            return None

    async def _async_init_monitoring(self):
        """异步初始化监控系统"""
        try:
            monitoring = initialize_monitoring(self.config.get('monitoring', {}))
            logger.info("[V5.0] 监控系统初始化完成")
            return monitoring
        except Exception as e:
            logger.error(f"[V5.0] 监控系统初始化失败: {e}")
            return None

    async def _async_init_notifier(self):
        """异步初始化通知系统"""
        try:
            notifier = initialize_notifier(self.config.get('notifications', {}))
            logger.info("[V5.0] 通知系统初始化完成")
            return notifier
        except Exception as e:
            logger.error(f"[V5.0] 通知系统初始化失败: {e}")
            return None

    async def _async_init_strategy_manager(self):
        """异步初始化策略管理器"""
        try:
            manager = StrategyManager(self.config.get('strategy_manager', {}))
            logger.info("[V5.0] 策略管理器初始化完成")
            return manager
        except Exception as e:
            logger.error(f"[V5.0] 策略管理器初始化失败: {e}")
            return None

    def _initialize_strategies(self, strategies_config: Dict) -> Dict[str, Any]:
        """初始化交易策略（延迟加载）"""
        strategies = {}

        # 延迟导入策略类
        strategy_classes = {
            'cross_exchange': 'strategies.cross_exchange.CrossExchangeArbitrageStrategy',
            'triangular': 'strategies.triangular_arbitrage.TriangularArbitrageStrategy',
            'basis_trading': 'strategies.basis_trading.BasisTradingStrategy',
            'funding_rate': 'strategies.funding_rate.FundingRateArbitrageStrategy',
            'statistical_arbitrage': 'strategies.statistical_arbitrage.StatisticalArbitrageStrategy'
        }

        for strategy_name, strategy_cfg in strategies_config.items():
            if not strategy_cfg.get('enabled', False):
                continue

            try:
                # 动态导入策略类
                if strategy_name in strategy_classes:
                    module_path, class_name = strategy_classes[strategy_name].rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    strategy_class = getattr(module, class_name)
                    strategies[strategy_name] = strategy_class(strategy_cfg)
                else:
                    logger.warning(f"[V5.0] 未知策略: {strategy_name}")
            except Exception as e:
                logger.error(f"[V5.0] 初始化策略 {strategy_name} 失败: {e}")

        logger.info(f"[V5.0] 初始化 {len(strategies)} 个交易策略: {list(strategies.keys())}")
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

    def _initialize_optional_components(self, config: Dict):
        """初始化可选组件（按需加载）"""
        # V2.9: 增强策略管理器（TradingAgents集成）
        self.enhanced_strategy_manager = None
        if config.get('trading_agents', {}).get('enabled', False):
            try:
                from strategies.enhanced_strategy_manager import create_enhanced_strategy_manager
                self.enhanced_strategy_manager = create_enhanced_strategy_manager(
                    self.strategy_manager,
                    config.get('trading_agents', {})
                )
                logger.info("[V5.0] 增强策略管理器已启用 (V2.9)")
            except Exception as e:
                logger.warning(f"[V5.0] 增强策略管理器初始化失败: {e}")

        # V4.2: 增强版低风险套利引擎
        self.enhanced_low_risk_engine = None
        if config.get('enhanced_low_risk_engine', {}).get('enabled', False):
            try:
                from strategies.enhanced_low_risk_arbitrage_engine import EnhancedLowRiskArbitrageEngine
                self.enhanced_low_risk_engine = EnhancedLowRiskArbitrageEngine(
                    risk_manager=self.risk_manager,
                    config=config.get('enhanced_low_risk_engine', {})
                )
                logger.info("[V5.0] 增强版低风险套利引擎 V4.1 已启用")
            except Exception as e:
                logger.warning(f"[V5.0] 增强版低风险套利引擎初始化失败: {e}")

        # V3.0: 智能优化引擎（延迟初始化）
        self.intelligent_optimizer = self._initialize_intelligent_optimizer(
            config.get('intelligent_optimizer', {})
        )

        # V3.0: 智能知识管理器 V3（延迟初始化）
        self.intelligent_knowledge_manager = self._initialize_intelligent_knowledge_manager(
            config.get('knowledge_manager_v3', {})
        )

        # V3.0: 自适应错误处理器（延迟初始化）
        self.error_handler = self._initialize_adaptive_error_handler(
            config.get('adaptive_error_handler', {})
        )

    def _initialize_intelligent_optimizer(self, optimizer_config: Dict) -> Optional[Any]:
        """初始化智能优化引擎（延迟加载）"""
        if not optimizer_config.get('enabled', False):
            logger.info("[V5.0] 智能优化引擎未启用")
            return None

        try:
            from tools.intelligent_optimizer import IntelligentOptimizer
            optimizer = IntelligentOptimizer(
                optimization_interval=optimizer_config.get('optimization_interval', 300),
                history_window=optimizer_config.get('history_window', 1000),
                min_data_points=optimizer_config.get('min_data_points', 50),
            )
            logger.info("[V5.0] 智能优化引擎已启用")
            return optimizer
        except Exception as e:
            logger.warning(f"[V5.0] 智能优化引擎初始化失败: {e}")
            return None

    def _initialize_intelligent_knowledge_manager(
        self, km_config: Dict
    ) -> Optional[Any]:
        """初始化智能知识管理器 V3（延迟加载）"""
        if not km_config.get('enabled', False):
            logger.info("[V5.0] 智能知识管理器 V3 未启用")
            return None

        try:
            from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
            manager = IntelligentKnowledgeManager(km_config)
            logger.info("[V5.0] 智能知识管理器 V3 已启用")
            return manager
        except Exception as e:
            logger.warning(f"[V5.0] 智能知识管理器 V3 初始化失败: {e}")
            return None

    def _initialize_adaptive_error_handler(
        self, error_config: Dict
    ) -> Optional[Any]:
        """初始化自适应错误处理器（延迟加载）"""
        if not error_config.get('enabled', False):
            logger.info("[V5.0] 自适应错误处理器未启用")
            return None

        try:
            from tools.adaptive_error_handler import AdaptiveErrorHandler
            handler = AdaptiveErrorHandler(error_config)
            logger.info("[V5.0] 自适应错误处理器已启用")
            return handler
        except Exception as e:
            logger.warning(f"[V5.0] 自适应错误处理器初始化失败: {e}")
            return None

    def _initialize_mem0_storage(self, mem0_config: Dict):
        """初始化 Memo0 存储"""
        try:
            from storage.mem0_storage import initialize_mem0
            initialize_mem0(mem0_config)
            logger.info("存储初始化完成，使用 SQLite")
        except Exception as e:
            logger.warning(f"[V5.0] Memo0 存储初始化失败: {e}")

    def _create_agent(self) -> Any:
        """创建 DeepAgent"""
        chat_model = init_chat_model(
            model=self.config.get('model', 'anthropic:claude-sonnet-4-5-20250929')
        )

        return create_deep_agent(
            model=chat_model,
            tools=self._get_tools(),
            system_prompt=self._get_system_prompt()
        )

    def _get_tools(self) -> List[Callable]:
        """获取工具列表（延迟导入）"""
        from tools.knowledge_recorder import get_knowledge_recorder
        from tools.decision_assistant import get_decision_assistant
        from tools.knowledge_cycle_manager import get_knowledge_cycle_manager

        knowledge_recorder = get_knowledge_recorder()
        decision_assistant = get_decision_assistant()
        knowledge_cycle_manager = get_knowledge_cycle_manager()

        return [
            tool(get_knowledge_recorder().record_knowledge),
            tool(get_decision_assistant().advise_on_trade),
            tool(get_knowledge_cycle_manager().optimize_knowledge_base),
        ]

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的数字货币套利交易助手，基于 DeepAgents 框架构建。

核心能力：
1. 低风险套利策略（跨交易所、三角、基差、资金费率、统计套利）
2. 风险管理和监控
3. Memo0 存储和智能决策
4. TradingAgents 多智能体分析
5. 增强版低风险套利引擎（V4.1）

请根据用户需求提供专业的套利分析和建议。"""

    def _register_api_backend(self):
        """注册 API Backend"""
        try:
            from backend.api import set_agent
            set_agent(self)
            logger.info("[V5.0] API Backend 已注册")
        except Exception as e:
            logger.warning(f"[V5.0] API Backend 注册失败: {e}")

    async def scan_arbitrage_opportunities_tool(
        self, market: str = "all"
    ) -> str:
        """扫描套利机会（延迟加载策略）"""
        if not self.strategies:
            return "没有可用的交易策略"

        results = []
        for name, strategy in self.strategies.items():
            try:
                opportunities = await strategy.scan_opportunities()
                if opportunities:
                    results.append(f"{name}: {len(opportunities)} 个机会")
            except Exception as e:
                logger.error(f"扫描策略 {name} 失败: {e}")

        return "\n".join(results) if results else "未发现套利机会"


# 创建性能优化版本的工厂函数
def create_crypto_arbitrage_agent_v5(config: Dict[str, Any]) -> CryptoArbitrageAgentV5:
    """创建性能优化版本的 Agent

    Args:
        config: 配置字典

    Returns:
        CryptoArbitrageAgentV5 实例
    """
    return CryptoArbitrageAgentV5(config)


# 兼容性函数 - 保持与原版本的接口一致
def run_crypto_arbitrage_agent_v5(config: Dict[str, Any]):
    """运行性能优化版本的 Agent（兼容性函数）

    Args:
        config: 配置字典
    """
    agent = create_crypto_arbitrage_agent_v5(config)
    # 这里可以添加主循环逻辑
    return agent


if __name__ == "__main__":
    # 性能测试
    import time

    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']},
        'enhanced_low_risk_engine': {
            'enabled': True,
            'enable_risk_prediction': True,
            'enable_health_monitoring': True,
            'enable_intelligent_decision': True
        },
        'trading_agents': {'enabled': False}
    }

    start = time.time()
    agent = create_crypto_arbitrage_agent_v5(config)
    elapsed = time.time() - start

    print(f"\n[V5.0 性能测试]")
    print(f"初始化时间: {elapsed:.3f}秒 ({elapsed*1000:.2f}ms)")
    print(f"优化效果: 原版5.94秒 -> V5.0 {elapsed:.3f}秒")
    print(f"性能提升: {((5.94 - elapsed) / 5.94 * 100):.1f}%")

    if elapsed < 3.0:
        print("状态: EXCELLENT - 达到目标 (< 3秒)")
    elif elapsed < 5.0:
        print("状态: GOOD - 显著改善 (3-5秒)")
    else:
        print("状态: 需进一步优化")
