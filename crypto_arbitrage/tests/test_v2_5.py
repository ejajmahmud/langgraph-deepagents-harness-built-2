"""CryptoArbitrage V2.5 测试套件

测试Memo0深度集成的所有功能：
1. 自动知识积累器测试
2. 智能决策引擎测试
3. 智能告警系统测试
4. 配置管理器测试
5. StrategyManager V2.5集成测试
6. 端到端知识流测试
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any


# ---------------------- Fixtures ----------------------


@pytest.fixture
def mock_storage():
    """Mock存储实例"""
    storage = Mock()
    storage.add_knowledge = Mock(return_value=True)
    storage.search_knowledge = Mock(return_value=[])
    storage.get_all_knowledge = Mock(return_value=[])
    return storage


@pytest.fixture
def mock_config():
    """Mock配置管理器实例"""
    config = Mock()
    config.get_monitoring_config = Mock(return_value={
        "enabled": True,
        "alert_methods": ["console"],
        "performance_thresholds": {
            "scan_timeout": 10,
            "execution_failure_rate": 0.1,
        },
        "metrics_interval": 60,
    })
    return config


@pytest.fixture
def sample_market_conditions():
    """示例市场条件"""
    return {
        "volatility": 2.5,
        "trend": "rising",
        "liquidity": "normal",
        "funding_rate": 0.01,
        "spread": 0.3
    }


@pytest.fixture
def sample_opportunity():
    """示例交易机会"""
    return {
        "symbol": "BTC/USDT",
        "profit_rate": 0.8,
        "position_size": 0.5,
        "entry_price": 65000,
        "volatility": 2.5,
        "expected_profit": 500,
        "_score": 75,
        "_strategy_name": "cross_exchange"
    }


@pytest.fixture
def sample_trade_result():
    """示例交易结果"""
    return {
        "status": "completed",
        "actual_profit": 480,
        "execution_time": 5.2,
        "error": None
    }


# ---------------------- 自动知识积累器测试 ----------------------


class TestAutoKnowledgeAccumulator:
    """测试自动知识积累器"""

    @pytest.mark.asyncio
    async def test_record_decision(self, mock_storage, sample_market_conditions, sample_opportunity):
        """测试决策记录"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 记录决策
        success = accumulator.record_decision(
            decision_type="trade_execution",
            market_conditions=sample_market_conditions,
            strategy="cross_exchange",
            reasoning="最佳机会，评分75",
            parameters={"profit_rate": 0.8, "score": 75},
            outcome="pending"
        )

        # 验证
        assert success is True
        assert mock_storage.add_knowledge.called
        call_args = mock_storage.add_knowledge.call_args
        assert call_args[1]["category"] == "decision"

    @pytest.mark.asyncio
    async def test_record_trade_result_success(self, mock_storage, sample_trade_result):
        """测试交易结果记录（成功）"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 记录交易结果
        success = accumulator.record_trade_result(
            trade_id="trade_123",
            strategy="cross_exchange",
            expected_profit=500,
            actual_profit=480,
            execution_time=5.2
        )

        # 验证
        assert success is True
        assert mock_storage.add_knowledge.called
        call_args = mock_storage.add_knowledge.call_args
        assert call_args[1]["category"] == "trade_result"

    @pytest.mark.asyncio
    async def test_record_trade_result_failure(self, mock_storage):
        """测试交易结果记录（失败）"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 记录失败的交易结果
        success = accumulator.record_trade_result(
            trade_id="trade_124",
            strategy="triangular",
            expected_profit=300,
            actual_profit=-50,
            execution_time=3.1,
            error="流动性不足"
        )

        # 验证
        assert success is True
        assert mock_storage.add_knowledge.called

    @pytest.mark.asyncio
    async def test_record_market_pattern(self, mock_storage, sample_market_conditions):
        """测试市场模式记录"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 记录市场模式
        success = accumulator.record_market_pattern(
            pattern_type="bullish_trend",
            conditions=sample_market_conditions,
            successful_strategies=["cross_exchange", "funding_rate"],
            failed_strategies=["triangular"],
            confidence=0.85,
            duration=4.5
        )

        # 验证
        assert success is True
        assert mock_storage.add_knowledge.called
        call_args = mock_storage.add_knowledge.call_args
        assert call_args[1]["category"] == "market_pattern"

    @pytest.mark.asyncio
    async def test_record_strategy_performance(self, mock_storage, sample_market_conditions):
        """测试策略表现记录"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 记录策略表现
        success = accumulator.record_strategy_performance(
            strategy="cross_exchange",
            period="daily",
            metrics={
                "total_trades": 20,
                "win_rate": 0.75,
                "total_profit": 2500,
                "avg_profit_per_trade": 125,
                "max_drawdown": 3.2,
                "sharpe_ratio": 2.1
            },
            market_conditions=sample_market_conditions
        )

        # 验证
        assert success is True
        assert mock_storage.add_knowledge.called

    @pytest.mark.asyncio
    async def test_query_similar_decisions(self, mock_storage, sample_market_conditions):
        """测试相似决策查询"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        # 设置mock返回值
        mock_storage.search_knowledge.return_value = [
            {
                "id": "decision_1",
                "content": "决策记录",
                "category": "decision",
                "metadata": {
                    "strategy": "cross_exchange",
                    "outcome": "completed"
                }
            }
        ]

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 查询相似决策
        results = accumulator.query_similar_decisions(
            market_conditions=sample_market_conditions,
            strategy="cross_exchange",
            top_k=5
        )

        # 验证
        assert len(results) > 0
        assert mock_storage.search_knowledge.called

    @pytest.mark.asyncio
    async def test_get_knowledge_stats(self, mock_storage):
        """测试知识统计"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        # 设置mock返回值
        mock_storage.get_all_knowledge.return_value = [
            {"category": "decision", "metadata": {"type": "decision", "timestamp": datetime.now().isoformat()}},
            {"category": "trade_result", "metadata": {"type": "trade_result", "timestamp": datetime.now().isoformat()}},
            {"category": "market_pattern", "metadata": {"type": "market_pattern", "timestamp": datetime.now().isoformat()}},
        ]

        accumulator = AutoKnowledgeAccumulator(mock_storage)

        # 获取统计
        stats = accumulator.get_knowledge_stats()

        # 验证
        assert stats["total"] == 3
        assert stats["by_category"]["decision"] == 1
        assert stats["by_category"]["trade_result"] == 1
        assert stats["by_category"]["market_pattern"] == 1


