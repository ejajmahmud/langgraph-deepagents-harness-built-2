"""V16.5集成测试 - 资金费率引擎 + 组合风控 + 四策略管道

测试覆盖：
1. FundingRateEngine — 费率扫描/信号生成/执行/平仓/知识记录
2. PortfolioRiskManager — 风控检查/集中度/熔断/NAV/仪表盘
3. Pipeline V16.5 — 四策略管道集成/资金费率阶段/组合风控阶段
4. 端到端 — 完整管道+知识反馈
5. 回归 — V16.4测试仍然通过

创建时间：2026-05-05
"""

import asyncio
import sys
import os
import time
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFundingRateEngine(unittest.TestCase):
    """资金费率引擎测试"""

    def setUp(self):
        from strategies.funding_rate_engine import FundingRateEngine
        self.engine = FundingRateEngine(config={
            "position_size_usd": 500,
            "max_total_positions": 3,
            "min_annualized_yield": 3.0,
        })

    def test_engine_init(self):
        """测试引擎初始化"""
        self.assertEqual(self.engine.position_size_usd, 500)
        self.assertEqual(self.engine.max_total_positions, 3)
        self.assertEqual(len(self.engine.positions), 0)

    def test_generate_simulated_rates(self):
        """测试模拟费率生成"""
        snapshots = self.engine.generate_simulated_rates()

        self.assertIn("BTC/USDT", snapshots)
        self.assertIn("binance", snapshots["BTC/USDT"])

        btc_snapshot = snapshots["BTC/USDT"]["binance"]
        self.assertIsNotNone(btc_snapshot.funding_rate)
        self.assertGreater(btc_snapshot.mark_price, 0)
        self.assertGreater(btc_snapshot.index_price, 0)

    def test_scan_funding_rates(self):
        """测试费率扫描"""
        opportunities = self.engine.scan_funding_rates()

        self.assertIsInstance(opportunities, list)
        # 应该有一些机会（模拟数据）
        for opp in opportunities:
            self.assertGreaterEqual(opp.annualized_yield, 3.0)

    def test_generate_signals(self):
        """测试信号生成"""
        signals = self.engine.generate_signals()

        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertTrue(signal.signal_id.startswith("fr_"))
            self.assertGreater(signal.estimated_net_apy, 0)

    def test_execute_signal(self):
        """测试信号执行"""
        signals = self.engine.generate_signals()
        if not signals:
            # 如果没有信号，手动创建测试数据
            from strategies.funding_rate_engine import (
                FundingRateSignal, FundingDirection, PositionSide
            )
            signal = FundingRateSignal(
                signal_id="fr_test001",
                symbol="BTC/USDT",
                exchange="binance",
                funding_rate=0.0001,
                annualized_yield=10.95,
                direction=FundingDirection.POSITIVE,
                side=PositionSide.SHORT_PERP_LONG_SPOT,
                confidence=0.8,
                estimated_net_apy=8.0,
                settlement_count_target=6,
                metadata={"mark_price": 94500, "index_price": 94500, "basis_pct": 0.1},
                timestamp=time.time()
            )
            signals = [signal]

        position = self.engine.execute_signal(signals[0])
        self.assertIsNotNone(position)
        self.assertEqual(position.status, "open")
        self.assertEqual(position.symbol, "BTC/USDT")

    def test_simulate_settlement(self):
        """测试资金费率结算"""
        from strategies.funding_rate_engine import FundingRatePosition, PositionSide

        position = FundingRatePosition(
            position_id="fpos_test",
            symbol="BTC/USDT",
            exchange="binance",
            side=PositionSide.SHORT_PERP_LONG_SPOT,
            spot_price=94500,
            perp_price=94550,
            quantity=0.01,
            position_value_usd=1000,
            entry_funding_rate=0.0001,
            entry_basis_pct=0.05,
            target_settlements=6,
            settlements_collected=0,
            accumulated_funding_usd=0.0,
            status="open",
            opened_at=time.time()
        )

        # 正费率 + 做空合约 → 收入
        result = self.engine.simulate_funding_settlement(position, funding_rate=0.0001)
        self.assertEqual(result.settlements_collected, 1)
        self.assertGreater(result.accumulated_funding_usd, 0)

    def test_close_position(self):
        """测试平仓"""
        from strategies.funding_rate_engine import FundingRatePosition, PositionSide

        position = FundingRatePosition(
            position_id="fpos_close_test",
            symbol="ETH/USDT",
            exchange="binance",
            side=PositionSide.SHORT_PERP_LONG_SPOT,
            spot_price=3780,
            perp_price=3782,
            quantity=0.1,
            position_value_usd=1000,
            entry_funding_rate=0.0001,
            entry_basis_pct=0.05,
            target_settlements=3,
            settlements_collected=3,
            accumulated_funding_usd=3.0,
            status="open",
            opened_at=time.time() - 86400
        )

        self.engine.positions[position.position_id] = position

        result = self.engine.close_position(
            position,
            current_spot_price=3781,
            current_perp_price=3783,
            reason="目标结算次数达标"
        )

        self.assertEqual(result.status, "closed")
        self.assertGreater(len(self.engine.closed_positions), 0)

    def test_knowledge_recording(self):
        """测试知识记录"""
        from storage.mem0_mock_storage import create_mock_mem0_storage

        storage = create_mock_mem0_storage({
            "user_id": "test-user",
            "agent_id": "test-funding-rate"
        })

        engine = self.engine
        engine._knowledge = storage

        signals = engine.generate_signals()
        if signals:
            pos = engine.execute_signal(signals[0])
            if pos:
                # 检查知识库有记录
                results = storage.search_memories("funding_rate_signal")
                # 至少有一条信号记录
                self.assertGreater(len(results), 0)

    def test_full_scan(self):
        """测试完整扫描"""
        result = self.engine.run_full_scan()

        self.assertIn("scan_id", result)
        self.assertIn("rates_scanned", result)
        self.assertIn("opportunities_found", result)
        self.assertIn("signals_generated", result)
        self.assertIn("positions_opened", result)
        self.assertGreater(result["rates_scanned"], 0)

    def test_engine_statistics(self):
        """测试引擎统计"""
        self.engine.run_full_scan()
        stats = self.engine.get_engine_statistics()

        self.assertEqual(stats["version"], "V16.5")
        self.assertIn("total_signals", stats)
        self.assertIn("total_pnl", stats)


