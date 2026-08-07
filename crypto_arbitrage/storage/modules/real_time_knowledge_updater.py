"""实时知识更新器 - V5.10 Phase 2.2

实现实时市场数据监控、知识更新触发、增量知识提取和智能调度。

核心功能：
1. 实时数据监控
2. 知识更新触发
3. 增量知识提取
4. 更新调度

基于：V5.10架构设计
创建时间：2026-04-19
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import statistics
import hashlib

logger = logging.getLogger(__name__)


class UpdatePriority(Enum):
    """更新优先级"""
    CRITICAL = "critical"  # 紧急更新
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


class UpdateStatus(Enum):
    """更新状态"""
    PENDING = "pending"  # 等待中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过


class KnowledgeGapType(Enum):
    """知识缺口类型"""
    MISSING_DATA = "missing_data"  # 缺少数据
    OUTDATED_INFO = "outdated_info"  # 信息过时
    CONFLICTING_INFO = "conflicting_info"  # 冲突信息
    LOW_CONFIDENCE = "low_confidence"  # 低置信度
    CONTEXT_MISMATCH = "context_mismatch"  # 上下文不匹配


@dataclass
class MarketDataSnapshot:
    """市场数据快照"""
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    volatility: float
    trend: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "volatility": self.volatility,
            "trend": self.trend,
            "metadata": self.metadata
        }


@dataclass
class KnowledgeUpdateTask:
    """知识更新任务"""
    task_id: str
    priority: UpdatePriority
    update_type: str
    data: Dict[str, Any]
    created_at: datetime
    status: UpdateStatus = UpdateStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "priority": self.priority.value,
            "update_type": self.update_type,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "result": self.result
        }


@dataclass
class KnowledgeGap:
    """知识缺口"""
    gap_id: str
    gap_type: KnowledgeGapType
    description: str
    severity: float  # 0-1
    affected_knowledge_ids: List[str]
    suggested_action: str
    detected_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type.value,
            "description": self.description,
            "severity": self.severity,
            "affected_knowledge_ids": self.affected_knowledge_ids,
            "suggested_action": self.suggested_action,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class UpdateStatistics:
    """更新统计"""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    skipped_updates: int = 0
    average_update_time: float = 0.0
    updates_by_priority: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    updates_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    knowledge_gaps_detected: int = 0
    knowledge_gaps_resolved: int = 0


class RealTimeKnowledgeUpdater:
    """实时知识更新器

    实现毫秒级数据监控、智能更新调度和增量知识提取。
    """

    # 监控参数
    MONITOR_INTERVAL = 1.0  # 秒
    DATA_BUFFER_SIZE = 100
    VOLATILITY_THRESHOLD = 0.02  # 2%波动率阈值

    # 更新参数
    MAX_CONCURRENT_UPDATES = 5
    UPDATE_TIMEOUT = 30.0  # 秒

    # 优先级权重
    PRIORITY_WEIGHTS = {
        UpdatePriority.CRITICAL: 4.0,
        UpdatePriority.HIGH: 3.0,
        UpdatePriority.MEDIUM: 2.0,
        UpdatePriority.LOW: 1.0
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化实时知识更新器

        Args:
            config: 配置字典
        """
        self.config = config

        # 监控参数
        self.monitor_interval = config.get('monitor_interval', self.MONITOR_INTERVAL)
        self.data_buffer_size = config.get('data_buffer_size', self.DATA_BUFFER_SIZE)
        self.volatility_threshold = config.get('volatility_threshold', self.VOLATILITY_THRESHOLD)

        # 更新参数
        self.max_concurrent_updates = config.get('max_concurrent_updates', self.MAX_CONCURRENT_UPDATES)
        self.update_timeout = config.get('update_timeout', self.UPDATE_TIMEOUT)

        # 数据缓冲
        self.market_data_buffer: deque = deque(maxlen=self.data_buffer_size)
        self.trading_activity_buffer: deque = deque(maxlen=self.data_buffer_size)

        # 更新队列
        self.update_queue: List[KnowledgeUpdateTask] = []
        self._task_id_counter = 0

        # 知识缺口
        self.knowledge_gaps: List[KnowledgeGap] = []

        # 统计信息
        self.stats = UpdateStatistics()

        # 运行状态
        self._is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._update_task: Optional[asyncio.Task] = None

        # 外部依赖
        self.knowledge_base: Dict[str, Dict[str, Any]] = {}
        self.update_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        logger.info("[OK] 实时知识更新器初始化完成")

    # ========== 实时数据监控 ==========

    async def monitor_market_data(self, symbols: List[str]) -> None:
        """监控市场数据

        Args:
            symbols: 监控的交易对列表
        """
        logger.info(f"开始监控市场数据: {symbols}")

        while self._is_running:
            try:
                # 模拟获取市场数据
                for symbol in symbols:
                    snapshot = await self._fetch_market_snapshot(symbol)
                    if snapshot:
                        await self._process_market_snapshot(snapshot)

                # 检测知识缺口
                await self.detect_knowledge_gaps()

                # 等待下一次监控
                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"市场数据监控错误: {e}")
                await asyncio.sleep(self.monitor_interval)

    async def monitor_trading_activity(self) -> None:
        """监控交易活动"""
        logger.info("开始监控交易活动")

        while self._is_running:
            try:
                # 获取最新交易活动
                activity = await self._fetch_trading_activity()
                if activity:
                    await self._process_trading_activity(activity)

                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"交易活动监控错误: {e}")
                await asyncio.sleep(self.monitor_interval)

    async def detect_knowledge_gaps(self) -> List[KnowledgeGap]:
        """检测知识缺口

        Returns:
            检测到的知识缺口列表
        """
        gaps = []

        # 检测过时知识
        outdated_gaps = await self._detect_outdated_knowledge()
        gaps.extend(outdated_gaps)

        # 检测缺失数据
        missing_gaps = await self._detect_missing_data()
        gaps.extend(missing_gaps)

        # 检测低置信度知识
        low_confidence_gaps = await self._detect_low_confidence_knowledge()
        gaps.extend(low_confidence_gaps)

        # 更新缺口列表
        self.knowledge_gaps = gaps
        self.stats.knowledge_gaps_detected = len(gaps)

        # 触发更新任务
        for gap in gaps:
            if gap.severity > 0.7:
                await self._trigger_gap_update(gap)

        return gaps

    # ========== 知识更新触发 ==========

    async def trigger_knowledge_update(
        self,
        update_type: str,
        data: Dict[str, Any],
        priority: UpdatePriority = UpdatePriority.MEDIUM
    ) -> str:
        """触发知识更新

        Args:
            update_type: 更新类型
            data: 更新数据
            priority: 优先级

        Returns:
            任务ID
        """
        task = KnowledgeUpdateTask(
            task_id=self._generate_task_id(),
            priority=priority,
            update_type=update_type,
            data=data,
            created_at=datetime.now()
        )

        self.update_queue.append(task)
        self.stats.total_updates += 1
        self.stats.updates_by_priority[priority.value] += 1
        self.stats.updates_by_type[update_type] += 1

        logger.info(f"创建更新任务: {task.task_id}, 类型: {update_type}, 优先级: {priority.value}")

        return task.task_id

    async def prioritize_updates(self) -> List[KnowledgeUpdateTask]:
        """更新优先级排序

        Returns:
            排序后的任务列表
        """
        # 计算优先级分数
        for task in self.update_queue:
            if task.status == UpdateStatus.PENDING:
                task.priority_score = self._calculate_priority_score(task)

        # 按优先级分数排序
        pending_tasks = [
            task for task in self.update_queue
            if task.status == UpdateStatus.PENDING
        ]
        pending_tasks.sort(key=lambda t: t.priority_score, reverse=True)

        return pending_tasks

    async def batch_update_knowledge(
        self,
        updates: List[Dict[str, Any]],
        priority: UpdatePriority = UpdatePriority.MEDIUM
    ) -> List[str]:
        """批量更新知识

        Args:
            updates: 更新列表
            priority: 优先级

        Returns:
            任务ID列表
        """
        task_ids = []

        for update in updates:
            task_id = await self.trigger_knowledge_update(
                update_type=update.get('type', 'generic'),
                data=update,
                priority=priority
            )
            task_ids.append(task_id)

        logger.info(f"批量创建 {len(task_ids)} 个更新任务")

        return task_ids

    # ========== 增量知识提取 ==========

    async def extract_incremental_knowledge(
        self,
        data_snapshot: MarketDataSnapshot
    ) -> List[Dict[str, Any]]:
        """提取增量知识

        Args:
            data_snapshot: 数据快照

        Returns:
            提取的知识列表
        """
        knowledge_list = []

        # 提取价格模式知识
        price_knowledge = await self._extract_price_pattern_knowledge(data_snapshot)
        if price_knowledge:
            knowledge_list.append(price_knowledge)

        # 提取成交量知识
        volume_knowledge = await self._extract_volume_knowledge(data_snapshot)
        if volume_knowledge:
            knowledge_list.append(volume_knowledge)

        # 提取波动率知识
        volatility_knowledge = await self._extract_volatility_knowledge(data_snapshot)
        if volatility_knowledge:
            knowledge_list.append(volatility_knowledge)

        return knowledge_list

    async def update_existing_knowledge(
        self,
        knowledge_id: str,
        new_data: Dict[str, Any]
    ) -> bool:
        """更新现有知识

        Args:
            knowledge_id: 知识ID
            new_data: 新数据

        Returns:
            是否成功
        """
        if knowledge_id not in self.knowledge_base:
            logger.warning(f"知识不存在: {knowledge_id}")
            return False

        # 更新知识
        existing = self.knowledge_base[knowledge_id]
        existing['data'].update(new_data)
        existing['updated_at'] = datetime.now().isoformat()

        logger.info(f"更新知识: {knowledge_id}")

        return True

    async def detect_obsolete_knowledge(
        self,
        max_age_hours: int = 24
    ) -> List[str]:
        """检测过时知识

        Args:
            max_age_hours: 最大年龄（小时）

        Returns:
            过时知识ID列表
        """
        obsolete_ids = []
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for knowledge_id, knowledge in self.knowledge_base.items():
            updated_at = knowledge.get('updated_at')
            if updated_at:
                try:
                    update_time = datetime.fromisoformat(updated_at)
                    if update_time < cutoff_time:
                        obsolete_ids.append(knowledge_id)
                except:
                    pass

        if obsolete_ids:
            logger.info(f"检测到 {len(obsolete_ids)} 条过时知识")

        return obsolete_ids

    # ========== 更新调度 ==========

    async def schedule_updates(self) -> None:
        """调度更新任务"""
        logger.info("开始调度更新任务")

        while self._is_running:
            try:
                # 获取优先级排序的任务
                pending_tasks = await self.prioritize_updates()

                # 限制并发数
                active_tasks = [
                    task for task in self.update_queue
                    if task.status == UpdateStatus.PROCESSING
                ]

                available_slots = self.max_concurrent_updates - len(active_tasks)

                # 执行任务
                for task in pending_tasks[:available_slots]:
                    asyncio.create_task(self._execute_update_task(task))

                # 清理已完成任务
                await self._cleanup_completed_tasks()

                await asyncio.sleep(0.1)  # 100ms检查一次

            except Exception as e:
                logger.error(f"更新调度错误: {e}")
                await asyncio.sleep(1.0)

    async def handle_update_conflicts(
        self,
        conflicting_updates: List[KnowledgeUpdateTask]
    ) -> List[KnowledgeUpdateTask]:
        """处理更新冲突

        Args:
            conflicting_updates: 冲突的更新任务

        Returns:
            解决冲突后的任务列表
        """
        # 简化版本：按优先级选择
        resolved_tasks = sorted(
            conflicting_updates,
            key=lambda t: self.PRIORITY_WEIGHTS[t.priority],
            reverse=True
        )

        # 标记低优先级任务为跳过
        for task in resolved_tasks[1:]:
            task.status = UpdateStatus.SKIPPED
            task.error_message = "被更高优先级任务覆盖"

        return [resolved_tasks[0]]

    async def optimize_update_frequency(self) -> Dict[str, Any]:
        """优化更新频率

        Returns:
            优化建议
        """
        # 分析更新模式
        update_intervals = []
        for task in self.update_queue:
            if task.started_at and task.completed_at:
                interval = (task.completed_at - task.started_at).total_seconds()
                update_intervals.append(interval)

        if not update_intervals:
            return {"current_interval": self.monitor_interval, "suggestion": "maintain"}

        # 计算统计信息
        avg_interval = statistics.mean(update_intervals)
        std_interval = statistics.stdev(update_intervals) if len(update_intervals) > 1 else 0

        # 优化建议
        if avg_interval < 1.0:
            suggestion = "increase"
            suggested_interval = max(avg_interval * 1.5, 1.0)
        elif avg_interval > 5.0:
            suggestion = "decrease"
            suggested_interval = min(avg_interval * 0.8, 5.0)
        else:
            suggestion = "maintain"
            suggested_interval = avg_interval

        return {
            "current_interval": self.monitor_interval,
            "average_update_time": avg_interval,
            "update_time_std": std_interval,
            "suggestion": suggestion,
            "suggested_interval": suggested_interval
        }

    # ========== 控制方法 ==========

    async def start(self) -> None:
        """启动更新器"""
        if self._is_running:
            logger.warning("更新器已在运行")
            return

        self._is_running = True

        # 启动监控任务
        self._monitor_task = asyncio.create_task(self.monitor_market_data(['BTC/USDT', 'ETH/USDT']))
        self._update_task = asyncio.create_task(self.schedule_updates())

        logger.info("[OK] 实时知识更新器已启动")

    async def stop(self) -> None:
        """停止更新器"""
        if not self._is_running:
            return

        self._is_running = False

        # 取消任务
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._update_task:
            self._update_task.cancel()

        # 等待任务完成
        try:
            await asyncio.gather(self._monitor_task, self._update_task, return_exceptions=True)
        except:
            pass

        logger.info("[OK] 实时知识更新器已停止")

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """注册回调函数

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.update_callbacks[event_type].append(callback)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_updates": self.stats.total_updates,
            "successful_updates": self.stats.successful_updates,
            "failed_updates": self.stats.failed_updates,
            "skipped_updates": self.stats.skipped_updates,
            "average_update_time": self.stats.average_update_time,
            "updates_by_priority": dict(self.stats.updates_by_priority),
            "updates_by_type": dict(self.stats.updates_by_type),
            "knowledge_gaps_detected": self.stats.knowledge_gaps_detected,
            "knowledge_gaps_resolved": self.stats.knowledge_gaps_resolved,
            "pending_tasks": len([t for t in self.update_queue if t.status == UpdateStatus.PENDING]),
            "processing_tasks": len([t for t in self.update_queue if t.status == UpdateStatus.PROCESSING])
        }

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.stats = UpdateStatistics()
        logger.info("统计信息已重置")

    # ========== 辅助方法 ==========

    async def _fetch_market_snapshot(self, symbol: str) -> Optional[MarketDataSnapshot]:
        """获取市场快照"""
        # 模拟数据
        import random
        return MarketDataSnapshot(
            timestamp=datetime.now(),
            symbol=symbol,
            price=random.uniform(30000, 70000) if 'BTC' in symbol else random.uniform(1500, 4000),
            volume=random.uniform(100, 1000),
            volatility=random.uniform(0.01, 0.05),
            trend=random.choice(['bullish', 'bearish', 'neutral'])
        )

    async def _fetch_trading_activity(self) -> Optional[Dict[str, Any]]:
        """获取交易活动"""
        # 模拟数据
        import random
        return {
            "timestamp": datetime.now().isoformat(),
            "activity_type": random.choice(['buy', 'sell', 'hold']),
            "volume": random.uniform(1, 10),
            "price": random.uniform(30000, 70000)
        }

    async def _process_market_snapshot(self, snapshot: MarketDataSnapshot) -> None:
        """处理市场快照"""
        self.market_data_buffer.append(snapshot)

        # 检查是否需要触发更新
        if len(self.market_data_buffer) > 1:
            prev_snapshot = self.market_data_buffer[-2]
            price_change = abs(snapshot.price - prev_snapshot.price) / prev_snapshot.price

            if price_change > self.volatility_threshold:
                # 触发高优先级更新
                await self.trigger_knowledge_update(
                    update_type="price_volatility",
                    data={
                        "symbol": snapshot.symbol,
                        "price_change": price_change,
                        "snapshot": snapshot.to_dict()
                    },
                    priority=UpdatePriority.HIGH
                )

        # 提取增量知识
        knowledge_list = await self.extract_incremental_knowledge(snapshot)
        for knowledge in knowledge_list:
            knowledge_id = self._generate_knowledge_id(knowledge)
            self.knowledge_base[knowledge_id] = {
                "content": knowledge.get('content', ''),
                "data": knowledge,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "quality_score": 0.7,
                "value_score": 0.6
            }

    async def _process_trading_activity(self, activity: Dict[str, Any]) -> None:
        """处理交易活动"""
        self.trading_activity_buffer.append(activity)

        # 触发更新
        await self.trigger_knowledge_update(
            update_type="trading_activity",
            data=activity,
            priority=UpdatePriority.LOW
        )

    async def _detect_outdated_knowledge(self) -> List[KnowledgeGap]:
        """检测过时知识"""
        gaps = []
        obsolete_ids = await self.detect_obsolete_knowledge(max_age_hours=24)

        for knowledge_id in obsolete_ids:
            gap = KnowledgeGap(
                gap_id=self._generate_gap_id(),
                gap_type=KnowledgeGapType.OUTDATED_INFO,
                description=f"知识 {knowledge_id} 已过时",
                severity=0.8,
                affected_knowledge_ids=[knowledge_id],
                suggested_action="更新或删除该知识",
                detected_at=datetime.now()
            )
            gaps.append(gap)

        return gaps

    async def _detect_missing_data(self) -> List[KnowledgeGap]:
        """检测缺失数据"""
        gaps = []

        # 检查是否有活跃交易对的知识缺失
        active_symbols = set(s.symbol for s in self.market_data_buffer)
        known_symbols = set(
            k.get('symbol') for k in self.knowledge_base.values()
            if 'symbol' in k.get('data', {})
        )

        missing_symbols = active_symbols - known_symbols
        for symbol in missing_symbols:
            gap = KnowledgeGap(
                gap_id=self._generate_gap_id(),
                gap_type=KnowledgeGapType.MISSING_DATA,
                description=f"缺少交易对 {symbol} 的知识",
                severity=0.7,
                affected_knowledge_ids=[],
                suggested_action=f"提取 {symbol} 的市场知识",
                detected_at=datetime.now()
            )
            gaps.append(gap)

        return gaps

    async def _detect_low_confidence_knowledge(self) -> List[KnowledgeGap]:
        """检测低置信度知识"""
        gaps = []

        for knowledge_id, knowledge in self.knowledge_base.items():
            quality_score = knowledge.get('quality_score', 1.0)
            if quality_score < 0.5:
                gap = KnowledgeGap(
                    gap_id=self._generate_gap_id(),
                    gap_type=KnowledgeGapType.LOW_CONFIDENCE,
                    description=f"知识 {knowledge_id} 置信度过低: {quality_score}",
                    severity=quality_score,
                    affected_knowledge_ids=[knowledge_id],
                    suggested_action="重新验证或增强该知识",
                    detected_at=datetime.now()
                )
                gaps.append(gap)

        return gaps

    async def _trigger_gap_update(self, gap: KnowledgeGap) -> None:
        """触发缺口更新"""
        await self.trigger_knowledge_update(
            update_type="knowledge_gap",
            data={
                "gap_id": gap.gap_id,
                "gap_type": gap.gap_type.value,
                "affected_knowledge_ids": gap.affected_knowledge_ids
            },
            priority=UpdatePriority.CRITICAL if gap.severity > 0.8 else UpdatePriority.HIGH
        )

    async def _execute_update_task(self, task: KnowledgeUpdateTask) -> None:
        """执行更新任务"""
        task.status = UpdateStatus.PROCESSING
        task.started_at = datetime.now()

        try:
            # 模拟更新执行
            await asyncio.sleep(0.5)

            # 调用回调
            for callback in self.update_callbacks.get(task.update_type, []):
                await callback(task)

            task.status = UpdateStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = {"success": True, "updated_at": task.completed_at.isoformat()}

            self.stats.successful_updates += 1

            # 更新平均时间
            update_time = (task.completed_at - task.started_at).total_seconds()
            total_time = self.stats.average_update_time * (self.stats.successful_updates - 1)
            self.stats.average_update_time = (total_time + update_time) / self.stats.successful_updates

            logger.info(f"完成更新任务: {task.task_id}")

        except Exception as e:
            task.status = UpdateStatus.FAILED
            task.completed_at = datetime.now()
            task.error_message = str(e)

            self.stats.failed_updates += 1
            logger.error(f"更新任务失败: {task.task_id}, 错误: {e}")

    async def _cleanup_completed_tasks(self) -> None:
        """清理已完成任务"""
        # 保留最近1000个任务
        if len(self.update_queue) > 1000:
            completed_count = len([t for t in self.update_queue if t.status in [UpdateStatus.COMPLETED, UpdateStatus.FAILED, UpdateStatus.SKIPPED]])

            if completed_count > 500:
                # 保留最新的500个已完成任务
                self.update_queue = [
                    task for task in self.update_queue
                    if task.status == UpdateStatus.PENDING or
                    task.status == UpdateStatus.PROCESSING or
                    (task.status in [UpdateStatus.COMPLETED, UpdateStatus.FAILED, UpdateStatus.SKIPPED] and
                     len([t for t in self.update_queue if self.update_queue.index(t) > self.update_queue.index(task)]) < 500)
                ]

    def _calculate_priority_score(self, task: KnowledgeUpdateTask) -> float:
        """计算优先级分数"""
        base_score = self.PRIORITY_WEIGHTS[task.priority]

        # 基于等待时间的加权
        wait_time = (datetime.now() - task.created_at).total_seconds()
        time_weight = min(wait_time / 60.0, 2.0)  # 最多2倍权重

        return base_score * (1 + time_weight * 0.1)

    async def _extract_price_pattern_knowledge(
        self,
        snapshot: MarketDataSnapshot
    ) -> Optional[Dict[str, Any]]:
        """提取价格模式知识"""
        if len(self.market_data_buffer) < 5:
            return None

        recent_prices = [s.price for s in list(self.market_data_buffer)[-5:]]

        # 简单趋势分析
        if recent_prices[-1] > recent_prices[0]:
            trend = "uptrend"
        elif recent_prices[-1] < recent_prices[0]:
            trend = "downtrend"
        else:
            trend = "sideways"

        return {
            "type": "price_pattern",
            "content": f"{snapshot.symbol} 显示 {trend} 模式",
            "symbol": snapshot.symbol,
            "trend": trend,
            "price_change": (recent_prices[-1] - recent_prices[0]) / recent_prices[0],
            "timestamp": snapshot.timestamp.isoformat()
        }

    async def _extract_volume_knowledge(
        self,
        snapshot: MarketDataSnapshot
    ) -> Optional[Dict[str, Any]]:
        """提取成交量知识"""
        if len(self.market_data_buffer) < 5:
            return None

        recent_volumes = [s.volume for s in list(self.market_data_buffer)[-5:]]
        avg_volume = statistics.mean(recent_volumes)

        volume_status = "high" if snapshot.volume > avg_volume * 1.5 else "normal"

        return {
            "type": "volume_pattern",
            "content": f"{snapshot.symbol} 成交量 {volume_status}",
            "symbol": snapshot.symbol,
            "volume": snapshot.volume,
            "avg_volume": avg_volume,
            "volume_ratio": snapshot.volume / avg_volume if avg_volume > 0 else 0,
            "timestamp": snapshot.timestamp.isoformat()
        }

    async def _extract_volatility_knowledge(
        self,
        snapshot: MarketDataSnapshot
    ) -> Optional[Dict[str, Any]]:
        """提取波动率知识"""
        if len(self.market_data_buffer) < 5:
            return None

        recent_prices = [s.price for s in list(self.market_data_buffer)[-5:]]
        price_std = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
        price_mean = statistics.mean(recent_prices)
        volatility = price_std / price_mean if price_mean > 0 else 0

        volatility_level = "high" if volatility > self.volatility_threshold else "normal"

        return {
            "type": "volatility_pattern",
            "content": f"{snapshot.symbol} 波动率 {volatility_level}",
            "symbol": snapshot.symbol,
            "volatility": volatility,
            "volatility_level": volatility_level,
            "timestamp": snapshot.timestamp.isoformat()
        }

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        self._task_id_counter += 1
        return f"task_{self._task_id_counter:06d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _generate_gap_id(self) -> str:
        """生成缺口ID"""
        return f"gap_{hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]}"

    def _generate_knowledge_id(self, knowledge: Dict[str, Any]) -> str:
        """生成知识ID"""
        content = knowledge.get('content', '')
        knowledge_type = knowledge.get('type', 'unknown')
        timestamp = knowledge.get('timestamp', datetime.now().isoformat())

        hash_input = f"{knowledge_type}_{content}_{timestamp}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()

        return f"knowledge_{hash_value[:12]}"


def create_real_time_knowledge_updater(
    config: Dict[str, Any]
) -> RealTimeKnowledgeUpdater:
    """创建实时知识更新器实例

    Args:
        config: 配置字典

    Returns:
        实时知识更新器实例
    """
    return RealTimeKnowledgeUpdater(config)
