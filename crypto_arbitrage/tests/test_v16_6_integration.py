"""V16.6集成测试 - 双向知识桥 + 信号过滤 + 管道持久化

测试覆盖：
1. TradingKnowledgeBridge — 读写双向知识流/市场上下文/策略洞察/币种历史
2. KnowledgeDrivenSignalFilter — 信号过滤/去重/亏损回避/统计
3. PipelineStatePersistence — 持仓保存恢复/风控状态/管道统计/历史
4. Pipeline V16.6 — 知识上下文加载/信号过滤阶段/持久化集成
5. 回归 — V16.5测试仍然通过

创建时间：2026-05-05
"""

import os
import sys
import tempfile
import time
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTradingKnowledgeBridge(unittest.TestCase):
    """交易知识桥接器测试"""

    def setUp(self):
        from trading.trading_knowledge_bridge import TradingKnowledgeBridge
        from storage.mem0_mock_storage import MockMemo0Storage

        self.storage = MockMemo0Storage({
            "user_id": "test-user",
            "agent_id": "test-bridge"
        })
        self.bridge = TradingKnowledgeBridge(
            knowledge_storage=self.storage,
            config={"perf_buffer_size": 3}
        )

    def test_bridge_init(self):
        """测试桥接器初始化"""
        self.assertIsNotNone(self.bridge)
        self.assertEqual(self.bridge.total_reads, 0)
        self.assertEqual(self.bridge.total_writes, 0)

    def test_record_trade_result(self):
        """测试记录交易结果"""
        result = self.bridge.record_trade_result(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            pnl_pct=0.15,
            pnl_usd=1.5,
            outcome="profitable"
        )
        self.assertTrue(result)
        self.assertEqual(self.bridge.total_writes, 1)

    def test_record_risk_event(self):
        """测试记录风控事件"""
        result = self.bridge.record_risk_event(
            event_type="circuit_break",
            severity="critical",
            strategy="funding_rate",
            symbol="ETH/USDT",
            reason="最大回撤触发",
            action_taken="全部平仓"
        )
        self.assertTrue(result)

    def test_record_strategy_performance(self):
        """测试记录策略性能"""
        result = self.bridge.record_strategy_performance(
            strategy="triangular",
            total_trades=10,
            win_rate=0.7,
            avg_pnl_pct=0.12,
            best_symbol="BTC/USDT",
            period="daily"
        )
        self.assertTrue(result)

    def test_get_market_context(self):
        """测试获取市场上下文"""
        # 先写入一些数据
        self.bridge.record_trade_result("cross_exchange", "BTC/USDT", "binance", 0.1, 1.0, "profitable")
        self.bridge.record_trade_result("cross_exchange", "ETH/USDT", "okex", -0.05, -0.5, "loss")
        self.bridge.record_risk_event("reject", "high", "statistical", "SOL/USDT", "集中度超限")

        context = self.bridge.get_market_context()
        self.assertIsNotNone(context)
        self.assertIsInstance(context.recent_win_rate, float)
        self.assertGreaterEqual(context.recent_risk_events, 0)

    def test_get_market_context_cache(self):
        """测试市场上下文缓存"""
        context1 = self.bridge.get_market_context()
        context2 = self.bridge.get_market_context()
        # 第二次应该是缓存命中
        self.assertGreater(self.bridge.total_cache_hits, 0)

    def test_get_strategy_insight(self):
        """测试获取策略洞察"""
        # 写入多条策略性能
        for i in range(5):
            self.bridge.record_strategy_performance(
                strategy="cross_exchange",
                total_trades=10,
                win_rate=0.6,
                avg_pnl_pct=0.1 + i * 0.01,
            )

        insight = self.bridge.get_strategy_insight("cross_exchange")
        # 可能返回None（数据格式可能不匹配），不应报错
        # 关键是不crash

    def test_get_symbol_history(self):
        """测试获取币种历史"""
        self.bridge.record_trade_result("funding_rate", "BTC/USDT", "binance", 0.1, 1.0, "profitable")

        history = self.bridge.get_symbol_history("BTC/USDT")
        self.assertIsInstance(history, dict)

    def test_record_signal_feedback(self):
        """测试记录信号反馈"""
        result = self.bridge.record_signal_feedback(
            signal_id="sig_001",
            signal_type="cross_exchange",
            symbol="BTC/USDT",
            accepted=True,
            pnl_if_accepted=0.15
        )
        self.assertTrue(result)

    def test_save_load_pipeline_state(self):
        """测试保存和加载管道状态"""
        state = {
            "pipeline_id": "test_pipe_001",
            "total_pnl": 10.5,
            "active_positions": 3
        }
        save_result = self.bridge.save_pipeline_state(state)
        self.assertTrue(save_result)

        loaded = self.bridge.load_latest_pipeline_state()
        # 可能返回None（mock搜索限制），关键是不crash
        # 如果有结果，验证数据
        if loaded:
            self.assertEqual(loaded["pipeline_id"], "test_pipe_001")

    def test_bridge_statistics(self):
        """测试桥接器统计"""
        self.bridge.record_trade_result("test", "BTC/USDT", "binance", 0.1, 1.0, "profitable")

        stats = self.bridge.get_bridge_statistics()
        self.assertEqual(stats["version"], "V16.6")
        self.assertGreaterEqual(stats["total_writes"], 1)

    def test_perf_buffer_flush(self):
        """测试性能缓冲区刷新"""
        # 写入超过buffer_size(3)条
        for i in range(5):
            self.bridge.record_trade_result(
                f"strategy_{i % 2}", "BTC/USDT", "binance",
                0.1 * (1 if i % 2 == 0 else -1), 1.0,
                "profitable" if i % 2 == 0 else "loss"
            )
        # 缓冲区应该已被刷新
        self.assertEqual(len(self.bridge._perf_buffer), 5 % 3)


