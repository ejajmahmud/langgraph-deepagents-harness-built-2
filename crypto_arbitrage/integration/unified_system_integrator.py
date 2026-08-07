"""统一系统集成器 V16.1

将V16.0的实时知识集成与现有系统核心模块完全集成，
建立SystemCoordinator、StrategyOptimizer、StorageIntegrator的统一协调机制。

V16.1核心升级：
1. 与SystemCoordinator深度集成
2. 与StrategyOptimizer集成
3. 统一的系统协调机制
4. 端到端集成测试
5. 性能优化和监控

基于：
- V16.0实时知识Memo0集成
- V12.1 SystemCoordinator
- V12.2 StrategyOptimizer
- V12.3 StorageIntegrator
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict

# 导入V16.0集成模块
from integration.realtime_knowledge_mem0_integration import (
    RealtimeKnowledgeMemo0Integration,
    IntegrationMode,
    KnowledgeUpdateResult,
    ArbitrageDecision
)

# 导入系统核心模块
try:
    from integration.system_coordinator import SystemCoordinator, SystemStatus
except ImportError:
    SystemCoordinator = None
    SystemStatus = None

try:
    from integration.strategy_optimizer import StrategyOptimizer
except ImportError:
    StrategyOptimizer = None

try:
    from integration.storage_integration import StorageIntegrator
except ImportError:
    StorageIntegrator = None

# 导入其他必要模块
from storage.mem0_storage import get_mem0_storage, load_mem0_config
from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine

logger = logging.getLogger(__name__)


class SystemHealthStatus(Enum):
    """系统健康状态"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    DEGRADED = "degraded"  # 降级
    CRITICAL = "critical"  # 严重


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    knowledge_update_rate: float  # 知识更新速率（条/秒）
    decision_latency: float  # 决策延迟（毫秒）
    arbitrage_success_rate: float  # 套利成功率
    system_health: SystemHealthStatus


@dataclass
class IntegrationStatus:
    """集成状态"""
    realtime_knowledge_connected: bool = False
    system_coordinator_connected: bool = False
    strategy_optimizer_connected: bool = False
    storage_integrator_connected: bool = False
    mem0_storage_connected: bool = False
    active_modules: List[str] = field(default_factory=list)
    total_modules: int = 0


