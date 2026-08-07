"""V5.10 Phase 2 - KnowledgeBasedDecisionMaker单元测试

测试基于知识的决策制定器的核心功能。
"""

import pytest
import asyncio
from datetime import datetime
from storage.modules import (
    KnowledgeBasedDecisionMaker,
    DecisionContext,
    DecisionType,
    KnowledgeRelevance,
    Decision,
    KnowledgeMatch
)


@pytest.fixture
def decision_maker():
    """创建决策制定器实例"""
    config = {
        'min_relevance': 0.5,
        'max_matches': 10,
        'confidence_threshold': 0.6
    }
    return KnowledgeBasedDecisionMaker(config)


@pytest.fixture
def sample_knowledge():
    """创建样本知识库"""
    return {
        "knowledge_001": {
            "content": "BTC/USDT 在牛市中表现良好",
            "metadata": {
                "category": "market_pattern",
                "symbol": "BTC/USDT"
            },
            "quality_score": 0.8,
            "value_score": 0.7,
            "confidence": 0.75
        },
        "knowledge_002": {
            "content": "ETH/USDT 在高波动率时谨慎交易",
            "metadata": {
                "category": "risk_management",
                "symbol": "ETH/USDT"
            },
            "quality_score": 0.7,
            "value_score": 0.8,
            "confidence": 0.7
        },
        "knowledge_003": {
            "content": "趋势跟随策略适合上升趋势市场",
            "metadata": {
                "category": "strategy",
                "strategy": "trend_following"
            },
            "quality_score": 0.9,
            "value_score": 0.85,
            "confidence": 0.85
        }
    }


