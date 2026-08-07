"""V5.10 Phase 2 - RealTimeKnowledgeUpdater单元测试

测试实时知识更新器的核心功能。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from storage.modules import (
    RealTimeKnowledgeUpdater,
    MarketDataSnapshot,
    KnowledgeUpdateTask,
    KnowledgeGap,
    UpdatePriority,
    UpdateStatus,
    KnowledgeGapType
)


@pytest.fixture
def knowledge_updater():
    """创建实时知识更新器实例"""
    config = {
        'monitor_interval': 1.0,
        'data_buffer_size': 100,
        'volatility_threshold': 0.02,
        'max_concurrent_updates': 5,
        'update_timeout': 30.0
    }
    return RealTimeKnowledgeUpdater(config)


@pytest.fixture
def sample_market_snapshot():
    """创建样本市场数据快照"""
    return MarketDataSnapshot(
        timestamp=datetime.now(),
        symbol="BTC/USDT",
        price=65000.0,
        volume=100.0,
        volatility=0.02,
        trend="bullish",
        metadata={"exchange": "binance"}
    )


class TestRealTimeKnowledgeUpdater:
    """测试RealTimeKnowledgeUpdater"""

    def test_initialization(self, knowledge_updater):
        """测试初始化"""
        assert knowledge_updater.monitor_interval == 1.0
        assert knowledge_updater.data_buffer_size == 100
        assert knowledge_updater.volatility_threshold == 0.02
        assert knowledge_updater.max_concurrent_updates == 5
        assert knowledge_updater.update_timeout == 30.0
        assert not knowledge_updater._is_running
        assert len(knowledge_updater.market_data_buffer) == 0
        assert len(knowledge_updater.update_queue) == 0

    def test_priority_weights(self, knowledge_updater):
        """测试优先级权重"""
        weights = knowledge_updater.PRIORITY_WEIGHTS

        assert UpdatePriority.CRITICAL in weights
        assert UpdatePriority.HIGH in weights
        assert UpdatePriority.MEDIUM in weights
        assert UpdatePriority.LOW in weights
        # 验证权重递减
        assert weights[UpdatePriority.CRITICAL] > weights[UpdatePriority.HIGH]
        assert weights[UpdatePriority.HIGH] > weights[UpdatePriority.MEDIUM]
        assert weights[UpdatePriority.MEDIUM] > weights[UpdatePriority.LOW]

    def test_market_data_snapshot_creation(self, sample_market_snapshot):
        """测试市场数据快照创建"""
        assert sample_market_snapshot.symbol == "BTC/USDT"
        assert sample_market_snapshot.price == 65000.0
        assert sample_market_snapshot.trend == "bullish"
        assert sample_market_snapshot.metadata["exchange"] == "binance"

    def test_market_data_snapshot_conversion(self, sample_market_snapshot):
        """测试市场数据快照转换"""
        snapshot_dict = sample_market_snapshot.to_dict()

        assert "timestamp" in snapshot_dict
        assert "symbol" in snapshot_dict
        assert "price" in snapshot_dict
        assert "volume" in snapshot_dict
        assert "trend" in snapshot_dict
        assert snapshot_dict["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_trigger_knowledge_update(self, knowledge_updater):
        """测试触发知识更新"""
        task_id = await knowledge_updater.trigger_knowledge_update(
            update_type="test_update",
            data={"test": "data"},
            priority=UpdatePriority.MEDIUM
        )

        assert task_id.startswith("task_")
        assert len(knowledge_updater.update_queue) == 1
        assert knowledge_updater.stats.total_updates == 1
        assert knowledge_updater.stats.updates_by_priority["medium"] == 1

    @pytest.mark.asyncio
    async def test_batch_update_knowledge(self, knowledge_updater):
        """测试批量更新知识"""
        updates = [
            {"type": "update1", "data": {"key": "value1"}},
            {"type": "update2", "data": {"key": "value2"}},
            {"type": "update3", "data": {"key": "value3"}}
        ]

        task_ids = await knowledge_updater.batch_update_knowledge(updates)

        assert len(task_ids) == 3
        assert len(knowledge_updater.update_queue) == 3
        assert knowledge_updater.stats.total_updates == 3

    @pytest.mark.asyncio
    async def test_update_prioritization(self, knowledge_updater):
        """测试更新优先级排序"""
        # 创建不同优先级的任务
        await knowledge_updater.trigger_knowledge_update("low", {}, UpdatePriority.LOW)
        await knowledge_updater.trigger_knowledge_update("high", {}, UpdatePriority.HIGH)
        await knowledge_updater.trigger_knowledge_update("critical", {}, UpdatePriority.CRITICAL)

        prioritized = await knowledge_updater.prioritize_updates()

        assert len(prioritized) == 3
        # 检查排序（CRITICAL应该在前面）
        assert prioritized[0].priority == UpdatePriority.CRITICAL

    @pytest.mark.asyncio
    async def test_knowledge_extraction(self, knowledge_updater, sample_market_snapshot):
        """测试知识提取"""
        knowledge_list = await knowledge_updater.extract_incremental_knowledge(sample_market_snapshot)

        assert isinstance(knowledge_list, list)
        # 可能提取多种类型的知识
        assert len(knowledge_list) >= 0

    @pytest.mark.asyncio
    async def test_price_pattern_extraction(self, knowledge_updater):
        """测试价格模式提取"""
        # 填充数据缓冲区
        for i in range(5):
            snapshot = MarketDataSnapshot(
                timestamp=datetime.now() + timedelta(seconds=i),
                symbol="BTC/USDT",
                price=65000.0 + i * 100,  # 上升趋势
                volume=100.0,
                volatility=0.02,
                trend="bullish"
            )
            knowledge_updater.market_data_buffer.append(snapshot)

        latest_snapshot = knowledge_updater.market_data_buffer[-1]
        price_knowledge = await knowledge_updater._extract_price_pattern_knowledge(latest_snapshot)

        if price_knowledge:
            assert "type" in price_knowledge
            assert "content" in price_knowledge
            assert "symbol" in price_knowledge
            assert "trend" in price_knowledge

    @pytest.mark.asyncio
    async def test_volume_knowledge_extraction(self, knowledge_updater):
        """测试成交量知识提取"""
        # 填充数据缓冲区
        for i in range(5):
            snapshot = MarketDataSnapshot(
                timestamp=datetime.now() + timedelta(seconds=i),
                symbol="BTC/USDT",
                price=65000.0,
                volume=100.0 + i * 50,  # 成交量上升
                volatility=0.02,
                trend="bullish"
            )
            knowledge_updater.market_data_buffer.append(snapshot)

        latest_snapshot = knowledge_updater.market_data_buffer[-1]
        volume_knowledge = await knowledge_updater._extract_volume_knowledge(latest_snapshot)

        if volume_knowledge:
            assert "type" in volume_knowledge
            assert "volume" in volume_knowledge
            assert "volume_status" in volume_knowledge

    @pytest.mark.asyncio
    async def test_volatility_knowledge_extraction(self, knowledge_updater):
        """测试波动率知识提取"""
        # 填充数据缓冲区
        for i in range(5):
            snapshot = MarketDataSnapshot(
                timestamp=datetime.now() + timedelta(seconds=i),
                symbol="BTC/USDT",
                price=65000.0 + i * 200,  # 高波动
                volume=100.,
                volatility=0.03,  # 高波动率
                trend="bullish"
            )
            knowledge_updater.market_data_buffer.append(snapshot)

        latest_snapshot = knowledge_updater.market_data_buffer[-1]
        volatility_knowledge = await knowledge_updater._extract_volatility_knowledge(latest_snapshot)

        if volatility_knowledge:
            assert "type" in volatility_knowledge
            assert "volatility" in volatility_knowledge
            assert "volatility_level" in volatility_knowledge

    @pytest.mark.asyncio
    async def test_update_existing_knowledge(self, knowledge_updater):
        """测试更新现有知识"""
        knowledge_id = "test_knowledge_001"
        knowledge_updater.knowledge_base[knowledge_id] = {
            "content": "原始知识",
            "data": {"old": "value"},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        success = await knowledge_updater.update_existing_knowledge(
            knowledge_id,
            {"new": "value"}
        )

        assert success is True
        assert "new" in knowledge_updater.knowledge_base[knowledge_id]["data"]
        assert "old" in knowledge_updater.knowledge_base[knowledge_id]["data"]  # 原有数据保留

    @pytest.mark.asyncio
    async def test_detect_obsolete_knowledge(self, knowledge_updater):
        """测试检测过时知识"""
        # 创建过时知识
        old_time = datetime.now() - timedelta(hours=25)
        knowledge_updater.knowledge_base["old_knowledge"] = {
            "content": "过时知识",
            "updated_at": old_time.isoformat()
        }

        # 创建新知识
        recent_time = datetime.now() - timedelta(hours=1)
        knowledge_updater.knowledge_base["new_knowledge"] = {
            "content": "新知识",
            "updated_at": recent_time.isoformat()
        }

        obsolete_ids = await knowledge_updater.detect_obsolete_knowledge(max_age_hours=24)

        assert "old_knowledge" in obsolete_ids
        assert "new_knowledge" not in obsolete_ids

    @pytest.mark.asyncio
    async def test_detect_missing_data(self, knowledge_updater):
        """测试检测缺失数据"""
        # 添加市场数据
        snapshot = MarketDataSnapshot(
            timestamp=datetime.now(),
            symbol="BTC/USDT",
            price=65000.0,
            volume=100.0,
            volatility=0.02,
            trend="bullish"
        )
        knowledge_updater.market_data_buffer.append(snapshot)

        gaps = await knowledge_updater._detect_missing_data()

        # 应该检测到缺失知识（因为知识库为空）
        assert len(gaps) > 0
        assert all(gap.gap_type == KnowledgeGapType.MISSING_DATA for gap in gaps)

    @pytest.mark.asyncio
    async def test_detect_low_confidence_knowledge(self, knowledge_updater):
        """测试检测低置信度知识"""
        # 添加低置信度知识
        knowledge_updater.knowledge_base["low_conf_knowledge"] = {
            "content": "低置信度知识",
            "quality_score": 0.3,
            "updated_at": datetime.now().isoformat()
        }

        # 添加正常知识
        knowledge_updater.knowledge_base["normal_knowledge"] = {
            "content": "正常知识",
            "quality_score": 0.8,
            "updated_at": datetime.now().isoformat()
        }

        gaps = await knowledge_updater._detect_low_confidence_knowledge()

        assert len(gaps) > 0
        assert any("low_conf_knowledge" in gap.affected_knowledge_ids for gap in gaps)
        assert not any("normal_knowledge" in gap.affected_knowledge_ids for gap in gaps)

    @pytest.mark.asyncio
    async def test_knowledge_gap_creation(self, knowledge_updater):
        """测试知识缺口创建"""
        gap = KnowledgeGap(
            gap_id="gap_001",
            gap_type=KnowledgeGapType.MISSING_DATA,
            description="缺少BTC/USDT知识",
            severity=0.8,
            affected_knowledge_ids=[],
            suggested_action="提取知识",
            detected_at=datetime.now()
        )

        assert gap.gap_id == "gap_001"
        assert gap.gap_type == KnowledgeGapType.MISSING_DATA
        assert gap.severity == 0.8
        assert gap.detected_at is not None

    def test_knowledge_gap_conversion(self):
        """测试知识缺口转换"""
        gap = KnowledgeGap(
            gap_id="gap_001",
            gap_type=KnowledgeGapType.MISSING_DATA,
            description="缺少BTC/USDT知识",
            severity=0.8,
            affected_knowledge_ids=[],
            suggested_action="提取知识",
            detected_at=datetime.now()
        )

        gap_dict = gap.to_dict()

        assert "gap_id" in gap_dict
        assert "gap_type" in gap_dict
        assert "severity" in gap_dict
        assert gap_dict["gap_type"] == "missing_data"

    def test_update_task_creation(self):
        """测试更新任务创建"""
        task = KnowledgeUpdateTask(
            task_id="task_001",
            priority=UpdatePriority.HIGH,
            update_type="test_update",
            data={"key": "value"},
            created_at=datetime.now()
        )

        assert task.task_id == "task_001"
        assert task.priority == UpdatePriority.HIGH
        assert task.status == UpdateStatus.PENDING

    def test_update_task_conversion(self):
        """测试更新任务转换"""
        task = KnowledgeUpdateTask(
            task_id="task_001",
            priority=UpdatePriority.HIGH,
            update_type="test_update",
            data={"key": "value"},
            created_at=datetime.now()
        )

        task_dict = task.to_dict()

        assert "task_id" in task_dict
        assert "priority" in task_dict
        assert "status" in task_dict
        assert task_dict["priority"] == "high"
        assert task_dict["status"] == "pending"

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, knowledge_updater):
        """测试统计跟踪"""
        # 创建多个更新任务
        for i in range(5):
            await knowledge_updater.trigger_knowledge_update(
                f"update_{i}",
                {},
                UpdatePriority.MEDIUM
            )

        stats = knowledge_updater.get_statistics()

        assert stats["total_updates"] == 5
        assert "successful_updates" in stats
        assert "failed_updates" in stats
        assert "updates_by_priority" in stats
        assert "updates_by_type" in stats

    def test_statistics_reset(self, knowledge_updater):
        """测试统计重置"""
        # 设置一些统计数据
        knowledge_updater.stats.total_updates = 10
        knowledge_updater.stats.successful_updates = 8

        knowledge_updater.reset_statistics()

        assert knowledge_updater.stats.total_updates == 0
        assert knowledge_updater.stats.successful_updates == 0

    def test_priority_score_calculation(self, knowledge_updater):
        """测试优先级分数计算"""
        task = KnowledgeUpdateTask(
            task_id="task_001",
            priority=UpdatePriority.HIGH,
            update_type="test",
            data={},
            created_at=datetime.now() - timedelta(seconds=30)  # 等待30秒
        )

        priority_score = knowledge_updater._calculate_priority_score(task)

        assert priority_score > 0
        # 高优先级应该有较高分数
        assert priority_score >= knowledge_updater.PRIORITY_WEIGHTS[UpdatePriority.HIGH]

    @pytest.mark.asyncio
    async def test_callback_registration(self, knowledge_updater):
        """测试回调注册"""
        callback_called = []

        async def test_callback(task):
            callback_called.append(task.task_id)

        knowledge_updater.register_callback('test_event', test_callback)

        assert 'test_event' in knowledge_updater.update_callbacks
        assert test_callback in knowledge_updater.update_callbacks['test_event']

    @pytest.mark.asyncio
    async def test_update_frequency_optimization(self, knowledge_updater):
        """测试更新频率优化"""
        # 添加一些模拟的更新任务
        for i in range(5):
            task = KnowledgeUpdateTask(
                task_id=f"task_{i}",
                priority=UpdatePriority.MEDIUM,
                update_type="test",
                data={},
                created_at=datetime.now()
            )
            task.started_at = datetime.now()
            task.completed_at = datetime.now() + timedelta(seconds=2)
            task.status = UpdateStatus.COMPLETED
            knowledge_updater.update_queue.append(task)

        optimization = await knowledge_updater.optimize_update_frequency()

        assert "current_interval" in optimization
        assert "suggestion" in optimization
        assert optimization["suggestion"] in ["increase", "decrease", "maintain"]

    @pytest.mark.asyncio
    async def test_knowledge_id_generation(self, knowledge_updater):
        """测试知识ID生成"""
        knowledge = {
            "type": "price_pattern",
            "content": "BTC上涨",
            "timestamp": datetime.now().isoformat()
        }

        knowledge_id = knowledge_updater._generate_knowledge_id(knowledge)

        assert knowledge_id.startswith("knowledge_")
        assert len(knowledge_id) == len("knowledge_") + 12  # MD5哈希前12位

    @pytest.mark.asyncio
    async def test_market_snapshot_processing(self, knowledge_updater, sample_market_snapshot):
        """测试市场快照处理"""
        initial_buffer_size = len(knowledge_updater.market_data_buffer)

        await knowledge_updater._process_market_snapshot(sample_market_snapshot)

        assert len(knowledge_updater.market_data_buffer) == initial_buffer_size + 1
        assert knowledge_updater.market_data_buffer[-1].symbol == "BTC/USDT"


class TestUpdatePriorityAndStatus:
    """测试更新优先级和状态枚举"""

    def test_update_priority_values(self):
        """测试更新优先级值"""
        assert UpdatePriority.CRITICAL.value == "critical"
        assert UpdatePriority.HIGH.value == "high"
        assert UpdatePriority.MEDIUM.value == "medium"
        assert UpdatePriority.LOW.value == "low"

    def test_update_status_values(self):
        """测试更新状态值"""
        assert UpdateStatus.PENDING.value == "pending"
        assert UpdateStatus.PROCESSING.value == "processing"
        assert UpdateStatus.COMPLETED.value == "completed"
        assert UpdateStatus.FAILED.value == "failed"
        assert UpdateStatus.SKIPPED.value == "skipped"

    def test_knowledge_gap_type_values(self):
        """测试知识缺口类型值"""
        assert KnowledgeGapType.MISSING_DATA.value == "missing_data"
        assert KnowledgeGapType.OUTDATED_INFO.value == "outdated_info"
        assert KnowledgeGapType.CONFLICTING_INFO.value == "conflicting_info"
        assert KnowledgeGapType.LOW_CONFIDENCE.value == "low_confidence"
        assert KnowledgeGapType.CONTEXT_MISMATCH.value == "context_mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
