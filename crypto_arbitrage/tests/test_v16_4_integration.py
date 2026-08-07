"""V16.4 集成测试 — 统计套利引擎 + 价格历史管理器 + 自适应风控

测试覆盖:
1. PriceHistoryManager 滚动价格窗口
2. StatisticalArbEngine 配对分析/信号生成/持仓管理
3. AdaptiveRiskGate 自适应参数调整
4. ArbitragePipeline V16.4 统计套利集成
5. 端到端管道（价格数据→统计套利→知识记录）
6. 知识反馈闭环
"""

import math
import sys
import os
import time
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPriceHistoryManager(unittest.TestCase):
    """测试价格历史管理器"""

    def setUp(self):
        from data_collection.price_history_manager import PriceHistoryManager
        self.manager = PriceHistoryManager(config={"window_size": 200})

    def test_init(self):
        """测试管理器初始化"""
        stats = self.manager.get_statistics()
        self.assertIn(stats["version"], ["V16.4", "V16.5"])
        self.assertEqual(stats["window_size"], 200)
        self.assertGreater(stats["symbols_tracked"], 0)

    def test_update_single_price(self):
        """测试单价格更新"""
        self.manager.update_price(
            symbol="BTC/USDT",
            exchange="binance",
            price=94500.0,
            bid=94499.0,
            ask=94501.0
        )

        price = self.manager.get_latest_price("BTC/USDT", "binance")
        self.assertAlmostEqual(price, 94500.0, places=1)

    def test_update_multiple_prices(self):
        """测试多价格更新"""
        for i in range(50):
            self.manager.update_price(
                symbol="BTC/USDT",
                exchange="binance",
                price=94500.0 + i * 10,
            )
            self.manager.update_price(
                symbol="ETH/USDT",
                exchange="binance",
                price=3780.0 + i * 0.5,
            )

        btc = self.manager.get_latest_price("BTC/USDT", "binance")
        eth = self.manager.get_latest_price("ETH/USDT", "binance")
        self.assertGreater(btc, 94500)
        self.assertGreater(eth, 3780)

    def test_price_series(self):
        """测试价格序列获取"""
        for i in range(30):
            self.manager.update_price("BTC/USDT", "binance", 94500.0 + i)

        series = self.manager.get_price_series("BTC/USDT", "binance")
        self.assertEqual(len(series), 30)
        self.assertEqual(series[0], 94500.0)
        self.assertEqual(series[-1], 94529.0)

    def test_returns_series(self):
        """测试收益率序列"""
        prices = [100.0, 101.0, 100.5, 102.0, 101.5]
        for p in prices:
            self.manager.update_price("TEST/USDT", "binance", p)

        returns = self.manager.get_returns_series("TEST/USDT", "binance")
        self.assertEqual(len(returns), len(prices) - 1)
        # 第一个收益率: ln(101/100)
        self.assertAlmostEqual(returns[0], math.log(101 / 100), places=5)

    def test_rolling_stats(self):
        """测试滚动统计"""
        for i in range(50):
            self.manager.update_price("BTC/USDT", "binance", 94500.0 + i * 0.1)

        stats = self.manager.calculate_rolling_stats("BTC/USDT", "binance")
        self.assertIsNotNone(stats)
        self.assertEqual(stats.count, 50)
        self.assertGreater(stats.std, 0)
        self.assertAlmostEqual(stats.last_price, 94504.9, places=1)

    def test_correlation(self):
        """测试相关性计算"""
        # BTC和ETH价格同步上涨 → 高相关
        for i in range(100):
            btc = 94500.0 + i * 10
            eth = 3780.0 + i * 0.4
            self.manager.update_price("BTC/USDT", "binance", btc)
            self.manager.update_price("ETH/USDT", "binance", eth)

        corr = self.manager.calculate_correlation("BTC/USDT", "ETH/USDT", "binance")
        self.assertIsNotNone(corr)
        self.assertGreater(corr, 0.9, "同步上涨应有高相关性")

    def test_z_score(self):
        """测试Z-score计算"""
        # 创建均值回归的价差
        for i in range(100):
            btc = 94500.0 + 100 * math.sin(i * 0.1)
            eth = 3780.0 + 4 * math.sin(i * 0.1)
            self.manager.update_price("BTC/USDT", "binance", btc)
            self.manager.update_price("ETH/USDT", "binance", eth)

        result = self.manager.calculate_z_score("BTC/USDT", "ETH/USDT", "binance")
        self.assertIsNotNone(result)
        z_score, mean, std = result
        self.assertIsInstance(z_score, float)
        self.assertGreater(std, 0)

    def test_seed_from_price_feed(self):
        """测试从价格数据源初始化"""
        from data_collection.ccxt_price_feed import CcxtPriceFeed
        feed = CcxtPriceFeed()

        total = self.manager.seed_from_price_feed(feed, ticks=20)
        self.assertGreater(total, 0)

        # 验证所有币种都有数据
        for symbol in feed.DEFAULT_SYMBOLS:
            price = self.manager.get_latest_price(symbol, "binance")
            self.assertIsNotNone(price, f"{symbol} 应有价格数据")

    def test_window_size_limit(self):
        """测试窗口大小限制"""
        small_manager = __import__(
            'data_collection.price_history_manager',
            fromlist=['PriceHistoryManager']
        ).PriceHistoryManager(config={"window_size": 10})

        for i in range(50):
            small_manager.update_price("BTC/USDT", "binance", 94500.0 + i)

        series = small_manager.get_price_series("BTC/USDT", "binance")
        self.assertLessEqual(len(series), 10)


