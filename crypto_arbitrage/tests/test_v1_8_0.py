"""V1.8.0 测试套件 (已升级到 V2.0)

测试内容:
1. 版本号一致性验证（现为 V2.0）
2. ExchangeManager 并发价格获取测试
3. StrategyManager 并发扫描测试
4. 配置验证测试
"""

import pytest
import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.exchange_api import ExchangeManager
from strategies.strategy_manager import StrategyManager
from strategies.cross_exchange import CrossExchangeArbitrageStrategy


# ===================== 1. 版本号一致性验证 =====================

class TestVersionConsistency:
    """验证 V2.0 版本号一致性（原 V1.8.0 测试，现已升级）"""

    def test_config_version(self):
        """配置文件应为 V2.0"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, 'config', 'config.yaml')
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'version: "2.0"' in content

    def test_base_version(self):
        """base.py 应为 V2.0"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, 'strategies', 'base.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'V2.0' in content


# ===================== 2. ExchangeManager 并发测试 =====================

class TestExchangeManagerBatch:
    """测试 ExchangeManager 并发价格获取"""

    @pytest.mark.asyncio
    async def test_get_tickers_batch_basic(self):
        """测试批量获取行情基础功能"""
        config = {
            'binance': {'enabled': True, 'api_key': 'test', 'secret': 'test'}
        }
        manager = ExchangeManager(config)

        # 模拟 fetch_ticker
        mock_ticker = {'last': 50000, 'bid': 49999, 'ask': 50001}
        with patch.object(manager.exchanges['binance'], 'fetch_ticker', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_ticker

            result = await manager.get_tickers_batch('binance', ['BTC/USDT', 'ETH/USDT'])

            assert 'BTC/USDT' in result
            assert 'ETH/USDT' in result
            assert result['BTC/USDT']['last'] == 50000
            assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_get_tickers_batch_partial_failure(self):
        """测试部分失败情况"""
        config = {
            'binance': {'enabled': True, 'api_key': 'test', 'secret': 'test'}
        }
        manager = ExchangeManager(config)

        call_count = 0

        async def mock_fetch(symbol):
            nonlocal call_count
            call_count += 1
            if symbol == 'BTC/USDT':
                return {'last': 50000}
            else:
                raise Exception("网络错误")

        with patch.object(manager.exchanges['binance'], 'fetch_ticker', side_effect=mock_fetch):
            result = await manager.get_tickers_batch('binance', ['BTC/USDT', 'ETH/USDT'])

            assert result['BTC/USDT']['last'] == 50000
            assert result['ETH/USDT'] is None  # 失败应为 None
            assert call_count == 2


# ===================== 3. StrategyManager 并发扫描测试 =====================

class TestStrategyManagerConcurrent:
    """测试 StrategyManager 并发扫描"""

    @pytest.mark.asyncio
    async def test_scan_all_strategies_concurrent(self):
        """测试并发扫描策略"""
        config = {'min_opportunity_score': 50}
        manager = StrategyManager(config)

        # 创建两个模拟策略
        mock_strategy1 = MagicMock()
        mock_strategy1.scan_opportunities = AsyncMock(return_value=[
            {'symbol': 'BTC/USDT', 'profit_rate': 1.0}
        ])

        mock_strategy2 = MagicMock()
        mock_strategy2.scan_opportunities = AsyncMock(return_value=[
            {'symbol': 'ETH/USDT', 'profit_rate': 0.8}
        ])

        manager.register_strategy('strategy1', mock_strategy1, 0.3)
        manager.register_strategy('strategy2', mock_strategy2, 0.3)

        # 扫描（应并发执行）
        opportunities = await manager.scan_all_strategies()

        assert len(opportunities) == 2
        assert mock_strategy1.scan_opportunities.call_count == 1
        assert mock_strategy2.scan_opportunities.call_count == 1

    @pytest.mark.asyncio
    async def test_scan_all_handles_strategy_error(self):
        """测试单策略失败不影响其他策略"""
        config = {'min_opportunity_score': 50}
        manager = StrategyManager(config)

        mock_strategy1 = MagicMock()
        mock_strategy1.scan_opportunities = AsyncMock(return_value=[
            {'symbol': 'BTC/USDT', 'profit_rate': 1.0}
        ])

        mock_strategy2 = MagicMock()
        mock_strategy2.scan_opportunities = AsyncMock(side_effect=Exception("策略错误"))

        manager.register_strategy('strategy1', mock_strategy1, 0.3)
        manager.register_strategy('strategy2', mock_strategy2, 0.3)

        # 扫描（strategy2 失败，strategy1 应成功）
        opportunities = await manager.scan_all_strategies()

        assert len(opportunities) == 1
        assert opportunities[0]['symbol'] == 'BTC/USDT'


# ===================== 4. 配置验证测试 =====================

class TestV18ConfigValidation:
    """V1.8.0 配置验证测试"""

    def test_strategy_manager_default_config(self):
        """测试默认配置"""
        config = {}
        manager = StrategyManager(config)

        assert manager.max_total_capital == 10000
        assert manager.max_strategy_allocation == 0.4
        assert manager.min_opportunity_score == 60
        assert manager.signal_aggregation == 'weighted'

    def test_strategy_manager_custom_config(self):
        """测试自定义配置"""
        config = {
            'max_total_capital': 50000,
            'max_strategy_allocation': 0.5,
            'min_opportunity_score': 80,
            'signal_aggregation': 'best'
        }
        manager = StrategyManager(config)

        assert manager.max_total_capital == 50000
        assert manager.max_strategy_allocation == 0.5
        assert manager.min_opportunity_score == 80
        assert manager.signal_aggregation == 'best'


# ===================== 运行测试 =====================

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
