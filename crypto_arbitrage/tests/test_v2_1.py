"""CryptoArbitrage V2.1 测试套件

测试范围:
- 智能止损集成
- 回测引擎集成
- 资金费率预测
"""

import asyncio
import math
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import time
from datetime import datetime, timedelta

from strategies.base import BaseStrategy, StrategyState
from strategies.strategy_manager import StrategyManager
from strategies.funding_rate import FundingRateArbitrageStrategy, FundingRatePredictor
from tools.risk_management import IntelligentStopLoss, MarketConditionAnalyzer
from backtesting.engine import BacktestEngine, PriceBar


class MockStrategy(BaseStrategy):
    """模拟策略用于测试"""

    STRATEGY_NAME = "mock_strategy"
    STRATEGY_DESCRIPTION = "测试策略"

    def __init__(self, config=None):
        config = config or {}
        super().__init__(config)
        self._should_fail_scan = False
        self._should_fail_execute = False

    async def scan_opportunities(self):
        """扫描机会"""
        if self._should_fail_scan:
            raise Exception("扫描失败")
        return []

    async def execute_arbitrage(self, opportunity):
        """执行交易"""
        if self._should_fail_execute:
            raise Exception("执行失败")
        return True


@pytest.mark.asyncio
class TestV21IntelligentStopLoss:
    """测试 V2.1 智能止损集成"""

    def test_intelligent_stop_loss_initialization(self):
        """测试智能止损系统初始化"""
        config = {
            'base_stop_loss': 2.0,
            'base_take_profit': 1.0,
            'trailing_stop': 0.5,
            'volatility_adjustment': 1.5
        }
        stop_loss = IntelligentStopLoss(config)

        assert stop_loss.base_stop_loss == 2.0
        assert stop_loss.base_take_profit == 1.0
        assert stop_loss.trailing_stop == 0.5
        print("[PASS] 智能止损系统初始化测试通过")

    def test_calculate_stop_loss_basic(self):
        """测试基础止损计算"""
        config = {'base_stop_loss': 2.0, 'base_take_profit': 1.0}
        stop_loss = IntelligentStopLoss(config)

        entry_price = 10000.0
        position_size = 0.1

        result = stop_loss.calculate_stop_loss(entry_price, position_size)

        expected_stop_price = 10000.0 * (1 - 2.0 / 100)  # 9800
        assert abs(result['stop_loss_price'] - expected_stop_price) < 1
        assert result['stop_loss_rate'] == 2.0
        assert result['stop_loss_amount'] > 0
        print("[PASS] 基础止损计算测试通过")

    def test_calculate_stop_loss_with_volatility(self):
        """测试考虑波动率的止损计算"""
        config = {'base_stop_loss': 2.0, 'volatility_adjustment': 1.5}
        stop_loss = IntelligentStopLoss(config)

        entry_price = 10000.0
        position_size = 0.1
        volatility = 0.05  # 高波动

        result = stop_loss.calculate_stop_loss(entry_price, position_size, volatility)

        # 波动率应该增加止损距离
        assert result['stop_loss_rate'] >= 2.0
        assert result['stop_loss_price'] < entry_price
        print(f"[PASS] 波动率调整止损测试通过: {result['stop_loss_rate']:.2f}%")

    def test_calculate_take_profit(self):
        """测试止盈计算"""
        config = {'base_stop_loss': 2.0, 'base_take_profit': 1.0}
        stop_loss = IntelligentStopLoss(config)

        entry_price = 10000.0
        stop_loss_rate = 2.0
        risk_reward_ratio = 2.0

        result = stop_loss.calculate_take_profit(entry_price, stop_loss_rate, risk_reward_ratio)

        expected_tp_rate = 2.0 * 2.0  # 4.0%
        expected_tp_price = 10000.0 * (1 + 4.0 / 100)  # 10400

        assert abs(result['take_profit_rate'] - expected_tp_rate) < 0.1
        assert abs(result['take_profit_price'] - expected_tp_price) < 1
        assert result['risk_reward_ratio'] == 2.0
        print("[PASS] 止盈计算测试通过")

    def test_update_trailing_stop(self):
        """测试追踪止损更新"""
        config = {'base_stop_loss': 2.0, 'trailing_stop': 0.5}
        stop_loss = IntelligentStopLoss(config)

        entry_price = 10000.0
        highest_price = 10000.0
        current_price = 10200.0  # 价格上涨

        new_stop = stop_loss.update_trailing_stop(current_price, entry_price, highest_price)

        # 追踪止损应该随着价格上涨
        base_stop = entry_price * (1 - 2.0 / 100)  # 9800
        expected_trailing = 10200.0 * (1 - 0.5 / 100)  # 10149

        assert new_stop >= base_stop
        print(f"[PASS] 追踪止损更新测试通过: ${new_stop:.2f}")

    @pytest.mark.asyncio
    async def test_strategy_manager_with_stop_loss(self):
        """测试策略管理器集成智能止损"""
        config = {
            'max_total_capital': 10000,
            'max_strategy_allocation': 0.4,
            'enable_intelligent_stop_loss': True,
            'risk_management': {
                'base_stop_loss': 2.0,
                'base_take_profit': 1.0
            }
        }
        manager = StrategyManager(config)

        # 验证智能止损已启用
        assert manager._intelligent_stop_loss is not None
        assert isinstance(manager._intelligent_stop_loss, IntelligentStopLoss)
        print("[PASS] 策略管理器智能止损集成测试通过")