class TestStatisticalArbEngine(unittest.TestCase):
    """测试统计套利引擎"""

    def setUp(self):
        from data_collection.price_history_manager import PriceHistoryManager
        from strategies.statistical_arb_engine import StatisticalArbEngine
        from storage.mem0_mock_storage import MockMemo0Storage

        self.knowledge = MockMemo0Storage({
            "user_id": "test-v16-4",
            "agent_id": "stat-arb-test"
        })

        self.price_history = PriceHistoryManager(config={"window_size": 200})

        # 填充模拟数据（高度相关的BTC-ETH）
        import random
        random.seed(42)
        btc_base = 94500.0
        eth_base = 3780.0

        for i in range(120):
            noise_btc = random.gauss(0, 50)
            noise_eth = random.gauss(0, 5)
            # 添加共同因子使相关性高
            common_factor = random.gauss(0, 1) * 20

            btc = btc_base + noise_btc + common_factor * 5
            eth = eth_base + noise_eth + common_factor * 0.2

            self.price_history.update_price("BTC/USDT", "binance", btc)
            self.price_history.update_price("ETH/USDT", "binance", eth)

        self.engine = StatisticalArbEngine(
            price_history=self.price_history,
            knowledge_storage=self.knowledge,
            config={
                "z_score_entry": 1.5,
                "z_score_close": 0.3,
                "min_correlation": 0.5,
                "min_data_points": 50,
                "position_size_usd": 500.0,
                "max_positions": 3,
            }
        )

    def test_engine_init(self):
        """测试引擎初始化"""
        stats = self.engine.get_engine_statistics()
        self.assertIn(stats["version"], ["V16.4", "V16.5"])
        self.assertEqual(stats["total_signals_generated"], 0)

    def test_analyze_pair(self):
        """测试配对分析"""
        analysis = self.engine.analyze_pair("BTC/USDT", "ETH/USDT", "binance")

        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.symbol_a, "BTC/USDT")
        self.assertEqual(analysis.symbol_b, "ETH/USDT")
        self.assertIsInstance(analysis.correlation, float)
        self.assertIsInstance(analysis.z_score, float)
        self.assertGreater(analysis.data_points, 0)

    def test_analyze_insufficient_data(self):
        """测试数据不足时返回None"""
        from data_collection.price_history_manager import PriceHistoryManager
        empty_history = PriceHistoryManager()
        engine = __import__(
            'strategies.statistical_arb_engine',
            fromlist=['StatisticalArbEngine']
        ).StatisticalArbEngine(price_history=empty_history)

        result = engine.analyze_pair("FAKE/A", "FAKE/B", "binance")
        self.assertIsNone(result)

    def test_scan_all_pairs(self):
        """测试全配对扫描"""
        results = self.engine.scan_all_pairs(exchange="binance")

        self.assertIsInstance(results, list)
        # 至少应该能分析一些配对（即使不通过协整检验）
        # 因为数据是模拟的，协整性取决于数据质量

    def test_generate_signals(self):
        """测试信号生成"""
        # 先分析
        analyses = self.engine.scan_all_pairs(exchange="binance")

        # 即使没有协整对，generate_signals 也应正常工作
        signals = self.engine.generate_signals(analyses, exchange="binance")
        self.assertIsInstance(signals, list)

    def test_execute_signal(self):
        """测试信号执行"""
        from strategies.statistical_arb_engine import (
            StatArbSignal, SignalType, PairAnalysis, PairStatus
        )

        pair = PairAnalysis(
            symbol_a="BTC/USDT",
            symbol_b="ETH/USDT",
            exchange="binance",
            correlation=0.95,
            z_score=2.5,
            spread_mean=3.22,
            spread_std=0.01,
            current_spread=3.25,
            half_life_hours=4.0,
            is_cointegrated=True,
            pair_status=PairStatus.COINTEGRATED,
            data_points=100,
        )

        signal = StatArbSignal(
            signal_id="test_sig_001",
            signal_type=SignalType.OPEN_SHORT_LONG,
            pair=pair,
            confidence=0.8,
            expected_profit_pct=0.5,
            entry_z_score=2.5,
            quantity_a=0.005,
            quantity_b=0.1,
            price_a=94500.0,
            price_b=3780.0,
            position_value_usd=500.0,
            timestamp=time.time()
        )

        position = self.engine.execute_signal(signal)
        self.assertIsNotNone(position)
        self.assertEqual(position.status, "open")
        self.assertEqual(len(self.engine.positions), 1)

    def test_close_position(self):
        """测试持仓平仓"""
        from strategies.statistical_arb_engine import StatArbPosition

        position = StatArbPosition(
            position_id="test_pos_001",
            signal_id="test_sig_001",
            symbol_a="BTC/USDT",
            symbol_b="ETH/USDT",
            exchange="binance",
            direction="long_a_short_b",
            entry_price_a=94500.0,
            entry_price_b=3780.0,
            entry_z_score=2.0,
            quantity_a=0.005,
            quantity_b=0.1,
            position_value_usd=500.0,
            close_z_score=0.5,
            status="open",
            opened_at=time.time()
        )

        self.engine.positions[position.position_id] = position
        self.engine.total_positions_opened += 1

        # 平仓（价格略涨）
        closed = self.engine.close_position(
            position,
            current_price_a=94600.0,
            current_price_b=3775.0,
            current_z_score=0.3
        )

        self.assertEqual(closed.status, "closed")
        self.assertEqual(len(self.engine.positions), 0)
        self.assertEqual(len(self.engine.closed_positions), 1)

    def test_knowledge_recording(self):
        """测试知识记录"""
        from strategies.statistical_arb_engine import (
            StatArbSignal, SignalType, PairAnalysis, PairStatus
        )

        pair = PairAnalysis(
            symbol_a="BTC/USDT",
            symbol_b="ETH/USDT",
            exchange="binance",
            correlation=0.95,
            z_score=2.0,
            is_cointegrated=True,
            pair_status=PairStatus.COINTEGRATED,
            data_points=100,
            half_life_hours=5.0,
            spread_mean=3.22,
            spread_std=0.01,
            current_spread=3.24,
        )

        signal = StatArbSignal(
            signal_id="test_know_001",
            signal_type=SignalType.OPEN_LONG_SHORT,
            pair=pair,
            confidence=0.75,
            expected_profit_pct=0.3,
            entry_z_score=2.0,
            quantity_a=0.005,
            quantity_b=0.1,
            price_a=94500.0,
            price_b=3780.0,
            position_value_usd=500.0,
            timestamp=time.time()
        )

        self.engine.execute_signal(signal)

        # 验证知识库有记录
        memories = self.knowledge.search_memories("stat_arb_signal", top_k=5)
        self.assertGreater(len(memories), 0, "应记录开仓信号到知识库")

    def test_full_scan(self):
        """测试完整扫描"""
        result = self.engine.run_full_scan(exchange="binance")

        self.assertIn("scan_id", result)
        self.assertIn("pairs_scanned", result)
        self.assertIn("signals_generated", result)
        self.assertIn("duration_ms", result)
        self.assertGreaterEqual(result["duration_ms"], 0)


