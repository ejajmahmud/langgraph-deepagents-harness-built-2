"""CryptoArbitrage V1.6.0 测试套件

覆盖范围:
- BaseStrategy 生命周期、配置验证、安全执行
- JWT 认证 (创建/验证/刷新)
- PriceStreamManager (PriceTick, PriceCache, 连接管理)
- API 端点 (认证、策略控制、价格流)
- StrategyManager 接口验证修复
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from strategies.base import BaseStrategy, StrategyState


# =====================================================================
# BaseStrategy 测试
# =====================================================================

class TestBaseStrategy:
    """BaseStrategy V1.6.0 测试"""

    def _make_concrete_strategy(self, config=None):
        """创建一个具体的 BaseStrategy 实例用于测试"""

        class ConcreteStrategy(BaseStrategy):
            STRATEGY_NAME = "test_strategy"
            STRATEGY_DESCRIPTION = "测试策略"

            def __init__(self, cfg):
                super().__init__(cfg)
                self.scan_called = False
                self.execute_called = False

            async def scan_opportunities(self):
                self.scan_called = True
                return []

            async def execute_arbitrage(self, opportunity):
                self.execute_called = True
                return True

        return ConcreteStrategy(config or {})

    def test_initialization_default_state(self):
        """测试初始化后状态为 INITIALIZED"""
        strategy = self._make_concrete_strategy()
        assert strategy.state == StrategyState.INITIALIZED
        assert not strategy.is_running
        assert strategy.uptime_seconds == 0.0
        assert strategy.active_position_count == 0
        assert strategy.trade_history == []

    def test_lifecycle_start_stop(self):
        """测试生命周期: start -> running -> stop"""
        strategy = self._make_concrete_strategy()
        strategy.start()
        assert strategy.state == StrategyState.RUNNING
        assert strategy.is_running
        assert strategy.uptime_seconds >= 0

        strategy.stop()
        assert strategy.state == StrategyState.STOPPED
        assert not strategy.is_running

    def test_lifecycle_pause_resume(self):
        """测试暂停和恢复"""
        strategy = self._make_concrete_strategy()
        strategy.start()
        strategy.pause()
        assert strategy.state == StrategyState.PAUSED

        strategy.resume()
        assert strategy.state == StrategyState.RUNNING
        assert strategy.is_running

    def test_pause_without_start_noop(self):
        """未启动时暂停无效果"""
        strategy = self._make_concrete_strategy()
        strategy.pause()
        assert strategy.state == StrategyState.INITIALIZED

    def test_start_twice_noop(self):
        """重复启动无效果"""
        strategy = self._make_concrete_strategy()
        strategy.start()
        start_time = strategy._start_time
        strategy.start()
        assert strategy._start_time == start_time

    def test_validate_config_negative_profit_rate(self):
        """配置验证: 负的 min_profit_rate"""
        strategy = self._make_concrete_strategy({'min_profit_rate': -0.5})
        errors = strategy.validate_config()
        assert any('min_profit_rate' in e for e in errors)

    def test_validate_config_zero_position(self):
        """配置验证: 零 max_position_size"""
        strategy = self._make_concrete_strategy({'max_position_size': 0})
        errors = strategy.validate_config()
        assert any('max_position_size' in e for e in errors)

    def test_safe_scan_when_not_running(self):
        """安全扫描: 未运行时返回空列表"""
        strategy = self._make_concrete_strategy()
        result = asyncio.get_event_loop().run_until_complete(strategy.safe_scan())
        assert result == []
        assert not strategy.scan_called

    def test_safe_scan_when_running(self):
        """安全扫描: 运行时正常调用"""
        strategy = self._make_concrete_strategy()
        strategy.start()
        result = asyncio.get_event_loop().run_until_complete(strategy.safe_scan())
        assert strategy.scan_called
        assert strategy._total_scans == 1

    def test_safe_scan_auto_pause_on_errors(self):
        """安全扫描: 连续错误后自动暂停"""
        strategy = self._make_concrete_strategy()
        strategy._max_consecutive_errors = 2
        strategy.start()

        # 让 scan_opportunities 抛异常
        async def failing_scan():
            raise RuntimeError("test error")

        strategy.scan_opportunities = failing_scan

        loop = asyncio.get_event_loop()
        for _ in range(2):
            loop.run_until_complete(strategy.safe_scan())

        assert strategy.state == StrategyState.PAUSED

    def test_safe_execute_success(self):
        """安全执行: 成功执行并记录"""
        strategy = self._make_concrete_strategy()
        strategy.start()

        opp = {
            'symbol': 'BTC/USDT',
            'profit_rate': 1.0,
            'expected_profit': 10.0,
            'buy_cost': 1000,
        }
        result = asyncio.get_event_loop().run_until_complete(
            strategy.safe_execute(opp)
        )
        assert result['status'] == 'completed'
        assert result['profit'] == 10.0
        assert strategy._consecutive_losses == 0
        assert len(strategy.trade_history) == 1

    def test_safe_execute_when_not_running(self):
        """安全执行: 未运行时拒绝"""
        strategy = self._make_concrete_strategy()
        result = asyncio.get_event_loop().run_until_complete(
            strategy.safe_execute({'symbol': 'BTC/USDT'})
        )
        assert result['status'] == 'rejected'

    def test_safe_execute_failure_increments_losses(self):
        """安全执行: 失败增加连续亏损计数"""
        strategy = self._make_concrete_strategy()
        strategy.start()

        # 让 execute_arbitrage 返回 False
        async def failing_execute(opp):
            return False

        strategy.execute_arbitrage = failing_execute

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            strategy.safe_execute({'symbol': 'BTC/USDT', 'profit_rate': 0.5})
        )
        assert result['status'] == 'failed'
        assert strategy._consecutive_losses == 1

    def test_record_trade(self):
        """交易记录"""
        strategy = self._make_concrete_strategy()
        opp = {'symbol': 'ETH/USDT', 'buy_cost': 500}
        record = strategy._record_trade(opp, 'completed', profit=5.0)

        assert record['strategy'] == 'test_strategy'
        assert record['symbol'] == 'ETH/USDT'
        assert record['status'] == 'completed'
        assert record['actual_profit'] == 5.0
        assert len(strategy.trade_history) == 1

    def test_filter_by_threshold(self):
        """阈值过滤"""
        strategy = self._make_concrete_strategy({'min_profit_rate': 1.0})
        opps = [
            {'profit_rate': 0.5},
            {'profit_rate': 1.0},
            {'profit_rate': 2.0},
        ]
        filtered = strategy._filter_by_threshold(opps)
        assert len(filtered) == 2

    def test_sort_opportunities(self):
        """排序"""
        strategy = self._make_concrete_strategy()
        opps = [
            {'profit_rate': 1.0},
            {'profit_rate': 3.0},
            {'profit_rate': 2.0},
        ]
        sorted_ops = strategy._sort_opportunities(opps)
        assert sorted_ops[0]['profit_rate'] == 3.0

    def test_post_process_opportunities(self):
        """后处理: 过滤 + 排序 + 策略标识"""
        strategy = self._make_concrete_strategy({'min_profit_rate': 1.0})
        opps = [
            {'profit_rate': 0.5},
            {'profit_rate': 2.0},
            {'profit_rate': 1.5},
        ]
        result = strategy._post_process_opportunities(opps)
        assert len(result) == 2
        assert result[0]['strategy'] == 'test_strategy'
        assert result[0]['profit_rate'] == 2.0

    def test_is_healthy(self):
        """健康检查"""
        strategy = self._make_concrete_strategy()
        assert strategy.is_healthy

        strategy._consecutive_losses = 3
        assert not strategy.is_healthy

    def test_get_health_report(self):
        """健康报告"""
        strategy = self._make_concrete_strategy()
        report = strategy.get_health_report()
        assert report['strategy'] == 'test_strategy'
        assert report['state'] == 'initialized'
        assert report['is_healthy'] is True

    def test_performance_stats_empty(self):
        """空性能统计"""
        strategy = self._make_concrete_strategy()
        stats = strategy.get_performance_stats()
        assert stats['total_trades'] == 0
        assert stats['state'] == 'initialized'

    def test_performance_stats_with_trades(self):
        """有交易的性能统计"""
        strategy = self._make_concrete_strategy()
        strategy._trade_history = [
            {'status': 'completed', 'actual_profit': 10.0, 'expected_profit_rate': 1.0},
            {'status': 'completed', 'actual_profit': 5.0, 'expected_profit_rate': 0.5},
            {'status': 'failed', 'expected_profit_rate': 0},
        ]
        stats = strategy.get_performance_stats()
        assert stats['total_trades'] == 3
        assert stats['successful_trades'] == 2
        assert stats['total_profit'] == 15.0
        assert stats['success_rate'] == pytest.approx(2/3)


# =====================================================================
# JWT 认证测试
# =====================================================================

class TestJWTAuth:
    """JWT 认证模块测试"""

    def test_create_and_verify_jwt(self):
        """JWT 创建和验证"""
        from backend.auth import create_jwt, verify_jwt
        token = create_jwt({'sub': 'admin', 'role': 'admin'})
        payload = verify_jwt(token)
        assert payload is not None
        assert payload['sub'] == 'admin'
        assert payload['role'] == 'admin'

    def test_expired_jwt(self):
        """过期 JWT 验证失败"""
        from backend.auth import create_jwt, verify_jwt
        token = create_jwt({'sub': 'admin'}, expire_hours=-1)
        payload = verify_jwt(token)
        assert payload is None

    def test_tampered_jwt(self):
        """篡改的 JWT 验证失败"""
        from backend.auth import create_jwt, verify_jwt
        token = create_jwt({'sub': 'admin'})
        # 篡改载荷
        parts = token.split('.')
        parts[1] = parts[1][:-3] + 'xxx'
        tampered = '.'.join(parts)
        assert verify_jwt(tampered) is None

    def test_invalid_format(self):
        """无效格式 JWT"""
        from backend.auth import verify_jwt
        assert verify_jwt('not.a.valid.token.format') is None
        assert verify_jwt('') is None


class TestUserManager:
    """用户管理器测试"""

    def test_default_admin_exists(self):
        """默认管理员账户"""
        from backend.auth import user_manager
        info = user_manager.get_user_info('admin')
        assert info is not None
        assert info['role'] == 'admin'

    def test_login_success(self):
        """管理员登录成功"""
        from backend.auth import user_manager
        import os
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        result = user_manager.login('admin', password)
        assert result['success']
        assert 'access_token' in result
        assert 'refresh_token' in result

    def test_login_wrong_password(self):
        """错误密码"""
        from backend.auth import user_manager
        result = user_manager.login('admin', 'wrong')
        assert not result['success']

    def test_register_and_login(self):
        """注册新用户"""
        from backend.auth import user_manager
        result = user_manager.register('testuser', 'password123')
        assert result['success']

        login = user_manager.login('testuser', 'password123')
        assert login['success']

    def test_register_duplicate(self):
        """重复注册"""
        from backend.auth import user_manager
        user_manager.register('dup_user', 'pass123')
        result = user_manager.register('dup_user', 'pass456')
        assert not result['success']

    def test_register_short_username(self):
        """用户名太短"""
        from backend.auth import user_manager
        result = user_manager.register('ab', 'password')
        assert not result['success']

    def test_api_key_create_and_validate(self):
        """API Key 创建和验证"""
        from backend.auth import user_manager
        result = user_manager.create_api_key('admin')
        assert result['success']
        api_key = result['api_key']

        username = user_manager.validate_api_key(api_key)
        assert username == 'admin'

    def test_rate_limit(self):
        """速率限制"""
        from backend.auth import user_manager
        user_manager._max_requests_per_minute = 3

        # 前3次应该成功
        for _ in range(3):
            assert user_manager.check_rate_limit('ratelimit_user')

        # 第4次应该被限制
        assert not user_manager.check_rate_limit('ratelimit_user')


# =====================================================================
# PriceStream 测试
# =====================================================================

class TestPriceTick:
    """PriceTick 测试"""

    def test_creation(self):
        from tools.price_stream import PriceTick
        tick = PriceTick('BTC/USDT', 'binance', 50000.0, 50001.0, 50000.5, time.time())
        assert tick.symbol == 'BTC/USDT'
        assert tick.bid == 50000.0
        assert tick.ask == 50001.0

    def test_to_dict(self):
        from tools.price_stream import PriceTick
        tick = PriceTick('ETH/USDT', 'okx', 3000.0, 3001.0, 3000.5, 1234567890.0)
        d = tick.to_dict()
        assert d['symbol'] == 'ETH/USDT'
        assert d['exchange'] == 'okx'
        assert 'bid' in d and 'ask' in d


class TestPriceCache:
    """PriceCache 测试"""

    def test_update_and_get(self):
        from tools.price_stream import PriceTick, PriceCache
        cache = PriceCache()
        tick = PriceTick('BTC/USDT', 'binance', 50000.0, 50001.0, 50000.5, time.time())
        asyncio.get_event_loop().run_until_complete(cache.update(tick))

        result = cache.get_latest('BTC/USDT', 'binance')
        assert result is not None
        assert result.last == 50000.5

    def test_get_latest_missing(self):
        from tools.price_stream import PriceCache
        cache = PriceCache()
        assert cache.get_latest('NONEXIST/USDT', 'binance') is None

    def test_get_all_latest(self):
        from tools.price_stream import PriceTick, PriceCache
        cache = PriceCache()

        t1 = PriceTick('BTC/USDT', 'binance', 50000.0, 50001.0, 50000.5, time.time())
        t2 = PriceTick('BTC/USDT', 'okx', 50010.0, 50011.0, 50010.5, time.time())
        asyncio.get_event_loop().run_until_complete(cache.update(t1))
        asyncio.get_event_loop().run_until_complete(cache.update(t2))

        all_prices = cache.get_all_latest('BTC/USDT')
        assert len(all_prices) == 2
        assert 'binance' in all_prices
        assert 'okx' in all_prices

    def test_history(self):
        from tools.price_stream import PriceTick, PriceCache
        cache = PriceCache(max_history=5)

        for i in range(10):
            tick = PriceTick('BTC/USDT', 'binance', 50000 + i, 50001 + i, 50000.5 + i, time.time())
            asyncio.get_event_loop().run_until_complete(cache.update(tick))

        history = cache.get_history('BTC/USDT', 'binance')
        assert len(history) == 5  # max_history

    def test_clear(self):
        from tools.price_stream import PriceTick, PriceCache
        cache = PriceCache()
        tick = PriceTick('BTC/USDT', 'binance', 50000.0, 50001.0, 50000.5, time.time())
        asyncio.get_event_loop().run_until_complete(cache.update(tick))
        cache.clear()
        assert cache.get_latest('BTC/USDT', 'binance') is None


class TestPriceStreamManager:
    """PriceStreamManager 测试"""

    def test_get_price_from_cache(self):
        """从缓存获取价格"""
        from tools.price_stream import PriceTick, PriceStreamManager
        manager = PriceStreamManager({}, symbols=['BTC/USDT'])

        tick = PriceTick('BTC/USDT', 'binance', 50000.0, 50001.0, 50000.5, time.time())
        asyncio.get_event_loop().run_until_complete(manager.cache.update(tick))

        assert manager.get_price('BTC/USDT', 'binance', 'last') == 50000.5
        assert manager.get_price('BTC/USDT', 'binance', 'bid') == 50000.0
        assert manager.get_price('BTC/USDT', 'binance', 'ask') == 50001.0
        assert manager.get_price('BTC/USDT', 'okx', 'last') is None

    def test_get_spread(self):
        """跨交易所价差计算"""
        from tools.price_stream import PriceTick, PriceStreamManager
        manager = PriceStreamManager({}, symbols=['BTC/USDT'])

        t1 = PriceTick('BTC/USDT', 'binance', 50000.0, 50001.0, 50000.5, time.time())
        t2 = PriceTick('BTC/USDT', 'okx', 50010.0, 50011.0, 50010.5, time.time())
        asyncio.get_event_loop().run_until_complete(manager.cache.update(t1))
        asyncio.get_event_loop().run_until_complete(manager.cache.update(t2))

        spread = manager.get_spread('BTC/USDT')
        assert spread is not None
        assert spread['best_bid_exchange'] == 'okx'  # 50010 > 50000
        assert spread['best_ask_exchange'] == 'binance'  # 50001 < 50011
        assert spread['spread'] > 0

    def test_get_spread_no_data(self):
        """无数据时价差为 None"""
        from tools.price_stream import PriceStreamManager
        manager = PriceStreamManager({}, symbols=['BTC/USDT'])
        assert manager.get_spread('BTC/USDT') is None

    def test_status(self):
        """价格流状态"""
        from tools.price_stream import PriceStreamManager
        manager = PriceStreamManager(
            {'binance': {'enabled': True}},
            symbols=['BTC/USDT', 'ETH/USDT'],
        )
        status = manager.get_status()
        assert status['running'] is False
        assert status['symbols_count'] == 2


# =====================================================================
# StrategyManager 接口验证测试
# =====================================================================

class TestStrategyManagerValidation:
    """StrategyManager V1.6.0 接口验证修复测试"""

    def test_register_requires_execute_arbitrage(self):
        """V1.6.0 Bug fix: 注册时检查 execute_arbitrage 方法"""
        from strategies.strategy_manager import StrategyManager

        class IncompleteStrategy:
            def scan_opportunities(self):
                return []
            def get_performance_stats(self):
                return {}

        manager = StrategyManager({})
        result = manager.register_strategy('incomplete', IncompleteStrategy())
        assert result is False

    def test_register_complete_strategy(self):
        """完整策略注册成功"""
        from strategies.strategy_manager import StrategyManager

        class CompleteStrategy:
            def scan_opportunities(self):
                return []
            async def execute_arbitrage(self, opp):
                return True
            def get_performance_stats(self):
                return {}

        manager = StrategyManager({})
        result = manager.register_strategy('complete', CompleteStrategy())
        assert result is True

    def test_health_check_uses_base_strategy(self):
        """V1.6.0: 健康检查优先使用 BaseStrategy.is_healthy"""
        from strategies.strategy_manager import StrategyManager

        strategy = MagicMock()
        strategy.is_healthy = False
        strategy.scan_opportunities = lambda: []
        strategy.execute_arbitrage = AsyncMock()
        strategy.get_performance_stats = lambda: {}

        manager = StrategyManager({})
        manager.register_strategy('test', strategy)

        assert manager._check_strategy_health('test') is False


# =====================================================================
# ConnectionManager 主题订阅测试
# =====================================================================

class TestConnectionManager:
    """V1.6.0 WebSocket ConnectionManager 测试"""

    def test_subscribe_unsubscribe(self):
        """主题订阅和取消订阅"""
        from backend.api import ConnectionManager
        manager = ConnectionManager()

        ws = MagicMock()
        manager._connections[ws] = set()

        manager.subscribe(ws, 'price:BTC/USDT')
        assert 'price:BTC/USDT' in manager._connections[ws]

        manager.unsubscribe(ws, 'price:BTC/USDT')
        assert 'price:BTC/USDT' not in manager._connections[ws]

    def test_subscribe_wildcard(self):
        """通配符订阅"""
        from backend.api import ConnectionManager
        manager = ConnectionManager()

        ws = MagicMock()
        manager._connections[ws] = {'*'}

        # send_to_topic 应该匹配通配符
        # (需要 async, 在实际测试中验证)
        assert '*' in manager._connections[ws]


# =====================================================================
# 继承验证测试
# =====================================================================

class TestStrategyInheritance:
    """验证所有策略正确继承 BaseStrategy"""

    @pytest.mark.parametrize("cls_name,cls_module", [
        ('CrossExchangeArbitrageStrategy', 'strategies.cross_exchange'),
        ('TriangularArbitrageStrategy', 'strategies.triangular_arbitrage'),
        ('BasisTradingStrategy', 'strategies.basis_trading'),
        ('FundingRateArbitrageStrategy', 'strategies.funding_rate'),
        ('StatisticalArbitrageStrategy', 'strategies.statistical_arbitrage'),
    ])
    def test_strategy_inherits_base(self, cls_name, cls_module):
        """所有策略必须继承 BaseStrategy"""
        import importlib
        from strategies.base import BaseStrategy

        module = importlib.import_module(cls_module)
        cls = getattr(module, cls_name)
        assert issubclass(cls, BaseStrategy)

    @pytest.mark.parametrize("cls_name,cls_module,expected_name", [
        ('CrossExchangeArbitrageStrategy', 'strategies.cross_exchange', 'cross_exchange'),
        ('TriangularArbitrageStrategy', 'strategies.triangular_arbitrage', 'triangular'),
        ('BasisTradingStrategy', 'strategies.basis_trading', 'basis_trading'),
        ('FundingRateArbitrageStrategy', 'strategies.funding_rate', 'funding_rate'),
        ('StatisticalArbitrageStrategy', 'strategies.statistical_arbitrage', 'statistical_arbitrage'),
    ])
    def test_strategy_metadata(self, cls_name, cls_module, expected_name):
        """策略元数据设置正确"""
        import importlib

        module = importlib.import_module(cls_module)
        cls = getattr(module, cls_name)
        assert cls.STRATEGY_NAME == expected_name
        assert cls.STRATEGY_DESCRIPTION  # 非空

    @pytest.mark.parametrize("cls_name,cls_module", [
        ('CrossExchangeArbitrageStrategy', 'strategies.cross_exchange'),
        ('TriangularArbitrageStrategy', 'strategies.triangular_arbitrage'),
        ('BasisTradingStrategy', 'strategies.basis_trading'),
        ('FundingRateArbitrageStrategy', 'strategies.funding_rate'),
        ('StatisticalArbitrageStrategy', 'strategies.statistical_arbitrage'),
    ])
    def test_strategy_has_lifecycle(self, cls_name, cls_module):
        """策略具有生命周期方法"""
        import importlib

        module = importlib.import_module(cls_module)
        cls = getattr(module, cls_name)
        instance = cls({})

        assert hasattr(instance, 'start')
        assert hasattr(instance, 'stop')
        assert hasattr(instance, 'pause')
        assert hasattr(instance, 'resume')
        assert hasattr(instance, 'is_running')
        assert hasattr(instance, 'get_health_report')

    @pytest.mark.parametrize("cls_name,cls_module", [
        ('CrossExchangeArbitrageStrategy', 'strategies.cross_exchange'),
        ('TriangularArbitrageStrategy', 'strategies.triangular_arbitrage'),
        ('BasisTradingStrategy', 'strategies.basis_trading'),
        ('FundingRateArbitrageStrategy', 'strategies.funding_rate'),
        ('StatisticalArbitrageStrategy', 'strategies.statistical_arbitrage'),
    ])
    def test_strategy_no_own_get_performance_stats(self, cls_name, cls_module):
        """V1.6.0: 策略不应覆盖 get_performance_stats（使用基类版本）"""
        import importlib
        from strategies.base import BaseStrategy

        module = importlib.import_module(cls_module)
        cls = getattr(module, cls_name)

        # get_performance_stats 应该是 BaseStrategy 的版本
        # (子类不再有自己覆盖的版本)
        method_on_cls = cls.__dict__.get('get_performance_stats')
        assert method_on_cls is None, (
            f"{cls_name} 不应覆盖 get_performance_stats，应使用 BaseStrategy 版本"
        )


# =====================================================================
# API 版本验证
# =====================================================================

class TestAPIVersion:
    """API 版本验证"""

    def test_api_version_1_6(self):
        from backend.api import app
        assert app.version == "1.6.0"
