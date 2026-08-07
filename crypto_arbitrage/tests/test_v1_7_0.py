"""V1.7.0 测试套件

测试内容:
1. 策略继承验证 - 所有5个策略正确继承 BaseStrategy
2. 重复代码消除验证 - 确认无独立 get_performance_stats
3. 硬编码交易所修复验证
4. 双重记录修复验证
5. BaseStrategy Memo0 集成测试
6. 交易循环增强测试
7. 策略配置验证测试
"""

import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.base import BaseStrategy, StrategyState
from strategies.cross_exchange import CrossExchangeArbitrageStrategy
from strategies.triangular_arbitrage import TriangularArbitrageStrategy
from strategies.basis_trading import BasisTradingStrategy
from strategies.funding_rate import FundingRateArbitrageStrategy
from strategies.statistical_arbitrage import StatisticalArbitrageStrategy


# ===================== 辅助函数 =====================

def make_base_config(**overrides):
    """创建基础策略配置"""
    config = {'min_profit_rate': 0.5, 'max_position_size': 1000}
    config.update(overrides)
    return config


# ===================== 1. 继承验证测试 =====================

class TestInheritance:
    """验证所有策略正确继承 BaseStrategy"""

    def test_cross_exchange_inherits_base(self):
        assert issubclass(CrossExchangeArbitrageStrategy, BaseStrategy)
        assert CrossExchangeArbitrageStrategy.STRATEGY_NAME == "cross_exchange"

    def test_triangular_inherits_base(self):
        assert issubclass(TriangularArbitrageStrategy, BaseStrategy)
        assert TriangularArbitrageStrategy.STRATEGY_NAME == "triangular"

    def test_basis_trading_inherits_base(self):
        assert issubclass(BasisTradingStrategy, BaseStrategy)
        assert BasisTradingStrategy.STRATEGY_NAME == "basis_trading"

    def test_funding_rate_inherits_base(self):
        assert issubclass(FundingRateArbitrageStrategy, BaseStrategy)
        assert FundingRateArbitrageStrategy.STRATEGY_NAME == "funding_rate"

    def test_statistical_arbitrage_inherits_base(self):
        assert issubclass(StatisticalArbitrageStrategy, BaseStrategy)
        assert StatisticalArbitrageStrategy.STRATEGY_NAME == "statistical_arbitrage"

    def test_all_have_strategy_description(self):
        strategies = [
            CrossExchangeArbitrageStrategy,
            TriangularArbitrageStrategy,
            BasisTradingStrategy,
            FundingRateArbitrageStrategy,
            StatisticalArbitrageStrategy,
        ]
        for cls in strategies:
            assert hasattr(cls, 'STRATEGY_DESCRIPTION')
            assert len(cls.STRATEGY_DESCRIPTION) > 5


# ===================== 2. 重复代码消除验证 =====================

class TestNoDuplicateMethods:
    """确认重构后没有重复的 get_performance_stats"""

    def test_no_own_get_performance_stats(self):
        """策略不应有自己的 get_performance_stats（应继承基类）"""
        strategies = [
            CrossExchangeArbitrageStrategy,
            TriangularArbitrageStrategy,
            BasisTradingStrategy,
            FundingRateArbitrageStrategy,
            StatisticalArbitrageStrategy,
        ]
        for cls in strategies:
            # 检查 get_performance_stats 是否定义在基类中而非子类
            assert 'get_performance_stats' not in cls.__dict__, \
                f"{cls.__name__} 不应有独立的 get_performance_stats"

    def test_all_have_base_get_performance_stats(self):
        """所有策略应通过继承获得 get_performance_stats"""
        strategies = [
            CrossExchangeArbitrageStrategy,
            TriangularArbitrageStrategy,
            BasisTradingStrategy,
            FundingRateArbitrageStrategy,
            StatisticalArbitrageStrategy,
        ]
        for cls in strategies:
            instance = cls(make_base_config())
            assert hasattr(instance, 'get_performance_stats')
            stats = instance.get_performance_stats()
            assert 'total_trades' in stats
            assert 'success_rate' in stats
            assert 'state' in stats


# ===================== 3. 硬编码交易所修复验证 =====================