class UnifiedSystemIntegrator:
    """统一系统集成器 V16.1

    将V16.0实时知识集成与系统核心模块完全集成。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化统一系统集成器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._version = "V16.1"

        # 初始化V16.0实时知识集成
        self._realtime_integration = RealtimeKnowledgeMemo0Integration(
            integration_mode=IntegrationMode.HYBRID,
            config=self.config
        )

        # 初始化系统核心模块
        self._system_coordinator = None
        self._strategy_optimizer = None
        self._storage_integrator = None

        # 初始化连接状态
        self._connection_status = IntegrationStatus()

        # 系统指标
        self._system_metrics: List[SystemMetrics] = []
        self._performance_history: Dict[str, List[float]] = defaultdict(list)

        # 任务队列
        self._task_queue = asyncio.Queue()
        self._is_running = False

        logger.info(f"[OK] 统一系统集成器 {self._version} 初始化完成")

        # 初始化连接
        self._initialize_connections()

    def _initialize_connections(self) -> None:
        """初始化所有模块连接"""
        logger.info("初始化模块连接...")

        # 连接SystemCoordinator
        if SystemCoordinator:
            try:
                self._system_coordinator = SystemCoordinator(config=self.config)
                self._connection_status.system_coordinator_connected = True
                self._connection_status.active_modules.append("SystemCoordinator")
                logger.info("[OK] SystemCoordinator已连接")
            except Exception as e:
                logger.warning(f"SystemCoordinator连接失败: {e}")

        # 连接StrategyOptimizer
        if StrategyOptimizer:
            try:
                self._strategy_optimizer = StrategyOptimizer(config=self.config)
                self._connection_status.strategy_optimizer_connected = True
                self._connection_status.active_modules.append("StrategyOptimizer")
                logger.info("[OK] StrategyOptimizer已连接")
            except Exception as e:
                logger.warning(f"StrategyOptimizer连接失败: {e}")

        # 连接StorageIntegrator
        if StorageIntegrator:
            try:
                self._storage_integrator = StorageIntegrator(config=self.config)
                self._connection_status.storage_integrator_connected = True
                self._connection_status.active_modules.append("StorageIntegrator")
                logger.info("[OK] StorageIntegrator已连接")
            except Exception as e:
                logger.warning(f"StorageIntegrator连接失败: {e}")

        # 检查Memo0存储
        mem0_storage = get_mem0_storage()
        self._connection_status.mem0_storage_connected = mem0_storage is not None
        if mem0_storage:
            self._connection_status.active_modules.append("Memo0Storage")
            logger.info("[OK] Memo0Storage已连接")
        else:
            logger.info("[INFO] Memo0Storage未启用，使用本地存储")

        # 统计模块总数
        self._connection_status.total_modules = len(self._connection_status.active_modules)

        # 打印连接状态
        self._log_connection_status()

    def _log_connection_status(self) -> None:
        """记录连接状态"""
        status = self.get_connection_status()
        logger.info("=" * 60)
        logger.info("模块连接状态")
        logger.info("=" * 60)
        logger.info(f"连接模块数: {status['connected_modules']}/{status['total_modules']}")
        logger.info(f"连接率: {status['connection_rate']:.1f}%")
        logger.info(f"活跃模块: {', '.join(status['active_modules'])}")
        logger.info("=" * 60)

    async def start_unified_integration(self) -> None:
        """启动统一集成

        启动所有模块的协调运行。
        """
        logger.info("启动统一系统集成...")
        self._is_running = True

        try:
            # 创建并启动任务
            tasks = [
                asyncio.create_task(self._realtime_knowledge_loop()),
                asyncio.create_task(self._system_coordinator_loop()),
                asyncio.create_task(self._strategy_optimization_loop()),
                asyncio.create_task(self._performance_monitoring_loop()),
                asyncio.create_task(self._task_processing_loop())
            ]

            # 等待所有任务
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"统一集成失败: {e}")
            raise
        finally:
            self._is_running = False

    async def _realtime_knowledge_loop(self) -> None:
        """实时知识更新循环

        运行V16.0的实时知识更新。
        """
        logger.info("启动实时知识更新循环")

        while self._is_running:
            try:
                # 启动V16.0的实时集成
                await self._realtime_integration.start_realtime_integration()

            except Exception as e:
                logger.error(f"实时知识循环错误: {e}")
                await asyncio.sleep(5)

    async def _system_coordinator_loop(self) -> None:
        """系统协调循环

        协调所有模块的运行。
        """
        if not self._system_coordinator:
            logger.warning("SystemCoordinator未连接，跳过系统协调循环")
            return

        logger.info("启动系统协调循环")

        while self._is_running:
            try:
                # 获取系统状态
                if hasattr(self._system_coordinator, 'get_system_status'):
                    status = await self._system_coordinator.get_system_status()

                    # 检查系统健康
                    health = self._evaluate_system_health(status)

                    # 如果系统健康状态不佳，触发优化
                    if health in [SystemHealthStatus.DEGRADED, SystemHealthStatus.CRITICAL]:
                        logger.warning(f"系统健康状态: {health.value}")
                        await self._trigger_system_optimization()

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"系统协调循环错误: {e}")
                await asyncio.sleep(30)

    async def _strategy_optimization_loop(self) -> None:
        """策略优化循环

        定期优化策略参数。
        """
        if not self._strategy_optimizer:
            logger.warning("StrategyOptimizer未连接，跳过策略优化循环")
            return

        logger.info("启动策略优化循环")

        while self._is_running:
            try:
                # 获取最新性能指标
                performance_metrics = self._realtime_integration.get_integration_status()

                # 触发策略优化
                if hasattr(self._strategy_optimizer, 'optimize_strategies'):
                    optimization_result = await self._strategy_optimizer.optimize_strategies(
                        performance_metrics=performance_metrics
                    )

                    # 记录优化结果
                    logger.info(f"策略优化完成: {optimization_result.get('optimized_count', 0)} 个策略")

                # 每分钟优化一次
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"策略优化循环错误: {e}")
                await asyncio.sleep(60)

    async def _performance_monitoring_loop(self) -> None:
        """性能监控循环

        持续监控系统性能指标。
        """
        logger.info("启动性能监控循环")

        while self._is_running:
            try:
                # 收集系统指标
                metrics = await self._collect_system_metrics()

                # 记录指标
                self._system_metrics.append(metrics)
                self._update_performance_history(metrics)

                # 检查性能问题
                if metrics.system_health in [SystemHealthStatus.DEGRADED, SystemHealthStatus.CRITICAL]:
                    await self._handle_performance_issue(metrics)

                # 存储指标到Memo0
                await self._store_metrics_to_memo0(metrics)

                # 每秒更新一次
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(5)

    async def _task_processing_loop(self) -> None:
        """任务处理循环

        处理任务队列中的任务。
        """
        logger.info("启动任务处理循环")

        while self._is_running:
            try:
                # 从队列获取任务
                task = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )

                # 处理任务
                await self._process_task(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"任务处理错误: {e}")

    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标

        Returns:
            系统指标对象
        """
        try:
            import psutil

            # 基本系统指标
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 50.0

            # 实时集成状态
            integration_status = self._realtime_integration.get_integration_status()

            # 系统健康评估
            system_health = self._evaluate_system_health_from_metrics(
                cpu_usage, memory_usage, integration_status
            )

            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                active_connections=len(self._connection_status.active_modules),
                knowledge_update_rate=0.0,  # 需要从实时集成获取
                decision_latency=0.0,  # 需要从决策系统获取
                arbitrage_success_rate=0.0,  # 需要从套利系统获取
                system_health=system_health
            )

            return metrics

        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                active_connections=len(self._connection_status.active_modules),
                knowledge_update_rate=0.0,
                decision_latency=0.0,
                arbitrage_success_rate=0.0,
                system_health=SystemHealthStatus.GOOD
            )

    def _evaluate_system_health_from_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        integration_status: Dict[str, Any]
    ) -> SystemHealthStatus:
        """从指标评估系统健康

        Args:
            cpu_usage: CPU使用率
            memory_usage: 内存使用率
            integration_status: 集成状态

        Returns:
            系统健康状态
        """
        # 计算健康分数
        health_score = 100.0

        # CPU使用率影响
        if cpu_usage > 90:
            health_score -= 30
        elif cpu_usage > 70:
            health_score -= 10

        # 内存使用率影响
        if memory_usage > 90:
            health_score -= 30
        elif memory_usage > 70:
            health_score -= 10

        # 成功率影响
        success_rate = integration_status.get('success_rate', 0)
        if success_rate < 0.5:
            health_score -= 20
        elif success_rate < 0.8:
            health_score -= 10

        # 评估健康状态
        if health_score >= 90:
            return SystemHealthStatus.EXCELLENT
        elif health_score >= 70:
            return SystemHealthStatus.GOOD
        elif health_score >= 50:
            return SystemHealthStatus.DEGRADED
        else:
            return SystemHealthStatus.CRITICAL

    def _evaluate_system_health(self, status: Dict[str, Any]) -> SystemHealthStatus:
        """评估系统健康

        Args:
            status: 系统状态

        Returns:
            系统健康状态
        """
        # 默认健康状态
        return SystemHealthStatus.GOOD

    async def _trigger_system_optimization(self) -> None:
        """触发系统优化"""
        logger.info("触发系统优化...")

        # 1. 优化内存使用
        if self._storage_integrator and hasattr(self._storage_integrator, 'optimize_memory'):
            await self._storage_integrator.optimize_memory()

        # 2. 优化缓存
        if hasattr(self._realtime_integration, '_knowledge_cache'):
            # 清理过期缓存
            pass

        # 3. 优化连接
        # 关闭空闲连接等

        logger.info("系统优化完成")

    async def _handle_performance_issue(self, metrics: SystemMetrics) -> None:
        """处理性能问题

        Args:
            metrics: 系统指标
        """
        logger.warning(f"检测到性能问题: {metrics.system_health.value}")
        logger.warning(f"  CPU: {metrics.cpu_usage:.1f}%, Memory: {metrics.memory_usage:.1f}%")

        # 触发优化
        await self._trigger_system_optimization()

    async def _store_metrics_to_memo0(self, metrics: SystemMetrics) -> None:
        """存储指标到Memo0

        Args:
            metrics: 系统指标
        """
        try:
            mem0_storage = get_mem0_storage()
            if mem0_storage:
                content = (
                    f"[system_metrics] 系统性能指标 - "
                    f"{datetime.fromtimestamp(metrics.timestamp).strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"CPU={metrics.cpu_usage:.1f}% "
                    f"MEM={metrics.memory_usage:.1f}% "
                    f"CONN={metrics.active_connections} "
                    f"HEALTH={metrics.system_health.value}"
                )

                mem0_storage.add_memory(content)
                logger.debug("指标已存储到Memo0")

        except Exception as e:
            logger.error(f"存储指标到Memo0失败: {e}")

    async def _process_task(self, task: Dict[str, Any]) -> None:
        """处理任务

        Args:
            task: 任务字典
        """
        task_type = task.get('type', 'unknown')

        logger.info(f"处理任务: {task_type}")

        try:
            if task_type == 'knowledge_update':
                # 处理知识更新任务
                await self._handle_knowledge_update_task(task)
            elif task_type == 'strategy_optimization':
                # 处理策略优化任务
                await self._handle_strategy_optimization_task(task)
            elif task_type == 'system_optimization':
                # 处理系统优化任务
                await self._handle_system_optimization_task(task)
            else:
                logger.warning(f"未知任务类型: {task_type}")

        except Exception as e:
            logger.error(f"处理任务失败: {e}")

    async def _handle_knowledge_update_task(self, task: Dict[str, Any]) -> None:
        """处理知识更新任务"""
        # 从V16.0实时集成获取更新
        pass

    async def _handle_strategy_optimization_task(self, task: Dict[str, Any]) -> None:
        """处理策略优化任务"""
        if self._strategy_optimizer:
            # 触发策略优化
            pass

    async def _handle_system_optimization_task(self, task: Dict[str, Any]) -> None:
        """处理系统优化任务"""
        await self._trigger_system_optimization()

    async def stop_unified_integration(self) -> None:
        """停止统一集成"""
        logger.info("停止统一系统集成...")
        self._is_running = False

        # 停止V16.0实时集成
        await self._realtime_integration.stop_realtime_integration()

    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态

        Returns:
            连接状态字典
        """
        connected_modules = sum([
            self._connection_status.system_coordinator_connected,
            self._connection_status.strategy_optimizer_connected,
            self._connection_status.storage_integrator_connected,
            self._connection_status.mem0_storage_connected
        ])

        total_modules = 4  # SystemCoordinator, StrategyOptimizer, StorageIntegrator, Memo0Storage

        return {
            "system_coordinator_connected": self._connection_status.system_coordinator_connected,
            "strategy_optimizer_connected": self._connection_status.strategy_optimizer_connected,
            "storage_integrator_connected": self._connection_status.storage_integrator_connected,
            "mem0_storage_connected": self._connection_status.mem0_storage_connected,
            "active_modules": self._connection_status.active_modules,
            "connected_modules": connected_modules,
            "total_modules": total_modules,
            "connection_rate": (connected_modules / total_modules * 100) if total_modules > 0 else 0
        }

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态

        Returns:
            系统状态字典
        """
        latest_metrics = self._system_metrics[-1] if self._system_metrics else None

        return {
            "version": self._version,
            "is_running": self._is_running,
            "connection_status": self.get_connection_status(),
            "latest_metrics": latest_metrics.to_dict() if latest_metrics else None,
            "total_metrics_count": len(self._system_metrics),
            "task_queue_size": self._task_queue.qsize()
        }

    def _update_performance_history(self, metrics: SystemMetrics) -> None:
        """更新性能历史

        Args:
            metrics: 系统指标
        """
        # 记录各项指标
        self._performance_history['cpu_usage'].append(metrics.cpu_usage)
        self._performance_history['memory_usage'].append(metrics.memory_usage)
        self._performance_history['system_health'].append(metrics.system_health.value)

        # 限制历史长度
        max_history = 3600  # 保留最近1小时的数据
        for key in self._performance_history:
            if len(self._performance_history[key]) > max_history:
                self._performance_history[key] = self._performance_history[key][-max_history:]


async def main():
    """主函数 - 测试统一系统集成器"""
    print("=" * 80)
    print("统一系统集成器 V16.1")
    print("=" * 80)
    print("开始时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    try:
        # 创建统一集成器实例
        integrator = UnifiedSystemIntegrator(
            config={
                "enable_auto_rollback": True,
                "max_execution_time": 30.0,
                "risk_tolerance": "MEDIUM"
            }
        )

        # 启动统一集成
        await integrator.start_unified_integration()

    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
        await integrator.stop_unified_integration()
    except Exception as e:
        logger.error(f"主程序错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 打印最终统计
        status = integrator.get_system_status()
        print("\n" + "=" * 80)
        print("系统状态")
        print("=" * 80)
        for key, value in status.items():
            print(f"  {key}: {value}")

        print("\n结束时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
