"""图谱动态更新机制 V15.9 Phase 3

动态更新知识图谱,保持知识时效性和准确性。

核心功能：
1. 知识添加 - 将新知识添加到图谱
2. 知识更新 - 更新现有知识
3. 知识删除 - 删除过期或低质量知识
4. 关系维护 - 维护知识之间的关系
5. 更新调度 - 智能的更新调度策略

性能目标：
- 更新延迟 < 1秒
- 更新吞吐量 > 100条/秒
- 图谱一致性 > 99%
- 时效性 > 95%

创建时间：2026-05-01 05:16
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import statistics
import time
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class UpdatePriority(Enum):
    """更新优先级"""
    HIGH = "high"  # 高优先级（立即更新）
    MEDIUM = "medium"  # 中优先级（10秒内更新）
    LOW = "low"  # 低优先级（1分钟内更新）


class UpdateStatus(Enum):
    """更新状态"""
    PENDING = "pending"  # 等待更新
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


@dataclass
class UpdateTask:
    """更新任务"""
    task_id: str
    knowledge_data: Dict[str, Any]
    priority: UpdatePriority
    status: UpdateStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "knowledge_data": self.knowledge_data,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message
        }


@dataclass
class UpdateMetrics:
    """更新指标"""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    avg_update_time_ms: float = 0.0
    graph_consistency_score: float = 0.0
    knowledge_freshness_score: float = 0.0

    def success_rate(self) -> float:
        """成功率"""
        if self.total_updates == 0:
            return 0.0
        return self.successful_updates / self.total_updates


class GraphDynamicUpdater:
    """图谱动态更新器

    管理知识图谱的动态更新。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化图谱动态更新器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 更新队列
        self.update_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

        # 任务管理
        self.tasks: Dict[str, UpdateTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # 更新统计
        self.metrics = UpdateMetrics()
        self.update_times: List[float] = []

        # 时效性管理
        self.knowledge_expiry_time = self.config.get("knowledge_expiry_time", 3600)  # 1小时

        # 质量阈值
        self.min_confidence_threshold = self.config.get("min_confidence_threshold", 0.6)

        logger.info("图谱动态更新器初始化完成")

    async def start(self) -> None:
        """启动更新器"""
        logger.info("启动图谱动态更新器")

        # 启动更新处理任务
        for i in range(3):  # 3个并发处理任务
            asyncio.create_task(self._process_updates())

    async def stop(self) -> None:
        """停止更新器"""
        logger.info("停止图谱动态更新器")

        # 等待所有任务完成
        for task in self.running_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def add_update_task(
        self,
        knowledge_data: Dict[str, Any],
        priority: UpdatePriority = UpdatePriority.MEDIUM
    ) -> str:
        """添加更新任务

        Args:
            knowledge_data: 知识数据
            priority: 更新优先级

        Returns:
            任务ID
        """
        task_id = f"update_{int(time.time() * 1000)}"

        task = UpdateTask(
            task_id=task_id,
            knowledge_data=knowledge_data,
            priority=priority,
            status=UpdateStatus.PENDING,
            created_at=time.time()
        )

        self.tasks[task_id] = task

        # 根据优先级确定延迟
        delay = self._get_priority_delay(priority)

        # 延迟执行任务
        asyncio.create_task(self._schedule_update(task_id, delay))

        logger.info(f"添加更新任务: {task_id} (优先级: {priority.value})")

        return task_id

    def _get_priority_delay(self, priority: UpdatePriority) -> float:
        """获取优先级对应的延迟

        Args:
            priority: 优先级

        Returns:
            延迟（秒）
        """
        if priority == UpdatePriority.HIGH:
            return 0.0  # 立即执行
        elif priority == UpdatePriority.MEDIUM:
            return 10.0  # 10秒
        else:
            return 60.0  # 1分钟

    async def _schedule_update(self, task_id: str, delay: float) -> None:
        """调度更新任务

        Args:
            task_id: 任务ID
            delay: 延迟（秒）
        """
        await asyncio.sleep(delay)

        task = self.tasks.get(task_id)
        if not task or task.status != UpdateStatus.PENDING:
            return

        try:
            await self.update_queue.put(task_id)
            logger.info(f"任务 {task_id} 已加入处理队列")
        except asyncio.QueueFull:
            logger.error(f"更新队列已满，任务 {task_id} 被丢弃")
            if task_id in self.tasks:
                self.tasks[task_id].status = UpdateStatus.FAILED
                self.tasks[task_id].error_message = "队列已满"

    async def _process_updates(self) -> None:
        """处理更新任务"""
        logger.info("启动更新处理任务")

        while True:
            try:
                # 从队列获取任务ID
                task_id = await asyncio.wait_for(
                    self.update_queue.get(),
                    timeout=1.0
                )

                task = self.tasks.get(task_id)
                if not task:
                    continue

                # 处理任务
                await self._execute_update(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"更新处理异常: {e}")

    async def _execute_update(self, task: UpdateTask) -> None:
        """执行更新

        Args:
            task: 更新任务
        """
        task.status = UpdateStatus.PROCESSING
        task.started_at = time.time()

        self.metrics.total_updates += 1
        start_time = time.time()

        try:
            # 验证知识质量
            if not self._validate_knowledge(task.knowledge_data):
                raise ValueError("知识质量不符合要求")

            # 执行更新
            success = await self._update_knowledge_graph(task.knowledge_data)

            if success:
                task.status = UpdateStatus.COMPLETED
                task.completed_at = time.time()
                self.metrics.successful_updates += 1

                # 计算更新时间
                update_time = (task.completed_at - start_time) * 1000
                self.update_times.append(update_time)

                logger.info(f"更新任务 {task.task_id} 完成")
            else:
                raise Exception("图谱更新失败")

        except Exception as e:
            task.status = UpdateStatus.FAILED
            task.completed_at = time.time()
            task.error_message = str(e)

            self.metrics.failed_updates += 1
            logger.error(f"更新任务 {task.task_id} 失败: {e}")

    def _validate_knowledge(self, knowledge_data: Dict[str, Any]) -> bool:
        """验证知识质量

        Args:
            knowledge_data: 知识数据

        Returns:
            是否有效
        """
        # 检查置信度
        confidence = knowledge_data.get("confidence", 0.0)
        if confidence < self.min_confidence_threshold:
            logger.warning(f"知识置信度过低: {confidence}")
            return False

        # 检查内容
        content = knowledge_data.get("content", "")
        if not content:
            logger.warning("知识内容为空")
            return False

        # 检查类型
        knowledge_type = knowledge_data.get("knowledge_type")
        if not knowledge_type:
            logger.warning("知识类型为空")
            return False

        return True

    async def _update_knowledge_graph(self, knowledge_data: Dict[str, Any]) -> bool:
        """更新知识图谱

        Args:
            knowledge_data: 知识数据

        Returns:
            是否成功
        """
        try:
            # 这里应该调用知识图谱更新API
            # 由于没有实际的图谱实现，我们模拟更新

            knowledge_id = knowledge_data.get("knowledge_id")
            knowledge_type = knowledge_data.get("knowledge_type")
            content = knowledge_data.get("content")

            # 模拟图谱更新延迟
            await asyncio.sleep(0.1)

            logger.info(f"更新知识图谱: {knowledge_type} - {content[:50]}...")

            return True

        except Exception as e:
            logger.error(f"图谱更新失败: {e}")
            return False

    async def cleanup_expired_knowledge(self) -> int:
        """清理过期知识

        Returns:
            清理的知识数量
        """
        logger.info("开始清理过期知识")

        cleaned_count = 0
        current_time = time.time()

        # 这里应该查询知识图谱，删除过期知识
        # 由于没有实际的图谱实现，我们模拟清理

        # 模拟清理100条过期知识
        cleaned_count = 100

        logger.info(f"清理了 {cleaned_count} 条过期知识")

        return cleaned_count

    async def consolidate_knowledge(self) -> int:
        """合并相似知识

        Returns:
            合并的知识数量
        """
        logger.info("开始合并相似知识")

        consolidated_count = 0

        # 这里应该查询知识图谱，合并相似知识
        # 由于没有实际的图谱实现，我们模拟合并

        # 模拟合并50条相似知识
        consolidated_count = 50

        logger.info(f"合并了 {consolidated_count} 条相似知识")

        return consolidated_count

    def get_metrics(self) -> UpdateMetrics:
        """获取更新指标

        Returns:
            更新指标
        """
        # 计算平均更新时间
        if self.update_times:
            self.metrics.avg_update_time_ms = statistics.mean(self.update_times)

        # 计算图谱一致性分数
        self.metrics.graph_consistency_score = self._calculate_consistency_score()

        # 计算知识时效性分数
        self.metrics.knowledge_freshness_score = self._calculate_freshness_score()

        return self.metrics

    def _calculate_consistency_score(self) -> float:
        """计算图谱一致性分数

        Returns:
            一致性分数 (0.0 - 1.0)
        """
        # 基于成功率计算
        if self.metrics.total_updates == 0:
            return 1.0

        success_rate = self.metrics.successful_updates / self.metrics.total_updates

        # 考虑失败率的影响
        consistency_score = success_rate * 0.9 + 0.1  # 至少0.1

        return consistency_score

    def _calculate_freshness_score(self) -> float:
        """计算知识时效性分数

        Returns:
            时效性分数 (0.0 - 1.0)
        """
        # 基于最近更新频率计算
        if not self.update_times:
            return 1.0

        # 计算最近1小时的更新次数
        recent_updates = sum(
            1 for t in self.update_times
            if (time.time() - t) < 3600
        )

        # 时效性分数基于更新频率
        if recent_updates >= 10:
            return 1.0
        elif recent_updates >= 5:
            return 0.8
        elif recent_updates >= 1:
            return 0.6
        else:
            return 0.4

    def reset_metrics(self) -> None:
        """重置更新指标"""
        self.metrics = UpdateMetrics()
        self.update_times.clear()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        return task.to_dict()


async def main():
    """主函数 - 测试图谱动态更新器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建图谱动态更新器
    updater = GraphDynamicUpdater()

    # 启动更新器
    await updater.start()

    # 测试数据
    test_knowledges = [
        {
            "knowledge_id": "test_001",
            "knowledge_type": "market_pattern",
            "content": "BTC/USDT 上升趋势，创新高",
            "confidence": 0.85,
            "evidence": ["价格连续上涨"]
        },
        {
            "knowledge_id": "test_002",
            "knowledge_type": "volatility_pattern",
            "content": "ETH/USDT 低波动率（<1%），适合套利",
            "confidence": 0.78,
            "evidence": ["波动率计算结果"]
        },
        {
            "knowledge_id": "test_003",
            "knowledge_type": "arbitrage_opportunity",
            "content": "Binance 和 Okex 之间存在套利机会",
            "confidence": 0.72,
            "evidence": ["价差分析"]
        }
    ]

    # 添加更新任务
    print("\n=== 添加更新任务 ===")
    task_ids = []

    for i, knowledge in enumerate(test_knowledges):
        priority = UpdatePriority.HIGH if i == 0 else UpdatePriority.MEDIUM
        task_id = await updater.add_update_task(knowledge, priority)
        task_ids.append(task_id)
        print(f"添加任务 {i+1}: {task_id}")

    # 等待任务完成
    print("\n=== 等待任务完成 ===")
    await asyncio.sleep(15)  # 等待15秒

    # 显示任务状态
    print("\n=== 任务状态 ===")
    for task_id in task_ids:
        status = updater.get_task_status(task_id)
        if status:
            print(f"任务 {task_id}: {status['status']}")
            if status['status'] == 'completed':
                print(f"  更新时间: {(status['completed_at'] - status['started_at'])*1000:.2f}ms")

    # 显示更新指标
    metrics = updater.get_metrics()
    print(f"\n=== 更新指标 ===")
    print(f"总更新数: {metrics.total_updates}")
    print(f"成功更新: {metrics.successful_updates}")
    print(f"失败更新: {metrics.failed_updates}")
    print(f"成功率: {metrics.success_rate()*100:.2f}%")
    print(f"平均更新时间: {metrics.avg_update_time_ms:.2f}ms")
    print(f"图谱一致性: {metrics.graph_consistency_score*100:.2f}%")
    print(f"知识时效性: {metrics.knowledge_freshness_score*100:.2f}%")

    # 停止更新器
    await updater.stop()


if __name__ == "__main__":
    asyncio.run(main())
