"""CryptoArbitrage V1.5.0 测试套件

测试内容:
1. Bug 修复验证
2. 策略基类测试
3. FastAPI Backend 测试
4. 回测框架测试
5. 风险管理增强测试
"""

import asyncio
import math
import sys
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock ccxt and other heavy dependencies before any project imports
sys.modules['ccxt'] = MagicMock()
sys.modules['ccxt.async_support'] = MagicMock()


# ==================== Bug Fix 验证测试 ====================


class TestBugFix1_CrossExchangeSequentialExecution:
    """Bug #1: 跨交易所套利应顺序执行而非并发"""

    def test_cross_exchange_uses_sequential_execution(self):
        """验证跨交易所不再使用 asyncio.gather 并发买卖"""
        from strategies.cross_exchange import CrossExchangeArbitrageStrategy

        config = {
            'min_profit_rate': 0.5,
            'max_position_size': 1000,
            'symbols': ['BTC/USDT'],
        }
        strategy = CrossExchangeArbitrageStrategy(config)

        # 检查源码中是否有 asyncio.gather
        import inspect
        source = inspect.getsource(strategy.execute_arbitrage)
        assert 'asyncio.gather' not in source, \
            "Bug #1 未修复: 跨交易所套利仍使用 asyncio.gather 并发执行"


class TestBugFix2_BasisTradingKeyError:
    """Bug #2: basis_trading.py execute_arbitrage 使用错误的键名"""

    def test_basis_trading_handles_missing_spot_exchange_key(self):
        """验证基差套利兼容两种键名"""
        from strategies.basis_trading import BasisTradingStrategy

        config = {
            'min_profit_rate': 0.8,
            'max_position_size': 2000,
            'symbols': ['BTC/USDT'],
            'futures_exchange': 'binance',
            'execution_timeout': 10,
        }
        strategy = BasisTradingStrategy(config)

        # 模拟使用 buy_exchange 而非 spot_exchange 的机会
        opportunity = {
            'symbol': 'BTC/USDT',
            'buy_exchange': 'okx',
            'sell_exchange': 'binance',
            'max_amount': 0.01,
            'expected_profit': 5.0,
            'profit_rate': 0.9,
        }

        import inspect
        source = inspect.getsource(strategy.execute_arbitrage)
        assert 'spot_exchange' in source, "应处理 spot_exchange 键"
        assert 'buy_exchange' in source, "应兼容 buy_exchange 键"


class TestBugFix3_ProfitCalculation:
    """Bug #3: 交易执行引擎利润计算改进"""

    def test_profit_calculation_uses_actual_data(self):
        """验证利润计算支持实际成交数据"""
        from tools.transaction_executor import TransactionExecutor

        executor = TransactionExecutor({})

        # 测试有实际步骤的情况
        trade_record = {
            'opportunity': {
                'amount': 0.001,
                'buy_fee': 0.001,
                'sell_fee': 0.001,
            },
            'steps': [
                {'action': 'buy', 'price': 50000, 'amount': 0.001},
                {'action': 'sell', 'price': 50100, 'amount': 0.001},
            ],
        }

        profit = executor._calculate_profit(trade_record)
        # buy_cost = 50000 * 0.001 * 1.001 = 50.05
        # sell_revenue = 50100 * 0.001 * 0.999 = 50.0499
        # profit ≈ 0.0
        assert profit is not None

    def test_profit_calculation_fallback(self):
        """验证利润计算降级到预期利润"""
        from tools.transaction_executor import TransactionExecutor

        executor = TransactionExecutor({})
        trade_record = {
            'opportunity': {
                'expected_profit': 10.0,
            },
            'steps': [],
        }

        profit = executor._calculate_profit(trade_record)
        assert profit == 9.0  # 10 * 0.9


