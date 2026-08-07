"""套利策略测试"""

import asyncio
import pytest

from strategies.cross_exchange import CrossExchangeArbitrageStrategy, LowRiskArbitrageFilter
from strategies.triangular_arbitrage import TriangularArbitrageStrategy
from tools.exchange_api import ArbitrageCalculator


class TestArbitrageCalculator:
    """套利计算器测试"""

    def test_cross_exchange_arbitrage_calculation(self):
        """测试跨交易所套利计算"""
        result = ArbitrageCalculator.calculate_cross_exchange_arbitrage(
            buy_exchange="binance",
            sell_exchange="okx",
            buy_price=50000.0,
            sell_price=50200.0,
            buy_fee=0.001,
            sell_fee=0.001,
            amount=0.1
        )

        assert result['buy_exchange'] == "binance"
        assert result['sell_exchange'] == "okx"
        assert result['buy_price'] == 50000.0
        assert result['sell_price'] == 50200.0
        assert result['profit'] > 0
        assert result['is_profitable'] is True

    def test_cross_exchange_arbitrage_negative_profit(self):
        """测试负收益的跨交易所套利"""
        result = ArbitrageCalculator.calculate_cross_exchange_arbitrage(
            buy_exchange="binance",
            sell_exchange="okx",
            buy_price=50200.0,
            sell_price=50000.0,
            buy_fee=0.001,
            sell_fee=0.001,
            amount=0.1
        )

        assert result['profit'] < 0
        assert result['is_profitable'] is False

    def test_triangular_arbitrage_calculation(self):
        """测试三角套利计算"""
        rates = {
            'BTC/USDT': 50000.0,
            'ETH/BTC': 0.05,
            'ETH/USDT': 2600.0
        }
        fees = {
            'BTC/USDT': 0.001,
            'ETH/BTC': 0.001,
            'ETH/USDT': 0.001
        }

        result = ArbitrageCalculator.calculate_triangular_arbitrage(
            rates=rates,
            fees=fees,
            amount=1000.0
        )

        assert 'initial_amount' in result
        assert 'final_amount' in result
        assert 'profit' in result
        assert 'profit_rate' in result
        assert 'path' in result


class TestCrossExchangeArbitrageStrategy:
    """跨交易所套利策略测试"""

    @pytest.fixture
    def strategy_config(self):
        """策略配置 fixture"""
        return {
            'min_profit_rate': 0.5,
            'max_position_size': 1000,
            'risk_tolerance': 0.1,
            'symbols': ['BTC/USDT', 'ETH/USDT']
        }

    @pytest.fixture
    def strategy(self, strategy_config):
        """策略实例 fixture"""
        return CrossExchangeArbitrageStrategy(strategy_config)

    def test_strategy_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.min_profit_rate == 0.5
        assert strategy.max_position_size == 1000
        assert len(strategy.symbols) == 2

    def test_performance_stats_empty(self, strategy):
        """测试空性能统计"""
        stats = strategy.get_performance_stats()
        assert stats['total_trades'] == 0
        assert stats['total_profit'] == 0
        assert stats['success_rate'] == 0


class TestLowRiskArbitrageFilter:
    """低风险套利过滤器测试"""

    @pytest.fixture
    def sample_opportunities(self):
        """示例套利机会 fixture"""
        return [
            {
                'symbol': 'BTC/USDT',
                'buy_exchange': 'binance',
                'sell_exchange': 'okx',
                'buy_price': 50000.0,
                'sell_price': 50100.0,
                'profit_rate': 0.15,
                'spread_rate': 0.2,
                'buy_cost': 5000.0,
                'profit': 7.5
            },
            {
                'symbol': 'BTC/USDT',
                'buy_exchange': 'binance',
                'sell_exchange': 'okx',
                'buy_price': 50000.0,
                'sell_price': 50300.0,
                'profit_rate': 0.5,
                'spread_rate': 0.6,
                'buy_cost': 5000.0,
                'profit': 25.0
            }
        ]

    def test_filter_by_min_profit_rate(self, sample_opportunities):
        """测试按最小收益率过滤"""
        filtered = LowRiskArbitrageFilter.filter_opportunities(
            sample_opportunities,
            min_profit_rate=0.4
        )

        assert len(filtered) == 1
        assert filtered[0]['profit_rate'] == 0.5

    def test_filter_by_volatility(self, sample_opportunities):
        """测试按波动率过滤"""
        filtered = LowRiskArbitrageFilter.filter_opportunities(
            sample_opportunities,
            max_volatility=0.5
        )

        assert len(filtered) == 2

    def test_calculate_risk_score(self, sample_opportunities):
        """测试风险评分计算"""
        score = LowRiskArbitrageFilter.calculate_risk_score(sample_opportunities[0])
        assert 0 <= score <= 100


class TestTriangularArbitrageStrategy:
    """三角套利策略测试"""

    @pytest.fixture
    def strategy_config(self):
        """策略配置 fixture"""
        return {
            'min_profit_rate': 0.3,
            'max_position_size': 500,
            'triangles': []
        }

    @pytest.fixture
    def strategy(self, strategy_config):
        """策略实例 fixture"""
        return TriangularArbitrageStrategy(strategy_config)

    def test_strategy_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.min_profit_rate == 0.3
        assert strategy.max_position_size == 500

    def test_performance_stats_empty(self, strategy):
        """测试空性能统计"""
        stats = strategy.get_performance_stats()
        assert stats['total_trades'] == 0
        assert stats['total_profit'] == 0
        assert stats['success_rate'] == 0


@pytest.mark.asyncio
class TestAsyncStrategies:
    """异步策略测试"""

    async def test_cross_exchange_scan_without_exchange(self):
        """测试没有交易所时的跨交易所扫描"""
        strategy = CrossExchangeArbitrageStrategy({
            'min_profit_rate': 0.5,
            'max_position_size': 1000,
            'symbols': ['BTC/USDT']
        })

        opportunities = await strategy.scan_opportunities()
        assert opportunities == []

    async def test_triangular_scan_without_exchange(self):
        """测试没有交易所时的三角扫描"""
        strategy = TriangularArbitrageStrategy({
            'min_profit_rate': 0.3,
            'max_position_size': 500
        })

        opportunities = await strategy.scan_opportunities("binance")
        assert opportunities == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
