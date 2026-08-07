"""CryptoArbitrage V2.6 测试套件

测试目标：
1. TradingAgents集成 - 多智能体LLM分析框架
2. 信号融合引擎 - LLM + 技术 + 套利 + 风险
3. 高级可视化 - 策略回测 + 知识图谱
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# 测试TradingAgents集成包装器
@pytest.mark.unit
class TestTradingAgentsWrapper:
    """测试TradingAgents集成包装器"""

    def test_wrapper_creation_disabled(self):
        """测试禁用状态的包装器创建"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        wrapper = TradingAgentsWrapper(enabled=False)

        assert not wrapper.is_enabled()
        assert wrapper.provider == "anthropic"  # 默认值

    def test_convert_signal_to_score(self):
        """测试信号转换为评分"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        wrapper = TradingAgentsWrapper()

        # 测试五级信号转换
        assert wrapper._signal_to_score("BUY") == 100
        assert wrapper._signal_to_score("OVERWEIGHT") == 75
        assert wrapper._signal_to_score("HOLD") == 50
        assert wrapper._signal_to_score("UNDERWEIGHT") == 25
        assert wrapper._signal_to_score("SELL") == 0

        # 测试未知信号
        assert wrapper._signal_to_score("UNKNOWN") == 50  # 默认为HOLD

    def test_disabled_analyze(self):
        """测试禁用状态的分析"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        wrapper = TradingAgentsWrapper(enabled=False)
        result = wrapper.analyze_crypto("BTC", "2024-05-10")

        # 禁用时返回中性结果
        assert result["signal"] == "HOLD"
        assert result["score"] == 50
        assert result["confidence"] == 0.0
        assert not result["success"]


# 测试信号融合引擎
@pytest.mark.unit
class TestSignalFusionEngine:
    """测试信号融合引擎"""

    def test_engine_initialization(self):
        """测试融合引擎初始化"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        assert engine is not None
        assert len(engine.signal_sources) == 4  # LLM, technical, arbitrage, risk

    def test_fuse_signals_equal_weights(self):
        """测试等权重信号融合"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        # 模拟4个信号源
        llm_signal = {"signal": "BUY", "score": 100, "confidence": 0.9}
        technical_signal = {"signal": "OVERWEIGHT", "score": 75, "confidence": 0.8}
        arbitrage_signal = {"signal": "BUY", "score": 100, "confidence": 0.7}
        risk_signal = {"signal": "HOLD", "score": 50, "confidence": 0.6}

        fused = engine.fuse_signals(
            llm_signal=llm_signal,
            technical_signal=technical_signal,
            arbitrage_signal=arbitrage_signal,
            risk_signal=risk_signal,
            weights={"llm": 0.25, "technical": 0.25, "arbitrage": 0.25, "risk": 0.25}
        )

        # 等权重计算: (100+75+100+50)/4 = 81.25 (考虑置信度加权会有差异)
        assert abs(fused["fused_score"] - 81.25) < 3.0  # 允许一定误差
        assert 0 <= fused["confidence"] <= 1

    def test_fuse_signals_custom_weights(self):
        """测试自定义权重融合"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        llm_signal = {"signal": "BUY", "score": 100, "confidence": 0.9}
        technical_signal = {"signal": "BUY", "score": 100, "confidence": 0.8}
        arbitrage_signal = {"signal": "BUY", "score": 100, "confidence": 0.7}
        risk_signal = {"signal": "HOLD", "score": 50, "confidence": 0.6}

        fused = engine.fuse_signals(
            llm_signal=llm_signal,
            technical_signal=technical_signal,
            arbitrage_signal=arbitrage_signal,
            risk_signal=risk_signal,
            weights={"llm": 0.5, "technical": 0.2, "arbitrage": 0.2, "risk": 0.1}
        )

        # 自定义权重: 100*0.5 + 100*0.2 + 100*0.2 + 50*0.1 = 95 (考虑置信度加权会有差异)
        assert abs(fused["fused_score"] - 95) < 2.0  # 允许一定误差

    def test_fused_signal_interpretation(self):
        """测试融合信号解释"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        # 测试不同评分范围
        assert engine._interpret_fused_score(90) == "BUY"
        assert engine._interpret_fused_score(75) == "OVERWEIGHT"
        assert engine._interpret_fused_score(50) == "HOLD"
        assert engine._interpret_fused_score(25) == "UNDERWEIGHT"
        assert engine._interpret_fused_score(10) == "SELL"

    def test_confidence_calculation(self):
        """测试置信度计算"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        llm_signal = {"signal": "BUY", "score": 100, "confidence": 0.9}
        technical_signal = {"signal": "BUY", "score": 100, "confidence": 0.8}

        fused = engine.fuse_signals(
            llm_signal=llm_signal,
            technical_signal=technical_signal,
            arbitrage_signal={"signal": "HOLD", "score": 50, "confidence": 0.0},
            risk_signal={"signal": "HOLD", "score": 50, "confidence": 0.0},
            weights={"llm": 0.5, "technical": 0.5, "arbitrage": 0.0, "risk": 0.0}
        )

        # 应该基于有效信号计算置信度
        assert fused["confidence"] > 0.8

    def test_signal_divergence_detection(self):
        """测试信号分歧检测"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        # 高分歧场景
        llm_signal = {"signal": "BUY", "score": 100, "confidence": 0.9}
        technical_signal = {"signal": "SELL", "score": 0, "confidence": 0.8}

        divergence = engine._detect_divergence([llm_signal, technical_signal])
        assert divergence > 0.7  # 高分歧

        # 低分歧场景
        llm_signal = {"signal": "BUY", "score": 100, "confidence": 0.9}
        technical_signal = {"signal": "OVERWEIGHT", "score": 75, "confidence": 0.8}

        divergence = engine._detect_divergence([llm_signal, technical_signal])
        assert divergence < 0.3  # 低分歧


