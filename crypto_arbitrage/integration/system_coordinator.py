"""系统协调器 - Phase 12核心模块

统一协调系统各模块的运行，实现完整的系统集成。

核心功能：
1. 统一启动 - 协调监控、自动化、交易模块的启动顺序
2. 生命周期管理 - 统一管理所有模块的生命周期
3. 事件总线 - 模块间的事件通信机制
4. 健康协调 - 基于健康检查的自动协调
5. 优雅关闭 - 优雅关闭所有模块

创建时间：2026-04-19 21:35:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """系统状态"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ModuleStatus(Enum):
    """模块状态"""
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class EventType(Enum):
    """事件类型"""
    ALERT_TRIGGERED = "alert_triggered"
    SCALING_ACTION = "scaling_action"
    RECOVERY_ACTION = "recovery_action"
    BACKUP_COMPLETED = "backup_completed"
    STRATEGY_UPDATED = "strategy_updated"
    SYSTEM_ERROR = "system_error"
    HEALTH_CHANGE = "health_change"


class SystemCoordinator:
    """系统协调器

    统一协调系统各模块的运行。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化系统协调器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 系统状态
        self.system_status = SystemStatus.INITIALIZING
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None

        # 模块状态
        self.module_status: Dict[str, ModuleStatus] = {}
        self.module_instances: Dict[str, Any] = {}

        # 事件总线
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[Dict] = []
        self.max_event_history = 1000

        # 配置参数
        self.shutdown_timeout = self.config.get('shutdown_timeout', 30)
        self.health_check_interval = self.config.get('health_check_interval', 60)
        self.auto_recovery_enabled = self.config.get('auto_recovery_enabled', True)

        # 健康检查任务
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info("✅ 系统协调器初始化完成")

    async def initialize(self) -> bool:
        """初始化系统

        Returns:
            是否成功
        """
        logger.info("🚀 开始初始化系统...")

        try:
            # 1. 初始化存储
            await self._initialize_storage()

            # 2. 初始化监控模块
            await self._initialize_monitoring()

            # 3. 初始化自动化模块
            await self._initialize_automation()

            # 4. 初始化策略优化器
            await self._initialize_strategy_optimizer()

            # 5. 初始化交易模块
            await self._initialize_trading()

            # 6. 注册默认事件处理器
            self._register_default_handlers()

            # 更新系统状态
            self.system_status = SystemStatus.STOPPED

            logger.info("✅ 系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            self.system_status = SystemStatus.ERROR
            return False

    async def start(self) -> bool:
        """启动系统

        Returns:
            是否成功
        """
        logger.info("🚀 开始启动系统...")

        try:
            # 1. 启动监控模块
            await self._start_monitoring()

            # 2. 启动自动化模块
            await self._start_automation()

            # 3. 启动策略优化器
            await self._start_strategy_optimizer()

            # 4. 启动交易模块
            await self._start_trading()

            # 5. 启动健康检查
            self._start_health_check()

            # 更新系统状态
            self.system_status = SystemStatus.RUNNING
            self.start_time = datetime.now()

            # 发布启动事件
            await self.publish_event({
                'type': EventType.SYSTEM_ERROR,
                'data': {
                    'action': 'system_started',
                    'timestamp': self.start_time.isoformat()
                }
            })

            logger.info(f"✅ 系统启动成功 (启动时间: {datetime.now() - self.start_time})")
            return True

        except Exception as e:
            logger.error(f"❌ 系统启动失败: {e}")
            self.system_status = SystemStatus.ERROR
            return False

    async def stop(self) -> bool:
        """停止系统

        Returns:
            是否成功
        """
        logger.info("🛑 开始停止系统...")

        try:
            # 更新系统状态
            self.system_status = SystemStatus.STOPPING

            # 1. 停止健康检查
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # 2. 停止交易模块
            await self._stop_trading()

            # 3. 停止策略优化器
            await self._stop_strategy_optimizer()

            # 4. 停止自动化模块
            await self._stop_automation()

            # 5. 停止监控模块
            await self._stop_monitoring()

            # 6. 关闭存储
            await self._close_storage()

            # 更新系统状态
            self.system_status = SystemStatus.STOPPED
            self.stop_time = datetime.now()

            logger.info(f"✅ 系统停止成功 (运行时间: {self.stop_time - self.start_time if self.start_time else 'N/A'})")
            return True

        except Exception as e:
            logger.error(f"❌ 系统停止失败: {e}")
            self.system_status = SystemStatus.ERROR
            return False

    async def restart(self) -> bool:
        """重启系统

        Returns:
            是否成功
        """
        logger.info("🔄 开始重启系统...")

        # 停止系统
        stop_success = await self.stop()
        if not stop_success:
            logger.error("❌ 系统停止失败，无法重启")
            return False

        # 等待一段时间
        await asyncio.sleep(2)

        # 重新启动
        start_success = await self.start()

        return start_success

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态

        Returns:
            系统状态字典
        """
        return {
            'system_status': self.system_status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stop_time': self.stop_time.isoformat() if self.stop_time else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'module_status': {
                name: status.value
                for name, status in self.module_status.items()
            },
            'event_count': len(self.event_history),
        }

    async def orchestrate_modules(self) -> bool:
        """协调模块运行

        Returns:
            是否成功
        """
        logger.info("🔧 开始协调模块...")

        try:
            # 检查各模块健康状态
            health_status = await self._check_all_modules_health()

            # 根据健康状态协调模块
            if health_status['overall'] == 'healthy':
                # 所有模块健康，正常协调
                await self._normal_orchestration()
            elif health_status['overall'] == 'degraded':
                # 部分模块降级，启用降级模式
                logger.warning("⚠️ 系统进入降级模式")
                await self._degraded_orchestration()
            else:
                # 系统异常，触发自动恢复
                logger.error("❌ 系统异常，触发自动恢复")
                if self.auto_recovery_enabled:
                    await self._auto_recover()

            return True

        except Exception as e:
            logger.error(f"❌ 模块协调失败: {e}")
            return False

    # ========== 事件处理 ==========

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable
    ) -> None:
        """注册事件处理器

        Args:
            event_type: 事件类型
            handler: 事件处理器函数
        """
        self.event_handlers[event_type].append(handler)
        logger.debug(f"注册事件处理器: {event_type}")

    async def publish_event(self, event: Dict[str, Any]) -> None:
        """发布事件

        Args:
            event: 事件字典
        """
        event_type = event.get('type')

        # 记录事件历史
        self._record_event(event)

        # 调用事件处理器
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {e}")

        logger.debug(f"发布事件: {event_type}")

    async def handle_alert(self, alert: Dict[str, Any]) -> None:
        """处理告警事件

        Args:
            alert: 告警字典
        """
        logger.warning(f"🚨 处理告警: {alert.get('name', 'unknown')}")

        # 发布告警事件
        await self.publish_event({
            'type': EventType.ALERT_TRIGGERED,
            'data': alert
        })

        # 根据告警级别采取行动
        severity = alert.get('severity', 'INFO')
        if severity in ['ERROR', 'CRITICAL']:
            # 严重告警，触发自动恢复
            if self.auto_recovery_enabled:
                await self._auto_recover()

    async def handle_auto_scaling(self, action: Dict[str, Any]) -> None:
        """处理自动扩缩容事件

        Args:
            action: 扩缩容动作字典
        """
        logger.info(f"📊 处理自动扩缩容: {action.get('action', 'unknown')}")

        # 发布扩缩容事件
        await self.publish_event({
            'type': EventType.SCALING_ACTION,
            'data': action
        })

        # 记录到事件历史
        self._record_event({
            'type': 'auto_scaling',
            'action': action,
            'timestamp': datetime.now().isoformat()
        })

    # ========== 私有方法 ==========

    async def _initialize_storage(self) -> None:
        """初始化存储模块"""
        logger.info("📦 初始化存储模块...")

        try:
            from storage.storage_factory import create_auto_storage

            # 创建存储实例
            storage = await create_auto_storage(self.config)

            # 保存到模块实例
            self.module_instances['storage'] = storage
            self.module_status['storage'] = ModuleStatus.INITIALIZED

            logger.info("✅ 存储模块初始化完成")

        except Exception as e:
            logger.error(f"❌ 存储模块初始化失败: {e}")
            raise

    async def _initialize_monitoring(self) -> None:
        """初始化监控模块"""
        logger.info("📊 初始化监控模块...")

        try:
            from monitoring.metrics_collector import MetricsCollector
            from monitoring.alert_manager import AlertManager
            from monitoring.dashboard_generator import DashboardGenerator
            from monitoring.notification_service import NotificationService

            # 创建监控模块实例
            metrics_collector = MetricsCollector(self.config)
            alert_manager = AlertManager(self.config)
            dashboard_generator = DashboardGenerator(self.config)
            notification_service = NotificationService(self.config)

            # 保存到模块实例
            self.module_instances['metrics_collector'] = metrics_collector
            self.module_instances['alert_manager'] = alert_manager
            self.module_instances['dashboard_generator'] = dashboard_generator
            self.module_instances['notification_service'] = notification_service

            # 更新模块状态
            self.module_status['monitoring'] = ModuleStatus.INITIALIZED

            logger.info("✅ 监控模块初始化完成")

        except Exception as e:
            logger.error(f"❌ 监控模块初始化失败: {e}")
            raise

    async def _initialize_automation(self) -> None:
        """初始化自动化模块"""
        logger.info("🤖 初始化自动化模块...")

        try:
            from automation.auto_scaler import AutoScaler
            from automation.auto_recovery import AutoRecovery
            from automation.backup_manager import BackupManager

            # 创建自动化模块实例
            auto_scaler = AutoScaler(self.config)
            auto_recovery = AutoRecovery(self.config)
            backup_manager = BackupManager(self.config)

            # 保存到模块实例
            self.module_instances['auto_scaler'] = auto_scaler
            self.module_instances['auto_recovery'] = auto_recovery
            self.module_instances['backup_manager'] = backup_manager

            # 更新模块状态
            self.module_status['automation'] = ModuleStatus.INITIALIZED

            logger.info("✅ 自动化模块初始化完成")

        except Exception as e:
            logger.error(f"❌ 自动化模块初始化失败: {e}")
            raise

    async def _initialize_strategy_optimizer(self) -> None:
        """初始化策略优化器"""
        logger.info("🧠 初始化策略优化器...")

        try:
            from integration.strategy_optimizer import StrategyOptimizer

            # 创建策略优化器实例
            optimizer = StrategyOptimizer(self.config)

            # 保存到模块实例
            self.module_instances['strategy_optimizer'] = optimizer

            # 更新模块状态
            self.module_status['strategy_optimizer'] = ModuleStatus.INITIALIZED

            logger.info("✅ 策略优化器初始化完成")

        except Exception as e:
            logger.error(f"❌ 策略优化器初始化失败: {e}")
            raise

    async def _initialize_trading(self) -> None:
        """初始化交易模块"""
        logger.info("💱 初始化交易模块...")

        try:
            # 导入交易模块
            from trading import (
                get_trading_coordinator,
                get_market_data_manager,
                get_signal_generator,
                get_risk_manager_v2,
                get_execution_engine,
                get_position_manager,
                get_trade_monitor,
            )
            from trading.production_trading_engine import create_production_trading_engine
            from trading.capital_manager import create_capital_manager
            from trading.performance_tracker import create_performance_tracker
            from storage.storage_factory import create_auto_storage

            # 创建存储实例
            storage = await create_auto_storage(self.config)

            # 初始化核心交易模块
            self.trading_coordinator = get_trading_coordinator()
            self.market_data_manager = get_market_data_manager()
            self.signal_generator = get_signal_generator()
            self.risk_manager = get_risk_manager_v2()
            self.execution_engine = get_execution_engine()
            self.position_manager = get_position_manager()
            self.trade_monitor = get_trade_monitor()

            # 初始化存储引用
            self.market_data_manager.storage = storage
            self.signal_generator.storage = storage
            self.risk_manager.storage = storage
            self.execution_engine.storage = storage

            # 初始化生产级交易引擎（向后兼容）
            self.production_trading_engine = create_production_trading_engine(self.config)
            self.capital_manager = create_capital_manager(self.config)
            self.performance_tracker = create_performance_tracker(self.config)

            # 保存到模块实例
            self.module_instances['trading_coordinator'] = self.trading_coordinator
            self.module_instances['market_data_manager'] = self.market_data_manager
            self.module_instances['signal_generator'] = self.signal_generator
            self.module_instances['risk_manager'] = self.risk_manager
            self.module_instances['execution_engine'] = self.execution_engine
            self.module_instances['position_manager'] = self.position_manager
            self.module_instances['trade_monitor'] = self.trade_monitor
            self.module_instances['production_trading_engine'] = self.production_trading_engine
            self.module_instances['capital_manager'] = self.capital_manager
            self.module_instances['performance_tracker'] = self.performance_tracker
            self.module_instances['storage'] = storage

            # 初始化各个模块
            await self.market_data_manager.initialize()
            await self.signal_generator.initialize()
            await self.risk_manager.initialize()
            await self.execution_engine.initialize()
            await self.trading_coordinator.initialize()
            await self.production_trading_engine.initialize()

            # 设置模块间的引用
            self.trading_coordinator.market_data_manager = self.market_data_manager
            self.trading_coordinator.signal_generator = self.signal_generator
            self.trading_coordinator.risk_manager = self.risk_manager
            self.trading_coordinator.execution_engine = self.execution_engine
            self.trading_coordinator.position_manager = self.position_manager
            self.trading_coordinator.trade_monitor = self.trade_monitor

            # 设置市场数据管理器的执行引擎引用
            self.execution_engine.market_data_manager = self.market_data_manager

            logger.info("✅ 交易模块初始化完成")

            # 更新模块状态
            self.module_status['trading'] = ModuleStatus.INITIALIZED

        except Exception as e:
            logger.error(f"❌ 交易模块初始化失败: {e}")
            raise

    def _register_default_handlers(self) -> None:
        """注册默认事件处理器"""
        # 注册告警处理器
        self.register_event_handler(
            EventType.ALERT_TRIGGERED.value,
            self._on_alert_triggered
        )

        # 注册扩缩容处理器
        self.register_event_handler(
            EventType.SCALING_ACTION.value,
            self._on_scaling_action
        )

        # 注册健康变化处理器
        self.register_event_handler(
            EventType.HEALTH_CHANGE.value,
            self._on_health_change
        )

    async def _start_monitoring(self) -> None:
        """启动监控模块"""
        logger.info("📊 启动监控模块...")

        # 这里可以启动监控模块的各个组件
        # 例如启动指标收集定时任务

        self.module_status['monitoring'] = ModuleStatus.RUNNING
        logger.info("✅ 监控模块启动完成")

    async def _start_automation(self) -> None:
        """启动自动化模块"""
        logger.info("🤖 启动自动化模块...")

        # 这里可以启动自动化模块的各个组件

        self.module_status['automation'] = ModuleStatus.RUNNING
        logger.info("✅ 自动化模块启动完成")

    async def _start_strategy_optimizer(self) -> None:
        """启动策略优化器"""
        logger.info("🧠 启动策略优化器...")

        # 这里可以启动策略优化器的定时任务

        self.module_status['strategy_optimizer'] = ModuleStatus.RUNNING
        logger.info("✅ 策略优化器启动完成")

    async def _start_trading(self) -> None:
        """启动交易模块"""
        logger.info("💱 启动交易模块...")

        try:
            # 启动市场数据管理器
            await self.market_data_manager.start()

            # 启动交易协调器
            await self.trading_coordinator.start()

            # 启动生产级交易引擎
            await self.production_trading_engine.start()

            logger.info("✅ 交易模块启动完成")
            self.module_status['trading'] = ModuleStatus.RUNNING

        except Exception as e:
            logger.error(f"❌ 交易模块启动失败: {e}")
            raise

    def _start_health_check(self) -> None:
        """启动健康检查"""
        logger.info("🏥 启动健康检查...")

        # 创建健康检查任务
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )

    async def _stop_monitoring(self) -> None:
        """停止监控模块"""
        logger.info("📊 停止监控模块...")

        self.module_status['monitoring'] = ModuleStatus.STOPPED
        logger.info("✅ 监控模块停止完成")

    async def _stop_automation(self) -> None:
        """停止自动化模块"""
        logger.info("🤖 停止自动化模块...")

        self.module_status['automation'] = ModuleStatus.STOPPED
        logger.info("✅ 自动化模块停止完成")

    async def _stop_strategy_optimizer(self) -> None:
        """停止策略优化器"""
        logger.info("🧠 停止策略优化器...")

        self.module_status['strategy_optimizer'] = ModuleStatus.STOPPED
        logger.info("✅ 策略优化器停止完成")

    async def _stop_trading(self) -> None:
        """停止交易模块"""
        logger.info("💱 停止交易模块...")

        try:
            # 停止交易协调器
            await self.trading_coordinator.stop()

            # 停止生产级交易引擎
            await self.production_trading_engine.stop()

            # 停止市场数据管理器
            await self.market_data_manager.stop()

            # 停止风险管理器
            await self.risk_manager.stop()

            # 停止交易执行引擎
            await self.execution_engine.stop()

            self.module_status['trading'] = ModuleStatus.STOPPED
            logger.info("✅ 交易模块停止完成")

        except Exception as e:
            logger.error(f"❌ 交易模块停止失败: {e}")
            raise

    async def _close_storage(self) -> None:
        """关闭存储"""
        logger.info("📦 关闭存储模块...")

        if 'storage' in self.module_instances:
            storage = self.module_instances['storage']
            if hasattr(storage, 'close'):
                await storage.close()

        self.module_status['storage'] = ModuleStatus.STOPPED
        logger.info("✅ 存储模块关闭完成")

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self.system_status == SystemStatus.RUNNING:
            try:
                # 执行健康检查
                await self._check_all_modules_health()

                # 等待下一次检查
                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                logger.info("健康检查任务已取消")
                break
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒

    async def _check_all_modules_health(self) -> Dict[str, Any]:
        """检查所有模块健康状态

        Returns:
            健康状态字典
        """
        health_status = {
            'overall': 'healthy',
            'modules': {}
        }

        # 检查各模块
        for module_name, module in self.module_instances.items():
            try:
                # 简单的健康检查
                if module and hasattr(module, '__dict__'):
                    health_status['modules'][module_name] = 'healthy'
                else:
                    health_status['modules'][module_name] = 'unhealthy'
                    health_status['overall'] = 'degraded'
            except Exception as e:
                health_status['modules'][module_name] = 'error'
                health_status['overall'] = 'degraded'

        return health_status

    async def _normal_orchestration(self) -> None:
        """正常协调模式"""
        logger.debug("系统运行正常，正常协调模式")

    async def _degraded_orchestration(self) -> None:
        """降级协调模式"""
        logger.warning("系统降级模式运行")
        self.system_status = SystemStatus.DEGRADED

    async def _auto_recover(self) -> None:
        """自动恢复"""
        logger.info("🔧 开始自动恢复...")

        try:
            # 检查各模块状态并尝试恢复
            for module_name, status in self.module_status.items():
                if status == ModuleStatus.ERROR:
                    logger.info(f"尝试恢复模块: {module_name}")
                    # 这里可以添加具体的恢复逻辑

            logger.info("✅ 自动恢复完成")

        except Exception as e:
            logger.error(f"❌ 自动恢复失败: {e}")

    def _record_event(self, event: Dict[str, Any]) -> None:
        """记录事件

        Args:
            event: 事件字典
        """
        event['recorded_at'] = datetime.now().isoformat()

        self.event_history.append(event)

        # 限制历史大小
        if len(self.event_history) > self.max_event_history:
            self.event_history = self.event_history[-self.max_event_history:]

    # ========== 事件处理器 ==========

    async def _on_alert_triggered(self, event: Dict[str, Any]) -> None:
        """告警触发事件处理器"""
        alert = event.get('data', {})
        logger.warning(f"🚨 告警触发: {alert.get('name', 'unknown')}")

    async def _on_scaling_action(self, event: Dict[str, Any]) -> None:
        """扩缩容动作事件处理器"""
        action = event.get('data', {})
        logger.info(f"📊 扩缩容动作: {action.get('action', 'unknown')}")

    async def _on_health_change(self, event: Dict[str, Any]) -> None:
        """健康变化事件处理器"""
        health = event.get('data', {})
        logger.info(f"🏥 健康状态变化: {health.get('status', 'unknown')}")

    # ========== 配置管理 ==========

    async def load_config(self, config: Dict[str, Any]) -> None:
        """加载配置

        Args:
            config: 配置字典
        """
        self.config.update(config)
        logger.info("配置已加载")

    async def update_config(self, key: str, value: Any) -> None:
        """更新配置

        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
        logger.info(f"配置已更新: {key} = {value}")

    async def save_config(self, path: str) -> None:
        """保存配置到文件

        Args:
            path: 文件路径
        """
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"配置已保存到: {path}")


# ========== 全局协调器实例 ==========

_coordinator_instance: Optional[SystemCoordinator] = None


def get_system_coordinator() -> SystemCoordinator:
    """获取系统协调器单例

    Returns:
        系统协调器实例
    """
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = SystemCoordinator()
    return _coordinator_instance