@pytest.fixture
def sample_context():
    """创建样本决策上下文"""
    return DecisionContext(
        market_data={
            "symbol": "BTC/USDT",
            "trend": "bullish",
            "price": 65000.0,
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


class TestKnowledgeBasedDecisionMaker:
    """测试KnowledgeBasedDecisionMaker"""

    def test_initialization(self, decision_maker):
        """测试初始化"""
        assert decision_maker.min_relevance == 0.5
        assert decision_maker.max_matches == 10
        assert decision_maker.confidence_threshold == 0.6
        assert decision_maker.decision_history == []
        assert decision_maker.decision_stats["total_decisions"] == 0

    def test_knowledge_base_injection(self, decision_maker, sample_knowledge):
        """测试知识库注入"""
        decision_maker.knowledge_base = sample_knowledge
        assert len(decision_maker.knowledge_base) == 3
        assert "knowledge_001" in decision_maker.knowledge_base
        assert decision_maker.knowledge_base["knowledge_001"]["content"] == "BTC/USDT 在牛市中表现良好"

    @pytest.mark.asyncio
    async def test_retrieve_relevant_knowledge(self, decision_maker, sample_knowledge, sample_context):
        """测试相关知识检索"""
        decision_maker.knowledge_base = sample_knowledge

        matches = await decision_maker.retrieve_relevant_knowledge(sample_context)

        assert isinstance(matches, list)
        assert len(matches) > 0
        assert all(isinstance(match, KnowledgeMatch) for match in matches)
        assert all(match.relevance_score >= decision_maker.min_relevance for match in matches)

    @pytest.mark.asyncio
    async def test_retrieve_with_limit(self, decision_maker, sample_knowledge, sample_context):
        """测试带限制的知识检索"""
        decision_maker.knowledge_base = sample_knowledge
        decision_maker.max_matches = 2

        matches = await decision_maker.retrieve_relevant_knowledge(sample_context, limit=2)

        assert len(matches) <= 2

    @pytest.mark.asyncio
    async def test_knowledge_relevance_levels(self, decision_maker, sample_knowledge, sample_context):
        """测试知识相关性等级"""
        decision_maker.knowledge_base = sample_knowledge

        matches = await decision_maker.retrieve_relevant_knowledge(sample_context)

        # 检查相关性等级
        assert all(match.relevance_level in KnowledgeRelevance for match in matches)
        # 检查相关性分数
        assert all(0 <= match.relevance_score <= 1 for match in matches)

    @pytest.mark.asyncio
    async def test_make_decision(self, decision_maker, sample_knowledge, sample_context):
        """测试制定决策"""
        decision_maker.knowledge_base = sample_knowledge

        decision = await decision_maker.make_decision(sample_context)

        assert isinstance(decision, Decision)
        assert decision.decision_id.startswith("decision_")
        assert decision.decision_type in DecisionType
        assert decision.action is not None
        assert decision.parameters is not None
        assert 0 <= decision.confidence <= 1
        assert decision.rationale is not None
        assert isinstance(decision.knowledge_matches, list)
        assert decision.created_at is not None

    @pytest.mark.asyncio
    async def test_decision_recording(self, decision_maker, sample_knowledge, sample_context):
        """测试决策记录"""
        decision_maker.knowledge_base = sample_knowledge

        initial_count = decision_maker.decision_stats["total_decisions"]

        await decision_maker.make_decision(sample_context)

        assert decision_maker.decision_stats["total_decisions"] == initial_count + 1
        assert len(decision_maker.decision_history) == 1

    @pytest.mark.asyncio
    async def test_decision_context_conversion(self, sample_context):
        """测试决策上下文转换"""
        context_dict = sample_context.to_dict()

        assert "market_data" in context_dict
        assert "trading_parameters" in context_dict
        assert "risk_profile" in context_dict
        assert "time_constraints" in context_dict
        assert context_dict["market_data"]["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_decision_confidence_calculation(self, decision_maker, sample_knowledge, sample_context):
        """测试决策置信度计算"""
        decision_maker.knowledge_base = sample_knowledge

        decision = await decision_maker.make_decision(sample_context)

        assert 0 <= decision.confidence <= 1
        # 应该有一定置信度
        assert decision.confidence > 0

    @pytest.mark.asyncio
    async def test_decision_rationale_generation(self, decision_maker, sample_knowledge, sample_context):
        """测试决策理由生成"""
        decision_maker.knowledge_base = sample_knowledge

        decision = await decision_maker.make_decision(sample_context)

        rationale = decision.rationale
        assert rationale.primary_reason is not None
        assert isinstance(rationale.supporting_reasons, list)
        assert isinstance(rationale.knowledge_sources, list)
        assert isinstance(rationale.confidence_factors, dict)
        assert isinstance(rationale.reasoning_chain, list)
        assert isinstance(rationale.limitations, list)

    @pytest.mark.asyncio
    async def test_decision_validation(self, decision_maker, sample_knowledge, sample_context):
        """测试决策验证"""
        decision_maker.knowledge_base = sample_knowledge

        decision = await decision_maker.make_decision(sample_context)

        is_valid, issues = await decision_maker.validate_decision(decision)

        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)

    @pytest.mark.asyncio
    async def test_decision_history_retrieval(self, decision_maker, sample_knowledge, sample_context):
        """测试决策历史检索"""
        decision_maker.knowledge_base = sample_knowledge

        # 创建多个决策
        for _ in range(5):
            await decision_maker.make_decision(sample_context)

        history = await decision_maker.get_decision_history(limit=3)

        assert len(history) == 3
        assert all(record.decision is not None for record in history)

    @pytest.mark.asyncio
    async def test_decision_type_filtering(self, decision_maker, sample_knowledge, sample_context):
        """测试决策类型过滤"""
        decision_maker.knowledge_base = sample_knowledge

        # 创建决策
        await decision_maker.make_decision(sample_context)

        # 按类型过滤
        history = await decision_maker.get_decision_history(
            limit=100,
            decision_type=DecisionType.TRADE
        )

        assert all(record.decision.decision_type == DecisionType.TRADE for record in history)

    @pytest.mark.asyncio
    async def test_decision_pattern_analysis(self, decision_maker, sample_knowledge, sample_context):
        """测试决策模式分析"""
        decision_maker.knowledge_base = sample_knowledge

        # 创建多个决策
        for _ in range(10):
            await decision_maker.make_decision(sample_context)

        patterns = await decision_maker.analyze_decision_patterns(days=7)

        assert "decision_frequency" in patterns
        assert "type_distribution" in patterns
        assert "confidence_trend" in patterns
        assert "success_rate" in patterns

    def test_decision_stats(self, decision_maker, sample_knowledge):
        """测试决策统计"""
        stats = decision_maker.get_decision_stats()

        assert "total_decisions" in stats
        assert "decisions_by_type" in stats
        assert "average_confidence" in stats
        assert "high_confidence_count" in stats
        assert "low_confidence_count" in stats

    def test_stats_reset(self, decision_maker):
        """测试统计重置"""
        decision_maker.decision_stats["total_decisions"] = 10

        decision_maker.reset_stats()

        assert decision_maker.decision_stats["total_decisions"] == 0
        assert decision_maker.decision_stats["average_confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_knowledge_matching(self, decision_maker, sample_knowledge):
        """测试知识匹配"""
        decision_maker.knowledge_base = sample_knowledge

        context = DecisionContext(
            market_data={"symbol": "BTC/USDT", "trend": "bullish"},
            trading_parameters={"strategy": "trend_following"},
            risk_profile={"level": "medium"},
            time_constraints={}
        )

        match_score = await decision_maker.match_knowledge_to_context(
            decision_maker.knowledge_base["knowledge_001"],
            context
        )

        assert 0 <= match_score <= 1

    @pytest.mark.asyncio
    async def test_knowledge_ranking(self, decision_maker, sample_knowledge):
        """测试知识排序"""
        decision_maker.knowledge_base = sample_knowledge

        context = DecisionContext(
            market_data={"symbol": "BTC/USDT", "trend": "bullish"},
            trading_parameters={"strategy": "trend_following"},
            risk_profile={"level": "medium"},
            time_constraints={}
        )

        matches = await decision_maker.retrieve_relevant_knowledge(context)
        ranked = await decision_maker.rank_knowledge_by_relevance(matches)

        assert len(ranked) == len(matches)
        # 检查是否按相关性排序
        for i in range(len(ranked) - 1):
            assert ranked[i].relevance_score >= ranked[i+1].relevance_score

    def test_composite_score_calculation(self, decision_maker, sample_knowledge):
        """测试综合分数计算"""
        match = KnowledgeMatch(
            knowledge_id="test_001",
            content="test content",
            relevance_score=0.8,
            relevance_level=KnowledgeRelevance.HIGHLY_RELEVANT,
            quality_score=0.7,
            value_score=0.6,
            confidence=0.75,
            metadata={}
        )

        composite_score = decision_maker._calculate_composite_score(match)

        assert 0 <= composite_score <= 1
        # 验证权重计算
        expected_score = (
            0.7 * 0.4 +  # quality
            0.6 * 0.3 +  # value
            0.8 * 0.2 +  # relevance
            0.75 * 0.1    # freshness
        )
        assert abs(composite_score - expected_score) < 0.01

    @pytest.mark.asyncio
    async def test_empty_knowledge_base(self, decision_maker, sample_context):
        """测试空知识库"""
        decision_maker.knowledge_base = {}

        matches = await decision_maker.retrieve_relevant_knowledge(sample_context)

        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_low_confidence_decision(self, decision_maker, sample_context):
        """测试低置信度决策"""
        decision_maker.confidence_threshold = 0.9
        decision_maker.knowledge_base = {}

        decision = await decision_maker.make_decision(sample_context)

        assert decision.confidence < 0.9

    def test_knowledge_weights(self, decision_maker):
        """测试知识权重"""
        weights = decision_maker.KNOWLEDGE_WEIGHTS

        assert "quality" in weights
        assert "value" in weights
        assert "relevance" in weights
        assert "freshness" in weights
        # 验证权重总和为1
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01


class TestKnowledgeMatch:
    """测试KnowledgeMatch"""

    def test_knowledge_match_creation(self):
        """测试知识匹配创建"""
        match = KnowledgeMatch(
            knowledge_id="test_001",
            content="test content",
            relevance_score=0.8,
            relevance_level=KnowledgeRelevance.HIGHLY_RELEVANT,
            quality_score=0.7,
            value_score=0.6,
            confidence=0.75,
            metadata={"category": "test"}
        )

        assert match.knowledge_id == "test_001"
        assert match.relevance_score == 0.8
        assert match.relevance_level == KnowledgeRelevance.HIGHLY_RELEVANT

    def test_knowledge_match_conversion(self):
        """测试知识匹配转换"""
        match = KnowledgeMatch(
            knowledge_id="test_001",
            content="test content",
            relevance_score=0.8,
            relevance_level=KnowledgeRelevance.HIGHLY_RELEVANT,
            quality_score=0.7,
            value_score=0.6,
            confidence=0.75,
            metadata={}
        )

        match_dict = match.to_dict()

        assert "knowledge_id" in match_dict
        assert "relevance_score" in match_dict
        assert "relevance_level" in match_dict
        assert match_dict["relevance_level"] == "highly_relevant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