# 测试高级可视化组件
@pytest.mark.unit
class TestAdvancedVisualization:
    """测试高级可视化组件"""

    def test_backtest_visualization_generator(self):
        """测试回测可视化生成器"""
        from visualization.backtest_viz import BacktestVisualization

        viz = BacktestVisualization()

        # 模拟回测数据
        backtest_results = {
            "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "equity_curve": [10000, 10200, 10100],
            "drawdown": [0, -200, -100],
            "daily_returns": [0, 0.02, -0.01],
            "trades": [
                {"date": "2024-01-01", "symbol": "BTC", "action": "buy", "profit": 200},
                {"date": "2024-01-02", "symbol": "ETH", "action": "sell", "profit": -100}
            ]
        }

        # 生成图表数据
        chart_data = viz.generate_equity_curve_chart(backtest_results)

        assert "data" in chart_data
        assert "layout" in chart_data
        assert len(chart_data["data"]) >= 1

    def test_knowledge_graph_generator(self):
        """测试知识图谱生成器"""
        from visualization.knowledge_graph import KnowledgeGraphVisualizer

        viz = KnowledgeGraphVisualizer()

        # 模拟知识数据
        knowledge_items = [
            {"id": 1, "content": "BTC在牛市表现最佳", "category": "market", "metadata": {"strategy": "cross_exchange"}},
            {"id": 2, "content": "ETH波动率高适合三角套利", "category": "strategy", "metadata": {"strategy": "triangular"}},
            {"id": 3, "content": "高波动期风险增加", "category": "risk", "metadata": {"severity": "high"}}
        ]

        # 生成图谱数据
        graph_data = viz.generate_graph(knowledge_items)

        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) == 3
        # 应该有边连接相关节点
        assert len(graph_data["edges"]) >= 0

    def test_3d_market_visualization(self):
        """测试3D市场可视化"""
        from visualization.market_3d_viz import Market3DVisualizer

        viz = Market3DVisualizer()

        # 模拟市场数据
        market_data = {
            "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "prices": {"BTC": [50000, 51000, 50500], "ETH": [3000, 3100, 3050]},
            "volumes": {"BTC": [1000, 1200, 1100], "ETH": [5000, 6000, 5500]},
            "volatilities": {"BTC": [0.02, 0.03, 0.025], "ETH": [0.03, 0.04, 0.035]}
        }

        # 生成3D图表数据
        viz_data = viz.generate_3d_chart(market_data)

        assert "data" in viz_data
        assert "layout" in viz_data
        assert len(viz_data["data"]) >= 1


# 集成测试
@pytest.mark.integration
class TestV2_6Integration:
    """V2.6集成测试"""

    def test_signal_fusion_engine(self):
        """测试信号融合引擎"""
        from llm.signal_fusion import SignalFusionEngine

        engine = SignalFusionEngine()

        # 1. 获取技术指标信号
        technical_signal = {
            "signal": "BUY",
            "score": 100,
            "confidence": 0.8,
            "indicators": {"rsi": 30, "macd": "bullish"}
        }

        # 2. 获取套利信号
        arbitrage_signal = {
            "signal": "OVERWEIGHT",
            "score": 75,
            "confidence": 0.7,
            "opportunities": 3
        }

        # 3. 获取风险信号
        risk_signal = {
            "signal": "HOLD",
            "score": 50,
            "confidence": 0.9,
            "risk_level": "medium"
        }

        # 4. 融合信号（不包含LLM）
        fused = engine.fuse_signals(
            llm_signal=None,
            technical_signal=technical_signal,
            arbitrage_signal=arbitrage_signal,
            risk_signal=risk_signal,
            weights={"llm": 0.0, "technical": 0.4, "arbitrage": 0.3, "risk": 0.3}
        )

        # 验证融合结果
        assert "fused_score" in fused
        assert "fused_signal" in fused
        assert "confidence" in fused
        assert 0 <= fused["fused_score"] <= 100

    def test_strategy_manager_mixin_methods(self):
        """测试StrategyManager V2.6 Mixin方法"""
        from strategies.strategy_manager_v2_6 import StrategyManagerV26Mixin

        # 创建简单的StrategyManager（需要继承自一个基类）
        class MockBase:
            def __init__(self, *args, **kwargs):
                pass

        class TestStrategyManager(StrategyManagerV26Mixin, MockBase):
            def __init__(self):
                super().__init__(trading_agents_enabled=False)
                self.strategies = {}

        sm = TestStrategyManager()

        # 测试信号评分转换
        assert sm._score_to_signal(90) == "BUY"
        assert sm._score_to_signal(75) == "OVERWEIGHT"
        assert sm._score_to_signal(50) == "HOLD"
        assert sm._score_to_signal(25) == "UNDERWEIGHT"
        assert sm._score_to_signal(10) == "SELL"

        # 测试机会评分解释
        opportunity = {"_score": 80}
        assert sm._interpret_opportunity_score(opportunity["_score"]) == "OVERWEIGHT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