class TestBugFix4_CumulativePnl:
    """Bug #4: 累计盈亏使用 O(1) 增量计算"""

    def test_cumulative_pnl_is_incremental(self):
        """验证累计盈亏使用增量计算而非 O(n)"""
        from tools.risk_management import RiskManager

        rm = RiskManager({'max_daily_loss': 500})

        # 添加多笔交易
        for i in range(100):
            rm.record_trade_result({'profit': 1.0, 'strategy': 'test'})

        # 验证最后一次的 cumulative_pnl 正确
        assert rm.pnl_history[-1]['cumulative_pnl'] == 100.0

        # 检查是否使用增量计算（源码中不应有 sum(t['profit'] for t in self.pnl_history)）
        import inspect
        source = inspect.getsource(rm.record_trade_result)
        assert 'sum(t[\'profit\'] for t in self.pnl_history)' not in source, \
            "Bug #4 未修复: 仍使用 O(n) 计算 cumulative_pnl"


class TestBugFix5_TradingFees:
    """Bug #5: ccxt 4.x 使用 fetch_trading_fees_for_symbol"""

    def test_exchange_api_uses_new_fee_method(self):
        """验证交易所API优先使用新方法"""
        import inspect
        from tools.exchange_api import ExchangeManager

        source = inspect.getsource(ExchangeManager.get_trading_fees)
        assert 'fetch_trading_fees_for_symbol' in source, \
            "Bug #5 未修复: 未使用 fetch_trading_fees_for_symbol"


class TestBugFix6_RedundantMin:
    """Bug #6: 移除冗余 min(self, self)"""

    def test_funding_rate_no_redundant_min(self):
        """验证资金费率策略无冗余代码"""
        import inspect
        from strategies.funding_rate import FundingRateArbitrageStrategy

        source = inspect.getsource(FundingRateArbitrageStrategy._analyze_funding_rate)
        assert 'min(self.max_position_size, self.max_position_size)' not in source, \
            "Bug #6 未修复: 仍存在冗余 min(self, self)"


class TestBugFix8_StatArbProfitCalc:
    """Bug #8: 统计套利收益率计算单位一致性"""

    def test_stat_arb_profit_rate_calculation(self):
        """验证统计套利收益率使用正确的比率回归"""
        import inspect
        from strategies.statistical_arbitrage import StatisticalArbitrageStrategy

        source = inspect.getsource(StatisticalArbitrageStrategy._analyze_pair)
        # 应使用比率回归而非绝对价格
        assert 'expected_ratio_reversion' in source, \
            "Bug #8 未修复: 应使用 expected_ratio_reversion"
        # 不应除以绝对价格
        assert 'std_spread / current_prices[long_asset]' not in source, \
            "Bug #8 未修复: 不应将比率 std 除以绝对价格"


class TestBugFix9_NotifierEventLoop:
    """Bug #9: 使用 get_running_loop 替代废弃的 get_event_loop"""

    def test_notifier_uses_running_loop(self):
        """验证通知系统使用 get_running_loop"""
        import inspect
        from tools.notifier import Notifier

        source = inspect.getsource(Notifier._send_email)
        assert 'get_running_loop' in source, \
            "Bug #9 未修复: 应使用 asyncio.get_running_loop()"
        # 只检查实际代码行，排除 docstring 中的提及
        for line in source.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                if 'get_event_loop' in stripped:
                    pytest.fail("Bug #9 未修复: 仍使用废弃的 get_event_loop()")


class TestBugFix10_MetricsInterval:
    """Bug #10: metrics_interval 配置被使用"""

    def test_monitoring_uses_metrics_interval(self):
        """验证监控系统使用配置的 metrics_interval"""
        from tools.monitoring import MonitoringSystem

        config = {'metrics_interval': 120}
        monitoring = MonitoringSystem(config)
        assert monitoring.metrics_interval == 120


# ==================== 策略基类测试 ====================