class TestNoHardcodedExchange:
    """确认没有 list(exchanges.keys())[0] 硬编码"""

    def test_no_list_keys_zero_in_source(self):
        """扫描源码确认无硬编码交易所"""
        files = [
            'strategies/basis_trading.py',
            'strategies/funding_rate.py',
            'strategies/statistical_arbitrage.py',
        ]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for filepath in files:
            full_path = os.path.join(base_dir, filepath)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert 'list(exchanges.keys())[0]' not in content, \
                f"{filepath} 仍包含硬编码交易所 list(exchanges.keys())[0]"

    def test_funding_rate_has_preferred_exchange(self):
        """funding_rate 策略应有 preferred_exchange 属性"""
        strategy = FundingRateArbitrageStrategy(make_base_config(
            symbols=['BTC/USDT:USDT'],
            spot_symbols=['BTC/USDT']
        ))
        assert hasattr(strategy, 'preferred_exchange')

    def test_statistical_arbitrage_has_preferred_exchange(self):
        """statistical_arbitrage 策略应有 preferred_exchange 属性"""
        strategy = StatisticalArbitrageStrategy(make_base_config())
        assert hasattr(strategy, 'preferred_exchange')

    def test_get_exchange_name_returns_preferred(self):
        """_get_exchange_name 应优先返回 preferred_exchange"""
        strategy = FundingRateArbitrageStrategy(make_base_config(
            preferred_exchange='binance',
            symbols=['BTC/USDT:USDT'],
            spot_symbols=['BTC/USDT']
        ))
        mock_manager = MagicMock()
        mock_manager.exchanges = {'binance': MagicMock(), 'okx': MagicMock()}
        result = strategy._get_exchange_name(mock_manager)
        assert result == 'binance'


# ===================== 4. 双重记录修复验证 =====================

class TestNoDoubleRecord:
    """确认 execute_arbitrage 中不再双重调用 _record_trade"""

    def test_cross_exchange_no_double_record(self):
        """cross_exchange execute_arbitrage 不应直接调用 _record_trade"""
        content = open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'strategies/cross_exchange.py'
        ), 'r', encoding='utf-8').read()

        # 在 execute_arbitrage 方法中不应有 self._record_trade
        exec_start = content.find('async def execute_arbitrage')
        next_method = content.find('\n    async def ', exec_start + 1)
        exec_body = content[exec_start:next_method] if next_method > 0 else content[exec_start:]

        assert 'self._record_trade' not in exec_body, \
            "cross_exchange.execute_arbitrage 不应直接调用 _record_trade"

    def test_triangular_no_double_record(self):
        """triangular execute_arbitrage 不应直接调用 _record_trade"""
        content = open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'strategies/triangular_arbitrage.py'
        ), 'r', encoding='utf-8').read()

        exec_start = content.find('async def execute_arbitrage')
        next_method = content.find('\n    async def ', exec_start + 1)
        exec_body = content[exec_start:next_method] if next_method > 0 else content[exec_start:]

        assert 'self._record_trade' not in exec_body, \
            "triangular.execute_arbitrage 不应直接调用 _record_trade"


# ===================== 5. 重复初始化修复验证 =====================

class TestNoDuplicateInit:
    """确认 triangular_arbitrage 不再重复初始化 triangles"""

    def test_triangles_not_assigned_twice(self):
        """self.triangles 不应被赋值两次"""
        content = open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'strategies/triangular_arbitrage.py'
        ), 'r', encoding='utf-8').read()

        count = content.count('self.triangles = config.get')
        assert count == 1, f"self.triangles 被赋值 {count} 次，应为 1 次"


# ===================== 6. BaseStrategy Memo0 集成测试 =====================