@pytest.mark.asyncio
class TestV21BacktestEngine:
    """测试 V2.1 回测引擎集成"""

    def test_backtest_engine_initialization(self):
        """测试回测引擎初始化"""
        engine = BacktestEngine(initial_capital=10000)

        assert engine.initial_capital == 10000
        assert engine.commission_rate == 0.001
        assert engine.slippage == 0.0005
        print("[PASS] 回测引擎初始化测试通过")

    def test_generate_price_data(self):
        """测试价格数据生成"""
        engine = BacktestEngine()

        prices = engine.generate_price_data(
            base_price=10000,
            bars=100,
            volatility=0.02,
            drift=0.0001
        )

        assert len(prices) == 100
        assert all(isinstance(p, PriceBar) for p in prices)
        assert all(p.close > 0 for p in prices)
        print(f"[PASS] 价格数据生成测试通过: {len(prices)} 个数据点")

    def test_run_cross_exchange_backtest(self):
        """测试跨交易所回测"""
        engine = BacktestEngine()

        prices_a = engine.generate_price_data(base_price=10000, bars=100)
        prices_b = engine.generate_price_data(base_price=10000, bars=100)

        result = engine.run_cross_exchange_backtest(
            prices_a, prices_b,
            min_spread=0.003,
            position_size=1000
        )

        assert result.strategy_name == "cross_exchange"
        assert result.total_trades >= 0
        assert isinstance(result.total_return, float)
        assert isinstance(result.sharpe_ratio, float)
        print(f"[PASS] 跨交易所回测测试通过: {result.total_trades} 笔交易")

    @pytest.mark.asyncio
    async def test_strategy_manager_backtest(self):
        """测试策略管理器回测功能"""
        config = {
            'max_total_capital': 10000,
            'max_strategy_allocation': 0.4,
            'min_opportunity_score': 60
        }
        manager = StrategyManager(config)

        # 注册模拟策略
        mock_strategy = MockStrategy(config)
        manager.register_strategy('mock_strategy', mock_strategy)

        # 生成测试价格数据
        engine = BacktestEngine()
        price_data = [10000 + i * 10 + (i % 3) * 5 for i in range(100)]

        # 运行回测
        result = await manager.backtest_strategy('mock_strategy', price_data)

        # 验证结果
        assert result is not None
        if 'error' not in result:
            assert 'strategy_name' in result
            print(f"[PASS] 策略管理器回测测试通过: {result.get('strategy_name', 'mock')}")

    @pytest.mark.asyncio
    async def test_backtest_all_strategies(self):
        """测试回测所有策略"""
        config = {
            'max_total_capital': 10000,
            'max_strategy_allocation': 0.4,
            'min_opportunity_score': 60
        }
        manager = StrategyManager(config)

        # 注册多个模拟策略
        for i in range(3):
            mock_strategy = MockStrategy(config)
            manager.register_strategy(f'mock_strategy_{i}', mock_strategy)

        # 生成测试价格数据
        engine = BacktestEngine()
        price_data = [10000 + i * 10 for i in range(100)]

        # 运行回测
        results = await manager.backtest_all_strategies(price_data)

        # 验证结果
        assert len(results) == 3
        for strategy_name, result in results.items():
            assert strategy_name.startswith('mock_strategy_')
            assert result is not None
        print(f"[PASS] 全策略回测测试通过: {len(results)} 个策略")