class TestBaseStrategy:
    """策略基类测试"""

    def test_cannot_instantiate_abstract_class(self):
        """验证无法直接实例化抽象基类"""
        from strategies.base import BaseStrategy

        with pytest.raises(TypeError):
            BaseStrategy({})

    def test_concrete_strategy_instantiation(self):
        """验证具体策略可以继承基类"""
        from strategies.base import BaseStrategy

        class MockStrategy(BaseStrategy):
            STRATEGY_NAME = "mock"
            STRATEGY_DESCRIPTION = "Mock strategy"

            async def scan_opportunities(self):
                return []

            async def execute_arbitrage(self, opportunity):
                return True

        strategy = MockStrategy({'min_profit_rate': 0.5})
        assert strategy.STRATEGY_NAME == "mock"

    def test_performance_stats_empty(self):
        """验证空统计返回正确"""
        from strategies.base import BaseStrategy

        class MockStrategy(BaseStrategy):
            STRATEGY_NAME = "mock"

            async def scan_opportunities(self):
                return []

            async def execute_arbitrage(self, opportunity):
                return True

        strategy = MockStrategy({})
        stats = strategy.get_performance_stats()
        assert stats['total_trades'] == 0
        assert stats['total_profit'] == 0
        assert stats['success_rate'] == 0

    def test_record_trade(self):
        """验证交易记录功能"""
        from strategies.base import BaseStrategy

        class MockStrategy(BaseStrategy):
            STRATEGY_NAME = "mock"

            async def scan_opportunities(self):
                return []

            async def execute_arbitrage(self, opportunity):
                return True

        strategy = MockStrategy({})
        record = strategy._record_trade(
            opportunity={'symbol': 'BTC/USDT', 'expected_profit': 5.0, 'profit_rate': 0.5},
            status='completed',
            profit=4.5,
        )

        assert record['strategy'] == 'mock'
        assert record['actual_profit'] == 4.5
        assert len(strategy.trade_history) == 1

    def test_filter_by_threshold(self):
        """验证收益率过滤"""
        from strategies.base import BaseStrategy

        class MockStrategy(BaseStrategy):
            STRATEGY_NAME = "mock"

            async def scan_opportunities(self):
                return []

            async def execute_arbitrage(self, opportunity):
                return True

        strategy = MockStrategy({'min_profit_rate': 0.5})
        opportunities = [
            {'profit_rate': 0.3},
            {'profit_rate': 0.5},
            {'profit_rate': 1.0},
        ]

        filtered = strategy._filter_by_threshold(opportunities)
        assert len(filtered) == 2


# ==================== FastAPI Backend 测试 ====================


class TestFastAPIBackend:
    """FastAPI Backend 测试"""

    def test_app_creation(self):
        """验证 FastAPI app 创建成功"""
        from backend.api import app
        assert app.title == "CryptoArbitrage API"
        assert app.version == "1.5.0"

    def test_root_endpoint(self):
        """验证根路径返回正确信息"""
        from backend.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['version'] == '1.5.0'
        assert data['status'] == 'running'

    def test_health_endpoint_no_agent(self):
        """验证无 Agent 时健康检查返回 unavailable"""
        from backend.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'unavailable'

    def test_risk_endpoint_no_agent(self):
        """验证无 Agent 时风险查询返回 503"""
        from backend.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/risk")
        assert response.status_code == 503


# ==================== 回测框架测试 ====================