# ---------------------- 智能决策引擎测试 ----------------------


class TestIntelligentDecisionEngine:
    """测试智能决策引擎"""

    @pytest.mark.asyncio
    async def test_recommend_strategy(self, mock_storage, sample_market_conditions):
        """测试策略推荐"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator
        from storage.intelligent_decision_engine import IntelligentDecisionEngine

        # 设置mock返回值
        mock_storage.search_knowledge.return_value = [
            {
                "metadata": {
                    "strategy": "cross_exchange",
                    "outcome": "completed",
                    "actual_profit": 500
                }
            },
            {
                "metadata": {
                    "strategy": "cross_exchange",
                    "outcome": "completed",
                    "actual_profit": 480
                }
            }
        ]

        auto_accumulator = AutoKnowledgeAccumulator(mock_storage)
        engine = IntelligentDecisionEngine(mock_storage, auto_accumulator)

        # 推荐策略
        result = engine.recommend_strategy(
            current_market_conditions=sample_market_conditions,
            available_strategies=["cross_exchange", "triangular", "funding_rate"],
            top_k=3
        )

        # 验证
        assert "recommendations" in result
        assert "market_analysis" in result
        assert len(result["recommendations"]) <= 3

    @pytest.mark.asyncio
    async def test_assess_opportunity_risk(self, mock_storage, sample_opportunity, sample_market_conditions):
        """测试机会风险评估"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator
        from storage.intelligent_decision_engine import IntelligentDecisionEngine

        auto_accumulator = AutoKnowledgeAccumulator(mock_storage)
        engine = IntelligentDecisionEngine(mock_storage, auto_accumulator)

        # 评估风险
        result = engine.assess_opportunity_risk(
            opportunity=sample_opportunity,
            strategy="cross_exchange",
            current_market_conditions=sample_market_conditions
        )

        # 验证
        assert "risk_level" in result
        assert "risk_score" in result
        assert "risk_factors" in result
        assert "recommendations" in result
        assert result["risk_level"] in ["low", "medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, mock_storage):
        """测试异常检测"""
        from storage.intelligent_decision_engine import IntelligentDecisionEngine
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

        # 设置mock返回值（历史价格）
        mock_storage.search_knowledge.return_value = [
            {"metadata": {"price": 65000}},
            {"metadata": {"price": 65100}},
            {"metadata": {"price": 64900}},
        ]

        auto_accumulator = AutoKnowledgeAccumulator(mock_storage)
        engine = IntelligentDecisionEngine(mock_storage, auto_accumulator)

        # 检测异常
        result = engine.detect_anomalies(
            current_market_data={
                "price": 66000,
                "volume": 1000000,
                "volatility": 2.5,
                "spread": 0.3
            }
        )

        # 验证
        assert "anomalies" in result
        assert "anomaly_score" in result
        assert "market_status" in result
        assert result["market_status"] in ["normal", "warning", "critical"]


# ---------------------- 智能告警系统测试 ----------------------


class TestIntelligentAlerting:
    """测试智能告警系统"""

    @pytest.mark.asyncio
    async def test_check_dynamic_threshold_normal(self, mock_config):
        """测试动态阈值检测（正常）"""
        from monitoring.intelligent_alerting import IntelligentAlerting

        with patch('storage.mem0_storage.get_unified_storage') as mock_get_storage:
            mock_get_storage.return_value = Mock()
            alerting = IntelligentAlerting(Mock(), mock_config)

            # 检测阈值（正常值）
            result = alerting.check_dynamic_threshold(
                metric_name="scan_timeout",
                current_value=5.0,
                historical_data=[4.5, 5.0, 5.2, 4.8, 5.0]
            )

            # 验证
            assert result["is_alert"] is False

    @pytest.mark.asyncio
    async def test_check_dynamic_threshold_alert(self, mock_config):
        """测试动态阈值检测（告警）"""
        from monitoring.intelligent_alerting import IntelligentAlerting

        with patch('storage.mem0_storage.get_unified_storage') as mock_get_storage:
            mock_get_storage.return_value = Mock()
            alerting = IntelligentAlerting(Mock(), mock_config)

            # 检测阈值（异常值）
            result = alerting.check_dynamic_threshold(
                metric_name="scan_timeout",
                current_value=15.0,
                historical_data=[4.5, 5.0, 5.2, 4.8, 5.0]
            )

            # 验证
            assert result["is_alert"] is True
            assert "severity" in result

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, mock_config):
        """测试异常检测"""
        from monitoring.intelligent_alerting import IntelligentAlerting

        with patch('storage.mem0_storage.get_unified_storage') as mock_get_storage:
            mock_get_storage.return_value = Mock()
            alerting = IntelligentAlerting(Mock(), mock_config)

            # 检测异常
            result = alerting.detect_anomalies(
                metric_name="execution_time",
                current_value=30.0,
                historical_data=[5.0, 5.5, 4.8, 5.2, 5.0, 5.1, 4.9, 5.0, 5.2, 5.1] * 5  # 50个历史值
            )

            # 验证
            assert "is_anomaly" in result
            assert "confidence" in result

    @pytest.mark.asyncio
    async def test_generate_alert(self, mock_config):
        """测试告警生成"""
        from monitoring.intelligent_alerting import IntelligentAlerting

        with patch('storage.mem0_storage.get_unified_storage') as mock_get_storage:
            mock_storage = Mock()
            mock_storage.add_knowledge = Mock(return_value=True)
            mock_get_storage.return_value = mock_storage

            alerting = IntelligentAlerting(mock_storage, mock_config)

            # 生成告警
            alert = alerting.generate_alert(
                alert_type="threshold",
                metric_name="scan_timeout",
                severity="high",
                message="扫描超时超过阈值",
                details={"current_value": 15.0, "threshold": 10.0}
            )

            # 验证
            assert alert["alert_id"] is not None
            assert alert["severity"] == "high"
            assert alert["acknowledged"] is False
            assert mock_storage.add_knowledge.called

    @pytest.mark.asyncio
    async def test_predict_alerts(self, mock_config):
        """测试告警预测"""
        from monitoring.intelligent_alerting import IntelligentAlerting

        with patch('storage.mem0_storage.get_unified_storage') as mock_get_storage:
            mock_get_storage.return_value = Mock()
            alerting = IntelligentAlerting(Mock(), mock_config)

            # 预测告警（使用足够的数据点）
            result = alerting.predict_alerts(
                metric_name="scan_timeout",
                current_trend=[5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0],
                forecast_horizon=5
            )

            # 验证
            assert "prediction" in result
            assert "confidence" in result
            # predicted_values可能不存在，取决于预测结果
            if result["prediction"] == "alert_expected":
                assert "predicted_values" in result
            assert result["prediction"] in ["normal", "alert_expected", "unknown"]