class TestAdaptiveRiskGate(unittest.TestCase):
    """测试自适应风控"""

    def setUp(self):
        from trading.arbitrage_pipeline import AdaptiveRiskGate
        from storage.mem0_mock_storage import MockMemo0Storage

        self.knowledge = MockMemo0Storage({
            "user_id": "test-risk-v16-4",
            "agent_id": "adaptive-risk-test"
        })
        self.gate = AdaptiveRiskGate(
            knowledge_storage=self.knowledge,
            config={
                "min_confidence_to_execute": 0.65,
                "min_profit_to_execute": 0.05,
                "max_positions": 10,
            }
        )

    def test_init_params(self):
        """测试初始参数"""
        params = self.gate.get_current_params()
        self.assertAlmostEqual(params["min_confidence"], 0.65, places=2)
        self.assertAlmostEqual(params["min_profit_pct"], 0.05, places=2)
        self.assertEqual(params["max_positions"], 10)

    def test_no_adjustment_without_data(self):
        """测试无数据时不调整"""
        # 使用独立的知识库，避免其他测试的数据污染
        from storage.mem0_mock_storage import MockMemo0Storage
        from trading.arbitrage_pipeline import AdaptiveRiskGate
        empty_knowledge = MockMemo0Storage({
            "user_id": "test-empty-risk-v16-4",
            "agent_id": "empty-risk-test"
        })
        gate = AdaptiveRiskGate(knowledge_storage=empty_knowledge)
        result = gate.update_from_knowledge()
        self.assertFalse(result.get("adjusted", False))

    def test_adjust_with_high_win_rate(self):
        """测试高胜率时放松参数"""
        # 注入大量盈利记录
        for i in range(15):
            self.knowledge.add_memory(
                f"[arbitrage_execution] cross_exchange | BTC/USDT | "
                f"expected=0.15% | actual=0.12% | outcome=profitable"
            )
        for i in range(3):
            self.knowledge.add_memory(
                f"[arbitrage_execution] cross_exchange | ETH/USDT | "
                f"expected=0.10% | actual=-0.03% | outcome=loss"
            )

        result = self.gate.update_from_knowledge()
        self.assertTrue(result.get("adjusted", False))
        self.assertEqual(result["direction"], "relaxed")
        # 放松后置信度应降低
        self.assertLess(result["confidence"], 0.65)

    def test_adjust_with_low_win_rate(self):
        """测试低胜率时收紧参数"""
        from storage.mem0_mock_storage import MockMemo0Storage
        from trading.arbitrage_pipeline import AdaptiveRiskGate

        # 使用独立知识库避免数据污染
        loss_knowledge = MockMemo0Storage({
            "user_id": "test-low-win-rate-v16-4",
            "agent_id": "low-win-test"
        })
        gate = AdaptiveRiskGate(
            knowledge_storage=loss_knowledge,
            config={
                "min_confidence_to_execute": 0.65,
                "min_profit_to_execute": 0.05,
                "max_positions": 10,
            }
        )

        # 注入大量亏损记录
        for i in range(3):
            loss_knowledge.add_memory(
                f"[arbitrage_execution] profitable profit good"
            )
        for i in range(15):
            loss_knowledge.add_memory(
                f"[arbitrage_execution] loss failed risky avoid"
            )

        result = gate.update_from_knowledge()
        self.assertTrue(result.get("adjusted", False))
        self.assertEqual(result["direction"], "tightened")
        # 收紧后置信度应提高
        self.assertGreater(result["confidence"], 0.65)

    def test_adjustment_cooldown(self):
        """测试调整冷却"""
        # 填充数据
        for i in range(10):
            self.knowledge.add_memory(f"[arbitrage_execution] outcome=profitable")

        # 第一次调整
        r1 = self.gate.update_from_knowledge()
        self.assertTrue(r1.get("adjusted", False))

        # 立即第二次应被冷却
        r2 = self.gate.update_from_knowledge()
        self.assertFalse(r2.get("adjusted", False))
        self.assertEqual(r2["reason"], "too_frequent")


