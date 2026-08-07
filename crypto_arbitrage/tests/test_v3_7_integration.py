"""V3.7 完整系统集成测试套件 - 最终版本
端到端测试 - 验证三个 Phase 的完整协作和数据流
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import Memo0DecisionSupport, MarketContext
from trading import ProductionTradingEngine, TradingMode
from ops import SystemHealthMonitor, AutoRecoveryEngine
from tools.risk_management import RiskManager


class TestV37BasicIntegration:
    """V3.7 基础集成测试"""

    @pytest.fixture
    def mock_memo0_storage(self):
        mock_storage = Mock()
        mock_storage.search = AsyncMock(return_value=[
            {
                'content': '牛市中跨交易所套利策略表现较好',
                'score': 0.9,
                'category': 'strategy',
                'source': 'memo0',
                'created_at': datetime.now().isoformat(),
                'metadata': {}
            }
        ])
        mock_storage.add = AsyncMock(return_value=True)
        return mock_storage

    @pytest.fixture
    def decision_support(self, mock_memo0_storage):
        return Memo0DecisionSupport(mock_memo0_storage)

    @pytest.fixture
    def trading_engine(self):
        risk_config = {
            'max_position_size': 0.1,
            'max_daily_loss': 1000.0,
            'stop_loss_percentage': 0.05
        }
        risk_manager = RiskManager(config=risk_config)

        engine_config = {
            'initial_mode': 'SIMULATION',
            'max_live_trades_per_day': 10,
            'live_position_limit': 0.1,
            'emergency_contacts': []
        }
        return ProductionTradingEngine(config=engine_config, risk_manager=risk_manager)

    @pytest.mark.asyncio
    async def test_phase1_to_phase2_basic(self, decision_support, trading_engine):
        """测试 Phase 1 到 Phase 2 的基础集成"""
        # Phase 1: 获取决策支持
        market_context = MarketContext(
            timestamp=datetime.now(),
            symbol='BTC/USDT',
            price=50000.0,
            volume_24h=1000000000,
            volatility=0.03,
            trend='uptrend',
            market_regime='bullish',
            technical_indicators={'rsi': 65},
            sentiment_score=0.4,
            liquidity_score=0.8
        )

        opportunity = {
            'type': 'cross_exchange_arbitrage',
            'expected_profit': 0.025,
            'risk_level': 'low'
        }

        insight = await decision_support.reason_about_opportunity(opportunity, market_context)

        assert insight.insight_type is not None
        assert insight.confidence > 0

        # Phase 2: 执行交易
        trade_opportunity = {
            'type': 'cross_exchange_arbitrage',
            'symbol': 'BTC/USDT',
            'price': 50000.0,
            'amount': 0.05,  # 符合风险限制 0.1
            'expected_profit': 50.0,
            'market_regime': 'stable'
        }

        await trading_engine.start()
        result = await trading_engine.execute_trade(trade_opportunity)

        assert result.status == 'COMPLETED'
        assert result.actual_profit is not None
        assert result.mode == TradingMode.SIMULATION

    @pytest.mark.asyncio
    async def test_knowledge_query(self, decision_support):
        """测试知识查询"""
        market_context = MarketContext(
            timestamp=datetime.now(),
            symbol='BTC/USDT',
            price=50000.0,
            volume_24h=1000000000,
            volatility=0.03,
            trend='uptrend',
            market_regime='bullish',
            technical_indicators={'rsi': 65},
            sentiment_score=0.4,
            liquidity_score=0.8
        )

        knowledge = await decision_support.get_relevant_knowledge(market_context)

        assert isinstance(knowledge, list)
        assert len(knowledge) > 0


class TestV37Coordination:
    """V3.7 系统协调测试"""

    @pytest.mark.asyncio
    async def test_three_phase_workflow(self):
        """测试三个 Phase 的完整工作流"""
        # 创建模拟的各个组件
        mock_storage = Mock()
        mock_storage.search = AsyncMock(return_value=[
            {
                'content': '牛市策略建议',
                'score': 0.85,
                'category': 'strategy',
                'source': 'memo0',
                'created_at': datetime.now().isoformat(),
                'metadata': {}
            }
        ])
        mock_storage.add = AsyncMock(return_value=True)

        # Phase 1: 决策支持
        decision_support = Memo0DecisionSupport(mock_storage)

        market_context = MarketContext(
            timestamp=datetime.now(),
            symbol='BTC/USDT',
            price=50000.0,
            volume_24h=1000000000,
            volatility=0.03,
            trend='uptrend',
            market_regime='bullish',
            technical_indicators={'rsi': 65},
            sentiment_score=0.4,
            liquidity_score=0.8
        )

        insight = await decision_support.get_decision_summary(market_context)
        assert insight is not None
        assert 'market_analysis' in insight
        assert 'available_knowledge' in insight

        # Phase 2: 交易执行
        risk_config = {'max_position_size': 0.1, 'max_daily_loss': 1000.0}
        risk_manager = RiskManager(config=risk_config)

        engine_config = {'initial_mode': 'SIMULATION', 'max_live_trades_per_day': 10}
        trading_engine = ProductionTradingEngine(config=engine_config, risk_manager=risk_manager)

        opportunity = {
            'type': 'cross_exchange_arbitrage',
            'symbol': 'BTC/USDT',
            'price': 50000.0,
            'amount': 0.05,
            'expected_profit': 50.0,
            'market_regime': 'stable'
        }

        await trading_engine.start()
        result = await trading_engine.execute_trade(opportunity)
        assert result.status == 'COMPLETED'

        # Phase 3: 健康监控
        from ops import create_system_health_monitor, ComponentHealthCheck

        monitor_config = {'check_interval': 60}
        health_monitor = create_system_health_monitor(config=monitor_config)

        # 注册测试组件
        mock_component = Mock()
        mock_component.check_health = AsyncMock(return_value={'status': 'healthy', 'score': 0.8})
        health_monitor.register_check(ComponentHealthCheck('test_component', mock_component))

        health_report = await health_monitor.run_checks()
        assert health_report is not None
        assert health_report.overall_status is not None


class TestV37DataConsistency:
    """V3.7 数据一致性测试"""

    @pytest.mark.asyncio
    async def test_decision_to_execution_data(self):
        """测试从决策到执行的数据流"""
        mock_storage = Mock()
        mock_storage.search = AsyncMock(return_value=[
            {
                'content': '套利机会分析',
                'score': 0.9,
                'category': 'strategy',
                'source': 'memo0',
                'created_at': datetime.now().isoformat(),
                'metadata': {}
            }
        ])

        decision_support = Memo0DecisionSupport(mock_storage)

        market_context = MarketContext(
            timestamp=datetime.now(),
            symbol='BTC/USDT',
            price=50000.0,
            volume_24h=1000000000,
            volatility=0.03,
            trend='uptrend',
            market_regime='bullish',
            technical_indicators={'rsi': 65},
            sentiment_score=0.4,
            liquidity_score=0.8
        )

        opportunity = {
            'type': 'cross_exchange_arbitrage',
            'expected_profit': 0.025,
            'risk_level': 'low'
        }

        insight = await decision_support.reason_about_opportunity(opportunity, market_context)

        # 验证决策数据完整性
        assert insight.insight_type is not None
        assert insight.confidence is not None
        assert insight.description is not None

        # 验证数据可以传递到交易执行
        risk_config = {'max_position_size': 0.1, 'max_daily_loss': 1000.0}
        risk_manager = RiskManager(config=risk_config)

        engine_config = {'initial_mode': 'SIMULATION', 'max_live_trades_per_day': 10}
        trading_engine = ProductionTradingEngine(config=engine_config, risk_manager=risk_manager)

        trade_opportunity = {
            'type': 'cross_exchange_arbitrage',
            'symbol': 'BTC/USDT',
            'price': 50000.0,
            'amount': 0.05,
            'expected_profit': 50.0,
            'market_regime': 'stable'
        }

        await trading_engine.start()
        result = await trading_engine.execute_trade(trade_opportunity)
        assert result.status == 'COMPLETED'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
