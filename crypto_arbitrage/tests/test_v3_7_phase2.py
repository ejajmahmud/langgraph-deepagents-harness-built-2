"""V3.7 Phase 2 完整测试套件

测试实盘交易能力建设的所有核心功能：
1. ProductionTradingEngine - 多模式交易执行
2. CapitalManager - 资金管理和仓位控制
3. PerformanceTracker - 数据收集和绩效分析
4. 集成测试 - 端到端功能验证
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# 导入被测试的模块
from trading.production_trading_engine import (
    ProductionTradingEngine,
    TradingMode,
    TradingState,
    create_production_trading_engine
)
from trading.capital_manager import (
    CapitalManager,
    KellyCriterion,
    RiskParity,
    create_capital_manager,
    StrategyPerformance
)
from trading.performance_tracker import (
    PerformanceTracker,
    create_performance_tracker
)

# 导入依赖模块
from tools.risk_management import (
    RiskManager,
    initialize_risk_manager
)


# ============== ProductionTradingEngine Tests ==============

class TestProductionTradingEngine:
    """生产级交易引擎测试"""

    @pytest.fixture
    def risk_config(self):
        """风险配置"""
        return {
            'max_daily_loss': 500,
            'max_position_size': 1000,
            'max_total_exposure': 5000,
            'max_drawdown': 10.0
        }

    @pytest.fixture
    def engine_config(self):
        """引擎配置"""
        return {
            'initial_mode': 'SIMULATION',
            'max_live_trades_per_day': 10,
            'live_position_limit': 0.05
        }

    @pytest.fixture
    def risk_manager(self, risk_config):
        """风险管理器"""
        return initialize_risk_manager(risk_config)

    @pytest.fixture
    def trading_engine(self, engine_config, risk_manager):
        """交易引擎"""
        return create_production_trading_engine(engine_config, risk_manager)

    @pytest.mark.asyncio
    async def test_engine_initialization(self, trading_engine):
        """测试引擎初始化"""
        assert trading_engine is not None
        assert trading_engine.current_mode == TradingMode.SIMULATION
        assert trading_engine.state == TradingState.IDLE
        assert not trading_engine.is_running

    @pytest.mark.asyncio
    async def test_engine_start_stop(self, trading_engine):
        """测试引擎启动和停止"""
        # 启动
        await trading_engine.start()
        assert trading_engine.is_running
        assert trading_engine.state == TradingState.SCANNING

        # 停止
        await trading_engine.stop()
        assert not trading_engine.is_running
        assert trading_engine.state == TradingState.STOPPED

    @pytest.mark.asyncio
    async def test_simulation_trade_execution(self, trading_engine):
        """测试模拟交易执行"""
        opportunity = {
            'type': 'cross_exchange_arbitrage',
            'symbol': 'BTC/USDT',
            'price': 50000.0,
            'amount': 100.0,
            'expected_profit': 50.0,
            'market_regime': 'stable'
        }

        await trading_engine.start()
        result = await trading_engine.execute_trade(opportunity)

        assert result.status == "COMPLETED"
        assert result.actual_profit is not None
        assert result.mode == TradingMode.SIMULATION
        assert trading_engine.statistics.total_trades == 1

    @pytest.mark.asyncio
    async def test_trading_mode_upgrade(self, trading_engine):
        """测试交易模式升级"""
        await trading_engine.start()

        # SIMULATION -> PAPER_TRADING
        success = await trading_engine.upgrade_trading_mode(TradingMode.PAPER_TRADING)
        assert success
        assert trading_engine.current_mode == TradingMode.PAPER_TRADING

        # PAPER_TRADING -> LIVE_TRADING (会失败，因为安全检查）
        success = await trading_engine.upgrade_trading_mode(TradingMode.LIVE_TRADING)
        assert not success  # 应该失败，因为历史交易不足

    @pytest.mark.asyncio
    async def test_emergency_stop(self, trading_engine):
        """测试紧急停止"""
        await trading_engine.start()
        await trading_engine.emergency_stop()

        assert trading_engine.state == TradingState.EMERGENCY
        assert not trading_engine.is_running

    def test_get_engine_status(self, trading_engine):
        """测试获取引擎状态"""
        status = trading_engine.get_engine_status()

        assert 'current_mode' in status
        assert 'state' in status
        assert 'statistics' in status
        assert 'risk_summary' in status

    def test_get_statistics(self, trading_engine):
        """测试获取统计信息"""
        stats = trading_engine.get_statistics()

        assert stats.total_trades == 0
        assert stats.profitable_trades == 0
        assert stats.total_profit == 0.0


# ============== CapitalManager Tests ==============

class TestCapitalManager:
    """资金管理器测试"""

    @pytest.fixture
    def capital_config(self):
        """资金配置"""
        return {
            'total_capital': 10000.0,
            'risk_per_trade': 0.01,  # 1%
            'max_total_risk': 0.03,  # 3%
            'min_cash_reserve': 0.1,  # 10%
            'default_allocation_method': 'equal'
        }

    @pytest.fixture
    def capital_manager(self, capital_config):
        """资金管理器"""
        return create_capital_manager(capital_config)

    def test_capital_manager_initialization(self, capital_manager):
        """测试资金管理器初始化"""
        assert capital_manager is not None
        assert capital_manager.total_capital == 10000.0
        assert capital_manager.risk_per_trade == 0.01

    def test_kelly_criterion_calculation(self):
        """测试凯利公式计算"""
        kelly = KellyCriterion()

        # 测试场景：胜率60%，平均盈利$100，平均亏损$50
        kelly_fraction = kelly.calculate_kelly_fraction(0.6, 100.0, 50.0)
        assert 0 < kelly_fraction < 1  # 应该在合理范围内

    def test_risk_parity_weights(self):
        """测试风险平价权重计算"""
        risk_parity = RiskParity()

        strategies = {
            'strategy_a': 0.02,  # 2% risk
            'strategy_b': 0.03,  # 3% risk
            'strategy_c': 0.04   # 4% risk
        }

        weights = risk_parity.calculate_risk_parity_weights(strategies)

        assert len(weights) == 3
        assert all(0 <= w <= 1 for w in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 0.01  # 权重和应该接近1

    def test_calculate_optimal_position(self, capital_manager):
        """测试计算最优仓位"""
        # 创建模拟策略性能
        performance = StrategyPerformance(
            strategy_name='test_strategy',
            total_trades=100,
            profitable_trades=60,
            win_rate=0.6,
            avg_profit_per_trade=50.0,
            avg_loss_per_trade=-30.0,
            risk_reward_ratio=1.67,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            last_update=datetime.now()
        )

        opportunity = {
            'confidence': 0.8,
            'market_regime': 'stable'
        }

        allocation = capital_manager.calculate_optimal_position(
            'test_strategy', performance, opportunity
        )

        assert allocation.position_size > 0
        assert 0 < allocation.position_weight <= 1
        assert allocation.risk_amount > 0

    def test_allocate_capital_equal(self, capital_manager):
        """测试等权重资金分配"""
        # 添加一些策略性能数据
        for i in range(3):
            performance = StrategyPerformance(
                strategy_name=f'strategy_{i}',
                total_trades=50,
                profitable_trades=30,
                win_rate=0.6,
                avg_profit_per_trade=40.0,
                avg_loss_per_trade=-25.0,
                risk_reward_ratio=1.6,
                max_drawdown=0.04,
                sharpe_ratio=1.2,
                last_update=datetime.now()
            )
            capital_manager.update_strategy_performance(
                f'strategy_{i}', [{} for _ in range(50)]
            )

        # 分配资金
        from llm.memo0_decision_support import MarketContext
        context = MarketContext(
            timestamp=datetime.now(),
            symbol='BTC/USDT',
            price=50000.0,
            volume_24h=1000000.0,
            volatility=0.03,
            trend='uptrend',
            market_regime='stable',
            technical_indicators={},
            sentiment_score=0.2,
            liquidity_score=0.8
        )

        allocation = capital_manager.allocate_capital(
            ['strategy_0', 'strategy_1', 'strategy_2'],
            context,
            allocation_method='equal'
        )

        assert len(allocation.allocations) == 3
        assert allocation.allocated_capital > 0
        assert allocation.allocation_efficiency > 0

    def test_get_capital_summary(self, capital_manager):
        """测试获取资金摘要"""
        summary = capital_manager.get_capital_summary()

        assert 'total_capital' in summary
        assert 'available_capital' in summary
        assert 'exposure_ratio' in summary
        assert summary['total_capital'] == 10000.0


# ============== PerformanceTracker Tests ==============

class TestPerformanceTracker:
    """绩效跟踪器测试"""

    @pytest.fixture
    def tracker_config(self):
        """跟踪器配置"""
        return {}

    @pytest.fixture
    def performance_tracker(self, tracker_config):
        """绩效跟踪器"""
        return create_performance_tracker(tracker_config)

    @pytest.mark.asyncio
    async def test_tracker_initialization(self, performance_tracker):
        """测试跟踪器初始化"""
        assert performance_tracker is not None
        assert performance_tracker.total_trades == 0

    @pytest.mark.asyncio
    async def test_record_trade(self, performance_tracker):
        """测试记录交易"""
        trade_data = {
            'trade_id': 'test_001',
            'strategy': 'test_strategy',
            'entry_time': datetime.now(),
            'exit_time': datetime.now() + timedelta(hours=1),
            'symbol': 'BTC/USDT',
            'entry_price': 50000.0,
            'exit_price': 50050.0,
            'position_size': 100.0,
            'trading_mode': 'SIMULATION',
            'expected_profit': 50.0,
            'actual_profit': 50.0,
            'execution_time': 1.5,
            'slippage': 0.0001,
            'market_regime': 'stable',
            'decision_confidence': 0.8,
            'risk_amount': 10.0
        }

        await performance_tracker.record_trade(trade_data)

        assert performance_tracker.total_trades == 1
        assert len(performance_tracker.trades) == 1

    @pytest.mark.asyncio
    async def test_generate_performance_report(self, performance_tracker):
        """测试生成绩效报告"""
        # 先记录一些交易
        for i in range(10):
            trade_data = {
                'trade_id': f'test_{i:03d}',
                'strategy': 'test_strategy',
                'entry_time': datetime.now(),
                'exit_time': datetime.now() + timedelta(hours=1),
                'symbol': 'BTC/USDT',
                'entry_price': 50000.0,
                'exit_price': 50000.0 + (50 if i % 2 == 0 else -30),
                'position_size': 100.0,
                'trading_mode': 'SIMULATION',
                'expected_profit': 50.0,
                'actual_profit': 50.0 if i % 2 == 0 else -30.0,
                'execution_time': 1.5,
                'slippage': 0.0001,
                'market_regime': 'stable',
                'decision_confidence': 0.8,
                'risk_amount': 10.0
            }
            await performance_tracker.record_trade(trade_data)

        # 生成报告
        report = await performance_tracker.generate_performance_report()

        assert report.total_return != 0
        assert report.win_rate > 0
        assert 0 <= report.sharpe_ratio

    @pytest.mark.asyncio
    async def test_analyze_risk_exposure(self, performance_tracker):
        """测试分析风险暴露"""
        # 记录一些交易
        trade_data = {
            'trade_id': 'test_risk',
            'strategy': 'test_strategy',
            'entry_time': datetime.now(),
            'symbol': 'BTC/USDT',
            'entry_price': 50000.0,
            'position_size': 100.0,
            'trading_mode': 'SIMULATION',
            'expected_profit': 50.0,
            'actual_profit': 50.0,
            'execution_time': 1.5,
            'slippage': 0.0001,
            'market_regime': 'stable',
            'decision_confidence': 0.8,
            'risk_amount': 10.0
        }
        await performance_tracker.record_trade(trade_data)

        # 分析风险
        risk_analysis = await performance_tracker.analyze_risk_exposure()

        assert risk_analysis.exposure_analysis is not None
        assert len(risk_analysis.recommendations) > 0

    @pytest.mark.asyncio
    async def test_perform_attribution_analysis(self, performance_tracker):
        """测试进行归因分析"""
        # 记录一些交易
        for i in range(5):
            trade_data = {
                'trade_id': f'attr_{i:03d}',
                'strategy': 'test_strategy',
                'entry_time': datetime.now(),
                'exit_time': datetime.now() + timedelta(hours=1),
                'symbol': 'BTC/USDT',
                'entry_price': 50000.0,
                'exit_price': 50050.0,
                'position_size': 100.0,
                'trading_mode': 'SIMULATION',
                'expected_profit': 50.0,
                'actual_profit': 50.0,
                'execution_time': 1.5,
                'slippage': 0.0001,
                'market_regime': 'stable',
                'decision_confidence': 0.8,
                'risk_amount': 10.0
            }
            await performance_tracker.record_trade(trade_data)

        # 归因分析
        attribution = await performance_tracker.perform_attribution_analysis()

        assert attribution.strategy_attribution is not None
        assert len(attribution.insights) > 0

    def test_get_summary(self, performance_tracker):
        """测试获取摘要"""
        summary = performance_tracker.get_summary()

        assert 'total_trades' in summary
        assert 'total_profit' in summary
        assert 'trades_by_strategy' in summary


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def config(self):
        """完整配置"""
        return {
            'trading': {
                'initial_mode': 'SIMULATION',
                'max_live_trades_per_day': 10,
                'live_position_limit': 0.05
            },
            'risk': {
                'max_daily_loss': 500,
                'max_position_size': 1000,
                'max_total_exposure': 5000,
                'max_drawdown': 10.0
            },
            'capital': {
                'total_capital': 10000.0,
                'risk_per_trade': 0.01,
                'max_total_risk': 0.03,
                'min_cash_reserve': 0.1
            }
        }

    @pytest.mark.asyncio
    async def test_end_to_end_trading_flow(self, config):
        """测试端到端交易流程"""
        # 初始化组件
        risk_manager = initialize_risk_manager(config['risk'])
        trading_engine = create_production_trading_engine(
            config['trading'], risk_manager
        )
        capital_manager = create_capital_manager(config['capital'])
        performance_tracker = create_performance_tracker({})

        # 启动引擎
        await trading_engine.start()

        # 创建交易机会
        opportunity = {
            'type': 'cross_exchange_arbitrage',
            'symbol': 'BTC/USDT',
            'price': 50000.0,
            'amount': 100.0,
            'expected_profit': 50.0,
            'market_regime': 'stable',
            'confidence': 0.8
        }

        # 执行交易
        execution = await trading_engine.execute_trade(opportunity)

        assert execution.status == "COMPLETED"

        # 记录到绩效跟踪器
        trade_data = {
            'trade_id': execution.trade_id,
            'strategy': opportunity['type'],
            'entry_time': datetime.now(),
            'exit_time': datetime.now() + timedelta(hours=1),
            'symbol': opportunity['symbol'],
            'entry_price': opportunity['price'],
            'exit_price': opportunity['price'] + 50,
            'position_size': opportunity['amount'],
            'trading_mode': execution.mode.value,
            'expected_profit': opportunity['expected_profit'],
            'actual_profit': execution.actual_profit,
            'execution_time': execution.execution_time,
            'slippage': 0.0001,
            'market_regime': opportunity['market_regime'],
            'decision_confidence': 0.8,
            'risk_amount': 10.0
        }

        await performance_tracker.record_trade(trade_data)

        # 验证结果
        assert trading_engine.statistics.total_trades == 1
        assert performance_tracker.total_trades == 1

        # 停止引擎
        await trading_engine.stop()

    @pytest.mark.asyncio
    async def test_multi_strategy_allocation(self, config):
        """测试多策略资金分配"""
        # 初始化资金管理器
        capital_manager = create_capital_manager(config['capital'])

        # 添加策略性能数据
        from llm.memo0_decision_support import MarketContext

        for i in range(3):
            performance = StrategyPerformance(
                strategy_name=f'strategy_{i}',
                total_trades=50,
                profitable_trades=30 + i * 5,
                win_rate=0.6 + i * 0.05,
                avg_profit_per_trade=40.0 + i * 10,
                avg_loss_per_trade=-25.0,
                risk_reward_ratio=1.6 + i * 0.2,
                max_drawdown=0.05 - i * 0.01,
                sharpe_ratio=1.2 + i * 0.3,
                last_update=datetime.now()
            )
            capital_manager.update_strategy_performance(
                f'strategy_{i}', [{} for _ in range(50)]
            )

        # 创建市场上下文
        context = MarketContext(
            timestamp=datetime.now(),
            symbol='BTC/USDT',
            price=50000.0,
            volume_24h=1000000.0,
            volatility=0.03,
            trend='uptrend',
            market_regime='stable',
            technical_indicators={},
            sentiment_score=0.2,
            liquidity_score=0.8
        )

        # 分配资金
        allocation = capital_manager.allocate_capital(
            ['strategy_0', 'strategy_1', 'strategy_2'],
            context,
            allocation_method='equal'
        )

        assert len(allocation.allocations) == 3
        assert allocation.allocated_capital > 0
        assert allocation.allocation_efficiency > 0


# ============== Performance Tests ==============

class TestPerformance:
    """性能测试"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'trading': {'initial_mode': 'SIMULATION'},
            'risk': {
                'max_daily_loss': 500,
                'max_position_size': 1000,
                'max_total_exposure': 5000,
                'max_drawdown': 10.0
            },
            'capital': {
                'total_capital': 10000.0,
                'risk_per_trade': 0.01,
                'max_total_risk': 0.03
            }
        }

    @pytest.mark.asyncio
    async def test_concurrent_trade_execution(self, config):
        """测试并发交易执行"""
        # 初始化组件
        risk_manager = initialize_risk_manager(config['risk'])
        trading_engine = create_production_trading_engine(
            config['trading'], risk_manager
        )

        await trading_engine.start()

        # 创建多个交易机会
        opportunities = [
            {
                'type': 'cross_exchange_arbitrage',
                'symbol': 'BTC/USDT',
                'price': 50000.0 + i * 100,
                'amount': 100.0,
                'expected_profit': 50.0 + i * 5,
                'market_regime': 'stable',
                'confidence': 0.8
            }
            for i in range(10)
        ]

        # 并发执行交易
        tasks = [trading_engine.execute_trade(opp) for opp in opportunities]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证结果
        successful_trades = [r for r in results if r.status == "COMPLETED"]
        assert len(successful_trades) > 0

        await trading_engine.stop()

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, config):
        """测试大数据集性能"""
        # 初始化组件
        performance_tracker = create_performance_tracker({})

        # 记录大量交易
        start_time = datetime.now()

        for i in range(1000):
            trade_data = {
                'trade_id': f'perf_{i:04d}',
                'strategy': 'test_strategy',
                'entry_time': datetime.now(),
                'exit_time': datetime.now() + timedelta(hours=1),
                'symbol': 'BTC/USDT',
                'entry_price': 50000.0,
                'exit_price': 50000.0 + (50 if i % 2 == 0 else -30),
                'position_size': 100.0,
                'trading_mode': 'SIMULATION',
                'expected_profit': 50.0,
                'actual_profit': 50.0 if i % 2 == 0 else -30.0,
                'execution_time': 1.5,
                'slippage': 0.0001,
                'market_regime': 'stable',
                'decision_confidence': 0.8,
                'risk_amount': 10.0
            }
            await performance_tracker.record_trade(trade_data)

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # 验证性能
        assert performance_tracker.total_trades == 1000
        assert elapsed_time < 10.0  # 应该在10秒内完成

        # 测试报告生成性能
        start_time = datetime.now()
        report = await performance_tracker.generate_performance_report()
        elapsed_time = (datetime.now() - start_time).total_seconds()

        assert elapsed_time < 5.0  # 报告生成应该在5秒内完成
        assert report.total_return != 0


# ============== Main Test Runner ==============

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])