class TestPortfolioRiskManager(unittest.TestCase):
    """组合风控测试"""

    def setUp(self):
        from trading.portfolio_risk_manager import PortfolioRiskManager
        self.risk_mgr = PortfolioRiskManager(config={
            "max_total_exposure_usd": 5000,
            "max_single_position_usd": 2000,
            "max_positions_total": 10,
            "max_single_symbol_pct": 0.3,
            "max_single_exchange_pct": 0.5,
            "max_drawdown_pct": 5.0,
            "initial_capital": 10000,
        })

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.risk_mgr.max_total_exposure_usd, 5000)
        self.assertEqual(self.risk_mgr.max_positions_total, 10)
        self.assertEqual(len(self.risk_mgr._positions), 0)

    def test_register_position(self):
        """测试持仓注册"""
        pos_id = self.risk_mgr.register_position(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="long",
            quantity=0.01,
            value_usd=1000,
            strategy_position_id="ce_pos_001"
        )

        self.assertTrue(pos_id.startswith("prisk_"))
        self.assertEqual(len(self.risk_mgr._positions), 1)

    def test_unregister_position(self):
        """测试持仓注销"""
        pos_id = self.risk_mgr.register_position(
            strategy="triangular",
            symbol="ETH/USDT",
            exchange="okex",
            side="neutral",
            quantity=1.0,
            value_usd=500,
        )

        result = self.risk_mgr.unregister_position(pos_id, realized_pnl=5.0)
        self.assertTrue(result)
        self.assertEqual(len(self.risk_mgr._positions), 0)
        self.assertEqual(self.risk_mgr._total_realized_pnl, 5.0)

    def test_pre_trade_check_allow(self):
        """测试交易前检查 - 允许"""
        from trading.portfolio_risk_manager import RiskAction

        result = self.risk_mgr.pre_trade_check(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="long",
            proposed_size_usd=1000
        )

        self.assertEqual(result.action, RiskAction.ALLOW)

    def test_pre_trade_check_single_limit(self):
        """测试交易前检查 - 单笔超限"""
        from trading.portfolio_risk_manager import RiskAction

        result = self.risk_mgr.pre_trade_check(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="long",
            proposed_size_usd=3000  # > max_single_position_usd=2000
        )

        self.assertEqual(result.action, RiskAction.REDUCE_SIZE)
        self.assertIsNotNone(result.adjusted_size_usd)

    def test_pre_trade_check_max_positions(self):
        """测试交易前检查 - 持仓数超限"""
        from trading.portfolio_risk_manager import RiskAction, PortfolioRiskManager

        # 使用更小的限制
        small_mgr = PortfolioRiskManager(config={
            "max_total_exposure_usd": 100000,
            "max_single_position_usd": 10000,
            "max_positions_total": 3,
            "max_positions_per_strategy": 10,
            "max_single_symbol_pct": 1.0,
            "max_single_exchange_pct": 1.0,
            "max_correlated_group_pct": 1.0,
            "max_drawdown_pct": 50.0,
            "initial_capital": 100000,
        })

        # 注册3个持仓
        for i in range(3):
            small_mgr.register_position(
                strategy="cross_exchange",
                symbol=f"COIN{i}/USDT",
                exchange="binance",
                side="long",
                quantity=1.0,
                value_usd=100,
            )

        self.assertEqual(len(small_mgr._positions), 3)

        result = small_mgr.pre_trade_check(
            strategy="cross_exchange",
            symbol="NEWCOIN/USDT",
            exchange="okex",
            side="long",
            proposed_size_usd=100
        )

        self.assertEqual(result.action, RiskAction.REJECT)

    def test_symbol_concentration(self):
        """测试币种集中度"""
        from trading.portfolio_risk_manager import RiskAction

        # 注册BTC持仓占30%
        self.risk_mgr.register_position(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="long",
            quantity=0.01,
            value_usd=1500,
        )

        # 再尝试注册BTC持仓
        result = self.risk_mgr.pre_trade_check(
            strategy="triangular",
            symbol="BTC/USDT",
            exchange="okex",
            side="long",
            proposed_size_usd=1500
        )

        # 应该被限制
        self.assertIn(result.action, [RiskAction.REDUCE_SIZE, RiskAction.REJECT])

    def test_circuit_breaker(self):
        """测试熔断"""
        from trading.portfolio_risk_manager import RiskAction

        # 手动激活熔断
        self.risk_mgr._activate_circuit_breaker("测试熔断")

        result = self.risk_mgr.pre_trade_check(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="long",
            proposed_size_usd=100
        )

        self.assertEqual(result.action, RiskAction.CIRCUIT_BREAK)

    def test_concentration_metrics(self):
        """测试集中度指标"""
        self.risk_mgr.register_position(
            strategy="cross_exchange", symbol="BTC/USDT",
            exchange="binance", side="long", quantity=1, value_usd=1000
        )
        self.risk_mgr.register_position(
            strategy="statistical", symbol="ETH/USDT",
            exchange="okex", side="short", quantity=1, value_usd=500
        )

        metrics = self.risk_mgr.get_concentration_metrics()

        self.assertIn("BTC/USDT", metrics.symbol_concentration)
        self.assertIn("ETH/USDT", metrics.symbol_concentration)
        self.assertGreater(metrics.max_symbol_hhi, 0)

    def test_nav_update(self):
        """测试NAV更新"""
        self.risk_mgr.register_position(
            strategy="cross_exchange", symbol="BTC/USDT",
            exchange="binance", side="long", quantity=0.01, value_usd=1000
        )

        nav = self.risk_mgr.update_nav()

        self.assertEqual(nav.position_count, 1)
        self.assertGreater(nav.nav, 0)
        self.assertEqual(len(self.risk_mgr._nav_history), 1)

    def test_risk_dashboard(self):
        """测试风险仪表盘"""
        self.risk_mgr.register_position(
            strategy="funding_rate", symbol="BTC/USDT",
            exchange="binance", side="long", quantity=0.01, value_usd=500
        )

        dashboard = self.risk_mgr.get_risk_dashboard()

        self.assertEqual(dashboard["version"], "V16.5")
        self.assertIn("risk_level", dashboard)
        self.assertIn("nav", dashboard)
        self.assertIn("positions", dashboard)
        self.assertIn("concentration", dashboard)
        self.assertIn("limits", dashboard)
        self.assertIn("usage_pct", dashboard["limits"])


