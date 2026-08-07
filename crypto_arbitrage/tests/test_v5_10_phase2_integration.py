"""V5.10 Phase 2 - 端到端集成测试

测试memo0驱动决策系统的完整流程。
"""

import pytest
import asyncio
from datetime import datetime
from storage.memo0_driven_decision_system import (
    Memo0DrivenDecisionSystem,
    DecisionRequest,
    DecisionResponse,
    SystemStatus,
    create_decision_system,
    quick_decision
)
from storage.modules import OutcomeType


@pytest.fixture
async def decision_system():
    """创建决策系统实例"""
    config = {
        'decision_maker_config': {
            'min_relevance': 0.5,
            'max_matches': 10,
            'confidence_threshold': 0.6
        },
        'updater_config': {
            'monitor_interval': 1.0,
            'data_buffer_size': 100
        },
        'calculator_config': {
            'risk_tolerance': 0.5
        },
        'feedback_config': {}
    }

    system = await create_decision_system(config, auto_start=False)
    yield system
    await system.stop()


@pytest.fixture
def sample_decision_request():
    """创建样本决策请求"""
    return DecisionRequest(
        request_id="test_request_001",
        market_data={
            "symbol": "BTC/USDT",
            "trend": "bullish",
            "price": 65000.0,
            "volume": 100.0,
            "volatility": 0.02
        },
        trading_parameters={
            "strategy": "trend_following",
            "amount": 1.0,
            "timeframe": "1h"
        },
        risk_profile={
            "level": "medium",
            "max_loss": 0.05
        },
        time_constraints={
            "max_execution_time": 10.0
        }
    )


