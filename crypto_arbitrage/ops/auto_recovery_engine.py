"""自动恢复引擎 V3.7 - 智能故障检测和恢复

提供自动化的故障检测和恢复能力，最小化系统停机时间。
核心功能：
1. 故障自动检测 - 实时检测系统异常
2. 优先级恢复策略 - 按优先级执行恢复
3. 多级恢复方案 - 自动升级恢复策略
4. 恢复追踪 - 详细记录恢复过程
5. 学习和优化 - 从恢复历史中学习
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .system_health_monitor import HealthStatus

logger = logging.getLogger(__name__)


class RecoveryActionType(Enum):
    """恢复操作类型"""
    RESTART_COMPONENT = "RESTART_COMPONENT"  # 重启组件
    CLEAR_CACHE = "CLEAR_CACHE"  # 清除缓存
    RESET_CONNECTION = "RESET_CONNECTION"  # 重置连接
    ROLLBACK_CONFIG = "ROLLBACK_CONFIG"  # 回滚配置
    SCALE_RESOURCES = "SCALE_RESOURCES"  # 扩展资源
    EMERGENCY_STOP = "EMERGENCY_STOP"  # 紧急停止
    CUSTOM_ACTION = "CUSTOM_ACTION"  # 自定义操作


class RecoveryPriority(Enum):
    """恢复优先级"""
    CRITICAL = "CRITICAL"  # 关键 - 立即执行
    HIGH = "HIGH"  # 高 - 尽快执行
    MEDIUM = "MEDIUM"  # 中 - 正常执行
    LOW = "LOW"  # 低 - 延后执行


class RecoveryStatus(Enum):
    """恢复状态"""
    PENDING = "PENDING"  # 等待执行
    IN_PROGRESS = "IN_PROGRESS"  # 执行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败
    CANCELLED = "CANCELLED"  # 已取消


@dataclass
class RecoveryAction:
    """恢复操作"""
    action_id: str
    action_type: RecoveryActionType
    priority: RecoveryPriority
    target: str  # 目标组件/服务
    description: str
    status: RecoveryStatus = RecoveryStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RecoveryPlan:
    """恢复计划"""
    plan_id: str
    issue_description: str
    severity: HealthStatus
    priority: RecoveryPriority
    actions: List[RecoveryAction]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED


@dataclass
class RecoveryReport:
    """恢复报告"""
    plan_id: str
    success: bool
    total_actions: int
    successful_actions: int
    failed_actions: int
    duration_seconds: float
    started_at: datetime
    completed_at: datetime
    details: Dict[str, Any]


class RecoveryActionExecutor:
    """恢复操作执行器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化执行器

        Args:
            config: 配置字典
        """
        self.config = config
        self.component_registry: Dict[str, Any] = {}

        # 执行统计
        self.execution_stats = defaultdict(lambda: {
            'total': 0,
            'success': 0,
            'failed': 0,
            'avg_duration': 0.0
        })

    def register_component(self, name: str, component: Any) -> None:
        """注册组件

        Args:
            name: 组件名称
            component: 组件实例
        """
        self.component_registry[name] = component
        logger.info(f"注册恢复组件: {name}")

    async def execute_action(self, action: RecoveryAction) -> Dict[str, Any]:
        """执行恢复操作

        Args:
            action: 恢复操作

        Returns:
            执行结果
        """
        action.status = RecoveryStatus.IN_PROGRESS
        action.started_at = datetime.now()

        logger.info(f"执行恢复操作: {action.action_type.value} - {action.target}")

        try:
            # 根据操作类型执行
            if action.action_type == RecoveryActionType.RESTART_COMPONENT:
                result = await self._restart_component(action.target)
            elif action.action_type == RecoveryActionType.CLEAR_CACHE:
                result = await self._clear_cache(action.target)
            elif action.action_type == RecoveryActionType.RESET_CONNECTION:
                result = await self._reset_connection(action.target)
            elif action.action_type == RecoveryActionType.ROLLBACK_CONFIG:
                result = await self._rollback_config(action.target)
            elif action.action_type == RecoveryActionType.SCALE_RESOURCES:
                result = await self._scale_resources(action.target)
            elif action.action_type == RecoveryActionType.EMERGENCY_STOP:
                result = await self._emergency_stop(action.target)
            else:
                result = {
                    'success': False,
                    'message': f"未知操作类型: {action.action_type}"
                }

            # 更新状态
            if result['success']:
                action.status = RecoveryStatus.COMPLETED
            else:
                action.status = RecoveryStatus.FAILED
                action.error_message = result.get('message', '未知错误')

            action.result = result
            action.completed_at = datetime.now()

            # 更新统计
            self._update_stats(action.action_type, action.status, action.completed_at - action.started_at)

            logger.info(f"恢复操作完成: {action.action_type.value} - 结果: {action.status.value}")

            return result

        except Exception as e:
            action.status = RecoveryStatus.FAILED
            action.error_message = str(e)
            action.completed_at = datetime.now()

            logger.error(f"恢复操作失败: {action.action_type.value} - {e}")

            return {
                'success': False,
                'message': f"执行异常: {str(e)}",
                'exception': str(e)
            }

    async def _restart_component(self, target: str) -> Dict[str, Any]:
        """重启组件

        Args:
            target: 目标组件

        Returns:
            执行结果
        """
        component = self.component_registry.get(target)

        if not component:
            return {
                'success': False,
                'message': f"组件 {target} 未注册"
            }

        try:
            # 尝试重启组件
            if hasattr(component, 'restart'):
                await component.restart()
            elif hasattr(component, 'stop') and hasattr(component, 'start'):
                await component.stop()
                await asyncio.sleep(2)  # 等待停止
                await component.start()
            else:
                return {
                    'success': False,
                    'message': f"组件 {target} 不支持重启"
                }

            return {
                'success': True,
                'message': f"组件 {target} 重启成功"
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"组件 {target} 重启失败: {str(e)}"
            }

    async def _clear_cache(self, target: str) -> Dict[str, Any]:
        """清除缓存

        Args:
            target: 目标缓存

        Returns:
            执行结果
        """
        component = self.component_registry.get(target)

        if not component:
            return {
                'success': False,
                'message': f"缓存 {target} 未注册"
            }

        try:
            if hasattr(component, 'clear'):
                component.clear()
            elif hasattr(component, 'cache_clear'):
                component.cache_clear()
            else:
                return {
                    'success': False,
                    'message': f"缓存 {target} 不支持清除"
                }

            return {
                'success': True,
                'message': f"缓存 {target} 清除成功"
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"缓存 {target} 清除失败: {str(e)}"
            }

    async def _reset_connection(self, target: str) -> Dict[str, Any]:
        """重置连接

        Args:
            target: 目标连接

        Returns:
            执行结果
        """
        component = self.component_registry.get(target)

        if not component:
            return {
                'success': False,
                'message': f"连接 {target} 未注册"
            }

        try:
            if hasattr(component, 'reconnect'):
                await component.reconnect()
            elif hasattr(component, 'close') and hasattr(component, 'connect'):
                component.close()
                await asyncio.sleep(1)
                await component.connect()
            else:
                return {
                    'success': False,
                    'message': f"连接 {target} 不支持重置"
                }

            return {
                'success': True,
                'message': f"连接 {target} 重置成功"
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"连接 {target} 重置失败: {str(e)}"
            }

    async def _rollback_config(self, target: str) -> Dict[str, Any]:
        """回滚配置

        Args:
            target: 目标配置

        Returns:
            执行结果
        """
        # 简化实现 - 实际需要配置管理器
        return {
            'success': False,
            'message': "配置回滚功能待实现"
        }

    async def _scale_resources(self, target: str) -> Dict[str, Any]:
        """扩展资源

        Args:
            target: 目标资源

        Returns:
            执行结果
        """
        # 简化实现 - 实际需要资源管理器
        return {
            'success': False,
            'message': "资源扩展功能待实现"
        }

    async def _emergency_stop(self, target: str) -> Dict[str, Any]:
        """紧急停止

        Args:
            target: 目标

        Returns:
            执行结果
        """
        component = self.component_registry.get(target)

        if not component:
            return {
                'success': False,
                'message': f"组件 {target} 未注册"
            }

        try:
            if hasattr(component, 'emergency_stop'):
                await component.emergency_stop()
            elif hasattr(component, 'stop'):
                await component.stop()
            else:
                return {
                    'success': False,
                    'message': f"组件 {target} 不支持停止"
                }

            return {
                'success': True,
                'message': f"组件 {target} 紧急停止成功"
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"组件 {target} 紧急停止失败: {str(e)}"
            }

    def _update_stats(
        self,
        action_type: RecoveryActionType,
        status: RecoveryStatus,
        duration: timedelta
    ) -> None:
        """更新执行统计

        Args:
            action_type: 操作类型
            status: 操作状态
            duration: 执行时长
        """
        stats = self.execution_stats[action_type]
        stats['total'] += 1

        if status == RecoveryStatus.COMPLETED:
            stats['success'] += 1
        else:
            stats['failed'] += 1

        # 更新平均执行时间
        duration_seconds = duration.total_seconds()
        avg_duration = stats['avg_duration']
        stats['avg_duration'] = (avg_duration * (stats['total'] - 1) + duration_seconds) / stats['total']


class AutoRecoveryEngine:
    """自动恢复引擎 V3.7

    提供智能化的故障检测和恢复能力。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        executor: Optional[RecoveryActionExecutor] = None
    ):
        """初始化自动恢复引擎

        Args:
            config: 配置字典
            executor: 执行器（可选）
        """
        self.config = config
        self.executor = executor or RecoveryActionExecutor(config)

        # 恢复计划队列
        self.plan_queue: deque = deque(maxlen=100)
        self.active_plan: Optional[RecoveryPlan] = None

        # 恢复历史
        self.history: deque = deque(maxlen=1000)

        # 运行状态
        self.is_running = False

        # 恢复策略
        self.recovery_strategies: Dict[str, List[RecoveryAction]] = {}

        # 统计信息
        self.stats = {
            'total_plans': 0,
            'successful_plans': 0,
            'failed_plans': 0,
            'total_actions': 0,
            'successful_actions': 0,
            'avg_recovery_time': 0.0
        }

        logger.info("自动恢复引擎初始化完成")

    def register_recovery_strategy(
        self,
        issue_pattern: str,
        actions: List[Dict[str, Any]]
    ) -> None:
        """注册恢复策略

        Args:
            issue_pattern: 问题模式
            actions: 操作列表
        """
        recovery_actions = []
        for action_config in actions:
            action = RecoveryAction(
                action_id=f"{issue_pattern}_{action_config['action_type']}",
                action_type=RecoveryActionType(action_config['action_type']),
                priority=RecoveryPriority(action_config['priority']),
                target=action_config['target'],
                description=action_config['description']
            )
            recovery_actions.append(action)

        self.recovery_strategies[issue_pattern] = recovery_actions
        logger.info(f"注册恢复策略: {issue_pattern} - {len(recovery_actions)} 个操作")

    def create_recovery_plan(
        self,
        issue_description: str,
        severity: HealthStatus,
        checks: List[Any]
    ) -> RecoveryPlan:
        """创建恢复计划

        Args:
            issue_description: 问题描述
            severity: 严重程度
            checks: 检查结果

        Returns:
            恢复计划
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 确定优先级
        if severity == HealthStatus.CRITICAL:
            priority = RecoveryPriority.CRITICAL
        elif severity == HealthStatus.UNHEALTHY:
            priority = RecoveryPriority.HIGH
        else:
            priority = RecoveryPriority.MEDIUM

        # 根据问题描述选择策略
        actions = self._select_recovery_actions(issue_description, severity, checks)

        plan = RecoveryPlan(
            plan_id=plan_id,
            issue_description=issue_description,
            severity=severity,
            priority=priority,
            actions=actions
        )

        self.plan_queue.append(plan)
        logger.info(f"创建恢复计划: {plan_id} - {len(actions)} 个操作")

        return plan

    def _select_recovery_actions(
        self,
        issue_description: str,
        severity: HealthStatus,
        checks: List[Any]
    ) -> List[RecoveryAction]:
        """选择恢复操作

        Args:
            issue_description: 问题描述
            severity: 严重程度
            checks: 检查结果

        Returns:
            操作列表
        """
        actions = []

        # 简化的策略选择逻辑
        # 在实际实现中，可以使用更复杂的匹配规则

        issue_lower = issue_description.lower()

        # 数据库相关问题
        if 'database' in issue_lower or 'db' in issue_lower:
            actions.append(RecoveryAction(
                action_id=f"reset_db_connection_{datetime.now().timestamp()}",
                action_type=RecoveryActionType.RESET_CONNECTION,
                priority=RecoveryPriority.HIGH,
                target="database",
                description="重置数据库连接"
            ))

        # 性能相关问题
        elif 'performance' in issue_lower or 'slow' in issue_lower:
            actions.append(RecoveryAction(
                action_id=f"clear_cache_{datetime.now().timestamp()}",
                action_type=RecoveryActionType.CLEAR_CACHE,
                priority=RecoveryPriority.MEDIUM,
                target="performance_monitor",
                description="清除性能缓存"
            ))

        # 组件相关问题
        elif 'component' in issue_lower:
            for check in checks:
                if hasattr(check, 'check_name'):
                    actions.append(RecoveryAction(
                        action_id=f"restart_{check.check_name}_{datetime.now().timestamp()}",
                        action_type=RecoveryActionType.RESTART_COMPONENT,
                        priority=RecoveryPriority.HIGH,
                        target=check.check_name,
                        description=f"重启组件 {check.check_name}"
                    ))

        # 严重问题 - 添加紧急停止
        if severity == HealthStatus.CRITICAL:
            actions.insert(0, RecoveryAction(
                action_id=f"emergency_stop_{datetime.now().timestamp()}",
                action_type=RecoveryActionType.EMERGENCY_STOP,
                priority=RecoveryPriority.CRITICAL,
                target="trading_engine",
                description="紧急停止交易引擎"
            ))

        return actions

    async def execute_recovery_plan(self, plan: RecoveryPlan) -> RecoveryReport:
        """执行恢复计划

        Args:
            plan: 恢复计划

        Returns:
            恢复报告
        """
        plan.status = "IN_PROGRESS"
        start_time = datetime.now()

        logger.info(f"开始执行恢复计划: {plan.plan_id} - {plan.issue_description}")

        successful_actions = 0
        failed_actions = 0

        try:
            # 按优先级排序操作
            sorted_actions = sorted(
                plan.actions,
                key=lambda a: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}[a.priority.value]
            )

            # 执行操作
            for action in sorted_actions:
                try:
                    result = await self.executor.execute_action(action)

                    if result['success']:
                        successful_actions += 1
                    else:
                        failed_actions += 1

                        # 如果操作失败且为关键操作，停止执行
                        if action.priority == RecoveryPriority.CRITICAL:
                            logger.error(f"关键操作失败，停止恢复: {action.action_id}")
                            break

                except Exception as e:
                    logger.error(f"恢复操作异常: {action.action_id} - {e}")
                    failed_actions += 1

            # 计算整体成功率
            total_actions = len(sorted_actions)
            success_rate = successful_actions / total_actions if total_actions > 0 else 0

            # 更新计划状态
            if success_rate >= 0.5:
                plan.status = "COMPLETED"
            else:
                plan.status = "FAILED"

            # 生成报告
            report = RecoveryReport(
                plan_id=plan.plan_id,
                success=success_rate >= 0.5,
                total_actions=total_actions,
                successful_actions=successful_actions,
                failed_actions=failed_actions,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.now(),
                details={
                    'issue_description': plan.issue_description,
                    'severity': plan.severity.value,
                    'success_rate': success_rate,
                    'actions': [
                        {
                            'action_id': a.action_id,
                            'type': a.action_type.value,
                            'status': a.status.value,
                            'result': a.result
                        }
                        for a in sorted_actions
                    ]
                }
            )

            # 记录历史
            self.history.append(report)

            # 更新统计
            self._update_stats(report)

            logger.info(
                f"恢复计划完成: {plan.plan_id} - "
                f"成功: {successful_actions}/{total_actions}, "
                f"耗时: {report.duration_seconds:.2f}秒"
            )

            return report

        except Exception as e:
            plan.status = "FAILED"
            logger.error(f"恢复计划执行异常: {plan.plan_id} - {e}")

            return RecoveryReport(
                plan_id=plan.plan_id,
                success=False,
                total_actions=len(plan.actions),
                successful_actions=successful_actions,
                failed_actions=failed_actions + len(plan.actions) - successful_actions,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                started_at=start_time,
                completed_at=datetime.now(),
                details={
                    'exception': str(e),
                    'issue_description': plan.issue_description
                }
            )

    def _update_stats(self, report: RecoveryReport) -> None:
        """更新统计信息

        Args:
            report: 恢复报告
        """
        self.stats['total_plans'] += 1
        self.stats['total_actions'] += report.total_actions
        self.stats['successful_actions'] += report.successful_actions

        if report.success:
            self.stats['successful_plans'] += 1
        else:
            self.stats['failed_plans'] += 1

        # 更新平均恢复时间
        avg_time = self.stats['avg_recovery_time']
        total_plans = self.stats['total_plans']
        self.stats['avg_recovery_time'] = (avg_time * (total_plans - 1) + report.duration_seconds) / total_plans

    async def start_auto_recovery(self) -> None:
        """启动自动恢复

        持续监控恢复队列并执行恢复计划。
        """
        self.is_running = True
        logger.info("自动恢复引擎启动")

        while self.is_running:
            try:
                # 检查是否有待执行的计划
                if self.plan_queue and not self.active_plan:
                    plan = self.plan_queue.popleft()
                    self.active_plan = plan

                    # 执行计划
                    report = await self.execute_recovery_plan(plan)

                    # 清除活动计划
                    self.active_plan = None

                await asyncio.sleep(1)  # 避免忙等待

            except Exception as e:
                logger.error(f"自动恢复异常: {e}")
                await asyncio.sleep(5)

    def stop_auto_recovery(self) -> None:
        """停止自动恢复"""
        self.is_running = False
        logger.info("自动恢复引擎停止")

    def get_recovery_status(self) -> Dict[str, Any]:
        """获取恢复状态

        Returns:
            状态信息
        """
        return {
            'is_running': self.is_running,
            'active_plan': self.active_plan.plan_id if self.active_plan else None,
            'queue_size': len(self.plan_queue),
            'stats': self.stats.copy(),
            'executor_stats': dict(self.executor.execution_stats)
        }


# 便捷函数
def create_auto_recovery_engine(
    config: Dict[str, Any],
    executor: Optional[RecoveryActionExecutor] = None
) -> AutoRecoveryEngine:
    """创建自动恢复引擎实例

    Args:
        config: 配置字典
        executor: 执行器（可选）

    Returns:
        自动恢复引擎实例
    """
    return AutoRecoveryEngine(config, executor)
