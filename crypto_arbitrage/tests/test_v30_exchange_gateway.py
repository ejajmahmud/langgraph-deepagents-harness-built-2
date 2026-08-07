"""V30.0 增强版套利引擎测试

测试内容:
- 交易所网关初始化
- 多交易所价格获取
- 套利机会扫描
- 风险评分计算
- 执行逻辑测试
"""

import asyncio
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.enhanced_low_risk_arbitrage_v30 import EnhancedLowRiskArbitrageV30
from tools.exchange_gateway import (
    BinanceGateway,
    OKXGateway,
    ExchangeMode,
    create_exchange_gateway,
    TickerPrice,
)


class TestExchangeGateway:
    """交易所网关测试"""

    @pytest.mark.asyncio
    async def test_create_binance_gateway(self):
        """测试创建Binance网关"""
        gateway = create_exchange_gateway('binance', {'mode': 'simulated'})
        assert gateway is not None
        assert gateway.name == 'Binance'
        assert gateway.is_simulated

    @pytest.mark.asyncio
    async def test_create_okx_gateway(self):
        """测试创建OKX网关"""
        gateway = create_exchange_gateway('okx', {'mode': 'simulated'})
        assert gateway is not None
        assert gateway.name == 'OKX'
        assert gateway.is_simulated

    @pytest.mark.asyncio
    async def test_gateway_initialize(self):
        """测试网关初始化"""
        gateway = BinanceGateway({'mode': 'simulated'})
        result = await gateway.initialize()
        assert result is True

    @pytest.mark.asyncio
    async def test_get_ticker(self):
        """测试获取价格数据"""
        gateway = BinanceGateway({'mode': 'simulated'})
        await gateway.initialize()

        # 设置模拟价格
        gateway._simulated_prices['BTC/USDT'] = 50000.0

        ticker = await gateway.get_ticker('BTC/USDT')
        assert ticker is not None
        assert ticker.symbol == 'BTC/USDT'
        assert ticker.last == 50000.0

    @pytest.mark.asyncio
    async def test_get_order_book(self):
        """测试获取订单簿"""
        gateway = BinanceGateway({'mode': 'simulated'})
        await gateway.initialize()

        gateway._simulated_prices['BTC/USDT'] = 50000.0

        order_book = await gateway.get_order_book('BTC/USDT', limit=10)
        assert order_book is not None
        assert len(order_book.bids) == 10
        assert len(order_book.asks) == 10

    @pytest.mark.asyncio
    async def test_get_balance(self):
        """测试获取余额"""
        gateway = BinanceGateway({'mode': 'simulated'})
        await gateway.initialize()

        balance = await gateway.get_balance('BTC')
        assert balance is not None
        assert balance.asset == 'BTC'
        assert balance.free == 0.1

    @pytest.mark.asyncio
    async def test_place_order(self):
        """测试下单"""
        gateway = BinanceGateway({'mode': 'simulated'})
        await gateway.initialize()

        order_id = await gateway.place_order(
            symbol='BTC/USDT',
            side='BUY',
            order_type='MARKET',
            quantity=0.01,
        )
        assert order_id is not None
        assert order_id.startswith('ORDER_')

    @pytest.mark.asyncio
    async def test_batch_ticker(self):
        """测试批量获取价格"""
        gateway = BinanceGateway({'mode': 'simulated'})
        await gateway.initialize()

        gateway._simulated_prices = {
            'BTC/USDT': 50000.0,
            'ETH/USDT': 3000.0,
            'SOL/USDT': 100.0,
        }

        results = await gateway.get_ticker_batch([
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT'
        ])
        assert len(results) >= 2


class TestEnhancedArbitrageV30:
    """V30增强版套利引擎测试"""

    @pytest.mark.asyncio
    async def test_strategy_init(self):
        """测试策略初始化"""
        config = {
            'exchanges': ['binance', 'okx'],
            'symbols': ['BTC/USDT', 'ETH/USDT'],
            'min_spread': 0.3,
            'max_risk_score': 0.7,
            'position_size': 1000,
            'mode': 'simulated',
        }

        strategy = EnhancedLowRiskArbitrageV30(config)
        assert strategy.STRATEGY_NAME == "enhanced_low_risk_v30"
        assert len(strategy._gateways) == 2

    @pytest.mark.asyncio
    async def test_strategy_initialize(self):
        """测试策略初始化"""
        config = {
            'exchanges': ['binance'],
            'symbols': ['BTC/USDT'],
            'mode': 'simulated',
        }

        strategy = EnhancedLowRiskArbitrageV30(config)
        result = await strategy.initialize()
        assert result is True

    @pytest.mark.asyncio
    async def test_scan_opportunities(self):
        """测试扫描套利机会"""
        config = {
            'exchanges': ['binance', 'okx'],
            'symbols': ['BTC/USDT'],
            'min_spread': 0.1,
            'max_risk_score': 0.9,
            'position_size': 1000,
            'mode': 'simulated',
        }

        strategy = EnhancedLowRiskArbitrageV30(config)
        await strategy.initialize()

        # 设置不同价格以产生价差
        binance = strategy._gateways['binance']
        binance._simulated_prices['BTC/USDT'] = 50000.0

        okx = strategy._gateways['okx']
        okx._simulated_prices['BTC/USDT'] = 50100.0

        opportunities = await strategy.scan_opportunities()

        # 应该有价差机会
        assert isinstance(opportunities, list)

    @pytest.mark.asyncio
    async def test_risk_score_calculation(self):
        """测试风险评分计算"""
        config = {
            'exchanges': ['binance'],
            'symbols': ['BTC/USDT'],
            'mode': 'simulated',
        }

        strategy = EnhancedLowRiskArbitrageV30(config)

        # 测试不同场景的风险评分
        risk1 = strategy._calculate_risk_score('binance', 'okx', 0.3)
        risk2 = strategy._calculate_risk_score('binance', 'okx', 0.8)
        risk3 = strategy._calculate_risk_score('binance', 'okx', 2.5)

        # 低价差应该有更高风险
        assert risk1 >= risk2

        # 极高价差应该有额外风险
        assert risk3 >= risk2

    @pytest.mark.asyncio
    async def test_performance_stats(self):
        """测试性能统计"""
        config = {
            'exchanges': ['binance'],
            'symbols': ['BTC/USDT'],
            'mode': 'simulated',
        }

        strategy = EnhancedLowRiskArbitrageV30(config)
        stats = strategy.get_performance_stats()

        assert stats is not None
        assert 'version' in stats
        assert stats['version'] == 'V30.0'


class TestCrossExchangeArbitrage:
    """跨交易所套利测试"""

    @pytest.mark.asyncio
    async def test_multi_exchange_prices(self):
        """测试多交易所价格获取"""
        binance = BinanceGateway({'mode': 'simulated'})
        okx = OKXGateway({'mode': 'simulated'})

        await binance.initialize()
        await okx.initialize()

        # 设置不同价格
        binance._simulated_prices['ETH/USDT'] = 3000.0
        okx._simulated_prices['ETH/USDT'] = 3020.0

        # 获取价格
        binance_ticker = await binance.get_ticker('ETH/USDT')
        okx_ticker = await okx.get_ticker('ETH/USDT')

        assert binance_ticker is not None
        assert okx_ticker is not None

        # 计算价差
        spread_pct = (okx_ticker.last - binance_ticker.last) / binance_ticker.last * 100

        assert spread_pct > 0


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])