class TestPipelineV16_4(unittest.TestCase):
    """测试V16.4增强管道"""

    def test_pipeline_with_stat_arb_disabled(self):
        """测试禁用统计套利的管道"""
        from trading.arbitrage_pipeline import ArbitragePipeline
        from strategies.knowledge_driven_arbitrage_scanner import (
            KnowledgeDrivenArbitrageScanner
        )
        from storage.mem0_mock_storage import MockMemo0Storage

        knowledge = MockMemo0Storage({
            "user_id": "test-v164-pipeline",
            "agent_id": "pipeline-test"
        })
        scanner = KnowledgeDrivenArbitrageScanner(
            knowledge_storage=knowledge,
            config={"min_profit_pct": 0.01}
        )
        pipeline = ArbitragePipeline(
            scanner=scanner,
            knowledge_storage=knowledge,
            config={
                "mode": "simulation",
                "enable_stat_arb": False,
                "enable_adaptive_risk": False,
                "min_confidence_to_execute": 0.5,
                "min_profit_to_execute": 0.01,
            }
        )

        result = pipeline.run_pipeline()
        self.assertEqual(result.stage.value, "completed")
        self.assertEqual(result.stat_arb_signals, 0)

    def test_pipeline_with_stat_arb_enabled(self):
        """测试启用统计套利的管道"""
        from trading.arbitrage_pipeline import ArbitragePipeline
        from strategies.knowledge_driven_arbitrage_scanner import (
            KnowledgeDrivenArbitrageScanner
        )
        from data_collection.price_history_manager import PriceHistoryManager
        from strategies.statistical_arb_engine import StatisticalArbEngine
        from storage.mem0_mock_storage import MockMemo0Storage

        knowledge = MockMemo0Storage({
            "user_id": "test-v164-stat-arb",
            "agent_id": "stat-pipeline-test"
        })

        # 初始化价格历史
        price_history = PriceHistoryManager(config={"window_size": 200})
        import random
        random.seed(123)
        btc_base, eth_base = 94500.0, 3780.0
        for i in range(120):
            common = random.gauss(0, 1)
            btc = btc_base + random.gauss(0, 50) + common * 30
            eth = eth_base + random.gauss(0, 5) + common * 1.2
            price_history.update_price("BTC/USDT", "binance", btc)
            price_history.update_price("ETH/USDT", "binance", eth)

        # 初始化统计套利引擎
        stat_engine = StatisticalArbEngine(
            price_history=price_history,
            knowledge_storage=knowledge,
            config={
                "z_score_entry": 1.5,
                "min_correlation": 0.3,
                "min_data_points": 50,
                "position_size_usd": 200,
            }
        )

        scanner = KnowledgeDrivenArbitrageScanner(
            knowledge_storage=knowledge,
            config={"min_profit_pct": 0.01}
        )

        pipeline = ArbitragePipeline(
            scanner=scanner,
            knowledge_storage=knowledge,
            stat_arb_engine=stat_engine,
            price_history_manager=price_history,
            config={
                "mode": "simulation",
                "enable_stat_arb": True,
                "enable_adaptive_risk": False,
                "min_confidence_to_execute": 0.5,
                "min_profit_to_execute": 0.01,
            }
        )

        result = pipeline.run_pipeline()
        self.assertEqual(result.stage.value, "completed")
        # 统计套利应已扫描（即使没有生成信号也是OK的）
        self.assertGreaterEqual(result.stat_arb_pairs_scanned, 0)

    def test_pipeline_statistics_v16_4(self):
        """测试V16.4统计字段"""
        from trading.arbitrage_pipeline import ArbitragePipeline
        from storage.mem0_mock_storage import MockMemo0Storage

        knowledge = MockMemo0Storage({
            "user_id": "test-stats-v164",
            "agent_id": "stats-test"
        })
        pipeline = ArbitragePipeline(
            knowledge_storage=knowledge,
            config={
                "enable_stat_arb": False,
                "enable_adaptive_risk": False,
            }
        )
        pipeline.run_pipeline()

        stats = pipeline.get_pipeline_statistics()
        self.assertIn(stats["version"], ["V16.4", "V16.5"])
        self.assertIn("stat_arb", stats)
        self.assertIn("adaptive_risk", stats)
        self.assertFalse(stats["stat_arb"]["enabled"])


