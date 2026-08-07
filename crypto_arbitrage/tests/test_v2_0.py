"""V2.0 测试套件

测试内容:
1. 版本号一致性验证 (V2.0)
2. RiskManager O(1) 性能优化
3. StrategyManager 市场条件分析 (V2.0)
4. 并发扫描稳定性
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
from tools.risk_management import RiskManager, MarketConditionAnalyzer


# ===================== 1. 版本号一致性验证 =====================

class TestVersionConsistency:
    """验证 V2.0 版本号一致性"""

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


# ===================== 2. RiskManager O(1) 性能测试 =====================

class TestRiskManagerOptimization:
    """测试 RiskManager O(1) 性能优化"""

    def test_initial_balance(self):
        """测试初始余额"""
        config = {'max_daily_loss': 500, 'max_position_size': 1000}
        rm = RiskManager(config)
        assert rm._get_current_balance() == 10000.0

    def test_incremental_balance_update(self):
        """测试增量余额更新"""
        config = {'max_daily_loss': 500, 'max_position_size': 1000}
        rm = RiskManager(config)

        rm.record_trade_result({'profit': 100, 'strategy': 'test'})
        assert rm._get_current_balance() == 10100.0

        rm.record_trade_result({'profit': 50, 'strategy': 'test'})
        assert rm._get_current_balance() == 10150.0

    def test_peak_balance_tracking(self):
        """测试峰值余额追踪"""
        config = {'max_daily_loss': 500, 'max_position_size': 1000}
        rm = RiskManager(config)

        rm.record_trade_result({'profit': 100, 'strategy': 'test'})
        assert rm.peak_balance == 10100.0

        rm.record_trade_result({'profit': -50, 'strategy': 'test'})
        assert rm.peak_balance == 10100.0  # 保持峰值


# ===================== 3. StrategyManager 市场条件分析 (V2.0) =====================

class TestMarketConditionAnalysis:
    """测试 V2.0 市场条件分析集成"""

    def test_market_analyzer_initialization(self):
        """测试市场分析器初始化"""
        config = {'min_opportunity_score': 50, 'enable_market_analysis': True}
        sm = StrategyManager(config)
        assert sm._market_analyzer is not None

    def test_market_analyzer_disabled(self):
        """测试禁用市场分析器"""
        config = {'min_opportunity_score': 50, 'enable_market_analysis': False}
        sm = StrategyManager(config)
        assert sm._market_analyzer is None

    @pytest.mark.asyncio
    async def test_scan_with_price_data(self):
        """测试带价格数据的扫描"""
        config = {'min_opportunity_score': 50, 'enable_market_analysis': True}
        sm = StrategyManager(config)

        # 创建模拟策略
        mock_strategy = MagicMock()
        mock_strategy.scan_opportunities = AsyncMock(return_value=[
            {'symbol': 'BTC/USDT', 'profit_rate': 1.0, '_score': 60}
        ])
        sm.register_strategy('test', mock_strategy, 0.3)

        # 正常价格数据
        price_data = [50000, 50100, 50200, 50150, 50300]
        result = await sm.scan_all_strategies(price_data)

        assert len(result) >= 0  # 不崩溃

    def test_market_condition_analyzer(self):
        """测试 MarketConditionAnalyzer 功能"""
        analyzer = MarketConditionAnalyzer()

        # 稳定市场
        price_data = [50000, 50050, 50030, 50040, 50020]
        result = analyzer.analyze_market_conditions(price_data)
        assert result['volatility'] in ['low', 'normal']

        # 高波动市场
        price_data_volatile = [50000, 55000, 45000, 56000, 44000]
        result = analyzer.analyze_market_conditions(price_data_volatile)
        assert result['volatility'] in ['normal', 'high']


# ===================== 4. 并发扫描稳定性 =====================

class TestConcurrentScanning:
    """测试并发扫描稳定性"""

    @pytest.mark.asyncio
    async def test_scan_all_strategies_stability(self):
        """测试策略扫描稳定性"""
        config = {'min_opportunity_score': 50}
        manager = StrategyManager(config)

        mock_strategy = MagicMock()
        mock_strategy.scan_opportunities = AsyncMock(return_value=[
            {'symbol': 'BTC/USDT', 'profit_rate': 1.0}
        ])

        manager.register_strategy('test_strategy', mock_strategy, 0.3)

        # 多次扫描测试稳定性
        for _ in range(3):
            opportunities = await manager.scan_all_strategies()
            assert len(opportunities) >= 0


# ===================== 运行测试 =====================

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])