# ---------------------- 配置管理器测试 ----------------------


class TestConfigManager:
    """测试配置管理器"""

    def test_load_config_defaults(self):
        """测试加载默认配置"""
        from config.config_manager import ConfigManager

        manager = ConfigManager()
        config = manager.load_config()

        # 验证默认值
        assert config is not None
        assert config["system"]["name"] == "CryptoArbitrage"
        assert config["system"]["version"] == "2.5"
        assert config["system"]["mode"] in ["simulation", "paper_trading", "live_trading"]

    def test_get_nested_config(self):
        """测试获取嵌套配置"""
        from config.config_manager import ConfigManager

        manager = ConfigManager()
        manager.load_config()

        # 获取嵌套配置
        api_key = manager.get("mem0.api_key")
        mode = manager.get("system.mode")

        # 验证
        assert api_key is not None
        assert mode is not None

    def test_set_config(self):
        """测试设置配置"""
        from config.config_manager import ConfigManager

        manager = ConfigManager()
        manager.load_config()

        # 设置配置
        manager.set("system.mode", "paper_trading")

        # 验证
        assert manager.get("system.mode") == "paper_trading"

    def test_validate_sensitivity(self):
        """测试敏感配置验证"""
        from config.config_manager import ConfigManager

        manager = ConfigManager()
        manager.load_config()

        # 验证敏感配置
        result = manager.validate_sensitivity()

        # 验证
        assert "warnings" in result
        assert "errors" in result

    def test_get_system_mode(self):
        """测试获取系统模式"""
        from config.config_manager import ConfigManager

        manager = ConfigManager()
        manager.load_config()

        # 获取系统模式
        mode = manager.get_system_mode()

        # 验证
        assert mode in ["simulation", "paper_trading", "live_trading"]

    def test_is_simulation(self):
        """测试是否为模拟模式"""
        from config.config_manager import ConfigManager

        manager = ConfigManager()
        manager.load_config()
        manager.set("system.mode", "simulation")

        # 验证
        assert manager.is_simulation() is True
        assert manager.is_paper_trading() is False
        assert manager.is_live_trading() is False