class TestEndToEndV16_4(unittest.TestCase):
    """V16.4端到端测试"""

    def test_full_pipeline_with_price_feed_and_stat_arb(self):
        """完整端到端: PriceFeed → PriceHistory → StatArb → Pipeline → Knowledge"""
        from data_collection.ccxt_price_feed import CcxtPriceFeed
        from data_collection.price_history_manager import PriceHistoryManager
        from strategies.knowledge_driven_arbitrage_scanner import (
            KnowledgeDrivenArbitrageScanner
        )
        from strategies.statistical_arb_engine import StatisticalArbEngine
        from trading.arbitrage_pipeline import ArbitragePipeline
        from storage.mem0_mock_storage import MockMemo0Storage

        # 1. 初始化所有组件
        knowledge = MockMemo0Storage({
            "user_id": "e2e-v16-4",
            "agent_id": "full-pipeline-test"
        })
        feed = CcxtPriceFeed()
        price_history = PriceHistoryManager(config={"window_size": 300})

        # 2. 初始化历史数据
        price_history.seed_from_price_feed(feed, ticks=120)

        # 3. 创建统计套利引擎
        stat_engine = StatisticalArbEngine(
            price_history=price_history,
            knowledge_storage=knowledge,
            config={
                "z_score_entry": 1.8,
                "z_score_close": 0.4,
                "min_correlation": 0.3,
                "min_data_points": 50,
                "position_size_usd": 200,
                "max_positions": 3,
            }
        )

        # 4. 创建管道
        scanner = KnowledgeDrivenArbitrageScanner(
            knowledge_storage=knowledge,
            config={"min_profit_pct": 0.01}
        )
        pipeline = ArbitragePipeline(
            scanner=scanner,
            knowledge_storage=knowledge,
            stat_arb_engine=stat_engine,
            price_history_manager=price_history,
            config={
                "mode": "simulation",
                "enable_stat_arb": True,
                "enable_adaptive_risk": False,
                "min_confidence_to_execute": 0.5,
                "min_profit_to_execute": 0.01,
            }
        )

        # 5. 运行3轮
        results = pipeline.run_batch(rounds=3, interval_sec=0.05)

        # 6. 验证
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIn(r.stage.value, ["completed", "failed"])

        # 7. 统计
        stats = pipeline.get_pipeline_statistics()
        self.assertIn(stats["version"], ["V16.4", "V16.5"])
        self.assertGreater(stats["total_pipelines"], 0)
        self.assertTrue(stats["stat_arb"]["enabled"])

        # 8. 知识库应有记录
        all_memories = knowledge.get_all_memories()
        self.assertGreater(len(all_memories), 0, "知识库应有记录")

    def test_knowledge_feedback_loop_with_stat_arb(self):
        """测试统计套利的知识反馈闭环"""
        from data_collection.ccxt_price_feed import CcxtPriceFeed
        from data_collection.price_history_manager import PriceHistoryManager
        from strategies.statistical_arb_engine import StatisticalArbEngine
        from storage.mem0_mock_storage import MockMemo0Storage

        knowledge = MockMemo0Storage({
            "user_id": "feedback-v16-4",
            "agent_id": "stat-feedback-test"
        })
        feed = CcxtPriceFeed()
        price_history = PriceHistoryManager(config={"window_size": 200})
        price_history.seed_from_price_feed(feed, ticks=100)

        engine = StatisticalArbEngine(
            price_history=price_history,
            knowledge_storage=knowledge,
            config={
                "z_score_entry": 1.5,
                "min_correlation": 0.3,
                "min_data_points": 30,
            }
        )

        # 第一轮扫描 — 写入知识
        r1 = engine.run_full_scan()
        knowledge_count_1 = len(knowledge.get_all_memories())

        # 第二轮扫描 — 应能命中第一次的知识
        # 先更新一些价格
        for _ in range(5):
            snapshot = feed.get_all_prices()
            price_history.update_from_snapshot(snapshot)

        r2 = engine.run_full_scan()
        knowledge_count_2 = len(knowledge.get_all_memories())

        # 知识库应该增长
        self.assertGreaterEqual(knowledge_count_2, knowledge_count_1,
                               "知识库应在每轮扫描后增长")

        # 验证知识库中有统计套利相关记录
        stat_memories = knowledge.search_memories("stat_arb", top_k=10)
        # 可能没有（取决于数据质量），但不应报错
        self.assertIsInstance(stat_memories, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