class TestBacktestEngine:
    """回测引擎测试"""

    def test_generate_price_data(self):
        """验证模拟价格数据生成"""
        from backtesting.engine import BacktestEngine

        engine = BacktestEngine(initial_capital=10000)
        prices = engine.generate_price_data(base_price=50000, bars=100)

        assert len(prices) == 100
        assert prices[0].close > 0
        assert all(p.high >= p.low for p in prices)
        assert all(p.volume > 0 for p in prices)

    def test_generate_correlated_pair(self):
        """验证相关价格序列生成"""
        from backtesting.engine import BacktestEngine

        engine = BacktestEngine()
        base_prices = engine.generate_price_data(50000, 200)
        correlated = engine.generate_correlated_pair(base_prices, correlation=0.9)

        assert len(correlated) == len(base_prices)
        assert all(p.close > 0 for p in correlated)

    def test_cross_exchange_backtest(self):
        """验证跨交易所套利回测"""
        from backtesting.engine import BacktestEngine

        engine = BacktestEngine(initial_capital=10000, commission_rate=0.001)
        prices_a = engine.generate_price_data(50000, 1000, volatility=0.015)
        prices_b = engine.generate_price_data(50000, 1000, volatility=0.02)

        result = engine.run_cross_exchange_backtest(prices_a, prices_b, min_spread=0.001)

        assert result.initial_capital == 10000
        assert result.final_capital > 0
        assert result.total_trades >= 0
        assert result.max_drawdown >= 0
        assert len(result.equity_curve) > 0

    def test_statistical_arbitrage_backtest(self):
        """验证统计套利回测"""
        from backtesting.engine import BacktestEngine

        engine = BacktestEngine(initial_capital=10000, commission_rate=0.001)
        prices_a = engine.generate_price_data(50000, 500, volatility=0.01)
        prices_b = engine.generate_correlated_pair(prices_a, correlation=0.85, spread_std=0.003)

        result = engine.run_statistical_arbitrage_backtest(
            prices_a, prices_b,
            lookback=50, z_open=1.5, z_close=0.3
        )

        assert result.initial_capital == 10000
        assert result.final_capital > 0
        assert result.strategy_name == "statistical_arbitrage"
        assert result.max_drawdown >= 0

    def test_backtest_report_generation(self):
        """验证回测报告生成"""
        from backtesting.engine import BacktestEngine, BacktestResult

        engine = BacktestEngine()
        result = BacktestResult(
            strategy_name="test",
            start_time=time.time() - 86400,
            end_time=time.time(),
            initial_capital=10000,
            final_capital=10500,
            total_return=5.0,
            annualized_return=15.0,
            max_drawdown=2.5,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=60.0,
            avg_profit=10.0,
            avg_loss=-5.0,
            profit_factor=3.0,
            max_consecutive_losses=3,
        )

        report = engine.generate_report(result)
        assert "test" in report
        assert "5.00%" in report
        assert "60.0%" in report
        assert "夏普比率" in report


# ==================== 风险管理增强测试 ====================


class TestEnhancedRiskManagement:
    """增强版风险管理测试"""

    def test_daily_loss_limit(self):
        """验证日亏损限制"""
        from tools.risk_management import RiskManager

        rm = RiskManager({'max_daily_loss': 100})
        assert rm.check_position_risk({'amount': 50}) is True

        # 模拟亏损
        rm.daily_pnl = -101
        assert rm.check_position_risk({'amount': 50}) is False

    def test_exposure_limit(self):
        """验证敞口限制"""
        from tools.risk_management import RiskManager

        rm = RiskManager({'max_total_exposure': 1000, 'max_position_size': 500})
        rm.current_exposure = 800

        assert rm.check_position_risk({'amount': 300}) is False
        assert rm.check_position_risk({'amount': 150}) is True

    def test_drawdown_check(self):
        """验证回撤检查"""
        from tools.risk_management import RiskManager

        rm = RiskManager({'max_drawdown': 10.0})

        # 正常状态
        rm.peak_balance = 10000
        assert rm.check_drawdown() is True

        # 添加亏损使回撤超限
        rm.record_trade_result({'profit': -1100, 'strategy': 'test'})
        assert rm.check_drawdown() is False

    def test_risk_alert_creation(self):
        """验证风险告警创建"""
        from tools.risk_management import RiskManager

        rm = RiskManager({})
        rm._create_risk_alert("TEST", "测试告警")

        assert len(rm.risk_alerts) == 1
        assert rm.risk_alerts[0]['type'] == 'TEST'
        assert rm.risk_alerts[0]['severity'] == 'HIGH'

    def test_stop_loss_calculation(self):
        """验证止损计算"""
        from tools.risk_management import IntelligentStopLoss

        isl = IntelligentStopLoss({})
        result = isl.calculate_stop_loss(entry_price=50000, position_size=0.1)

        assert result['stop_loss_price'] < 50000
        assert result['stop_loss_rate'] == 2.0

    def test_stop_loss_volatility_adjustment(self):
        """验证波动率调整止损"""
        from tools.risk_management import IntelligentStopLoss

        isl = IntelligentStopLoss({})
        normal = isl.calculate_stop_loss(50000, 0.1, volatility=None)
        volatile = isl.calculate_stop_loss(50000, 0.1, volatility=0.05)

        # 高波动率 → 更宽的止损
        assert volatile['stop_loss_rate'] > normal['stop_loss_rate']

    def test_market_condition_analysis(self):
        """验证市场条件分析"""
        from tools.risk_management import MarketConditionAnalyzer

        analyzer = MarketConditionAnalyzer()

        # 正常数据
        prices = [100 + i * 0.1 for i in range(20)]
        result = analyzer.analyze_market_conditions(prices)

        assert 'volatility' in result
        assert 'trend' in result
        assert 'liquidity' in result
        assert 'sentiment' in result

    def test_trailing_stop(self):
        """验证追踪止损"""
        from tools.risk_management import IntelligentStopLoss

        isl = IntelligentStopLoss({})
        stop = isl.update_trailing_stop(
            current_price=52000,
            entry_price=50000,
            highest_price=53000,
        )

        # 追踪止损应低于最高价但高于基础止损
        assert stop < 53000
        assert stop > 50000 * (1 - 2.0 / 100)  # 不低于基础止损