# ---------------------- 端到端集成测试 ------------------


class TestE2EKnowledgeFlow:
    """测试端到端知识流"""

    @pytest.mark.asyncio
    async def test_complete_knowledge_flow(self, mock_storage, sample_market_conditions, sample_opportunity, sample_trade_result):
        """测试完整的知识流：决策→执行→结果学习"""
        from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator
        from storage.intelligent_decision_engine import IntelligentDecisionEngine

        # 初始化
        accumulator = AutoKnowledgeAccumulator(mock_storage)
        engine = IntelligentDecisionEngine(mock_storage, accumulator)

        # 设置mock返回计数
        add_knowledge_count = 0
        original_add_knowledge = mock_storage.add_knowledge

        def count_add_knowledge(*args, **kwargs):
            nonlocal add_knowledge_count
            add_knowledge_count += 1
            return original_add_knowledge(*args, **kwargs)

        mock_storage.add_knowledge = Mock(side_effect=count_add_knowledge)

        # 步骤1: 记录决策
        decision_success = accumulator.record_decision(
            decision_type="trade_execution",
            market_conditions=sample_market_conditions,
            strategy="cross_exchange",
            reasoning="最佳机会",
            parameters={"profit_rate": 0.8},
            outcome="pending"
        )
        assert decision_success is True

        # 步骤2: 智能决策引擎推荐
        recommendation = engine.recommend_strategy(
            current_market_conditions=sample_market_conditions,
            available_strategies=["cross_exchange"],
            top_k=3
        )
        assert "recommendations" in recommendation

        # 步骤3: 记录交易结果
        result_success = accumulator.record_trade_result(
            trade_id="trade_123",
            strategy="cross_exchange",
            expected_profit=500,
            actual_profit=480,
            execution_time=5.2
        )
        assert result_success is True

        # 步骤4: 验证知识积累（使用计数而非get_all_knowledge返回值）
        # 因为mock的get_all_knowledge可能返回空列表
        assert add_knowledge_count >= 2  # 至少记录了决策和结果

        # 步骤5: 查询相似决策
        similar = accumulator.query_similar_decisions(
            market_conditions=sample_market_conditions,
            top_k=5
        )
        # mock返回空列表是正常的，我们只验证方法被调用
        assert mock_storage.search_knowledge.called


# ---------------------- 运行所有测试 ------------------


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