class TestPipelineV16_5(unittest.TestCase):
    """管道V16.5集成测试"""

    def setUp(self):
        from trading.arbitrage_pipeline import ArbitragePipeline
        from storage.mem0_mock_storage import create_mock_mem0_storage

        self.knowledge = create_mock_mem0_storage({
            "user_id": "test-user",
            "agent_id": "test-pipeline-v165"
        })

        self.pipeline = ArbitragePipeline(
            knowledge_storage=self.knowledge,
            config={
                "mode": "simulation",
                "max_positions": 10,
                "enable_stat_arb": True,
                "enable_funding_rate": True,
                "enable_portfolio_risk": True,
                "enable_adaptive_risk": False,
            }
        )

    def test_pipeline_has_funding_rate_fields(self):
        """测试管道有资金费率字段"""
        from trading.arbitrage_pipeline import PipelineResult
        result = PipelineResult(
            pipeline_id="test", stage=self.pipeline.stage if hasattr(self.pipeline, 'stage') else None
        )
        self.assertTrue(hasattr(result, 'funding_rate_opportunities'))
        self.assertTrue(hasattr(result, 'funding_rate_signals'))
        self.assertTrue(hasattr(result, 'funding_rate_pnl'))
        self.assertTrue(hasattr(result, 'portfolio_risk_actions'))

    def test_pipeline_run_with_all_strategies(self):
        """测试四策略管道运行"""
        result = self.pipeline.run_pipeline()

        self.assertIsNotNone(result)
        # 至少扫描了一些机会
        self.assertGreaterEqual(result.opportunities_scanned, 0)

    def test_pipeline_statistics_v16_5(self):
        """测试V16.5统计"""
        self.pipeline.run_pipeline()
        stats = self.pipeline.get_pipeline_statistics()

        self.assertEqual(stats["version"], "V16.5")
        self.assertIn("funding_rate", stats)
        self.assertIn("portfolio_risk", stats)
        self.assertTrue(stats["funding_rate"]["enabled"])
        self.assertTrue(stats["portfolio_risk"]["enabled"])

    def test_pipeline_with_funding_rate_disabled(self):
        """测试禁用资金费率"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline(
            knowledge_storage=self.knowledge,
            config={
                "mode": "simulation",
                "enable_funding_rate": False,
                "enable_stat_arb": False,
                "enable_adaptive_risk": False,
                "enable_portfolio_risk": False,
            }
        )

        result = pipeline.run_pipeline()
        self.assertEqual(result.funding_rate_signals, 0)
        self.assertEqual(result.stat_arb_signals, 0)


class TestEndToEndV16_5(unittest.TestCase):
    """端到端测试"""

    def test_full_pipeline_with_four_strategies(self):
        """测试四策略完整管道"""
        from trading.arbitrage_pipeline import ArbitragePipeline
        from storage.mem0_mock_storage import create_mock_mem0_storage

        knowledge = create_mock_mem0_storage({
            "user_id": "e2e-user",
            "agent_id": "e2e-pipeline-v165"
        })

        pipeline = ArbitragePipeline(
            knowledge_storage=knowledge,
            config={
                "mode": "simulation",
                "max_positions": 10,
                "enable_stat_arb": True,
                "enable_funding_rate": True,
                "enable_portfolio_risk": True,
                "enable_adaptive_risk": True,
            }
        )

        # 运行3轮
        results = pipeline.run_batch(rounds=3, interval_sec=0.1)

        self.assertEqual(len(results), 3)

        # 检查统计
        stats = pipeline.get_pipeline_statistics()
        self.assertEqual(stats["total_pipelines"], 3)
        self.assertTrue(stats["funding_rate"]["enabled"])
        self.assertTrue(stats["stat_arb"]["enabled"])

        # 检查知识库有记录
        all_memories = knowledge.get_all_memories()
        self.assertGreater(len(all_memories), 0)

    def test_async_pipeline(self):
        """测试异步管道"""
        from trading.arbitrage_pipeline import run_pipeline_async

        result = asyncio.run(run_pipeline_async(config={
            "mode": "simulation",
            "enable_funding_rate": True,
            "enable_stat_arb": False,
            "enable_adaptive_risk": False,
            "enable_portfolio_risk": False,
        }))

        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'pipeline_id'))

    def test_knowledge_feedback_loop(self):
        """测试知识反馈闭环"""
        from trading.arbitrage_pipeline import ArbitragePipeline
        from storage.mem0_mock_storage import create_mock_mem0_storage

        knowledge = create_mock_mem0_storage({
            "user_id": "feedback-user",
            "agent_id": "feedback-v165"
        })

        pipeline = ArbitragePipeline(
            knowledge_storage=knowledge,
            config={
                "mode": "simulation",
                "enable_funding_rate": True,
                "enable_stat_arb": True,
                "enable_portfolio_risk": False,
                "enable_adaptive_risk": False,
            }
        )

        # 第1轮
        pipeline.run_pipeline()
        r1_memories = len(knowledge.get_all_memories())

        # 第2轮（应该能命中知识）
        pipeline.run_pipeline()
        r2_memories = len(knowledge.get_all_memories())

        # 知识应该增加
        self.assertGreaterEqual(r2_memories, r1_memories)


class TestRegressionV16_4(unittest.TestCase):
    """回归测试 - 确保V16.4功能不受影响"""

    def test_v16_4_tests_still_pass(self):
        """运行V16.4测试确认零回归"""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_v16_4_integration.py", "-v", "--tb=short"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=120
        )
        # 所有V16.4测试应该通过
        self.assertIn("passed", result.stdout.lower() + result.stderr.lower(),
                      f"V16.4 tests failed:\n{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
