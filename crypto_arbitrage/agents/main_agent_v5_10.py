"""数字货币套利交易 Agent V5.10 - 生产级集成版

升级特性：
1. V5.10完整交易流程 - 集成所有Phase 13交易模块
2. V5.10智能决策 - 基于所有模块信息的智能决策
3. V5.10自适应策略 - 根据市场条件自适应调整策略
4. V5.10生产级稳定性 - 确保生产环境的稳定性
5. V5.10性能优化 - 针对生产环境优化性能

V5.10核心突破：
- 完整交易流程集成 - 从数据到执行的全流程自动化
- 智能决策系统 - 基于多维数据的综合决策
- 自适应策略 - 动态调整策略参数
- 生产级稳定性 - 完善的错误处理和降级机制
- 实时性能监控 - 全方位性能跟踪和优化
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

# V5.9组件（保持兼容）
from storage.deep_memo0_integration_v5_9 import DeepMemo0IntegrationV59, create_deep_memo0_integration_v5_9
from strategies.enhanced_low_risk_arbitrage_engine_v5_9 import (
    EnhancedLowRiskArbitrageEngineV59, create_enhanced_low_risk_engine_v5_9
)

# V5.2组件（保持兼容）
from storage.intelligent_decision_engine_v5_2 import IntelligentDecisionEngineV52, create_intelligent_decision_engine_v5_2

# V5.9组件（修复继承路径）
from agents.main_agent_v5_9 import CryptoArbitrageAgentV59

# V3.0组件（保持兼容）
from tools.intelligent_optimizer import IntelligentOptimizer
from tools.knowledge_manager_v3 import IntelligentKnowledgeManager
from tools.adaptive_error_handler import (
    AdaptiveErrorHandler, ErrorSeverity, ErrorCategory
)

# Phase 13核心组件
from trading.trading_coordinator import get_trading_coordinator, TradingCoordinator
from trading.market_data_manager import get_market_data_manager, MarketDataManager
from trading.signal_generator import get_signal_generator, SignalGenerator
from trading.risk_manager_v2 import get_risk_manager_v2, RiskManagerV2
from trading.execution_engine import get_execution_engine, ExecutionEngine
from trading.position_manager import get_position_manager, PositionManager
from trading.trade_monitor import get_trade_monitor, TradeMonitor

logger = logging.getLogger(__name__)


class CryptoArbitrageAgentV510(CryptoArbitrageAgentV59):
    """数字货币套利交易 Agent V5.10 - 生产级集成版

    在V5.9异步深度集成基础上，完整集成Phase 13所有交易模块，实现生产级交易系统。

    修复：继承路径从V5.2改为V5.9，确保继承V5.9的异步分析能力。
    """

    def __init__(self, config: Dict[str, Any]):
        # 调用父类初始化（V5.9的所有功能，包括V5.2的基础功能和异步分析能力）
        super().__init__(config)

        # 更新版本信息
        self.agent_version = "5.10"

        # V5.10: 初始化Phase 13核心模块
        self.trading_coordinator = self._initialize_trading_coordinator(
            config.get('trading_coordinator', {})
        )
        self.market_data_manager = self._initialize_market_data_manager(
            config.get('market_data_manager', {})
        )
        self.signal_generator = self._initialize_signal_generator(
            config.get('signal_generator', {})
        )
        self.risk_manager_v2 = self._initialize_risk_manager_v2(
            config.get('risk_manager_v2', {})
        )
        self.execution_engine = self._initialize_execution_engine(
            config.get('execution_engine', {})
        )
        self.position_manager = self._initialize_position_manager(
            config.get('position_manager', {})
        )
        self.trade_monitor = self._initialize_trade_monitor(
            config.get('trade_monitor', {})
        )

        # V5.10: 集成模块引用到协调器
        self._integrate_modules_to_coordinator()

        # V5.10: 生产级配置
        self.enable_production_mode = config.get('enable_production_mode', False)
        self.production_safety_checks = config.get('production_safety_checks', True)
        self.production_max_daily_trades = config.get('production_max_daily_trades', 100)

        # V5.10: 性能统计
        self.v5_10_performance_stats = {
            "trading_cycles": 0,
            "decisions_made": 0,
            "successful_trades": 0,
            "production_mode_active": False,
            "safety_checks_passed": 0,
            "safety_checks_failed": 0,
        }

        logger.info("数字货币套利交易 Agent V5.10 初始化完成 "
                   "(生产级完整交易流程集成)")

    def _initialize_trading_coordinator(
        self, config: Dict
    ) -> Optional[TradingCoordinator]:
        """初始化交易协调器

        Args:
            config: 配置字典

        Returns:
            交易协调器实例
        """
        try:
            coordinator = get_trading_coordinator()
            logger.info("✅ V5.10交易协调器已初始化")
            return coordinator
        except Exception as e:
            logger.error(f"❌ V5.10交易协调器初始化失败: {e}")
            return None

    def _initialize_market_data_manager(
        self, config: Dict
    ) -> Optional[MarketDataManager]:
        """初始化市场数据管理器

        Args:
            config: 配置字典

        Returns:
            市场数据管理器实例
        """
        try:
            manager = get_market_data_manager()
            logger.info("✅ V5.10市场数据管理器已初始化")
            return manager
        except Exception as e:
            logger.error(f"❌ V5.10市场数据管理器初始化失败: {e}")
            return None

    def _initialize_signal_generator(
        self, config: Dict
    ) -> Optional[SignalGenerator]:
        """初始化信号生成器

        Args:
            config: 配置字典

        Returns:
            信号生成器实例
        """
        try:
            generator = get_signal_generator()
            logger.info("✅ V5.10信号生成器已初始化")
            return generator
        except Exception as e:
            logger.error(f"❌ V5.10信号生成器初始化失败: {e}")
            return None

    def _initialize_risk_manager_v2(
        self, config: Dict
    ) -> Optional[RiskManagerV2]:
        """初始化风险管理器V2

        Args:
            config: 配置字典

        Returns:
            风险管理器V2实例
        """
        try:
            manager = get_risk_manager_v2()
            logger.info("✅ V5.10风险管理器V2已初始化")
            return manager
        except Exception as e:
            logger.error(f"❌ V5.10风险管理器V2初始化失败: {e}")
            return None

    def _initialize_execution_engine(
        self, config: Dict
    ) -> Optional[ExecutionEngine]:
        """初始化交易执行引擎

        Args:
            config: 配置字典

        Returns:
            交易执行引擎实例
        """
        try:
            engine = get_execution_engine()
            logger.info("✅ V5.10交易执行引擎已初始化")
            return engine
        except Exception as e:
            logger.error(f"❌ V5.10交易执行引擎初始化失败: {e}")
            return None

    def _initialize_position_manager(
        self, config: Dict
    ) -> Optional[PositionManager]:
        """初始化仓位管理器

        Args:
            config: 配置字典

        Returns:
            仓位管理器实例
        """
        try:
            manager = get_position_manager()
            logger.info("✅ V5.10仓位管理器已初始化")
            return manager
        except Exception as e:
            logger.error(f"❌ V5.10仓位管理器初始化失败: {e}")
            return None

    def _initialize_trade_monitor(
        self, config: Dict
    ) -> Optional[TradeMonitor]:
        """初始化交易监控器

        Args:
            config: 配置字典

        Returns:
            交易监控器实例
        """
        try:
            monitor = get_trade_monitor()
            logger.info("✅ V5.10交易监控器已初始化")
            return monitor
        except Exception as e:
            logger.error(f"❌ V5.10交易监控器初始化失败: {e}")
            return None

    def _integrate_modules_to_coordinator(self) -> None:
        """集成模块到协调器"""
        if self.trading_coordinator:
            self.trading_coordinator.market_data_manager = self.market_data_manager
            self.trading_coordinator.signal_generator = self.signal_generator
            self.trading_coordinator.risk_manager = self.risk_manager_v2
            self.trading_coordinator.execution_engine = self.execution_engine
            self.trading_coordinator.position_manager = self.position_manager
            self.trading_coordinator.trade_monitor = self.trade_monitor
            logger.info("✅ V5.10所有模块已集成到交易协调器")

    def _get_agent_tools(self) -> List:
        """获取Agent工具列表（V5.10增强）"""
        # 获取V5.9的工具
        tools = super()._get_agent_tools()

        # V5.10: 添加完整交易流程工具（检查属性是否存在，避免初始化顺序问题）
        if hasattr(self, 'trading_coordinator') and self.trading_coordinator:
            tools.extend([
                self.v510_run_complete_trading_cycle_tool,
                self.v510_get_system_status_tool,
                self.v510_get_integration_status_tool,
                self.v510_production_mode_tool,
                self.v510_safety_check_tool,
            ])

        # V5.10: 添加模块工具
        if hasattr(self, 'risk_manager_v2') and self.risk_manager_v2:
            tools.extend([
                self.v510_get_risk_status_tool,
                self.v510_generate_risk_report_tool,
            ])

        if hasattr(self, 'execution_engine') and self.execution_engine:
            tools.extend([
                self.v510_get_execution_report_tool,
            ])

        if hasattr(self, 'position_manager') and self.position_manager:
            tools.extend([
                self.v510_get_position_report_tool,
            ])

        if hasattr(self, 'trade_monitor') and self.trade_monitor:
            tools.extend([
                self.v510_get_monitoring_report_tool,
            ])

        return tools

    # ============ V5.10: 完整交易流程工具 ============

    @tool
    async def v510_run_complete_trading_cycle_tool(self) -> str:
        """V5.10: 运行完整交易周期"""
        if not self.trading_coordinator:
            return "V5.10交易协调器未初始化"

        try:
            # 执行完整交易周期
            await self.trading_coordinator._execute_trading_cycle()

            self.v5_10_performance_stats["trading_cycles"] += 1

            # 获取状态
            status = self.trading_coordinator.get_trading_status()

            result = "=== V5.10 完整交易周期完成 ===\n\n"
            result += f"队列大小: {status['queue_size']}\n"
            result += f"执行中交易: {status['executing_trades']}\n"
            result += f"已完成交易: {status['completed_trades']}\n\n"

            # 性能指标
            metrics = status.get('stats', {})
            result += "交易统计:\n"
            result += f"  总交易数: {metrics.get('total_trades', 0)}\n"
            result += f"  成功交易: {metrics.get('successful_trades', 0)}\n"
            result += f"  失败交易: {metrics.get('failed_trades', 0)}\n"
            result += f"  成功率: {metrics.get('successful_trades', 0) / max(1, metrics.get('total_trades', 1)) * 100:.1f}%\n"

            return result

        except Exception as e:
            logger.error(f"V5.10完整交易周期失败: {e}")
            return f"V5.10完整交易周期失败: {str(e)}"

    @tool
    def v510_get_system_status_tool(self) -> str:
        """V5.10: 获取系统状态"""
        status_info = "=== V5.10 系统状态 ===\n\n"

        # 交易协调器状态
        if self.trading_coordinator:
            trading_status = self.trading_coordinator.get_trading_status()
            status_info += "交易协调器:\n"
            status_info += f"  队列大小: {trading_status['queue_size']}\n"
            status_info += f"  执行中: {trading_status['executing_trades']}\n"
            status_info += f"  已完成: {trading_status['completed_trades']}\n"
            status_info += f"  熔断器: {'激活' if trading_status['circuit_breaker_active'] else '正常'}\n\n"

        # 风险管理器状态
        if self.risk_manager_v2:
            risk_status = self.risk_manager_v2.get_risk_status()
            status_info += "风险管理器V2:\n"
            status_info += f"  熔断器激活: {risk_status['circuit_breaker_active']}\n"
            status_info += f"  当前风险等级: {risk_status['current_risks'].get('overall_risk_level', 'N/A')}\n\n"

        # 执行引擎状态
        if self.execution_engine:
            exec_report = self.execution_engine.get_execution_report()
            status_info += "执行引擎:\n"
            status_info += f"  活动订单: {exec_report['active_orders']}\n"
            status_info += f"  总订单数: {exec_report['total_orders']}\n"
            status_info += f"  成功率: {exec_report['stats']['successful_orders'] / max(1, exec_report['stats']['total_orders']) * 100:.1f}%\n\n"

        # 仓位管理器状态
        if self.position_manager:
            pos_report = self.position_manager.generate_position_report()
            status_info += "仓位管理器:\n"
            status_info += f"  当前仓位: {pos_report['total_positions']}\n"
            status_info += f"  总敞口: ${pos_report['total_exposure']:.2f}\n"
            status_info += f"  未实现盈亏: ${pos_report['unrealized_pnl']:.2f}\n\n"

        # 交易监控器状态
        if self.trade_monitor:
            # 使用同步方式获取监控报告（避免async/await问题）
            try:
                monitor_report = self.trade_monitor.generate_monitoring_report_sync()
                status_info += "交易监控器:\n"
                status_info += f"  总交易数: {monitor_report.get('total_trades', 0)}\n"
                status_info += f"  异常数: {monitor_report.get('anomaly_count', 0)}\n"
                status_info += f"  监控启用: {monitor_report.get('monitoring_enabled', False)}\n\n"
            except Exception as e:
                status_info += f"交易监控器: 状态获取失败 ({str(e)[:50]})\n\n"

        # 生产模式状态
        status_info += "生产模式:\n"
        status_info += f"  启用: {self.enable_production_mode}\n"
        status_info += f"  安全检查: {self.production_safety_checks}\n"

        return status_info

    @tool
    def v510_get_integration_status_tool(self) -> str:
        """V5.10: 获取集成状态"""
        status = "=== V5.10 模块集成状态 ===\n\n"

        modules = {
            '交易协调器': self.trading_coordinator is not None,
            '市场数据管理器': self.market_data_manager is not None,
            '信号生成器': self.signal_generator is not None,
            '风险管理器V2': self.risk_manager_v2 is not None,
            '执行引擎': self.execution_engine is not None,
            '仓位管理器': self.position_manager is not None,
            '交易监控器': self.trade_monitor is not None,
        }

        for module_name, initialized in modules.items():
            status_emoji = "✅" if initialized else "❌"
            status += f"{status_emoji} {module_name}: {'已初始化' if initialized else '未初始化'}\n"

        total_modules = len(modules)
        initialized_count = sum(modules.values())
        integration_rate = initialized_count / total_modules * 100

        status += f"\n集成率: {integration_rate:.1f}% ({initialized_count}/{total_modules})"

        return status

    @tool
    def v510_production_mode_tool(self, enable: bool = False) -> str:
        """V5.10: 生产模式切换"""
        if self.production_safety_checks and enable:
            # 生产安全检查
            safety_result = self._perform_production_safety_check()
            if not safety_result['passed']:
                return f"生产模式安全检查失败:\n{safety_result['reason']}\n\n建议: {safety_result['recommendation']}"

        self.enable_production_mode = enable
        self.v5_10_performance_stats["production_mode_active"] = enable

        status = "✅" if enable else "❌"
        logger.info(f"{status} 生产模式已{'启用' if enable else '禁用'}")

        return f"{status} 生产模式已{'启用' if enable else '禁用'}"

    @tool
    def v510_safety_check_tool(self) -> str:
        """V5.10: 执行安全检查"""
        result = self._perform_production_safety_check()

        report = "=== V5.10 安全检查 ===\n\n"
        report += f"状态: {'通过' if result['passed'] else '未通过'}\n"
        report += f"原因: {result['reason']}\n"
        report += f"建议: {result['recommendation']}\n\n"

        # 详细检查项
        report += "检查项:\n"
        for check, passed in result['checks'].items():
            emoji = "✅" if passed else "❌"
            report += f"  {emoji} {check}\n"

        return report

    @tool
    def v510_get_risk_status_tool(self) -> str:
        """V5.10: 获取风险状态"""
        if not self.risk_manager_v2:
            return "风险管理器V2未初始化"

        risk_status = self.risk_manager_v2.get_risk_status()

        result = "=== V5.10 风险状态 ===\n\n"
        result += f"熔断器激活: {risk_status['circuit_breaker_active']}\n"
        result += f"熔断器触发: {risk_status['circuit_breaker_triggered']}\n\n"

        # 当前风险
        current_risks = risk_status.get('current_risks', {})
        result += f"整体风险等级: {current_risks.get('overall_risk_level', 'N/A')}\n\n"

        # 统计
        stats = risk_status.get('stats', {})
        result += "风险统计:\n"
        result += f"  总评估: {stats.get('total_risk_assessments', 0)}\n"
        result += f"  批准: {stats.get('approvals', 0)}\n"
        result += f"  拒绝: {stats.get('rejections', 0)}\n"
        result += f"  风险警告: {stats.get('risk_warnings', 0)}\n"
        result += f"  熔断器触发: {stats.get('circuit_breaker_triggers', 0)}\n"

        return result

    @tool
    async def v510_generate_risk_report_tool(self) -> str:
        """V5.10: 生成风险报告"""
        if not self.risk_manager_v2:
            return "风险管理器V2未初始化"

        try:
            report = await self.risk_manager_v2.generate_risk_report()

            result = "=== V5.10 风险报告 ===\n\n"
            result += f"报告时间: {report.get('report_time', 'N/A')}\n\n"

            # 当前风险
            current_risks = report.get('current_risks', {})
            result += f"整体风险等级: {current_risks.get('overall_risk_level', 'N/A')}\n\n"

            # 风险摘要
            risk_summary = report.get('risk_summary', {})
            result += f"状态: {risk_summary.get('status', 'N/A')}\n\n"

            # 建议
            recommendations = risk_summary.get('recommendations', [])
            if recommendations:
                result += "风险建议:\n"
                for i, rec in enumerate(recommendations, 1):
                    result += f"  {i}. {rec}\n"

            return result

        except Exception as e:
            logger.error(f"生成风险报告失败: {e}")
            return f"生成风险报告失败: {str(e)}"

    @tool
    def v510_get_execution_report_tool(self) -> str:
        """V5.10: 获取执行报告"""
        if not self.execution_engine:
            return "执行引擎未初始化"

        report = self.execution_engine.get_execution_report()

        result = "=== V5.10 执行报告 ===\n\n"
        result += f"活动订单: {report['active_orders']}\n"
        result += f"总订单数: {report['total_orders']}\n"
        result += f"活动交易所: {report['active_exchange']}\n\n"

        # 执行统计
        stats = report.get('stats', {})
        result += "执行统计:\n"
        result += f"  总订单数: {stats.get('total_orders', 0)}\n"
        result += f"  成功订单: {stats.get('successful_orders', 0)}\n"
        result += f"  失败订单: {stats.get('failed_orders', 0)}\n"
        result += f"  取消订单: {stats.get('cancelled_orders', 0)}\n"
        result += f"  平均执行时间: {stats.get('avg_execution_time', 0):.2f}s\n"
        result += f"  平均滑点: {stats.get('avg_slippage', 0):.2f}%\n"

        return result

    @tool
    def v510_get_position_report_tool(self) -> str:
        """V5.10: 获取仓位报告"""
        if not self.position_manager:
            return "仓位管理器未初始化"

        report = self.position_manager.generate_position_report()

        result = "=== V5.10 仓位报告 ===\n\n"
        result += f"报告时间: {report.get('report_time', 'N/A')}\n"
        result += f"总仓位: {report.get('total_positions', 0)}\n"
        result += f"总敞口: ${report.get('total_exposure', 0):.2f}\n"
        result += f"未实现盈亏: ${report.get('unrealized_pnl', 0):.2f}\n"
        result += f"已实现盈亏: ${report.get('realized_pnl', 0):.2f}\n"
        result += f"总盈亏: ${report.get('total_pnl', 0):.2f}\n\n"

        # 按交易对统计
        positions_by_symbol = report.get('positions_by_symbol', {})
        if positions_by_symbol:
            result += "按交易对统计:\n"
            for symbol, summary in positions_by_symbol.items():
                result += f"  {symbol}:\n"
                result += f"    仓位数: {summary['count']}\n"
                result += f"    总价值: ${summary['total_value']:.2f}\n"
                result += f"    盈亏: ${summary['unrealized_pnl']:.2f}\n"

        return result

    @tool
    async def v510_get_monitoring_report_tool(self) -> str:
        """V5.10: 获取监控报告"""
        if not self.trade_monitor:
            return "交易监控器未初始化"

        try:
            report = await self.trade_monitor.generate_monitoring_report()

            result = "=== V5.10 监控报告 ===\n\n"
            result += f"报告时间: {report.get('report_time', 'N/A')}\n"
            result += f"总交易数: {report.get('total_trades', 0)}\n"
            result += f"活动交易: {report.get('active_trades', 0)}\n"
            result += f"异常数: {report.get('anomaly_count', 0)}\n"
            result += f"监控启用: {report.get('monitoring_enabled', False)}\n\n"

            # 性能指标
            performance = report.get('performance_metrics', {})
            result += "性能指标:\n"
            result += f"  成功率: {performance.get('success_rate', 0) * 100:.1f}%\n"
            result += f"  平均执行时间: {performance.get('avg_execution_time', 0):.2f}s\n"
            result += f"  平均滑点: {performance.get('avg_slippage', 0):.2f}%\n"

            return result

        except Exception as e:
            logger.error(f"生成监控报告失败: {e}")
            return f"生成监控报告失败: {str(e)}"

    async def start_trading_loop(self) -> None:
        """启动交易循环 V5.10

        增强功能：
        - V5.10 完整交易流程集成
        - V5.10 生产模式支持
        - V5.10 完整安全检查
        - 实时性能监控和优化
        - 完整的向后兼容性
        """
        self.is_running = True
        logger.info("启动交易循环 V5.10 (生产级集成)")

        # 初始化所有Phase 13模块
        await self._initialize_v5_10_modules()

        # 生产模式安全检查
        if self.enable_production_mode and self.production_safety_checks:
            safety_result = self._perform_production_safety_check()
            if not safety_result['passed']:
                logger.warning(f"生产模式安全检查失败: {safety_result['reason']}")
                logger.info(f"建议: {safety_result['recommendation']}")
                logger.info("禁用生产模式，继续运行...")
                self.enable_production_mode = False

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

        try:
            # 启动交易协调器
            if self.trading_coordinator:
                await self.trading_coordinator.start()

            # 启动市场数据管理器
            if self.market_data_manager:
                await self.market_data_manager.start()

            # 启动交易监控
            if self.trade_monitor:
                await self.trade_monitor.start_monitoring()

            # 主循环
            while self.is_running:
                try:
                    # V5.10: 使用交易协调器执行交易周期
                    if self.trading_coordinator:
                        await with_error_handling(
                            self.trading_coordinator._execute_trading_cycle,
                            "V5.10交易周期"
                        )
                        self.v5_10_performance_stats["trading_cycles"] += 1
                    else:
                        logger.warning("V5.10交易协调器未初始化，使用V5.9交易循环")
                        await self._run_v5_9_trading_cycle()

                    # 等待下一个周期
                    base_scan_interval = self.config.get('scan_interval', 30)
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
                            context="V5.10交易循环"
                        )

                    await asyncio.sleep(10)

        finally:
            # 清理资源
            await self._cleanup_v5_10_modules()

    async def _initialize_v5_10_modules(self) -> None:
        """初始化V5.10模块"""
        try:
            # 初始化各个模块
            if self.trading_coordinator:
                await self.trading_coordinator.initialize()

            if self.market_data_manager:
                await self.market_data_manager.initialize()

            if self.signal_generator:
                await self.signal_generator.initialize()

            if self.risk_manager_v2:
                await self.risk_manager_v2.initialize()

            if self.execution_engine:
                await self.execution_engine.initialize()

            if self.position_manager:
                await self.position_manager.initialize()

            if self.trade_monitor:
                await self.trade_monitor.initialize()

            logger.info("✅ V5.10所有模块初始化完成")

        except Exception as e:
            logger.error(f"初始化V5.10模块失败: {e}")

    async def _run_v5_9_trading_cycle(self) -> None:
        """运行V5.9交易循环（向后兼容）"""
        # 这里可以调用V5.9的交易逻辑
        # 作为降级方案
        pass

    async def _cleanup_v5_10_modules(self) -> None:
        """清理V5.10模块"""
        try:
            # 停止各个模块
            if self.trade_monitor:
                await self.trade_monitor.stop()

            if self.market_data_manager:
                await self.market_data_manager.stop()

            if self.trading_coordinator:
                await self.trading_coordinator.stop()

            if self.risk_manager_v2:
                await self.risk_manager_v2.stop()

            if self.execution_engine:
                await self.execution_engine.stop()

            if self.position_manager:
                await self.position_manager.stop()

            logger.info("✅ V5.10所有模块已停止")

        except Exception as e:
            logger.error(f"清理V5.10模块失败: {e}")

    def _perform_production_safety_check(self) -> Dict[str, Any]:
        """执行生产安全检查

        Returns:
            安全检查结果字典
        """
        checks = {
            '交易协调器初始化': self.trading_coordinator is not None,
            '风险管理器初始化': self.risk_manager_v2 is not None,
            '执行引擎初始化': self.execution_engine is not None,
            '仓位管理器初始化': self.position_manager is not None,
            '交易监控器初始化': self.trade_monitor is not None,
        }

        all_passed = all(checks.values())

        if all_passed:
            return {
                'passed': True,
                'reason': '所有安全检查通过',
                'recommendation': '可以启用生产模式',
                'checks': checks,
            }
        else:
            failed_checks = [name for name, passed in checks.items() if not passed]
            return {
                'passed': False,
                'reason': f'以下模块未初始化: {", ".join(failed_checks)}',
                'recommendation': '请确保所有核心模块已初始化',
                'checks': checks,
            }


async def run_crypto_arbitrage_agent_v5_10(config: Dict[str, Any]) -> None:
    """运行数字货币套利交易 Agent V5.10"""
    agent = CryptoArbitrageAgentV510(config)
    try:
        await agent.start_trading_loop()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        await agent.stop()