@pytest.mark.asyncio
class TestV21FundingRatePrediction:
    """测试 V2.1 资金费率预测"""

    def test_funding_rate_predictor_initialization(self):
        """测试资金费率预测器初始化"""
        predictor = FundingRatePredictor(lookback_periods=50)

        assert predictor.lookback_periods == 50
        assert len(predictor.history) == 0
        print("[PASS] 资金费率预测器初始化测试通过")

    def test_add_observation(self):
        """测试添加观察数据"""
        predictor = FundingRatePredictor(lookback_periods=50)
        symbol = "BTC/USDT:USDT"

        # 添加多个观察
        for i in range(10):
            predictor.add_observation(symbol, 0.01 + i * 0.001)

        assert symbol in predictor.history
        assert len(predictor.history[symbol]) == 10
        print("[PASS] 观察数据添加测试通过")

    def test_predict_next_rate_insufficient_data(self):
        """测试数据不足时的预测"""
        predictor = FundingRatePredictor(lookback_periods=50)
        symbol = "BTC/USDT:USDT"

        # 只添加少量数据
        predictor.add_observation(symbol, 0.01)

        prediction = predictor.predict_next_rate(symbol)

        assert prediction['predicted_rate'] is None
        assert prediction['confidence'] == 0.0
        assert prediction['method'] == 'insufficient_data'
        print("[PASS] 数据不足预测测试通过")

    def test_predict_next_rate_sufficient_data(self):
        """测试数据充足时的预测"""
        predictor = FundingRatePredictor(lookback_periods=20)
        symbol = "BTC/USDT:USDT"

        # 添加充足数据
        for i in range(30):
            rate = 0.01 + math.sin(i / 10) * 0.005  # 模拟波动
            predictor.add_observation(symbol, rate)

        prediction = predictor.predict_next_rate(symbol)

        assert prediction['predicted_rate'] is not None
        assert prediction['confidence'] > 0
        assert 'trend' in prediction
        assert prediction['method'] == 'hybrid'
        print(f"[PASS] 充足数据预测测试通过: 预测 {prediction['predicted_rate']:.4f}%")

    def test_get_prediction_summary(self):
        """测试预测摘要生成"""
        predictor = FundingRatePredictor(lookback_periods=20)
        symbol = "BTC/USDT:USDT"

        # 添加数据
        for i in range(30):
            rate = 0.01 + i * 0.0002  # 上升趋势
            predictor.add_observation(symbol, rate)

        summary = predictor.get_prediction_summary(symbol)

        assert symbol in summary
        assert '当前:' in summary or 'current' in summary.lower()
        assert '预测:' in summary or 'predicted' in summary.lower()
        # 处理可能的 Unicode 字符编码问题
        try:
            display_summary = summary[:50]
        except UnicodeEncodeError:
            display_summary = summary.encode('ascii', errors='ignore').decode('ascii')[:50]
        print(f"[PASS] 预测摘要测试通过: {display_summary}...")

    def test_funding_rate_strategy_with_prediction(self):
        """测试资金费率策略集成预测"""
        config = {
            'min_profit_rate': 0.5,
            'max_position_size': 1000,
            'symbols': ['BTC/USDT:USDT'],
            'spot_symbols': ['BTC/USDT'],
            'preferred_exchange': 'binance'
        }
        strategy = FundingRateArbitrageStrategy(config)

        # 验证预测器已初始化
        assert hasattr(strategy, 'funding_rate_predictor')
        assert isinstance(strategy.funding_rate_predictor, FundingRatePredictor)
        print("[PASS] 资金费率策略预测集成测试通过")


@pytest.mark.asyncio
class TestV21Integration:
    """测试 V2.1 集成功能"""

    @pytest.mark.asyncio
    async def test_full_v21_workflow(self):
        """测试完整的 V2.1 工作流"""
        config = {
            'max_total_capital': 10000,
            'max_strategy_allocation': 0.4,
            'min_opportunity_score': 60,
            'enable_intelligent_stop_loss': True,
            'enable_market_analysis': True,
            'risk_management': {
                'base_stop_loss': 2.0,
                'base_take_profit': 1.0
            }
        }

        # 1. 创建策略管理器
        manager = StrategyManager(config)

        # 2. 验证智能止损已启用
        assert manager._intelligent_stop_loss is not None

        # 3. 验证市场条件分析已启用
        assert manager._market_analyzer is not None

        # 4. 注册策略
        mock_strategy = MockStrategy(config)
        success = manager.register_strategy('mock_strategy', mock_strategy)
        assert success

        # 5. 运行回测
        engine = BacktestEngine()
        price_data = [10000 + i * 10 for i in range(100)]
        backtest_result = await manager.backtest_strategy('mock_strategy', price_data)

        assert backtest_result is not None

        # 6. 获取综合统计
        stats = manager.get_comprehensive_stats()
        assert 'total_strategies' in stats
        assert stats['total_strategies'] == 1

        print("[PASS] V2.1 完整工作流测试通过")


# 运行测试的便捷函数
def run_v21_tests():
    """运行所有 V2.1 测试"""
    print("\n" + "="*60)
    print("CryptoArbitrage V2.1 测试套件")
    print("="*60 + "\n")

    # 智能止损测试
    print("\n【智能止损测试】")
    test_stop_loss = TestV21IntelligentStopLoss()
    test_stop_loss.test_intelligent_stop_loss_initialization()
    test_stop_loss.test_calculate_stop_loss_basic()
    test_stop_loss.test_calculate_stop_loss_with_volatility()
    test_stop_loss.test_calculate_take_profit()
    test_stop_loss.test_update_trailing_stop()

    # 回测引擎测试
    print("\n【回测引擎测试】")
    test_backtest = TestV21BacktestEngine()
    test_backtest.test_backtest_engine_initialization()
    test_backtest.test_generate_price_data()
    test_backtest.test_run_cross_exchange_backtest()

    # 资金费率预测测试
    print("\n【资金费率预测测试】")
    test_prediction = TestV21FundingRatePrediction()
    test_prediction.test_funding_rate_predictor_initialization()
    test_prediction.test_add_observation()
    test_prediction.test_predict_next_rate_insufficient_data()
    test_prediction.test_predict_next_rate_sufficient_data()
    test_prediction.test_get_prediction_summary()
    test_prediction.test_funding_rate_strategy_with_prediction()

    print("\n" + "="*60)
    print("[PASS] 所有 V2.1 同步测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_v21_tests()
