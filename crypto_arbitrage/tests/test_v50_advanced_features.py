"""Test Suite for V50.0 Advanced Trading Features

Comprehensive testing of:
1. Advanced Options Strategy
2. Perpetual Futures Arbitrage
3. AI Signal Fusion
4. Advanced Portfolio Rebalancer

创建时间: 2026-05-08
"""

import pytest
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import V50.0 modules
from strategies.advanced_options_strategy import (
    AdvancedOptionsStrategy,
    BlackScholesModel,
    OptionType,
    OptionStyle,
    PositionSide,
    StrategyMode,
    OptionGreeks,
    OptionContract,
    OptionPosition,
    create_options_strategy
)

from strategies.perpetual_futures_arbitrage import (
    PerpetualFuturesArbitrage,
    FundingRateCalculator,
    PerpetualContract,
    FundingPeriod,
    create_perpetual_arbitrage
)

from strategies.ai_signal_fusion import (
    SignalFusionEngine,
    SignalSource,
    SignalDirection,
    TradingSignal,
    FusedSignal,
    create_signal_fusion_engine
)

from strategies.advanced_portfolio_rebalancer import (
    PortfolioRebalancer,
    RebalanceMethod,
    RebalanceTrigger,
    AssetClass,
    PortfolioAsset,
    Portfolio,
    create_portfolio_rebalancer,
    create_portfolio
)


class TestV50_0Config:
    """V50.0配置测试"""

    @pytest.fixture
    def options_config(self):
        return {
            'min_confidence': 0.6,
            'volatility_threshold': 0.03,
            'risk_free_rate': 0.05,
            'max_position_size': 10
        }

    @pytest.fixture
    def perp_config(self):
        return {
            'min_profit_threshold': 0.0001,
            'min_confidence': 0.6,
            'funding_period': '8h'
        }

    @pytest.fixture
    def fusion_config(self):
        return {
            'min_consensus': 0.5,
            'conflict_threshold': 0.4
        }

    @pytest.fixture
    def rebalancer_config(self):
        return {
            'rebalance_method': 'risk_parity',
            'target_volatility': 0.05,
            'rebalance_threshold': 0.05
        }


class TestV50_1_AdvancedOptions(TestV50_0Config):
    """高级期权策略测试"""

    @pytest.fixture
    def strategy(self, options_config):
        return create_options_strategy(options_config)

    def test_v50_options_creation(self, strategy):
        assert strategy is not None
        assert strategy.min_confidence == 0.6
        print("✅ V50 Options Creation: PASS")

    def test_black_scholes_price(self):
        price = BlackScholesModel.calculate_price(
            s=50000, k=50000, t=30/365,
            r=0.05, sigma=0.3,
            option_type=OptionType.CALL
        )
        assert price > 0
        print(f"✅ Black-Scholes Price: {price:.2f}")

    def test_greeks_calculation(self):
        greeks = BlackScholesModel.calculate_greeks(
            s=50000, k=50000, t=30/365,
            r=0.05, sigma=0.3,
            option_type=OptionType.CALL
        )
        assert -1 <= greeks.delta <= 1
        print(f"✅ Greeks: delta={greeks.delta:.4f}, theta={greeks.theta:.2f}")

    def test_volatility_arbitrage(self, strategy):
        result = strategy.analyze(
            underlying="BTC",
            current_price=50000,
            implied_volatility=0.4,
            historical_volatility=0.25,
            time_to_expiry=30/365,
            strategy_mode=StrategyMode.VOLATILITY_ARB,
            strike_price=50000,
            option_type=OptionType.CALL
        )
        assert result.signal in ["buy_option", "sell_option", "hold"]
        print(f"✅ Volatility Arbitrage: signal={result.signal}, confidence={result.confidence:.2f}")

    def test_iron_condor(self, strategy):
        result = strategy.analyze(
            underlying="BTC",
            current_price=50000,
            implied_volatility=0.3,
            historical_volatility=0.25,
            time_to_expiry=30/365,
            strategy_mode=StrategyMode.IRON_CONDOR
        )
        assert result.strategy_mode == StrategyMode.IRON_CONDOR
        print(f"✅ Iron Condor: signal={result.signal}")


class TestV50_2_PerpetualFutures(TestV50_0Config):
    """永续期货套利测试"""

    @pytest.fixture
    def engine(self, perp_config):
        return create_perpetual_arbitrage(perp_config)

    @pytest.fixture
    def contract(self):
        from datetime import datetime, timedelta
        return PerpetualContract(
            symbol="BTC-PERP",
            underlying="BTC",
            index_price=50000,
            mark_price=50100,
            last_funding_rate=0.0001,
            next_funding_time=datetime.now() + timedelta(hours=4),
            open_interest=1000000000,
            volume_24h=5000000000,
            funding_rate_history=[]
        )

    def test_v50_perp_creation(self, engine):
        assert engine is not None
        print("✅ V50 Perpetual Creation: PASS")

    def test_funding_rate_calculator(self):
        rate = FundingRateCalculator.calculate_implied_rate(
            mark_price=50100,
            index_price=50000,
            time_to_funding=4
        )
        print(f"✅ Implied Rate: {rate:.6f}")

    def test_funding_prediction(self, engine, contract):
        engine.add_contract(contract)
        prediction = engine.predict_funding_rate(contract)
        assert prediction is not None
        print(f"✅ Funding Prediction: predicted={prediction.predicted_rate:.6f}")

    def test_arbitrage_opportunity(self, engine, contract):
        engine.add_contract(contract)
        opp = engine.analyze_funding_arbitrage(
            contract=contract,
            current_funding_rate=0.0001,
            predicted_funding_rate=0.0005,
            funding_period_hours=8
        )
        assert opp.symbol == contract.symbol
        print(f"✅ Arbitrage Opportunity: side={opp.side}")