class TestDecisionSystemIntegration:
    """测试决策系统集成"""

    @pytest.mark.asyncio
    async def test_system_initialization(self, decision_system):
        """测试系统初始化"""
        assert decision_system.status == SystemStatus.INITIALIZING
        assert decision_system.decision_maker is not None
        assert decision_system.knowledge_updater is not None
        assert decision_system.confidence_calculator is not None
        assert decision_system.feedback_loop is not None

    @pytest.mark.asyncio
    async def test_system_start_stop(self, decision_system):
        """测试系统启动和停止"""
        # 启动系统
        await decision_system.start()
        assert decision_system.status == SystemStatus.RUNNING

        # 停止系统
        await decision_system.stop()
        assert decision_system.status == SystemStatus.STOPPED

    @pytest.mark.asyncio
    async def test_full_decision_flow(self, decision_system, sample_decision_request):
        """测试完整决策流程"""
        await decision_system.start()

        # 添加一些初始知识
        await decision_system.add_knowledge(
            content="BTC/USDT 在牛市中表现良好",
            metadata={
                "category": "market_pattern",
                "symbol": "BTC/USDT"
            }
        )

        await decision_system.add_knowledge(
            content="趋势跟随策略适合上升趋势",
            metadata={
                "category": "strategy",
                "strategy": "trend_following"
            }
        )

        # 制定决策
        response = await decision_system.make_decision(sample_decision_request)

        # 验证响应
        assert isinstance(response, DecisionResponse)
        assert response.request_id == "test_request_001"
        assert response.decision is not None
        assert response.confidence_report is not None
        assert response.processing_time > 0
        assert response.system_status == SystemStatus.RUNNING

        # 验证决策
        assert response.decision.decision_id.startswith("decision_")
        assert response.decision.confidence > 0
        assert response.decision.rationale is not None

        await decision_system.stop()

    @pytest.mark.asyncio
    async def test_knowledge_base_operations(self, decision_system):
        """测试知识库操作"""
        # 添加知识
        knowledge_id_1 = await decision_system.add_knowledge(
            content="测试知识1",
            metadata={"category": "test"}
        )
        assert knowledge_id_1.startswith("knowledge_")

        knowledge_id_2 = await decision_system.add_knowledge(
            content="测试知识2",
            metadata={"category": "test"}
        )
        assert knowledge_id_2.startswith("knowledge_")

        # 验证知识库大小
        assert len(decision_system.knowledge_base) >= 2

        # 获取知识库摘要
        summary = await decision_system.get_knowledge_base_summary()
        assert summary["total_knowledge"] >= 2

    @pytest.mark.asyncio
    async def test_decision_outcome_recording(self, decision_system, sample_decision_request):
        """测试决策结果记录"""
        await decision_system.start()

        # 制定决策
        response = await decision_system.make_decision(sample_decision_request)
        decision_id = response.decision.decision_id

        # 记录决策结果
        await decision_system.record_outcome(
            decision_id=decision_id,
            outcome_type=OutcomeType.SUCCESS,
            actual_return=0.05,
            actual_risk=0.02,
            execution_time=10.0,
            market_conditions={
                "trend": "bullish",
                "volatility": 0.02
            }
        )

        # 验证反馈循环统计
        feedback_stats = decision_system.feedback_loop.get_statistics()
        assert feedback_stats["total_outcomes"] > 0

        await decision_system.stop()

    @pytest.mark.asyncio
    async def test_system_metrics(self, decision_system, sample_decision_request):
        """测试系统指标"""
        await decision_system.start()

        # 添加知识并制定决策
        await decision_system.add_knowledge(
            content="测试知识",
            metadata={"category": "test"}
        )

        await decision_system.make_decision(sample_decision_request)

        # 获取系统指标
        metrics = await decision_system.get_system_metrics()

        assert metrics.total_decisions >= 1
        assert metrics.knowledge_base_size >= 1
        assert metrics.system_health > 0
        assert metrics.timestamp is not None

        await decision_system.stop()

    @pytest.mark.asyncio
    async def test_system_report_generation(self, decision_system):
        """测试系统报告生成"""
        await decision_system.start()

        # 生成系统报告
        report = await decision_system.generate_system_report()

        # 验证报告内容
        assert "system_status" in report
        assert "metrics" in report
        assert "decision_maker" in report
        assert "knowledge_updater" in report
        assert "confidence_calculator" in report
        assert "feedback_loop" in report
        assert "knowledge_base" in report
        assert "generated_at" in report

        await decision_system.stop()

    @pytest.mark.asyncio
    async def test_decision_history(self, decision_system, sample_decision_request):
        """测试决策历史"""
        await decision_system.start()

        # 制定多个决策
        for i in range(3):
            await decision_system.make_decision(sample_decision_request)

        # 获取决策历史
        history = await decision_system.get_decision_history(limit=2)

        assert len(history) == 2
        assert all(decision.decision is not None for decision in history)

        await decision_system.stop()

    @pytest.mark.asyncio
    async def test_knowledge_base_optimization(self, decision_system):
        """测试知识库优化"""
        # 添加一些知识
        await decision_system.add_knowledge(
            content="低质量知识",
            metadata={"category": "test", "quality": "low"}
        )

        await decision_system.add_knowledge(
            content="高质量知识",
            metadata={"category": "test", "quality": "high"}
        )

        # 优化知识库
        optimization_result = await decision_system.optimize_knowledge_base()

        # 验证优化结果
        assert "status" in optimization_result

    @pytest.mark.asyncio
    async def test_confidence_report_generation(self, decision_system, sample_decision_request):
        """测试置信度报告生成"""
        await decision_system.start()

        # 添加知识
        await decision_system.add_knowledge(
            content="测试知识",
            metadata={"category": "test"}
        )

        # 制定决策
        response = await decision_system.make_decision(sample_decision_request)

        # 验证置信度报告
        confidence_report = response.confidence_report
        assert confidence_report.confidence_score is not None
        assert confidence_report.factor_analyses is not None
        assert confidence_report.generated_at is not None

        await decision_system.stop()