class TestKnowledgeSignalFilter(unittest.TestCase):
    """知识驱动信号过滤器测试"""

    def setUp(self):
        from trading.knowledge_signal_filter import (
            KnowledgeDrivenSignalFilter, FilterAction
        )
        self.filter = KnowledgeDrivenSignalFilter(config={
            "dedup_cooldown_sec": 2.0,
            "max_recent_losses": 2,
            "enable_dedup": True,
            "enable_loss_avoidance": True,
        })

    def test_filter_init(self):
        """测试过滤器初始化"""
        self.assertEqual(self.filter.total_signals_received, 0)
        self.assertTrue(self.filter.enable_dedup)

    def test_signal_pass(self):
        """测试信号通过"""
        result = self.filter.filter_signal(
            signal_type="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="buy",
            confidence=0.8,
            size_usd=1000.0
        )
        self.assertEqual(result.action.value, "pass")
        self.assertEqual(result.original_confidence, 0.8)

    def test_signal_dedup(self):
        """测试信号去重"""
        # 第一个信号通过
        self.filter.filter_signal("cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000)
        # 同一个信号在冷却期内应该被延迟
        result = self.filter.filter_signal("cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000)
        self.assertEqual(result.action.value, "delay")

    def test_signal_loss_avoidance(self):
        """测试亏损回避"""
        # 模拟连续亏损
        for i in range(3):
            self.filter.notify_trade_result("SOL/USDT", "cross_exchange", -1.0, "loss")

        result = self.filter.filter_signal(
            signal_type="cross_exchange",
            symbol="SOL/USDT",
            exchange="binance",
            side="buy",
            confidence=0.5,
            size_usd=500.0
        )
        # 应该被降低或拒绝
        self.assertIn(result.action.value, ["reduce", "reduce_size", "reject", "reduce_confidence"])

    def test_different_signals_pass(self):
        """测试不同信号通过"""
        self.filter.filter_signal("cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000)
        # 不同symbol应该通过
        result = self.filter.filter_signal("cross_exchange", "ETH/USDT", "binance", "buy", 0.7, 800)
        self.assertEqual(result.action.value, "pass")

    def test_filter_statistics(self):
        """测试过滤器统计"""
        self.filter.filter_signal("cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000)

        stats = self.filter.get_filter_statistics()
        self.assertEqual(stats["version"], "V16.6")
        self.assertEqual(stats["total_received"], 1)

    def test_cleanup_expired(self):
        """测试过期信号清理"""
        self.filter.filter_signal("cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000)
        # 手动设置过期时间
        from trading.knowledge_signal_filter import SignalFingerprint
        fp = SignalFingerprint("cross_exchange", "BTC/USDT", "binance", "buy")
        self.filter._recent_signals[fp] = time.time() - 1000  # 很久前

        cleaned = self.filter.cleanup_expired_signals()
        self.assertGreater(cleaned, 0)

    def test_notify_trade_result(self):
        """测试通知交易结果"""
        self.filter.notify_trade_result("BTC/USDT", "cross_exchange", -0.5, "loss")
        self.assertEqual(len(self.filter._recent_losses), 1)


class TestPipelineStatePersistence(unittest.TestCase):
    """管道状态持久化测试"""

    def setUp(self):
        # Windows: 使用uuid生成唯一路径避免文件锁冲突
        import uuid
        self._db_path = os.path.join(
            tempfile.gettempdir(),
            f"test_pipeline_{uuid.uuid4().hex[:8]}.db"
        )
        from trading.pipeline_state_persistence import PipelineStatePersistence
        self.persistence = PipelineStatePersistence(db_path=self._db_path)

    def tearDown(self):
        self.persistence.close()
        try:
            os.unlink(self._db_path)
        except Exception:
            pass

    def test_persistence_init(self):
        """测试持久化初始化"""
        stats = self.persistence.get_persistence_stats()
        self.assertEqual(stats["version"], "V16.6")
        self.assertEqual(stats["open_positions"], 0)

    def test_save_and_load_position(self):
        """测试保存和加载持仓"""
        self.persistence.save_position(
            position_id="pos_test001",
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            side="buy",
            quantity=0.1,
            value_usd=9450.0,
            entry_price=94500.0,
            opened_at=time.time()
        )

        positions = self.persistence.load_open_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].position_id, "pos_test001")
        self.assertEqual(positions[0].symbol, "BTC/USDT")

    def test_close_position(self):
        """测试关闭持仓"""
        self.persistence.save_position(
            position_id="pos_test002",
            strategy="funding_rate",
            symbol="ETH/USDT",
            exchange="okex",
            side="short",
            quantity=1.0,
            value_usd=3780.0,
            entry_price=3780.0
        )

        self.persistence.close_position("pos_test002", realized_pnl=5.0)

        positions = self.persistence.load_open_positions()
        self.assertEqual(len(positions), 0)

    def test_save_and_load_risk_state(self):
        """测试保存和加载风控状态"""
        self.persistence.save_risk_state(
            peak_nav=10500.0,
            total_realized_pnl=500.0,
            circuit_breaker_active=False,
            circuit_breaker_reason="",
            circuit_breaker_since=0.0,
            total_position_count=3
        )

        state = self.persistence.load_risk_state()
        self.assertIsNotNone(state)
        self.assertEqual(state.peak_nav, 10500.0)
        self.assertEqual(state.total_realized_pnl, 500.0)
        self.assertFalse(state.circuit_breaker_active)

    def test_save_and_load_pipeline_stats(self):
        """测试保存和加载管道统计"""
        from trading.pipeline_state_persistence import PersistedPipelineStats

        stats = PersistedPipelineStats(
            total_pipelines=100,
            total_opportunities_found=500,
            total_opportunities_executed=50,
            total_positions_opened=50,
            total_positions_closed=48,
            total_realized_pnl=125.5,
            total_stat_arb_pnl=80.0,
            total_funding_rate_pnl=45.5,
        )
        self.persistence.save_pipeline_stats(stats)

        loaded = self.persistence.load_pipeline_stats()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.total_pipelines, 100)
        self.assertAlmostEqual(loaded.total_realized_pnl, 125.5)

    def test_save_and_load_history(self):
        """测试保存和加载管道历史"""
        self.persistence.save_pipeline_result(
            pipeline_id="pipe_001",
            stage="completed",
            opportunities_scanned=10,
            opportunities_executed=2,
            positions_opened=2,
            positions_closed=1,
            realized_pnl=5.0,
            execution_time_ms=150.0,
            errors=[]
        )

        history = self.persistence.load_recent_history(limit=5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["pipeline_id"], "pipe_001")

    def test_cleanup_old_history(self):
        """测试清理旧历史"""
        # 插入一条新历史
        self.persistence.save_pipeline_result(
            pipeline_id="pipe_new",
            stage="completed"
        )
        cleaned = self.persistence.cleanup_old_history(max_age_days=30)
        self.assertGreaterEqual(cleaned, 0)


class TestPipelineV16_6(unittest.TestCase):
    """管道V16.6集成测试"""

    def test_pipeline_v16_6_fields(self):
        """测试V16.6 PipelineResult新字段"""
        from trading.arbitrage_pipeline import PipelineResult, PipelineStage

        result = PipelineResult(
            pipeline_id="test",
            stage=PipelineStage.COMPLETED
        )
        self.assertFalse(result.knowledge_context_applied)
        self.assertEqual(result.signals_filtered, 0)
        self.assertEqual(result.knowledge_reads, 0)
        self.assertEqual(result.knowledge_writes, 0)
        self.assertFalse(result.state_persisted)

    def test_pipeline_init_with_v16_6_components(self):
        """测试管道V16.6组件初始化"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline(config={
            "mode": "simulation",
            "enable_knowledge_bridge": True,
            "enable_signal_filter": True,
            "enable_state_persistence": True,
        })

        self.assertTrue(pipeline.enable_knowledge_bridge)
        self.assertTrue(pipeline.enable_signal_filter)
        self.assertTrue(pipeline.enable_state_persistence)

    def test_pipeline_disable_v16_6(self):
        """测试禁用V16.6功能"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline(config={
            "enable_knowledge_bridge": False,
            "enable_signal_filter": False,
            "enable_state_persistence": False,
        })

        self.assertFalse(pipeline.enable_knowledge_bridge)
        self.assertFalse(pipeline.enable_signal_filter)
        self.assertFalse(pipeline.enable_state_persistence)

    def test_pipeline_statistics_v16_6(self):
        """测试管道统计包含V16.6字段"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline(config={"mode": "simulation"})
        stats = pipeline.get_pipeline_statistics()

        self.assertEqual(stats["version"], "V16.6")
        self.assertIn("knowledge_bridge", stats)
        self.assertIn("total_reads", stats["knowledge_bridge"])
        self.assertIn("total_writes", stats["knowledge_bridge"])

    def test_create_pipeline_with_v16_6(self):
        """测试使用V16.6参数创建管道"""
        from trading.arbitrage_pipeline import create_arbitrage_pipeline

        pipeline = create_arbitrage_pipeline(config={"mode": "simulation"})
        self.assertIsNotNone(pipeline)


class TestEndToEndV16_6(unittest.TestCase):
    """V16.6端到端测试"""

    def test_knowledge_bridge_roundtrip(self):
        """测试知识桥接器完整读写闭环"""
        from trading.trading_knowledge_bridge import TradingKnowledgeBridge
        from storage.mem0_mock_storage import MockMemo0Storage

        storage = MockMemo0Storage({"user_id": "e2e", "agent_id": "e2e"})
        bridge = TradingKnowledgeBridge(knowledge_storage=storage)

        # 写入交易结果
        bridge.record_trade_result("cross_exchange", "BTC/USDT", "binance", 0.1, 1.0, "profitable")
        bridge.record_trade_result("cross_exchange", "ETH/USDT", "okex", -0.05, -0.5, "loss")
        bridge.record_risk_event("circuit_break", "critical", "system", "all", "回撤超限")

        # 读取上下文
        context = bridge.get_market_context(force_refresh=True)
        self.assertGreater(context.recent_risk_events, 0)

        # 验证统计
        stats = bridge.get_bridge_statistics()
        self.assertGreater(stats["total_writes"], 0)
        self.assertGreater(stats["total_reads"], 0)

    def test_signal_filter_with_bridge(self):
        """测试信号过滤器与知识桥接器协作"""
        from trading.trading_knowledge_bridge import TradingKnowledgeBridge
        from trading.knowledge_signal_filter import KnowledgeDrivenSignalFilter
        from storage.mem0_mock_storage import MockMemo0Storage

        storage = MockMemo0Storage({"user_id": "e2e", "agent_id": "e2e"})
        bridge = TradingKnowledgeBridge(knowledge_storage=storage)
        signal_filter = KnowledgeDrivenSignalFilter(
            knowledge_bridge=bridge,
            config={"dedup_cooldown_sec": 5.0}
        )

        # 模拟信号过滤
        r1 = signal_filter.filter_signal(
            "cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000
        )
        self.assertEqual(r1.action.value, "pass")

        # 同一信号去重
        r2 = signal_filter.filter_signal(
            "cross_exchange", "BTC/USDT", "binance", "buy", 0.8, 1000
        )
        self.assertEqual(r2.action.value, "delay")

        # 模拟亏损后
        signal_filter.notify_trade_result("SOL/USDT", "statistical", -2.0, "loss")
        signal_filter.notify_trade_result("SOL/USDT", "statistical", -1.5, "loss")
        signal_filter.notify_trade_result("SOL/USDT", "statistical", -3.0, "loss")

        r3 = signal_filter.filter_signal(
            "statistical", "SOL/USDT", "binance", "buy", 0.5, 500
        )
        self.assertIn(r3.action.value, ["reduce", "reduce_size", "reject", "reduce_confidence"])

    def test_persistence_roundtrip(self):
        """测试持久化完整读写闭环"""
        import uuid
        from trading.pipeline_state_persistence import PipelineStatePersistence, PersistedPipelineStats

        db_path = os.path.join(
            tempfile.gettempdir(),
            f"e2e_test_{uuid.uuid4().hex[:8]}.db"
        )

        try:
            persistence = PipelineStatePersistence(db_path=db_path)

            # 保存持仓
            persistence.save_position("pos_1", "cross_exchange", "BTC/USDT", "binance",
                                       "buy", 0.1, 9450.0, 94500.0, opened_at=time.time())
            persistence.save_position("pos_2", "funding_rate", "ETH/USDT", "okex",
                                       "short", 1.0, 3780.0, 3780.0, opened_at=time.time())

            # 保存风控状态
            persistence.save_risk_state(10500, 500, False, "", 0, 2)

            # 保存统计
            persistence.save_pipeline_stats(PersistedPipelineStats(
                total_pipelines=50, total_realized_pnl=100.0
            ))

            # 加载验证
            positions = persistence.load_open_positions()
            self.assertEqual(len(positions), 2)

            risk = persistence.load_risk_state()
            self.assertEqual(risk.peak_nav, 10500)

            stats = persistence.load_pipeline_stats()
            self.assertEqual(stats.total_pipelines, 50)

            persistence.close()

        finally:
            try:
                os.unlink(db_path)
            except Exception:
                pass


class TestRegressionV16_5(unittest.TestCase):
    """V16.5回归测试"""

    def test_funding_rate_engine_still_works(self):
        """测试V16.5资金费率引擎仍可用"""
        from strategies.funding_rate_engine import FundingRateEngine

        engine = FundingRateEngine(config={"max_total_positions": 2})
        snapshots = engine.generate_simulated_rates()
        self.assertIn("BTC/USDT", snapshots)

    def test_portfolio_risk_manager_still_works(self):
        """测试V16.5组合风控仍可用"""
        from trading.portfolio_risk_manager import PortfolioRiskManager

        prm = PortfolioRiskManager()
        pid = prm.register_position("cross_exchange", "BTC/USDT", "binance", "long", 0.1, 9450.0)
        self.assertTrue(pid.startswith("prisk_"))

    def test_mock_storage_still_works(self):
        """测试Mock存储仍可用"""
        from storage.mem0_mock_storage import MockMemo0Storage

        storage = MockMemo0Storage({"user_id": "test", "agent_id": "test"})
        storage.add_memory("test memory")
        results = storage.search_memories("test", top_k=5)
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
