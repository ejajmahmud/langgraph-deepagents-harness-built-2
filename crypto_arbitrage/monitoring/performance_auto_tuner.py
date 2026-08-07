"""性能自动调优系统 V5.9 - PerformanceAutoTuner

V5.9 Phase 3核心模块：性能自动调优系统
基于V5.9 Phase 3的所有优化模块，实现智能化的自动性能调优。

核心功能：
1. 智能参数调整 - 基于性能指标自动调整参数
2. 优化策略执行 - 执行缓存、并发、内存优化
3. 性能目标管理 - 设定和追踪性能目标
4. 自动优化决策 - 基于规则的自动化决策
5. 优化效果评估 - 评估优化效果和持续改进

技术突破：
- 自动化调优: 减少人工干预
- 智能决策: 基于规则和指标
- 持续优化: 持续改进性能
- 效果评估: 量化优化成果
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class OptimizationAction(Enum):
    """优化动作"""
    ADJUST_CACHE_SIZE = "ADJUST_CACHE_SIZE"
    ADJUST_CONCURRENT = "ADJUST_CONCURRENT"
    TRIGGER_GC = "TRIGGER_GC"
    COMPRESS_HISTORY = "COMPRESS_HISTORY"
    WARMUP_CACHE = "WARMUP_CACHE"
    ADJUST_TIMEOUT = "ADJUST_TIMEOUT"
    ENABLE_OPTIMIZATION = "ENABLE_OPTIMIZATION"
    DISABLE_OPTIMIZATION = "DISABLE_OPTIMIZATION"


class OptimizationStatus(Enum):
    """优化状态"""
    PENDING = "PENDING"       # 待执行
    RUNNING = "RUNNING"       # 执行中
    COMPLETED = "COMPLETED"   # 已完成
    FAILED = "FAILED"         # 失败
    CANCELLED = "CANCELLED"   # 已取消


@dataclass
class PerformanceGoal:
    """性能目标"""
    name: str
    target_value: float
    current_value: float
    unit: str
    priority: int  # 1-10，10最高
    achieved: bool = False
    history: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, value)

    def update(self, value: float, timestamp: float) -> None:
        """更新当前值"""
        self.current_value = value
        self.achieved = value >= self.target_value
        self.history.append((timestamp, value))

        # 限制历史长度
        if len(self.history) > 100:
            self.history.pop(0)


@dataclass
class OptimizationActionRecord:
    """优化动作记录"""
    id: str
    action: OptimizationAction
    description: str
    parameters: Dict[str, Any]
    status: OptimizationStatus = OptimizationStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class OptimizationReport:
    """优化报告"""
    period_start: float
    period_end: float
    actions_executed: int
    actions_successful: int
    actions_failed: int
    performance_improvement: Dict[str, float]  # 指标名 -> 改进幅度
    goals_achieved: List[str]
    goals_not_achieved: List[str]
    recommendations: List[str]


class PerformanceAutoTuner:
    """性能自动调优系统 V5.9

    实现智能化的自动性能调优，包括：
    - 智能参数调整
    - 优化策略执行
    - 性能目标管理
    - 自动优化决策
    - 优化效果评估
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化性能自动调优系统

        Args:
            config: 配置字典，包含:
                - tuning_interval: 调优间隔（秒）
                - enable_auto_tuning: 是否启用自动调优
                - max_concurrent_actions: 最大并发动作数
                - action_timeout: 动作超时时间（秒）
        """
        self.config = config

        # 配置
        self.tuning_interval = config.get('tuning_interval', 60)
        self.enable_auto_tuning = config.get('enable_auto_tuning', True)
        self.max_concurrent_actions = config.get('max_concurrent_actions', 3)
        self.action_timeout = config.get('action_timeout', 30)

        # 优化组件引用
        self.cache_optimizer = None
        self.concurrent_controller = None
        self.memory_optimizer = None
        self.dashboard = None

        # 性能目标
        self.performance_goals: Dict[str, PerformanceGoal] = {}
        self._initialize_performance_goals()

        # 优化动作队列
        self._action_queue: List[OptimizationActionRecord] = []
        self._action_history: List[OptimizationActionRecord] = []
        self._max_history = 100

        # 性能基准
        self._baseline_metrics: Optional[Dict[str, float]] = None
        self._current_metrics: Dict[str, float] = {}

        # 控制状态
        self._running = False
        self._tuner_task: Optional[asyncio.Task] = None
        self._action_semaphore = asyncio.Semaphore(self.max_concurrent_actions)

        # 优化规则
        self._optimization_rules = self._initialize_optimization_rules()

        logger.info(
            f"✅ 性能自动调优系统V5.9初始化成功: "
            f"auto_tuning={self.enable_auto_tuning}, "
            f"interval={self.tuning_interval}s"
        )

    def _initialize_performance_goals(self) -> None:
        """初始化性能目标"""
        self.performance_goals = {
            'cache_hit_rate': PerformanceGoal(
                name='cache_hit_rate',
                target_value=0.95,
                current_value=0.0,
                unit='%',
                priority=8
            ),
            'response_time': PerformanceGoal(
                name='response_time',
                target_value=2.0,  # 目标2秒以下
                current_value=0.0,
                unit='s',
                priority=9
            ),
            'concurrent_capability': PerformanceGoal(
                name='concurrent_capability',
                target_value=10.0,  # 目标10个并发
                current_value=0.0,
                unit='count',
                priority=7
            ),
            'memory_efficiency': PerformanceGoal(
                name='memory_efficiency',
                target_value=0.8,  # 目标80%效率
                current_value=0.0,
                unit='ratio',
                priority=6
            ),
            'error_rate': PerformanceGoal(
                name='error_rate',
                target_value=0.01,  # 目标1%以下
                current_value=0.0,
                unit='%',
                priority=10
            )
        }

    def _initialize_optimization_rules(self) -> List[Dict[str, Any]]:
        """初始化优化规则"""
        return [
            {
                'name': 'cache_hit_rate_low',
                'condition': lambda m: m.get('cache_hit_rate', 0) < 0.7,
                'action': OptimizationAction.ADJUST_CACHE_SIZE,
                'priority': 8,
                'description': '缓存命中率过低，调整缓存大小'
            },
            {
                'name': 'memory_high_usage',
                'condition': lambda m: m.get('memory_mb', 0) > 800,
                'action': OptimizationAction.TRIGGER_GC,
                'priority': 9,
                'description': '内存使用过高，触发垃圾回收'
            },
            {
                'name': 'response_time_high',
                'condition': lambda m: m.get('avg_response_time', 0) > 5.0,
                'action': OptimizationAction.ADJUST_CONCURRENT,
                'priority': 9,
                'description': '响应时间过长，调整并发参数'
            },
            {
                'name': 'history_large',
                'condition': lambda m: m.get('history_size', 0) > 1000,
                'action': OptimizationAction.COMPRESS_HISTORY,
                'priority': 5,
                'description': '历史记录过大，压缩历史数据'
            },
            {
                'name': 'cache_hit_rate_target',
                'condition': lambda m: 0.7 <= m.get('cache_hit_rate', 0) < 0.9,
                'action': OptimizationAction.WARMUP_CACHE,
                'priority': 6,
                'description': '缓存命中率接近目标，预热缓存'
            }
        ]

    async def start(self) -> None:
        """启动自动调优系统"""
        self._running = True

        # 记录性能基准
        await self._record_baseline()

        # 启动调优任务
        if self.enable_auto_tuning:
            self._tuner_task = asyncio.create_task(self._tuning_loop())

        logger.info("性能自动调优系统已启动")

    async def stop(self) -> None:
        """停止自动调优系统"""
        self._running = False

        # 取消调优任务
        if self._tuner_task:
            self._tuner_task.cancel()

        # 等待所有动作完成
        while self._get_running_actions():
            await asyncio.sleep(0.1)

        logger.info("性能自动调优系统已停止")

    def set_cache_optimizer(self, optimizer) -> None:
        """设置缓存优化器"""
        self.cache_optimizer = optimizer

    def set_concurrent_controller(self, controller) -> None:
        """设置并发控制器"""
        self.concurrent_controller = controller

    def set_memory_optimizer(self, optimizer) -> None:
        """设置内存优化器"""
        self.memory_optimizer = optimizer

    def set_dashboard(self, dashboard) -> None:
        """设置Dashboard"""
        self.dashboard = dashboard

    async def _tuning_loop(self) -> None:
        """调优循环"""
        while self._running:
            try:
                # 收集当前指标
                await self._collect_metrics()

                # 更新性能目标
                self._update_performance_goals()

                # 评估优化需求
                actions = await self._evaluate_optimization_needs()

                # 执行优化动作
                for action in actions:
                    await self._enqueue_action(action)

                # 处理动作队列
                await self._process_action_queue()

                await asyncio.sleep(self.tuning_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调优循环错误: {e}")
                await asyncio.sleep(self.tuning_interval)

    async def _record_baseline(self) -> None:
        """记录性能基准"""
        await self._collect_metrics()
        self._baseline_metrics = self._current_metrics.copy()
        logger.info("性能基准已记录")

    async def _collect_metrics(self) -> None:
        """收集性能指标"""
        # 从Dashboard获取指标
        if self.dashboard:
            self._current_metrics = {
                'timestamp': time.time(),
                'cpu_percent': self.dashboard._current_metrics.get('cpu_percent', 0),
                'memory_mb': self.dashboard._current_metrics.get('memory_mb', 0),
                'cache_hit_rate': self.dashboard._current_metrics.get('cache', {}).get('hit_rate', 0),
                'concurrent_tasks': self.dashboard._current_metrics.get('concurrency', {}).get('current_concurrency', 0),
                'avg_response_time': 0.0,  # 需要从实际数据获取
                'throughput': self.dashboard._current_metrics.get('concurrency', {}).get('throughput', 0),
                'error_rate': 0.0,  # 需要从实际数据获取
                'history_size': 0  # 需要从实际数据获取
            }

    def _update_performance_goals(self) -> None:
        """更新性能目标"""
        timestamp = time.time()

        if 'cache_hit_rate' in self.performance_goals:
            self.performance_goals['cache_hit_rate'].update(
                self._current_metrics.get('cache_hit_rate', 0),
                timestamp
            )

        if 'response_time' in self.performance_goals:
            self.performance_goals['response_time'].update(
                self._current_metrics.get('avg_response_time', 0),
                timestamp
            )

        if 'concurrent_capability' in self.performance_goals:
            self.performance_goals['concurrent_capability'].update(
                self._current_metrics.get('concurrent_tasks', 0),
                timestamp
            )

        if 'memory_efficiency' in self.performance_goals and self.memory_optimizer:
            memory_metrics = self.memory_optimizer.get_metrics()
            self.performance_goals['memory_efficiency'].update(
                memory_metrics.memory_efficiency,
                timestamp
            )

    async def _evaluate_optimization_needs(self) -> List[Dict[str, Any]]:
        """评估优化需求"""
        actions = []

        # 检查优化规则
        for rule in self._optimization_rules:
            if rule['condition'](self._current_metrics):
                actions.append({
                    'action': rule['action'],
                    'priority': rule['priority'],
                    'description': rule['description'],
                    'rule_name': rule['name']
                })

        # 按优先级排序
        actions.sort(key=lambda x: x['priority'], reverse=True)

        return actions

    async def _enqueue_action(self, action_info: Dict[str, Any]) -> None:
        """将动作加入队列"""
        action_record = OptimizationActionRecord(
            id=f"action_{int(time.time() * 1000000)}",
            action=action_info['action'],
            description=action_info['description'],
            parameters={'rule_name': action_info['rule_name']}
        )

        self._action_queue.append(action_record)
        logger.debug(f"优化动作已加入队列: {action_info['action'].value}")

    async def _process_action_queue(self) -> None:
        """处理动作队列"""
        if not self._action_queue:
            return

        # 处理队列中的动作
        while self._action_queue and self._get_running_actions() < self.max_concurrent_actions:
            action_record = self._action_queue.pop(0)
            asyncio.create_task(self._execute_action(action_record))

    def _get_running_actions(self) -> int:
        """获取正在运行的动作数"""
        return sum(
            1 for action in self._action_history
            if action.status == OptimizationStatus.RUNNING
        )

    async def _execute_action(self, action_record: OptimizationActionRecord) -> None:
        """执行优化动作"""
        action_record.status = OptimizationStatus.RUNNING
        action_record.started_at = time.time()

        try:
            # 获取信号量
            async with self._action_semaphore:
                # 根据动作类型执行相应的优化
                if action_record.action == OptimizationAction.ADJUST_CACHE_SIZE:
                    result = await self._adjust_cache_size()
                elif action_record.action == OptimizationAction.ADJUST_CONCURRENT:
                    result = await self._adjust_concurrent()
                elif action_record.action == OptimizationAction.TRIGGER_GC:
                    result = await self._trigger_gc()
                elif action_record.action == OptimizationAction.COMPRESS_HISTORY:
                    result = await self._compress_history()
                elif action_record.action == OptimizationAction.WARMUP_CACHE:
                    result = await self._warmup_cache()
                else:
                    result = {'status': 'skipped', 'reason': 'unknown_action'}

                action_record.result = result
                action_record.status = OptimizationStatus.COMPLETED
                action_record.completed_at = time.time()

                logger.info(
                    f"优化动作执行完成: {action_record.action.value}, "
                    f"耗时={action_record.duration:.2f}s"
                )

        except Exception as e:
            action_record.error = str(e)
            action_record.status = OptimizationStatus.FAILED
            action_record.completed_at = time.time()
            logger.error(f"优化动作执行失败: {e}")

        # 添加到历史
        self._action_history.append(action_record)
        if len(self._action_history) > self._max_history:
            self._action_history.pop(0)

    async def _adjust_cache_size(self) -> Dict[str, Any]:
        """调整缓存大小"""
        if not self.cache_optimizer:
            return {'status': 'skipped', 'reason': 'cache_optimizer_not_available'}

        cache_info = self.cache_optimizer.get_cache_info()
        current_size = cache_info.get('total_entries', 0)
        target_size = int(current_size * 1.2)  # 增加20%

        # 这里应该实际调整缓存大小
        # 暂时只返回建议
        return {
            'status': 'suggested',
            'current_size': current_size,
            'target_size': target_size,
            'increase': target_size - current_size
        }

    async def _adjust_concurrent(self) -> Dict[str, Any]:
        """调整并发参数"""
        if not self.concurrent_controller:
            return {'status': 'skipped', 'reason': 'concurrent_controller_not_available'}

        metrics = self.concurrent_controller.get_metrics()
        current_concurrent = metrics.current_concurrent

        # 根据系统负载调整
        cpu_usage = self._current_metrics.get('cpu_percent', 0)
        if cpu_usage > 80:
            target_concurrent = max(1, int(current_concurrent * 0.8))
        elif cpu_usage < 30:
            target_concurrent = min(10, int(current_concurrent * 1.2))
        else:
            target_concurrent = current_concurrent

        return {
            'status': 'suggested',
            'current_concurrent': current_concurrent,
            'target_concurrent': target_concurrent,
            'adjustment': target_concurrent - current_concurrent
        }

    async def _trigger_gc(self) -> Dict[str, Any]:
        """触发垃圾回收"""
        if not self.memory_optimizer:
            return {'status': 'skipped', 'reason': 'memory_optimizer_not_available'}

        result = await self.memory_optimizer.optimize_gc()
        return result

    async def _compress_history(self) -> Dict[str, Any]:
        """压缩历史记录"""
        # 这里应该实际压缩历史记录
        # 暂时只返回建议
        return {
            'status': 'suggested',
            'current_size': self._current_metrics.get('history_size', 0),
            'target_size': 100
        }

    async def _warmup_cache(self) -> Dict[str, Any]:
        """预热缓存"""
        if not self.cache_optimizer:
            return {'status': 'skipped', 'reason': 'cache_optimizer_not_available'}

        result = await self.cache_optimizer.smart_warmup()
        return result

    def generate_optimization_report(
        self,
        period_seconds: int = 3600
    ) -> OptimizationReport:
        """生成优化报告

        Args:
            period_seconds: 报告周期（秒）

        Returns:
            优化报告
        """
        period_end = time.time()
        period_start = period_end - period_seconds

        # 筛选周期内的动作
        period_actions = [
            action for action in self._action_history
            if action.created_at >= period_start
        ]

        # 统计动作
        total_actions = len(period_actions)
        successful_actions = sum(
            1 for action in period_actions
            if action.status == OptimizationStatus.COMPLETED
        )
        failed_actions = sum(
            1 for action in period_actions
            if action.status == OptimizationStatus.FAILED
        )

        # 计算性能改进
        performance_improvement = {}
        if self._baseline_metrics:
            for key, current_value in self._current_metrics.items():
                if key in self._baseline_metrics and isinstance(current_value, (int, float)):
                    baseline_value = self._baseline_metrics[key]
                    if baseline_value > 0:
                        improvement = (current_value - baseline_value) / baseline_value
                        performance_improvement[key] = improvement

        # 统计目标达成情况
        goals_achieved = [
            name for name, goal in self.performance_goals.items()
            if goal.achieved
        ]
        goals_not_achieved = [
            name for name, goal in self.performance_goals.items()
            if not goal.achieved
        ]

        # 生成建议
        recommendations = []
        for goal_name, goal in self.performance_goals.items():
            if not goal.achieved:
                recommendations.append(
                    f"{goal_name}: 当前{goal.current_value:.2f}{goal.unit}, "
                    f"目标{goal.target_value:.2f}{goal.unit}"
                )

        return OptimizationReport(
            period_start=period_start,
            period_end=period_end,
            actions_executed=total_actions,
            actions_successful=successful_actions,
            actions_failed=failed_actions,
            performance_improvement=performance_improvement,
            goals_achieved=goals_achieved,
            goals_not_achieved=goals_not_achieved,
            recommendations=recommendations
        )

    def get_performance_goals(self) -> Dict[str, PerformanceGoal]:
        """获取性能目标"""
        return self.performance_goals.copy()

    def get_action_history(self, count: int = 10) -> List[OptimizationActionRecord]:
        """获取动作历史"""
        return self._action_history[-count:]


def create_performance_auto_tuner(config: Dict[str, Any]) -> PerformanceAutoTuner:
    """创建性能自动调优系统实例

    Args:
        config: 配置字典

    Returns:
        PerformanceAutoTuner实例
    """
    return PerformanceAutoTuner(config)