class TestBaseStrategyMemo0:
    """测试 BaseStrategy 的 Memo0 知识记录功能"""

    def test_record_trade_to_memory_success(self):
        """成功交易应记录到知识库"""
        strategy = CrossExchangeArbitrageStrategy(make_base_config())
        with patch('storage.mem0_storage.add_trading_knowledge') as mock_add:
            strategy._record_trade_to_memory({
                'status': 'completed',
                'symbol': 'BTC/USDT',
                'actual_profit': 5.0,
                'actual_profit_rate': 0.5,
            })
            mock_add.assert_called_once()
            args = mock_add.call_args
            assert args[0][0] == 'trade_success'
            assert 'BTC/USDT' in args[0][1]
            assert '$5.00' in args[0][1]

    def test_record_trade_to_memory_failure(self):
        """失败交易应记录到知识库"""
        strategy = CrossExchangeArbitrageStrategy(make_base_config())
        with patch('storage.mem0_storage.add_trading_knowledge') as mock_add:
            strategy._record_trade_to_memory({
                'status': 'failed',
                'symbol': 'ETH/USDT',
                'error': '余额不足',
            })
            mock_add.assert_called_once()
            args = mock_add.call_args
            assert args[0][0] == 'trade_failure'
            assert '余额不足' in args[0][1]

    def test_record_trade_to_memory_silent_on_error(self):
        """Memo0 不可用时应静默失败"""
        strategy = CrossExchangeArbitrageStrategy(make_base_config())
        with patch('storage.mem0_storage.add_trading_knowledge', side_effect=Exception("no storage")):
            # 不应抛出异常
            strategy._record_trade_to_memory({
                'status': 'completed',
                'symbol': 'BTC/USDT',
            })


# ===================== 7. 策略配置验证测试 =====================

class TestConfigValidation:
    """测试策略配置验证"""

    def test_basis_trading_requires_futures_exchange(self):
        """基差套利必须配置 futures_exchange"""
        strategy = BasisTradingStrategy(make_base_config())
        errors = strategy.validate_config()
        assert any('futures_exchange' in e for e in errors)

    def test_basis_trading_valid_with_futures(self):
        """配置 futures_exchange 后应通过验证"""
        strategy = BasisTradingStrategy(make_base_config(
            futures_exchange='binance'
        ))
        errors = strategy.validate_config()
        assert not any('futures_exchange' in e for e in errors)

    def test_funding_rate_symbol_mismatch(self):
        """永续和现货交易对数量不匹配应报错"""
        strategy = FundingRateArbitrageStrategy(make_base_config(
            symbols=['BTC/USDT:USDT', 'ETH/USDT:USDT'],
            spot_symbols=['BTC/USDT']  # 不匹配
        ))
        errors = strategy.validate_config()
        assert any('不匹配' in e for e in errors)

    def test_all_strategies_start_in_initialized(self):
        """所有策略创建后应处于 INITIALIZED 状态"""
        strategies = [
            CrossExchangeArbitrageStrategy(make_base_config()),
            TriangularArbitrageStrategy(make_base_config()),
            BasisTradingStrategy(make_base_config(futures_exchange='binance')),
            FundingRateArbitrageStrategy(make_base_config(
                symbols=['BTC/USDT:USDT'],
                spot_symbols=['BTC/USDT']
            )),
            StatisticalArbitrageStrategy(make_base_config()),
        ]
        for s in strategies:
            assert s.state == StrategyState.INITIALIZED
            assert s.is_healthy

    def test_strategy_lifecycle(self):
        """测试策略生命周期"""
        strategy = CrossExchangeArbitrageStrategy(make_base_config())
        assert strategy.state == StrategyState.INITIALIZED

        strategy.start()
        assert strategy.state == StrategyState.RUNNING
        assert strategy.is_running

        strategy.pause()
        assert strategy.state == StrategyState.PAUSED
        assert not strategy.is_running

        strategy.resume()
        assert strategy.state == StrategyState.RUNNING

        strategy.stop()
        assert strategy.state == StrategyState.STOPPED


# ===================== 8. 版本号验证 =====================

class TestVersionConsistency:
    """验证版本号一致性"""

    def test_main_agent_version(self):
        """main_agent.py 应使用 V1.7.0"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, 'agents', 'main_agent.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # V1.7.0 应在日志输出中
        assert content.count('V1.7.0') >= 2  # 至少两处（初始化+循环）
        # 不应有 V1.4.0 或 V1.5.0 的日志
        assert 'V1.4.0 完整版' not in content
        assert 'V1.5.0 初始化完成' not in content

    def test_base_version(self):
        """base.py 应使用 V1.7.0"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, 'strategies', 'base.py')
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'V1.7.0' in content


# ===================== 运行测试 =====================

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
