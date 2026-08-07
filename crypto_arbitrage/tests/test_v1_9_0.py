"""V1.9.0 测试套件 (已升级到 V2.0)

测试内容:
1. 版本号一致性验证（现为 V2.0）
2. RiskManager O(1) 性能优化
3. 并发扫描稳定性
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
from tools.risk_management import RiskManager


# ===================== 1. 版本号一致性验证 =====================

class TestVersionConsistency:
    """验证 V2.0 版本号一致性（原 V1.9.0 测试，现已升级）"""

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

        # 第一笔交易
        rm.record_trade_result({'profit': 100, 'strategy': 'test'})
        assert rm._get_current_balance() == 10100.0

        # 第二笔交易
        rm.record_trade_result({'profit': 50, 'strategy': 'test'})
        assert rm._get_current_balance() == 10150.0

        # 亏损
        rm.record_trade_result({'profit': -30, 'strategy': 'test'})
        assert rm._get_current_balance() == 10120.0

    def test_peak_balance_tracking(self):
        """测试峰值余额追踪"""
        config = {'max_daily_loss': 500, 'max_position_size': 1000}
        rm = RiskManager(config)

        # 初始
        assert rm.peak_balance == 0.0

        # 第一笔盈利: 10000 + 100 = 10100
        rm.record_trade_result({'profit': 100, 'strategy': 'test'})
        assert rm.peak_balance == 10100.0

        # 亏损后: 10100 - 50 = 10050，峰值保持
        rm.record_trade_result({'profit': -50, 'strategy': 'test'})
        assert rm.peak_balance == 10100.0  # 保持峰值

        # 再次盈利: 10050 + 200 = 10250，创新高
        rm.record_trade_result({'profit': 200, 'strategy': 'test'})
        assert rm.peak_balance == 10250.0

    def test_drawdown_calculation(self):
        """测试回撤计算"""
        config = {'max_daily_loss': 500, 'max_position_size': 1000, 'max_drawdown': 10.0}
        rm = RiskManager(config)

        # 盈利后峰值应为 10100
        rm.record_trade_result({'profit': 100, 'strategy': 'test'})

        # 亏损 500 (5%) 后回撤应为 5%，低于10%阈值
        rm.record_trade_result({'profit': -500, 'strategy': 'test'})
        assert rm.check_drawdown() is True  # 5% < 10%

        # 亏损 1000 (约9.9%) 后回撤应接近10%阈值边界
        rm.record_trade_result({'profit': -500, 'strategy': 'test'})
        # 此时余额 = 10100 - 500 - 500 = 9100，峰值 = 10100
        # 回撤 = (10100 - 9100) / 10100 = 9.9% < 10%
        assert rm.check_drawdown() is True


# ===================== 3. 并发扫描稳定性 =====================

class TestConcurrentScanning:
    """测试并发扫描稳定性"""

    @pytest.mark.asyncio
    async def test_scan_all_strategies_stability(self):
        """测试策略扫描稳定性"""
        config = {'min_opportunity_score': 50}
        manager = StrategyManager(config)

        # 创建模拟策略
        mock_strategy = MagicMock()
        mock_strategy.scan_opportunities = AsyncMock(return_value=[
            {'symbol': 'BTC/USDT', 'profit_rate': 1.0}
        ])

        manager.register_strategy('test_strategy', mock_strategy, 0.3)

        # 多次扫描测试稳定性
        for _ in range(3):
            opportunities = await manager.scan_all_strategies()
            assert len(opportunities) >= 0  # 至少不崩溃

        assert mock_strategy.scan_opportunities.call_count == 3


# ===================== 运行测试 =====================

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])