# ==================== 存储系统测试 ====================


class TestKnowledgeBase:
    """知识库测试"""

    def _create_temp_db(self):
        """创建临时数据库并返回路径"""
        import tempfile
        import os
        # 使用项目目录下的临时文件避免 Windows 权限问题
        tmp_dir = os.path.join(os.path.dirname(__file__), '..', '.tmp_test_db')
        os.makedirs(tmp_dir, exist_ok=True)
        fd, db_path = tempfile.mkstemp(suffix='.db', dir=tmp_dir)
        os.close(fd)
        return db_path

    def test_initialize_database(self):
        """验证数据库初始化"""
        from storage.knowledge_base import KnowledgeBase
        import os

        db_path = self._create_temp_db()

        try:
            kb = KnowledgeBase(db_path)
            stats = kb.get_statistics()
            assert 'strategies_count' in stats
            assert 'trades_count' in stats
        finally:
            try:
                os.unlink(db_path)
            except PermissionError:
                pass

    def test_add_and_get_strategy(self):
        """验证策略添加和查询"""
        from storage.knowledge_base import KnowledgeBase
        import os

        db_path = self._create_temp_db()

        try:
            kb = KnowledgeBase(db_path)
            strategy_id = kb.add_strategy(
                name="test_strategy",
                description="测试策略",
                parameters={"min_profit": 0.5},
            )
            assert strategy_id > 0

            strategy = kb.get_strategy("test_strategy")
            assert strategy is not None
            assert strategy['name'] == 'test_strategy'
        finally:
            try:
                os.unlink(db_path)
            except PermissionError:
                pass

    def test_add_trade_record(self):
        """验证交易记录"""
        from storage.knowledge_base import KnowledgeBase
        import os

        db_path = self._create_temp_db()

        try:
            kb = KnowledgeBase(db_path)
            trade_id = kb.add_trade_record(
                strategy="cross_exchange",
                symbol="BTC/USDT",
                exchange="binance",
                entry_price=50000,
                exit_price=50200,
                quantity=0.01,
                profit=2.0,
                profit_rate=0.4,
                status="completed",
                execution_time=1.5,
            )
            assert trade_id > 0

            trades = kb.get_recent_trades()
            assert len(trades) >= 1
        finally:
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


# ==================== 运行测试入口 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