class TestV50_3_AISignalFusion(TestV50_0Config):
    """AI信号融合测试"""

    @pytest.fixture
    def engine(self, fusion_config):
        return create_signal_fusion_engine(fusion_config)

    @pytest.fixture
    def signals(self, engine):
        symbol = "BTC/USDT"
        signals = [
            engine.create_signal(
                SignalSource.TECHNICAL,
                SignalDirection.BULLISH,
                strength=0.8,
                confidence=0.7
            ),
            engine.create_signal(
                SignalSource.FUNDAMENTAL,
                SignalDirection.BULLISH,
                strength=0.6,
                confidence=0.8
            ),
            engine.create_signal(
                SignalSource.SENTIMENT,
                SignalDirection.BEARISH,
                strength=0.5,
                confidence=0.6
            )
        ]
        for sig in signals:
            engine.add_signal(symbol, sig)
        return signals

    def test_v50_fusion_creation(self, engine):
        assert engine is not None
        print("✅ V50 Signal Fusion Creation: PASS")

    def test_signal_aggregation(self, engine, signals):
        agg = engine.aggregate_signals("BTC/USDT", method="weighted")
        assert agg.aggregate_direction is not None
        print(f"✅ Aggregation: direction={agg.aggregate_direction.value}")

    def test_signal_fusion(self, engine, signals):
        fused = engine.fuse_signals("BTC/USDT", method="weighted")
        assert fused.direction is not None
        print(f"✅ Fused Signal: direction={fused.direction.value}, score={fused.combined_score:.2f}")


class TestV50_4_PortfolioRebalancer(TestV50_0Config):
    """投资组合再平衡测试"""

    @pytest.fixture
    def rebalancer(self, rebalancer_config):
        return create_portfolio_rebalancer(rebalancer_config)

    @pytest.fixture
    def portfolio(self):
        return create_portfolio(
            name="TestPortfolio",
            total_value=100000,
            assets={
                'BTC': {
                    'asset_class': AssetClass.CRYPTO,
                    'current_weight': 0.4,
                    'target_weight': 0.4,
                    'current_value': 40000,
                    'return_1d': 0.02,
                    'volatility': 0.05
                },
                'ETH': {
                    'asset_class': AssetClass.CRYPTO,
                    'current_weight': 0.35,
                    'target_weight': 0.35,
                    'current_value': 35000,
                    'return_1d': 0.015,
                    'volatility': 0.06
                },
                'SOL': {
                    'asset_class': AssetClass.CRYPTO,
                    'current_weight': 0.25,
                    'target_weight': 0.25,
                    'current_value': 25000,
                    'return_1d': -0.01,
                    'volatility': 0.08
                }
            }
        )

    def test_v50_rebalancer_creation(self, rebalancer):
        assert rebalancer is not None
        print("✅ V50 Rebalancer Creation: PASS")

    def test_risk_parity_weights(self, rebalancer, portfolio):
        rebalancer.set_portfolio(portfolio)
        weights = rebalancer.calculate_risk_parity_weights(
            portfolio.assets,
            target_volatility=0.05
        )
        assert len(weights) == 3
        print(f"✅ Risk Parity Weights: {weights}")

    def test_min_variance_weights(self, rebalancer, portfolio):
        rebalancer.set_portfolio(portfolio)
        weights = rebalancer.calculate_min_variance_weights(portfolio.assets)
        print(f"✅ Min Variance Weights: {weights}")

    def test_rebalance_execution(self, rebalancer, portfolio):
        rebalancer.set_portfolio(portfolio)
        result = rebalancer.rebalance(method="risk_parity")
        assert result.method == RebalanceMethod.RISK_PARITY
        print(f"✅ Rebalance: trades={len(result.trades)}, sharpe={result.sharpe_ratio:.2f}")

    def test_should_rebalance(self, rebalancer, portfolio):
        rebalancer.set_portfolio(portfolio)
        # 手动设置资产权重触发阈值
        portfolio.assets['BTC'].target_weight = 0.2
        should = rebalancer.should_rebalance(RebalanceTrigger.THRESHOLD_BASED)
        print(f"✅ Should Rebalance: {should}")


class TestV50_Integration:
    """集成测试"""

    def test_v50_module_imports(self):
        """测试所有模块可以正确导入"""
        assert AdvancedOptionsStrategy is not None
        assert PerpetualFuturesArbitrage is not None
        assert SignalFusionEngine is not None
        assert PortfolioRebalancer is not None
        print("✅ V50 Module Imports: PASS")


# ============= 测试运行器 =============

def run_v50_tests():
    """运行V50.0测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_v50_tests()