class TestDecisionRequestAndResponse:
    """测试决策请求和响应"""

    def test_decision_request_creation(self, sample_decision_request):
        """测试决策请求创建"""
        assert sample_decision_request.request_id == "test_request_001"
        assert sample_decision_request.market_data["symbol"] == "BTC/USDT"
        assert sample_decision_request.trading_parameters["strategy"] == "trend_following"
        assert sample_decision_request.risk_profile["level"] == "medium"

    def test_decision_response_structure(self, decision_system):
        """测试决策响应结构"""
        # 模拟响应
        from storage.modules import Decision, DecisionRationale

        decision = Decision(
            decision_id="test_decision_001",
            decision_type="trade",
            action="buy",
            parameters={"amount": 1.0},
            rationale=DecisionRationale(
                primary_reason="测试理由",
                supporting_reasons=["支持理由"],
                knowledge_sources=["knowledge_001"],
                confidence_factors={"test": 0.8},
                reasoning_chain=["步骤1", "步骤2"],
                limitations=["局限性"]
            ),
            confidence=0.8,
            knowledge_matches=[],
            context=sample_decision_request,
            created_at=datetime.now()
        )

        response = DecisionResponse(
            request_id="test_request_001",
            decision=decision,
            confidence_report=None,
            processing_time=0.5,
            system_status=SystemStatus.RUNNING,
            timestamp=datetime.now()
        )

        assert response.request_id == "test_request_001"
        assert response.decision.decision_id == "test_decision_001"
        assert response.processing_time == 0.5
        assert response.system_status == SystemStatus.RUNNING


class TestQuickDecisionFunction:
    """测试快速决策函数"""

    @pytest.mark.asyncio
    async def test_quick_decision(self):
        """测试快速决策函数"""
        response = await quick_decision(
            market_data={
                "symbol": "BTC/USDT",
                "trend": "bullish",
                "price": 65000.0,
                "volume": 100.0
            },
            trading_parameters={
                "strategy": "trend_following",
                "amount": 1.0
            },
            risk_profile={
                "level": "medium",
                "max_loss": 0.05
            }
        )

        assert response.decision is not None
        assert response.confidence_report is not None
        assert response.processing_time > 0


class TestSystemStatus:
    """测试系统状态"""

    def test_system_status_values(self):
        """测试系统状态值"""
        assert SystemStatus.INITIALIZING.value == "initializing"
        assert SystemStatus.RUNNING.value == "running"
        assert SystemStatus.PAUSED.value == "paused"
        assert SystemStatus.STOPPING.value == "stopping"
        assert SystemStatus.STOPPED.value == "stopped"
        assert SystemStatus.ERROR.value == "error"


class TestSystemHealthCalculation:
    """测试系统健康度计算"""

    @pytest.mark.asyncio
    async def test_health_with_all_modules(self, decision_system):
        """测试所有模块存在时的健康度"""
        await decision_system.start()
        await decision_system.add_knowledge(
            content="测试知识",
            metadata={"category": "test"}
        )

        health = decision_system._calculate_system_health()

        assert 0 <= health <= 1
        assert health > 0.5  # 应该有较高健康度

        await decision_system.stop()

    @pytest.mark.asyncio
    async def test_health_with_missing_modules(self, decision_system):
        """测试缺少模块时的健康度"""
        # 移除一些模块
        decision_system.decision_maker = None

        health = decision_system._calculate_system_health()

        assert health < 0.5  # 应该有较低健康度

    @pytest.mark.asyncio
    async def test_health_with_empty_knowledge_base(self, decision_system):
        """测试空知识库时的健康度"""
        decision_system.knowledge_base = {}

        health = decision_system._calculate_system_health()

        assert health < 1.0  # 应该略微降低健康度


class TestConcurrentOperations:
    """测试并发操作"""

    @pytest.mark.asyncio
    async def test_concurrent_decision_making(self, decision_system):
        """测试并发决策制定"""
        await decision_system.start()

        # 添加知识
        await decision_system.add_knowledge(
            content="测试知识",
            metadata={"category": "test"}
        )

        # 创建多个决策请求
        requests = [
            DecisionRequest(
                request_id=f"request_{i}",
                market_data={"symbol": "BTC/USDT", "trend": "bullish"},
                trading_parameters={"strategy": "trend_following"},
                risk_profile={"level": "medium"},
                time_constraints={}
            )
            for i in range(5)
        ]

        # 并发执行决策
        responses = await asyncio.gather(*[
            decision_system.make_decision(req) for req in requests
        ])

        assert len(responses) == 5
        assert all(resp.decision is not None for resp in responses)

        await decision_system.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
