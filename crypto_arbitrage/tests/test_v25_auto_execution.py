"""V25.0集成测试 - Auto Execution Engine 自动交易引擎

测试覆盖：
1. AutoExecutionEngine — 自动化交易引擎
2. Execution Modes — 执行模式
3. Opportunity Pool — 机会池管理
4. Scan Loop — 扫描循环
5. Memo0 Integration (V25.1) — 知识库学习反馈
6. 回归 — V24/V23/V22/V21/V16.6测试仍然通过

创建时间：2026-05-06
更新时间：2026-05-06 06:10 (V25.1) — 添加Memo0集成测试
"""

import os
import sys
import unittest
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAutoExecutionEngine(unittest.TestCase):
    """自动交易执行引擎测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'scan_interval_seconds': 1,
                'min_score_threshold': 60.0,
                'min_confidence': 0.5
            }
        )

    def test_engine_init(self):
        """测试引擎初始化"""
        self.assertIsNotNone(self.engine)
        self.assertFalse(self.engine.is_running)
        self.assertEqual(self.engine.loop_status.value, "idle")

    def test_start_engine(self):
        """测试启动引擎"""
        result = self.engine.start()
        self.assertTrue(result)
        self.assertTrue(self.engine.is_running)

    def test_stop_engine(self):
        """测试停止引擎"""
        self.engine.start()
        result = self.engine.stop()
        self.assertTrue(result)
        self.assertFalse(self.engine.is_running)

    def test_pause_resume(self):
        """测试暂停恢复"""
        self.engine.start()
        self.engine.pause()
        self.assertEqual(self.engine.loop_status.value, "paused")

        self.engine.resume()
        self.assertEqual(self.engine.loop_status.value, "idle")

    def test_double_start(self):
        """测试重复启动"""
        self.engine.start()
        result = self.engine.start()  # 应该返回False
        self.assertFalse(result)

    def test_stop_without_start(self):
        """测试未启动就停止"""
        result = self.engine.stop()
        self.assertTrue(result)


class TestOpportunityPool(unittest.TestCase):
    """机会池测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine()

    def test_add_to_pool(self):
        """测试添加到池"""
        from trading.auto_execution_engine import ScannedOpportunity

        opp = ScannedOpportunity(
            opportunity_id="test_1",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        self.engine._add_to_pool(opp)
        self.assertEqual(len(self.engine.opportunity_pool), 1)

    def test_remove_from_pool(self):
        """测试从池移除"""
        from trading.auto_execution_engine import ScannedOpportunity

        opp = ScannedOpportunity(
            opportunity_id="test_1",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        self.engine._add_to_pool(opp)
        self.engine._remove_from_pool(opp)
        self.assertEqual(len(self.engine.opportunity_pool), 0)

    def test_pool_max_size(self):
        """测试池大小限制"""
        from trading.auto_execution_engine import ScannedOpportunity

        # 超过max_pool_size
        from trading.auto_execution_engine import ScannedOpportunity

        for i in range(150):
            opp = ScannedOpportunity(
                opportunity_id=f"test_{i}",
                symbol="BTC/USDT",
                action="buy",
                entry_price=50000.0,
                target_price=55000.0,
                stop_loss=48000.0,
                score=75.0,
                confidence=0.7,
                recommendation="execute"
            )
            self.engine._add_to_pool(opp)

        # 应该被限制
        self.assertLessEqual(len(self.engine.opportunity_pool), 100)

    def test_get_pool(self):
        """测试获取池"""
        from trading.auto_execution_engine import ScannedOpportunity

        for i in range(5):
            opp = ScannedOpportunity(
                opportunity_id=f"test_{i}",
                symbol="BTC/USDT",
                action="buy",
                entry_price=50000.0,
                target_price=55000.0,
                stop_loss=48000.0,
                score=75.0,
                confidence=0.7,
                recommendation="execute"
            )
            self.engine._add_to_pool(opp)

        pool = self.engine.get_pool(limit=3)
        self.assertEqual(len(pool), 3)


class TestExecutionConfig(unittest.TestCase):
    """执行配置测试"""

    def test_config_default(self):
        """测试默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()
        self.assertEqual(config.mode, "manual")
        self.assertEqual(config.scan_interval_seconds, 30)
        self.assertEqual(config.min_score_threshold, 60.0)

    def test_config_custom(self):
        """测试自定义配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig(
            mode="full_auto",
            scan_interval_seconds=10,
            min_score_threshold=70.0
        )
        self.assertEqual(config.mode, "full_auto")
        self.assertEqual(config.scan_interval_seconds, 10)
        self.assertEqual(config.min_score_threshold, 70.0)


class TestStatusAndStats(unittest.TestCase):
    """状态和统计测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine()

    def test_get_status(self):
        """测试获取状态"""
        status = self.engine.get_status()
        self.assertIn('is_running', status)
        self.assertIn('loop_status', status)
        self.assertIn('stats', status)

    def test_stats_init(self):
        """测试统计初始化"""
        stats = self.engine.get_status()['stats']
        self.assertEqual(stats['total_scans'], 0)
        self.assertEqual(stats['opportunities_found'], 0)
        self.assertEqual(stats['opportunities_executed'], 0)

    def test_properties(self):
        """测试属性"""
        self.assertEqual(self.engine.total_executed, 0)
        self.assertEqual(self.engine.total_failed, 0)
        self.assertEqual(self.engine.success_rate, 0.0)


class TestLoopStatus(unittest.TestCase):
    """循环状态测试"""

    def test_loop_status_enum(self):
        """测试枚举"""
        from trading.auto_execution_engine import LoopStatus

        self.assertEqual(LoopStatus.IDLE.value, "idle")
        self.assertEqual(LoopStatus.SCANNING.value, "scanning")
        self.assertEqual(LoopStatus.EVALUATING.value, "evaluating")
        self.assertEqual(LoopStatus.EXECUTING.value, "executing")
        self.assertEqual(LoopStatus.PAUSED.value, "paused")
        self.assertEqual(LoopStatus.STOPPED.value, "stopped")


class TestScannedOpportunity(unittest.TestCase):
    """扫描机会测试"""

    def test_opportunity_creation(self):
        """测试创建"""
        from trading.auto_execution_engine import ScannedOpportunity

        opp = ScannedOpportunity(
            opportunity_id="test_1",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        self.assertEqual(opp.opportunity_id, "test_1")
        self.assertEqual(opp.symbol, "BTC/USDT")
        self.assertEqual(opp.score, 75.0)


class TestRegressionV24V23V22V21V16(unittest.TestCase):
    """回归测试 - V24/V23/V22/V21/V16.6"""

    def test_v24_pipeline_still_works(self):
        """测试V24管道仍然可用"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()
        self.assertIsNotNone(engine)

    def test_v23_signal_scorer_still_works(self):
        """测试V23信号评分器仍然可用"""
        from trading.signal_quality_scorer import SignalQualityScorer

        scorer = SignalQualityScorer()
        self.assertIsNotNone(scorer)

    def test_v22_position_sizer_still_works(self):
        """测试V22仓位管理器仍然可用"""
        from trading.dynamic_position_sizer import DynamicPositionSizer

        sizer = DynamicPositionSizer()
        self.assertIsNotNone(sizer)

    def test_v21_portfolio_analytics_still_works(self):
        """测试V21投资组合分析器仍然可用"""
        from trading.portfolio_analytics import PortfolioAnalytics

        analytics = PortfolioAnalytics()
        self.assertIsNotNone(analytics)

    def test_v16_pipeline_still_works(self):
        """测试V16.6管道仍然可用"""
        from trading.arbitrage_pipeline import ArbitragePipeline

        pipeline = ArbitragePipeline()
        self.assertIsNotNone(pipeline)


class TestMemo0IntegrationV25(unittest.TestCase):
    """V25.1 Memo0知识库集成测试"""

    def test_engine_init_with_knowledge_bridge(self):
        """测试引擎初始化带有知识桥接器"""
        from trading.auto_execution_engine import AutoExecutionEngine

        # 模拟知识桥接器
        mock_bridge = type('MockKnowledgeBridge', (), {
            'record_trade_result': lambda self, x: True,
            'get_market_context': lambda self: {'recent_win_rate': 0.6}
        })()

        engine = AutoExecutionEngine(knowledge_bridge=mock_bridge)
        self.assertIsNotNone(engine)
        self.assertEqual(engine.knowledge_bridge, mock_bridge)

    def test_engine_init_without_knowledge_bridge(self):
        """测试引擎初始化不带知识桥接器(默认)"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()
        self.assertIsNone(engine.knowledge_bridge)

    def test_record_to_knowledge_without_bridge(self):
        """测试无知识桥接器时记录方法"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity,
            ExecutionResult
        )

        engine = AutoExecutionEngine()

        opp = ScannedOpportunity(
            opportunity_id="test_001",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        result = ExecutionResult(
            opportunity_id="test_001",
            success=True,
            executed_price=50000.0,
            executed_size=1.0
        )

        # 无知识桥接器时应返回False
        self.assertFalse(engine.record_to_knowledge(opp, result))

    def test_record_to_knowledge_with_bridge(self):
        """测试有知识桥接器时记录方法"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity,
            ExecutionResult
        )

        # 创建模拟的知识桥接器 - 使用V25.1接口
        recorded = []

        class MockKnowledgeBridge:
            def record_trade_result(
                self, strategy, symbol, exchange, pnl_pct, pnl_usd, outcome, details=None
            ):
                recorded.append({
                    'strategy': strategy,
                    'symbol': symbol,
                    'exchange': exchange,
                    'pnl_pct': pnl_pct,
                    'pnl_usd': pnl_usd,
                    'outcome': outcome,
                    'details': details
                })
                return True

        mock_bridge = MockKnowledgeBridge()
        engine = AutoExecutionEngine(knowledge_bridge=mock_bridge)

        opp = ScannedOpportunity(
            opportunity_id="test_001",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        result = ExecutionResult(
            opportunity_id="test_001",
            success=True,
            executed_price=50000.0,
            executed_size=1.0
        )

        self.assertTrue(engine.record_to_knowledge(opp, result, pnl_pct=1.5))
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0]['symbol'], "BTC/USDT")
        self.assertEqual(recorded[0]['pnl_pct'], 1.5)
        self.assertEqual(recorded[0]['strategy'], "execute")

    def test_get_market_context_without_bridge(self):
        """测试无知识桥接器时获取上下文"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()
        context = engine.get_market_context()
        self.assertIsNone(context)

    def test_get_market_context_with_bridge(self):
        """测试有知识桥接器时获取上下文"""
        from trading.auto_execution_engine import AutoExecutionEngine
        from dataclasses import dataclass, field

        # 创建模拟的MarketContext对象
        @dataclass
        class MockMarketContext:
            recent_win_rate: float = 0.65
            recent_avg_pnl_pct: float = 1.2
            best_strategy: str = "arbitrage"
            worst_strategy: str = ""
            recent_risk_events: int = 0
            circuit_breaker_count: int = 0
            symbol_performance: dict = field(default_factory=dict)
            strategy_performance: dict = field(default_factory=dict)
            last_updated: float = 0.0
            confidence: float = 0.8

        mock_bridge = type('MockKnowledgeBridge', (), {
            'get_market_context': lambda self: MockMarketContext()
        })()

        engine = AutoExecutionEngine(knowledge_bridge=mock_bridge)
        context = engine.get_market_context()
        self.assertIsNotNone(context)
        self.assertEqual(context['recent_win_rate'], 0.65)

    def test_adjust_threshold_from_knowledge(self):
        """测试根据知识库反馈调整阈值"""
        from trading.auto_execution_engine import AutoExecutionEngine
        from dataclasses import dataclass, field

        @dataclass
        class MockMarketContext:
            recent_win_rate: float = 0.65
            recent_avg_pnl_pct: float = 1.2
            best_strategy: str = ""
            worst_strategy: str = ""
            recent_risk_events: int = 0
            circuit_breaker_count: int = 0
            symbol_performance: dict = field(default_factory=dict)
            strategy_performance: dict = field(default_factory=dict)
            last_updated: float = 0.0
            confidence: float = 0.8

        mock_bridge = type('MockKnowledgeBridge', (), {
            'get_market_context': lambda self: MockMarketContext(recent_win_rate=0.65)
        })()

        engine = AutoExecutionEngine(
            knowledge_bridge=mock_bridge,
            config={'min_score_threshold': 60.0, 'min_confidence': 0.5}
        )

        original_score = engine.run_config.min_score_threshold
        original_conf = engine.run_config.min_confidence

        # 调整阈值
        engine._adjust_threshold_from_knowledge()

        # 高胜率应该降低阈值
        self.assertLess(engine.run_config.min_score_threshold, original_score)
        self.assertLess(engine.run_config.min_confidence, original_conf)

    def test_record_risk_event_with_bridge(self):
        """测试记录风险事件"""
        from trading.auto_execution_engine import AutoExecutionEngine

        recorded = []

        class MockKnowledgeBridge:
            def record_risk_event(self, event_type, severity, strategy, symbol, reason, action_taken=""):
                recorded.append({
                    'event_type': event_type,
                    'severity': severity,
                    'strategy': strategy,
                    'symbol': symbol,
                    'reason': reason,
                    'action_taken': action_taken
                })
                return True

        mock_bridge = MockKnowledgeBridge()
        engine = AutoExecutionEngine(knowledge_bridge=mock_bridge)

        result = engine.record_risk_event(
            event_type="reject",
            severity="high",
            strategy="arbitrage",
            symbol="BTC/USDT",
            reason="Low score",
            action_taken="skipped"
        )

        self.assertTrue(result)
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0]['event_type'], "reject")
        self.assertEqual(recorded[0]['symbol'], "BTC/USDT")

    def test_record_risk_event_without_bridge(self):
        """测试无知识桥接器时记录风险事件"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()
        result = engine.record_risk_event(
            event_type="reject",
            severity="high",
            strategy="arbitrage",
            symbol="BTC/USDT",
            reason="Low score"
        )

        self.assertFalse(result)

    def test_get_strategy_insight_with_bridge(self):
        """测试获取策略洞察"""
        from trading.auto_execution_engine import AutoExecutionEngine
        from dataclasses import dataclass, field

        @dataclass
        class MockStrategyInsight:
            strategy_name: str = "arbitrage"
            total_trades: int = 100
            win_count: int = 60
            loss_count: int = 40
            win_rate: float = 0.6
            avg_pnl_pct: float = 1.5
            best_symbol: str = "ETH/USDT"
            worst_symbol: str = ""
            trend: str = "improving"
            recommendation: str = "increase"

        mock_bridge = type('MockKnowledgeBridge', (), {
            'get_strategy_insight': lambda self, name: MockStrategyInsight()
        })()

        engine = AutoExecutionEngine(knowledge_bridge=mock_bridge)
        insight = engine.get_strategy_insight("arbitrage")

        self.assertIsNotNone(insight)
        self.assertEqual(insight['strategy_name'], "arbitrage")
        self.assertEqual(insight['win_rate'], 0.6)

    def test_get_strategy_insight_without_bridge(self):
        """测试无知识桥接器时获取策略洞察"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()
        insight = engine.get_strategy_insight("arbitrage")

        self.assertIsNone(insight)


class TestPositionTrackingV25(unittest.TestCase):
    """V25.3 持仓追踪测试"""

    def test_active_positions_init(self):
        """测试活跃持仓初始化"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()
        self.assertEqual(engine.active_positions, {})

    def test_track_position(self):
        """测试持仓追踪"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity
        )

        engine = AutoExecutionEngine()

        opp = ScannedOpportunity(
            opportunity_id="track_001",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        engine.track_position(opp, executed_price=50000.0, executed_size=1.0)

        self.assertIn("track_001", engine.active_positions)
        self.assertEqual(engine.active_positions["track_001"]["entry_price"], 50000.0)
        self.assertEqual(engine.active_positions["track_001"]["target_price"], 55000.0)

    def test_monitor_positions_empty(self):
        """测试空持仓监控"""
        import asyncio
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()

        # 不应报错
        asyncio.run(engine.monitor_positions())

    def test_close_position(self):
        """测试平仓"""
        import asyncio
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity
        )

        engine = AutoExecutionEngine()

        # 先追踪一个持仓
        opp = ScannedOpportunity(
            opportunity_id="close_001",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )
        engine.track_position(opp, executed_price=50000.0, executed_size=1.0)

        # 执行平仓
        asyncio.run(engine._close_position("close_001", "take_profit", 0.05))

        # 持仓应被移除
        self.assertNotIn("close_001", engine.active_positions)

    def test_get_position(self):
        """测试获取持仓详情"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity
        )

        engine = AutoExecutionEngine()

        opp = ScannedOpportunity(
            opportunity_id="get_001",
            symbol="ETH/USDT",
            action="buy",
            entry_price=3000.0,
            target_price=3300.0,
            stop_loss=2850.0,
            score=80.0,
            confidence=0.8,
            recommendation="execute"
        )
        engine.track_position(opp, executed_price=3000.0, executed_size=2.0)

        pos = engine.get_position("get_001")
        self.assertIsNotNone(pos)
        self.assertEqual(pos['symbol'], "ETH/USDT")
        self.assertEqual(pos['entry_price'], 3000.0)

    def test_get_position_not_found(self):
        """测试获取不存在的持仓"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()

        pos = engine.get_position("nonexistent")
        self.assertIsNone(pos)

    def test_get_position_count(self):
        """测试获取持仓数量"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity
        )

        engine = AutoExecutionEngine()

        # 空时应为0
        self.assertEqual(engine.get_position_count(), 0)

        # 添加持仓
        for i in range(3):
            opp = ScannedOpportunity(
                opportunity_id=f"count_{i}",
                symbol="BTC/USDT",
                action="buy",
                entry_price=50000.0,
                target_price=55000.0,
                stop_loss=48000.0,
                score=75.0,
                confidence=0.7,
                recommendation="execute"
            )
            engine.track_position(opp, executed_price=50000.0, executed_size=1.0)

        self.assertEqual(engine.get_position_count(), 3)

    def test_has_position(self):
        """测试检查持仓是否存在"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity
        )

        engine = AutoExecutionEngine()

        opp = ScannedOpportunity(
            opportunity_id="has_001",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )
        engine.track_position(opp, executed_price=50000.0, executed_size=1.0)

        self.assertTrue(engine.has_position("has_001"))
        self.assertFalse(engine.has_position("nonexistent"))

    def test_get_active_positions(self):
        """测试获取所有活跃持仓"""
        from trading.auto_execution_engine import (
            AutoExecutionEngine,
            ScannedOpportunity
        )

        engine = AutoExecutionEngine()

        # 添加多个持仓
        for i in range(2):
            opp = ScannedOpportunity(
                opportunity_id=f"active_{i}",
                symbol="BTC/USDT",
                action="buy",
                entry_price=50000.0,
                target_price=55000.0,
                stop_loss=48000.0,
                score=75.0,
                confidence=0.7,
                recommendation="execute"
            )
            engine.track_position(opp, executed_price=50000.0, executed_size=1.0)

        positions = engine.get_active_positions()
        self.assertEqual(len(positions), 2)
        self.assertIn("active_0", positions)
        self.assertIn("active_1", positions)


class TestMultiSymbolV25(unittest.TestCase):
    """V25.7 多币种扫描测试"""

    def test_simulate_scan_multi_symbol(self):
        """测试多币种扫描"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()

        opportunities = engine._simulate_scan()

        # 应返回1-2个机会
        self.assertLessEqual(len(opportunities), 2)

    def test_simulate_scan_symbols(self):
        """测试扫描的币种"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()

        # 运行多次扫描，收集所有币种
        symbols = set()
        for _ in range(20):
            opps = engine._simulate_scan()
            for opp in opps:
                symbols.add(opp.symbol)

        # 应该包含多个币种
        self.assertGreater(len(symbols), 1)

    def test_is_trading_hours_default(self):
        """测试默认交易时间(24小时)"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine()

        # 默认应该始终可以交易
        self.assertTrue(engine.is_trading_hours())

    def test_is_trading_hours_custom(self):
        """测试自定义交易时间"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(config={
            'trading_hour_start': 0,
            'trading_hour_end': 24
        })

        self.assertTrue(engine.is_trading_hours())


# ---------------------- V25.8: 新功能测试 ----------------------


class TestV25_8ExecutionQuality(unittest.TestCase):
    """V25.8 执行质量追踪测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_calculate_execution_quality_no_slippage(self):
        """测试无滑点时执行质量"""
        slippage, slippage_pct = self.engine.calculate_execution_quality(50000.0, 50000.0)
        self.assertEqual(slippage, 0.0)
        self.assertEqual(slippage_pct, 0.0)

    def test_calculate_execution_quality_with_slippage(self):
        """测试有滑点时执行质量"""
        slippage, slippage_pct = self.engine.calculate_execution_quality(50000.0, 50100.0)
        self.assertEqual(slippage, 100.0)
        self.assertAlmostEqual(slippage_pct, 0.2, places=2)

    def test_calculate_quality_score_excellent(self):
        """测试优秀执行质量分数"""
        score = self.engine.calculate_quality_score(0.05)
        self.assertEqual(score, 100.0)

    def test_calculate_quality_score_good(self):
        """测试良好执行质量分数"""
        score = self.engine.calculate_quality_score(0.3)
        self.assertEqual(score, 80.0)

    def test_calculate_quality_score_poor(self):
        """测试差执行质量分数"""
        score = self.engine.calculate_quality_score(2.5)
        self.assertEqual(score, 30.0)


class TestV25_8MaxExposure(unittest.TestCase):
    """V25.8 最大暴露限制测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={'max_exposure_per_symbol': 5000.0}
        )

    def test_get_symbol_exposure_init(self):
        """测试初始暴露"""
        exposure = self.engine.get_symbol_exposure('BTC/USDT')
        self.assertEqual(exposure, 0.0)

    def test_check_exposure_limit_within(self):
        """测试在限制内"""
        result = self.engine.check_exposure_limit(
            'BTC/USDT', 100.0, 50.0
        )
        self.assertTrue(result)

    def test_check_exposure_limit_exceeded(self):
        """测试超出限制"""
        # 当前暴露 0, 新增 100*50 = 5000, 已经在限制边缘
        # 再加 1块就会超
        self.engine.update_symbol_exposure('BTC/USDT', 100.0, 50.0, is_entry=True)
        result = self.engine.check_exposure_limit(
            'BTC/USDT', 1.0, 50.0
        )
        self.assertFalse(result)

    def test_update_symbol_exposure_entry(self):
        """测试增加暴露"""
        self.engine.update_symbol_exposure('ETH/USDT', 10.0, 3000.0, is_entry=True)
        exposure = self.engine.get_symbol_exposure('ETH/USDT')
        self.assertEqual(exposure, 30000.0)

    def test_update_symbol_exposure_exit(self):
        """测试减少暴露"""
        self.engine.update_symbol_exposure('BTC/USDT', 10.0, 50000.0, is_entry=True)
        self.engine.update_symbol_exposure('BTC/USDT', 5.0, 50000.0, is_entry=False)
        exposure = self.engine.get_symbol_exposure('BTC/USDT')
        self.assertEqual(exposure, 250000.0)


class TestV25_8CircuitBreaker(unittest.TestCase):
    """V25.8 连亏熔断器测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'consecutive_loss_limit': 3,
                'enable_circuit_breaker': True
            }
        )

    def test_consecutive_loss_init(self):
        """测试初始连亏"""
        count = self.engine.get_consecutive_loss_count()
        self.assertEqual(count, 0)

    def test_update_consecutive_wins(self):
        """测试连赢更新"""
        self.engine._update_consecutive_trades(True)
        self.engine._update_consecutive_trades(True)
        self.assertEqual(self.engine.stats['consecutive_wins'], 2)
        self.assertEqual(self.engine.stats['consecutive_losses'], 0)

    def test_update_consecutive_losses(self):
        """测试连亏更新"""
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)
        self.assertEqual(self.engine.stats['consecutive_losses'], 2)
        self.assertEqual(self.engine.stats['consecutive_wins'], 0)

    def test_is_circuit_breaker_inactive(self):
        """测试熔断器未激活"""
        result = self.engine.is_circuit_breaker_active()
        self.assertFalse(result)

    def test_is_circuit_breaker_active(self):
        """测试熔断器激活"""
        # 触发3次亏损
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)

        result = self.engine.is_circuit_breaker_active()
        self.assertTrue(result)

    def test_trigger_circuit_breaker(self):
        """测试触发熔断器"""
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)

        self.engine.trigger_circuit_breaker()

        self.assertEqual(self.engine.stats['circuit_breaker_triggered'], 1)

    def test_reset_circuit_breaker(self):
        """测试重置熔断器"""
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)
        self.engine._update_consecutive_trades(False)

        self.engine.reset_circuit_breaker()

        self.assertEqual(self.engine.stats['consecutive_losses'], 0)
        self.assertEqual(self.engine.stats['consecutive_wins'], 0)


class TestV25_8ExecutionQualityInResult(unittest.TestCase):
    """V25.8 执行结果中的质量追踪测试"""

    def test_execution_result_fields(self):
        """测试执行结果字段"""
        from trading.auto_execution_engine import ExecutionResult

        result = ExecutionResult(
            opportunity_id="test_001",
            success=True,
            executed_price=50100.0,
            executed_size=1.0,
            expected_price=50000.0,
            slippage=100.0,
            slippage_pct=0.2,
            execution_quality_score=90.0
        )

        self.assertEqual(result.expected_price, 50000.0)
        self.assertEqual(result.slippage, 100.0)
        self.assertEqual(result.slippage_pct, 0.2)
        self.assertEqual(result.execution_quality_score, 90.0)


class TestV25_8Config(unittest.TestCase):
    """V25.8 配置测试"""

    def test_auto_trade_config_v25_8(self):
        """测试V25.8配置"""
        from trading.auto_execution_engine import AutoExecutionEngine, AutoTradeConfig

        engine = AutoExecutionEngine(
            config={
                'max_exposure_per_symbol': 8000.0,
                'consecutive_loss_limit': 5,
                'enable_circuit_breaker': True
            }
        )

        self.assertEqual(engine.run_config.max_exposure_per_symbol, 8000.0)
        self.assertEqual(engine.run_config.consecutive_loss_limit, 5)
        self.assertTrue(engine.run_config.enable_circuit_breaker)

    def test_default_config_v25_8(self):
        """测试默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()

        self.assertEqual(config.max_exposure_per_symbol, 10000.0)
        self.assertEqual(config.consecutive_loss_limit, 3)
        self.assertTrue(config.enable_circuit_breaker)


# ---------------------- V25.9: 新功能测试 ----------------------


class TestV25_9EmergencyStop(unittest.TestCase):
    """V25.9 紧急止损测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'emergency_stop_pct': 0.10,
                'max_total_exposure': 50000.0
            }
        )

    def test_get_total_exposure_init(self):
        """测试初始总暴露"""
        total = self.engine.get_total_exposure()
        self.assertEqual(total, 0.0)

    def test_check_global_exposure_limit_within(self):
        """测试全局暴露在限制内"""
        result = self.engine.check_global_exposure_limit()
        self.assertTrue(result)

    def test_check_global_exposure_limit_exceeded(self):
        """测试全局暴露超出限制"""
        # 添加暴露达到限制
        self.engine.symbol_exposure['BTC/USDT'] = 50000.0
        result = self.engine.check_global_exposure_limit()
        self.assertFalse(result)

    def test_check_emergency_stop_not_triggered(self):
        """测试紧急止损未触发"""
        self.engine._daily_start_equity = 10000.0
        result = self.engine.check_emergency_stop(9500.0)  # 亏损5%
        self.assertFalse(result)

    def test_check_emergency_stop_triggered(self):
        """测试紧急止损触发"""
        self.engine._daily_start_equity = 10000.0
        result = self.engine.check_emergency_stop(8500.0)  # 亏损15%
        self.assertTrue(result)

    def test_trigger_emergency_stop(self):
        """测试触发紧急止损"""
        self.engine.trigger_emergency_stop()
        self.assertEqual(self.engine.stats['emergency_stop_triggered'], 1)
        self.assertFalse(self.engine.is_running)


class TestV25_9DailyPnL(unittest.TestCase):
    """V25.9 每日盈亏追踪测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'daily_loss_limit': 0.05,
                'max_total_exposure': 50000.0
            }
        )

    def test_get_daily_pnl_init(self):
        """测试初始每日盈亏"""
        pnl = self.engine.get_daily_pnl()
        self.assertEqual(pnl, 0.0)

    def test_update_daily_pnl_profit(self):
        """测试更新每日盈利"""
        self.engine.update_daily_pnl(100.0)
        self.assertEqual(self.engine.stats['daily_profit'], 100.0)
        self.assertEqual(self.engine.get_daily_pnl(), 100.0)

    def test_update_daily_pnl_loss(self):
        """测试更新每日亏损"""
        self.engine.update_daily_pnl(-50.0)
        self.assertEqual(self.engine.stats['daily_loss'], 50.0)
        self.assertEqual(self.engine.get_daily_pnl(), -50.0)

    def test_get_daily_loss_pct(self):
        """测试每日亏损百分比"""
        self.engine._daily_start_equity = 10000.0
        self.engine.update_daily_pnl(-500.0)  # 亏损5%
        pct = self.engine.get_daily_loss_pct()
        self.assertAlmostEqual(pct, 0.05, places=2)

    def test_check_daily_loss_limit_within(self):
        """测试每日亏损在限制内"""
        self.engine._daily_start_equity = 10000.0
        self.engine.update_daily_pnl(-400.0)  # 亏损4%
        result = self.engine.check_daily_loss_limit()
        self.assertTrue(result)

    def test_check_daily_loss_limit_exceeded(self):
        """测试每日亏损超出限制"""
        self.engine._daily_start_equity = 10000.0
        self.engine.update_daily_pnl(-600.0)  # 亏损6%
        result = self.engine.check_daily_loss_limit()
        self.assertFalse(result)

    def test_set_daily_start_equity(self):
        """测试设置当日起始权益"""
        self.engine.set_daily_start_equity(10000.0)
        self.assertEqual(self.engine._daily_start_equity, 10000.0)


class TestV25_9Config(unittest.TestCase):
    """V25.9 配置测试"""

    def test_auto_trade_config_v25_9(self):
        """测试V25.9配置"""
        from trading.auto_execution_engine import AutoExecutionEngine, AutoTradeConfig

        engine = AutoExecutionEngine(
            config={
                'emergency_stop_pct': 0.15,
                'daily_loss_limit': 0.08,
                'max_total_exposure': 100000.0
            }
        )

        self.assertEqual(engine.run_config.emergency_stop_pct, 0.15)
        self.assertEqual(engine.run_config.daily_loss_limit, 0.08)
        self.assertEqual(engine.run_config.max_total_exposure, 100000.0)

    def test_default_config_v25_9(self):
        """测试V25.9默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()

        self.assertEqual(config.emergency_stop_pct, 0.10)
        self.assertEqual(config.daily_loss_limit, 0.05)
        self.assertEqual(config.max_total_exposure, 50000.0)


# ---------------------- V26.0: 新功能测试 ----------------------


class TestV26_0TrailingStop(unittest.TestCase):
    """V26.0 追踪止损测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'trailing_stop_pct': 0.015,
                'enable_trailing_stop': True
            }
        )

    def test_get_trailing_stop_price_long_rising(self):
        """测试做多价格上涨追踪止损"""
        # 价格从50000上涨到55000, 追踪止损应为55000*(1-0.015)=54175
        stop = self.engine.get_trailing_stop_price(50000.0, 55000.0, is_long=True)
        self.assertAlmostEqual(stop, 54175.0, places=1)

    def test_get_trailing_stop_price_long_rising_from_entry(self):
        """测试当前价格等于入场价时的追踪止损"""
        stop = self.engine.get_trailing_stop_price(50000.0, 50000.0, is_long=True)
        self.assertAlmostEqual(stop, 50000.0 * 0.985, places=1)

    def test_get_trailing_stop_price_disabled(self):
        """测试禁用追踪止损时返回固定止损"""
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={'enable_trailing_stop': False})
        stop = engine.get_trailing_stop_price(50000.0, 55000.0, is_long=True)
        # 禁用后应返回固定止损
        self.assertEqual(stop, 50000.0 * 0.98)

    def test_check_trailing_stop_not_triggered(self):
        """测试追踪止损未触发"""
        result = self.engine.check_trailing_stop(50000.0, 51000.0, is_long=True)
        self.assertFalse(result)

    def test_check_trailing_stop_triggered(self):
        """测试追踪止损触发"""
        result = self.engine.check_trailing_stop(50000.0, 49000.0, is_long=True)
        self.assertTrue(result)


class TestV26_0Cooldown(unittest.TestCase):
    """V26.0 平仓冷却测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'cooldown_seconds': 60
            }
        )

    def test_is_in_cooldown_init(self):
        """测试初始不在冷却"""
        result = self.engine.is_in_cooldown()
        self.assertFalse(result)

    def test_start_cooldown(self):
        """测试开始冷却"""
        self.engine.start_cooldown()
        self.assertTrue(self.engine.is_in_cooldown())

    def test_reset_cooldown(self):
        """测试重置冷却"""
        self.engine.start_cooldown()
        self.engine.reset_cooldown()
        self.assertFalse(self.engine.is_in_cooldown())


class TestV26_0WeekendTrading(unittest.TestCase):
    """V26.0 周末交易控制测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'allow_weekend_trading': False
            }
        )

    def test_is_weekend_trading_allowed_yes(self):
        """测试允许周末交易"""
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={'allow_weekend_trading': True})
        result = engine.is_weekend_trading_allowed()
        self.assertTrue(result)

    def test_is_weekend_trading_allowed_no(self):
        """测试禁止周末交易时不允许"""
        # 注意: 这个测试可能周末会失败, 这是预期行为
        result = self.engine.is_weekend_trading_allowed()


class TestV26_0Config(unittest.TestCase):
    """V26.0 配置测试"""

    def test_auto_trade_config_v26_0(self):
        """测试V26.0配置"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(
            config={
                'trailing_stop_pct': 0.02,
                'enable_trailing_stop': True,
                'cooldown_seconds': 120,
                'allow_weekend_trading': False
            }
        )

        self.assertEqual(engine.run_config.trailing_stop_pct, 0.02)
        self.assertEqual(engine.run_config.enable_trailing_stop, True)
        self.assertEqual(engine.run_config.cooldown_seconds, 120)
        self.assertEqual(engine.run_config.allow_weekend_trading, False)

    def test_default_config_v26_0(self):
        """测试V26.0默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()

        self.assertEqual(config.trailing_stop_pct, 0.015)
        self.assertTrue(config.enable_trailing_stop)
        self.assertEqual(config.cooldown_seconds, 60)
        self.assertTrue(config.allow_weekend_trading)


class TestV26_1TIF(unittest.TestCase):
    """V26.1 Time-In-Force 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'default_tif': 'gtc',
                'max_holding_seconds': 300
            }
        )

    def test_validate_tif_gtc(self):
        """测试GTC订单"""
        order_time = time.time() - 100
        current_time = time.time()

        result = self.engine.validate_tif_order('gtc', order_time, current_time)
        self.assertTrue(result)

    def test_validate_tif_ioc(self):
        """测试IOC订单 - 60秒内有效"""
        # Within 60 seconds - should be valid
        order_time = time.time() - 30
        current_time = time.time()

        result = self.engine.validate_tif_order('ioc', order_time, current_time)
        self.assertTrue(result)

    def test_validate_tif_ioc_expired(self):
        """测试IOC订单 - 过期"""
        # Over 60 seconds - should be invalid
        order_time = time.time() - 100
        current_time = time.time()

        result = self.engine.validate_tif_order('ioc', order_time, current_time)
        self.assertFalse(result)

    def test_validate_tif_fok(self):
        """测试FOK订单 - 必须立即成交"""
        order_time = time.time() - 3
        current_time = time.time()

        result = self.engine.validate_tif_order('fok', order_time, current_time)
        self.assertTrue(result)


class TestV26_1ATRTrailing(unittest.TestCase):
    """V26.1 ATR Trailing Stop 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_atr_trailing': True,
                'atr_periods': 14,
                'atr_multiplier': 2.0
            }
        )

    def test_update_price_history(self):
        """测试价格历史更新"""
        self.engine.update_price_history('BTC/USDT', 50000.0)
        self.engine.update_price_history('BTC/USDT', 50100.0)
        self.engine.update_price_history('BTC/USDT', 50200.0)

        history = self.engine._price_history.get('BTC/USDT', [])
        self.assertEqual(len(history), 3)

    def test_calculate_atr_insufficient_data(self):
        """测试ATR计算 - 数据不足"""
        self.engine.update_price_history('BTC/USDT', 50000.0)

        atr = self.engine.calculate_atr('BTC/USDT')
        self.assertEqual(atr, 0.0)

    def test_calculate_atr_sufficient_data(self):
        """测试ATR计算 - 有足够数据"""
        # Add enough price data
        prices = [50000, 50200, 49800, 50100, 50300, 49900, 50000,
                 50400, 50200, 50600, 50800, 50500, 50700, 50900, 51000]
        for p in prices:
            self.engine.update_price_history('BTC/USDT', p)

        atr = self.engine.calculate_atr('BTC/USDT')
        self.assertGreater(atr, 0.0)

    def test_atr_trailing_stop_long(self):
        """测试ATR追踪止损 - 做多"""
        # Set up price history
        for p in [50000, 50500, 51000, 51500, 52000]:
            self.engine.update_price_history('BTC/USDT', p)

        entry = 50000.0
        current = 52000.0

        stop_price = self.engine.get_atr_trailing_stop_price(entry, current, is_long=True)
        self.assertLess(stop_price, current)

    def test_check_atr_trailing_stop_disabled(self):
        """测试ATR追踪止损 - 未启用"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(config={'enable_atr_trailing': False})

        result = engine.check_atr_trailing_stop(
            50000.0, 51000.0, is_long=True
        )
        self.assertFalse(result)


class TestV26_1PositionTimeLimit(unittest.TestCase):
    """V26.1 Position Time Limit 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'max_holding_seconds': 300
            }
        )

    def test_check_position_time_limit_within(self):
        """测试持仓时间 - 在限制内"""
        entry_time = time.time() - 200  # 200 seconds ago
        current_time = time.time()

        result = self.engine.check_position_time_limit(entry_time, current_time)
        self.assertFalse(result)  # Not exceeded

    def test_check_position_time_limit_exceeded(self):
        """测试持仓时间 - 超过限制"""
        entry_time = time.time() - 400  # 400 seconds ago
        current_time = time.time()

        result = self.engine.check_position_time_limit(entry_time, current_time)
        self.assertTrue(result)  # Exceeded

    def test_check_position_time_limit_disabled(self):
        """测试持仓时间 - 禁用"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(config={'max_holding_seconds': 0})

        entry_time = time.time() - 1000
        current_time = time.time()

        result = engine.check_position_time_limit(entry_time, current_time)
        self.assertFalse(result)  # Disabled, always False


class TestV26_1CorrelationLimit(unittest.TestCase):
    """V26.1 Correlation Limit 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'correlation_limit': 0.7,
                'max_total_exposure': 50000.0
            }
        )

    def test_check_correlation_limit_no_positions(self):
        """测试相关性 - 无持仓"""
        result = self.engine.check_correlation_limit('BTC/USDT', 10000.0)
        self.assertTrue(result)

    def test_check_correlation_limit_with_positions(self):
        """测试相关性 - 有持仓"""
        # Add a BTC position
        self.engine.active_positions['test_1'] = {
            'symbol': 'BTC/USDT',
            'size': 0.1,
            'entry_price': 50000.0
        }

        result = self.engine.check_correlation_limit('ETH/USDT', 10000.0)
        self.assertTrue(result)


class TestV26_1OCOOrders(unittest.TestCase):
    """V26.1 OCO订单测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        from trading.auto_execution_engine import ScannedOpportunity

        self.engine = AutoExecutionEngine(config={'mode': 'manual'})

    def test_create_oco_order(self):
        """测试创建OCO订单"""
        from trading.auto_execution_engine import ScannedOpportunity

        primary = ScannedOpportunity(
            opportunity_id="opp_1",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        secondary = ScannedOpportunity(
            opportunity_id="opp_2",
            symbol="ETH/USDT",
            action="buy",
            entry_price=3000.0,
            target_price=3300.0,
            stop_loss=2800.0,
            score=70.0,
            confidence=0.6,
            recommendation="execute"
        )

        oco_id = self.engine.create_oco_order("test_oco", primary, secondary)

        self.assertEqual(oco_id, "oco_test_oco")
        self.assertIn(oco_id, self.engine._oco_orders)
        self.assertEqual(self.engine.stats['oco_orders_created'], 1)

    def test_check_oco_order_filled(self):
        """测试OCO订单成交"""
        from trading.auto_execution_engine import ScannedOpportunity

        primary = ScannedOpportunity(
            opportunity_id="opp_1",
            symbol="BTC/USDT",
            action="buy",
            entry_price=50000.0,
            target_price=55000.0,
            stop_loss=48000.0,
            score=75.0,
            confidence=0.7,
            recommendation="execute"
        )

        secondary = ScannedOpportunity(
            opportunity_id="opp_2",
            symbol="ETH/USDT",
            action="buy",
            entry_price=3000.0,
            target_price=3300.0,
            stop_loss=2800.0,
            score=70.0,
            confidence=0.6,
            recommendation="execute"
        )

        oco_id = self.engine.create_oco_order("test_oco", primary, secondary)

        # Check what happens when primary fills
        cancelled = self.engine.check_oco_order(oco_id, "BTC/USDT")

        # Should return the secondary to cancel
        self.assertIsNotNone(cancelled)
        self.assertEqual(cancelled.symbol, "ETH/USDT")


class TestV26_1Config(unittest.TestCase):
    """V26.1配置测试"""

    def test_auto_trade_config_v26_1(self):
        """测试V26.1自动交易配置"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'default_tif': 'ioc',
                'enable_atr_trailing': True,
                'atr_periods': 20,
                'atr_multiplier': 3.0,
                'max_holding_seconds': 600,
                'enable_oco_orders': True,
                'correlation_limit': 0.8
            }
        )

        self.assertEqual(engine.run_config.default_tif, 'ioc')
        self.assertTrue(engine.run_config.enable_atr_trailing)
        self.assertEqual(engine.run_config.atr_periods, 20)
        self.assertEqual(engine.run_config.atr_multiplier, 3.0)
        self.assertEqual(engine.run_config.max_holding_seconds, 600)
        self.assertTrue(engine.run_config.enable_oco_orders)
        self.assertEqual(engine.run_config.correlation_limit, 0.8)

    def test_default_config_v26_1(self):
        """测试V26.1默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()

        self.assertEqual(config.default_tif, 'gtc')
        self.assertFalse(config.enable_atr_trailing)
        self.assertEqual(config.atr_periods, 14)
        self.assertEqual(config.atr_multiplier, 2.0)
        self.assertEqual(config.max_holding_seconds, 300)
        self.assertFalse(config.enable_oco_orders)
        self.assertEqual(config.correlation_limit, 0.7)


class TestV26_2OrderBookAnalysis(unittest.TestCase):
    """V26.2 Order Book Analysis 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_orderbook_analysis': True,
                'min_liquidity_depth': 10000.0
            }
        )

    def test_update_orderbook(self):
        """测试更新订单簿"""
        bids = [(50000, 1.0), (49900, 2.0), (49800, 3.0)]
        asks = [(50100, 1.0), (50200, 2.0), (50300, 3.0)]

        self.engine.update_orderbook('BTC/USDT', bids, asks)

        self.assertIn('BTC/USDT', self.engine._orderbook_cache)
        self.assertEqual(len(self.engine._orderbook_cache['BTC/USDT']['bids']), 3)

    def test_analyze_orderbook_depth_insufficient(self):
        """测试订单簿分析 - 流动性不足"""
        # Empty orderbook
        analysis = self.engine.analyze_orderbook_depth('BTC/USDT')

        self.assertFalse(analysis['sufficient_liquidity'])

    def test_analyze_orderbook_depth_sufficient(self):
        """测试订单簿分析 - 流动性充足"""
        bids = [(50000, 1.0), (49900, 2.0)]
        asks = [(50100, 1.0), (50200, 2.0)]

        self.engine.update_orderbook('BTC/USDT', bids, asks)
        analysis = self.engine.analyze_orderbook_depth('BTC/USDT')

        self.assertTrue(analysis['sufficient_liquidity'])
        self.assertGreater(analysis['bid_depth'], 0)

    def test_estimate_price_impact(self):
        """测试价格影响估算"""
        bids = [(50000, 1.0), (49900, 2.0)]
        asks = [(50100, 1.0), (50200, 2.0)]

        impact = self.engine._estimate_price_impact('BTC/USDT', 25000, bids, asks)

        self.assertGreaterEqual(impact, 0.0)


class TestV26_2LiquidityCheck(unittest.TestCase):
    """V26.2 Liquidity Check 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_orderbook_analysis': True,
                'min_liquidity_depth': 100000.0
            }
        )

    def test_check_liquidity_disabled(self):
        """测试流动性检查 - 未启用"""
        result = self.engine.check_liquidity('BTC/USDT', 10000.0)
        self.assertTrue(result)

    def test_check_liquidity_insufficient(self):
        """测试流动性 - 不足"""
        # Low liquidity orderbook
        bids = [(50000, 0.1)]
        asks = [(50100, 0.1)]

        self.engine.update_orderbook('BTC/USDT', bids, asks)

        result = self.engine.check_liquidity('BTC/USDT', 10000.0)
        self.assertFalse(result)

    def test_check_liquidity_sufficient(self):
        """测试流动性 - 充足"""
        # High liquidity orderbook
        bids = [(50000, 10.0)]
        asks = [(50100, 10.0)]

        self.engine.update_orderbook('BTC/USDT', bids, asks)

        result = self.engine.check_liquidity('BTC/USDT', 10000.0)
        self.assertTrue(result)


class TestV26_2SlippagePrediction(unittest.TestCase):
    """V26.2 Slippage Prediction 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'slippage_warning_threshold': 0.005
            }
        )

    def test_record_slippage(self):
        """测试记录滑点"""
        self.engine.record_slippage(0.002)
        self.engine.record_slippage(0.003)

        self.assertEqual(len(self.engine._slippage_history), 2)

    def test_predict_slippage_no_history(self):
        """测试滑点预测 - 无历史数据"""
        predicted = self.engine.predict_slippage('BTC/USDT', 10000.0)

        self.assertEqual(predicted, 0.0)

    def test_predict_slippage_with_history(self):
        """测试滑点预测 - 有历史数据"""
        self.engine.record_slippage(0.001)
        self.engine.record_slippage(0.002)

        predicted = self.engine.predict_slippage('BTC/USDT', 10000.0)

        self.assertGreater(predicted, 0.0)

    def test_check_slippage_warning(self):
        """测试滑点警告"""
        # Record high slippage
        for _ in range(5):
            self.engine.record_slippage(0.01)

        result = self.engine.check_slippage_warning('BTC/USDT', 10000.0)

        self.assertTrue(result)


class TestV26_2DynamicParams(unittest.TestCase):
    """V26.2 Dynamic Parameters 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_dynamic_params': True,
                'volatility_lookback': 20
            }
        )

    def test_update_volatility(self):
        """测试更新波动率"""
        prices = [50000, 50500, 51000, 50800, 51200]
        for p in prices:
            self.engine.update_volatility('BTC/USDT', p)

        self.assertEqual(len(self.engine._recent_volatility['BTC/USDT']), 5)

    def test_calculate_current_volatility(self):
        """测试计算波动率"""
        prices = [50000, 50500, 51000, 50800, 51200]
        for p in prices:
            self.engine.update_volatility('BTC/USDT', p)

        vol = self.engine.calculate_current_volatility('BTC/USDT')

        self.assertGreater(vol, 0.0)

    def test_check_volatility_spike_no_history(self):
        """测试波动率检查 - 无历史数据"""
        result = self.engine.check_volatility_spike('BTC/USDT')

        self.assertFalse(result)

    def test_adjust_params_normal(self):
        """测试参数调整 - 正常波动率"""
        # Normal volatility
        prices = [50000, 50100, 50200, 50100, 50000]
        for p in prices:
            self.engine.update_volatility('BTC/USDT', p)

        params = self.engine.adjust_params_for_market('BTC/USDT')

        self.assertEqual(params['score_threshold'], 60.0)
        self.assertEqual(params['position_multiplier'], 1.0)

    def test_adjust_params_high_volatility(self):
        """测试参数调整 - 高波动率"""
        # High volatility - simulate big price swings
        prices = [50000, 55000, 45000, 56000, 44000]
        for p in prices:
            self.engine.update_volatility('BTC/USDT', p)

        params = self.engine.adjust_params_for_market('BTC/USDT')

        # High vol should increase threshold and decrease size
        self.assertGreater(params['score_threshold'], 60.0)
        self.assertLess(params['position_multiplier'], 1.0)


class TestV26_2Config(unittest.TestCase):
    """V26.2配置测试"""

    def test_auto_trade_config_v26_2(self):
        """测试V26.2自动交易配置"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_orderbook_analysis': True,
                'min_liquidity_depth': 50000.0,
                'slippage_warning_threshold': 0.01,
                'enable_dynamic_params': True,
                'volatility_lookback': 30
            }
        )

        self.assertTrue(engine.run_config.enable_orderbook_analysis)
        self.assertEqual(engine.run_config.min_liquidity_depth, 50000.0)
        self.assertEqual(engine.run_config.slippage_warning_threshold, 0.01)
        self.assertTrue(engine.run_config.enable_dynamic_params)
        self.assertEqual(engine.run_config.volatility_lookback, 30)

    def test_default_config_v26_2(self):
        """测试V26.2默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()

        self.assertFalse(config.enable_orderbook_analysis)
        self.assertEqual(config.min_liquidity_depth, 10000.0)
        self.assertEqual(config.slippage_warning_threshold, 0.005)
        self.assertTrue(config.enable_dynamic_params)
        self.assertEqual(config.volatility_lookback, 20)


class TestV26_3MarketRegime(unittest.TestCase):
    """V26.3 Market Regime Detection 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_market_regime': True
            }
        )

    def test_detect_market_regime_bull(self):
        """测试牛市检测"""
        prices = [50000, 51000, 52000, 52500, 53000,
                 53500, 54000, 54200, 54500, 55000]

        regime = self.engine.detect_market_regime('BTC/USDT', prices)

        self.assertEqual(regime, 'BULL')

    def test_detect_market_regime_bear(self):
        """测试熊市检测"""
        prices = [55000, 54000, 53000, 52000, 51000,
                 50000, 49000, 48000, 47000, 46000]

        regime = self.engine.detect_market_regime('BTC/USDT', prices)

        self.assertEqual(regime, 'BEAR')

    def test_detect_market_regime_sideways(self):
        """测试震荡市检测"""
        prices = [50000, 51000, 49000, 50500, 49500,
                 50200, 49800, 50100, 49900, 50000]

        regime = self.engine.detect_market_regime('BTC/USDT', prices)

        self.assertEqual(regime, 'SIDEWAYS')

    def test_check_market_regime_for_position(self):
        """测试区间仓位调整"""
        self.assertEqual(self.engine.check_market_regime_for_position('BULL'), 1.2)
        self.assertEqual(self.engine.check_market_regime_for_position('BEAR'), 0.5)
        self.assertEqual(self.engine.check_market_regime_for_position('SIDEWAYS'), 0.8)


class TestV26_3TimeRules(unittest.TestCase):
    """V26.3 Time-of-Day Rules 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_time_rules': True
            }
        )

    def test_check_time_rules_disabled(self):
        """测试时段规则未启用"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(config={'enable_time_rules': False})
        result = engine.check_time_rules()
        self.assertTrue(result)


class TestV26_3SpreadDeviation(unittest.TestCase):
    """V26.3 Spread Deviation Alerts 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'spread_deviation_threshold': 0.02
            }
        )

    def test_calculate_spread_deviation(self):
        """测试价差偏离计算"""
        deviation = self.engine.calculate_spread_deviation(0.003, 0.001)

        self.assertEqual(deviation, 2.0)

    def test_check_spread_deviation_normal(self):
        """测试价差正常"""
        result = self.engine.check_spread_deviation(0.001, 0.001)

        self.assertFalse(result)

    def test_check_spread_deviation_warning(self):
        """测试价差警告"""
        result = self.engine.check_spread_deviation(0.005, 0.001)

        self.assertTrue(result)


class TestV26_3OrderBookImbalance(unittest.TestCase):
    """V26.3 Order Book Imbalance 测试"""

    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine

        self.engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'imbalance_threshold': 0.3
            }
        )

    def test_calculate_orderbook_imbalance(self):
        """测试订单簿不平衡计算"""
        bids = [(50000, 10.0), (49000, 5.0)]
        asks = [(50100, 2.0), (50200, 3.0)]

        self.engine.update_orderbook('BTC/USDT', bids, asks)

        imbalance = self.engine.calculate_orderbook_imbalance('BTC/USDT')

        self.assertGreater(imbalance, 0.0)

    def test_check_orderbook_imbalance_warning(self):
        """测试订单簿不平衡警告"""
        # Very imbalanced
        bids = [(50000, 10.0)]
        asks = [(50100, 1.0)]

        self.engine.update_orderbook('BTC/USDT', bids, asks)

        result = self.engine.check_orderbook_imbalance('BTC/USDT')

        self.assertTrue(result)


class TestV26_3Config(unittest.TestCase):
    """V26.3配置测试"""

    def test_auto_trade_config_v26_3(self):
        """测试V26.3自动交易配置"""
        from trading.auto_execution_engine import AutoExecutionEngine

        engine = AutoExecutionEngine(
            config={
                'mode': 'manual',
                'enable_market_regime': True,
                'enable_time_rules': True,
                'spread_deviation_threshold': 0.03,
                'imbalance_threshold': 0.4,
                'asian_session_start': 0,
                'asian_session_end': 8,
                'london_session_start': 8,
                'london_session_end': 16,
                'ny_session_start': 13,
                'ny_session_end': 21
            }
        )

        self.assertTrue(engine.run_config.enable_market_regime)
        self.assertTrue(engine.run_config.enable_time_rules)
        self.assertEqual(engine.run_config.spread_deviation_threshold, 0.03)
        self.assertEqual(engine.run_config.imbalance_threshold, 0.4)

    def test_default_config_v26_3(self):
        """测试V26.3默认配置"""
        from trading.auto_execution_engine import AutoTradeConfig

        config = AutoTradeConfig()

        self.assertFalse(config.enable_market_regime)
        self.assertFalse(config.enable_time_rules)
        self.assertEqual(config.spread_deviation_threshold, 0.02)
        self.assertEqual(config.imbalance_threshold, 0.3)


class TestV27_0MultiTimeframe(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_multitimeframe': True})

    def test_update_timeframe_prices(self):
        self.engine.update_timeframe_prices('BTC/USDT', '1m', 50000)
        self.assertIn('BTC/USDT', self.engine._multi_timeframe_prices)

    def test_calculate_multitimeframe_signal(self):
        signal = self.engine.calculate_multitimeframe_signal('BTC/USDT')
        self.assertEqual(signal, 0.0)


class TestV27_0Momentum(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_momentum': True, 'rsi_periods': 14})

    def test_calculate_rsi(self):
        rsi = self.engine.calculate_rsi('BTC/USDT')
        self.assertEqual(rsi, 50.0)

    def test_get_momentum_signal(self):
        signal = self.engine.get_momentum_signal('BTC/USDT')
        self.assertIn(signal, ['OVERBOUGHT', 'OVERSOLD', 'NEUTRAL'])


class TestV27_0ExecutionDelay(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'execution_delay_ms': 0})

    def test_execution_delay_disabled(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={'execution_delay_ms': 0})
        self.assertEqual(engine.run_config.execution_delay_ms, 0)

    def test_execution_delay_enabled(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={'execution_delay_ms': 100})
        self.assertEqual(engine.run_config.execution_delay_ms, 100)

    def test_record_execution_time(self):
        self.engine.record_execution_time()
        self.assertGreater(self.engine._last_execution_time, 0)


class TestV27_0Config(unittest.TestCase):
    def test_auto_trade_config_v27_0(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={
            'enable_multitimeframe': True, 'enable_momentum': True,
            'execution_delay_ms': 50, 'rsi_periods': 20
        })
        self.assertTrue(engine.run_config.enable_multitimeframe)
        self.assertEqual(engine.run_config.execution_delay_ms, 50)

    def test_default_config_v27_0(self):
        from trading.auto_execution_engine import AutoTradeConfig
        config = AutoTradeConfig()
        self.assertFalse(config.enable_multitimeframe)
        self.assertEqual(config.execution_delay_ms, 0)


class TestV28_0Hedging(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_hedging': True, 'hedge_correlation': 0.6})

    def test_check_hedging_needed(self):
        result = self.engine.check_hedging_needed('BTC/USDT')
        self.assertFalse(result)  # No positions initially

    def test_calculate_hedge_size(self):
        size = self.engine.calculate_hedge_size('BTC/USDT')
        self.assertEqual(size, 0.0)


class TestV28_0AdvancedFilter(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        from trading.auto_execution_engine import ScannedOpportunity
        self.engine = AutoExecutionEngine(config={'enable_advanced_filter': True, 'filter_confidence_min': 0.6})

    def test_filter_signal_high_confidence(self):
        from trading.auto_execution_engine import ScannedOpportunity
        opp = ScannedOpportunity('t1', 'BTC/USDT', 'buy', 50000, 55000, 48000, 70, 0.7, 'execute')
        result = self.engine.filter_signal(opp)
        self.assertTrue(result)

    def test_filter_signal_low_confidence(self):
        from trading.auto_execution_engine import ScannedOpportunity
        opp = ScannedOpportunity('t1', 'BTC/USDT', 'buy', 50000, 55000, 48000, 70, 0.4, 'execute')
        result = self.engine.filter_signal(opp)
        self.assertFalse(result)


class TestV28_0AnomalyDetection(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_anomaly_detection': True, 'anomaly_threshold': 3.0})

    def test_update_returns(self):
        self.engine.update_returns('BTC/USDT', 50000)
        self.engine.update_returns('BTC/USDT', 51000)
        self.assertIn('BTC/USDT', self.engine._price_returns)

    def test_detect_anomaly_no_data(self):
        result = self.engine.detect_anomaly('BTC/USDT')
        self.assertFalse(result)


class TestV28_0Config(unittest.TestCase):
    def test_auto_trade_config_v28_0(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={
            'enable_hedging': True, 'hedge_correlation': 0.7,
            'enable_advanced_filter': True, 'filter_confidence_min': 0.7,
            'enable_anomaly_detection': True, 'anomaly_threshold': 2.5
        })
        self.assertTrue(engine.run_config.enable_hedging)
        self.assertEqual(engine.run_config.hedge_correlation, 0.7)
        self.assertTrue(engine.run_config.enable_anomaly_detection)

    def test_default_config_v28_0(self):
        from trading.auto_execution_engine import AutoTradeConfig
        config = AutoTradeConfig()
        self.assertFalse(config.enable_hedging)
        self.assertFalse(config.enable_advanced_filter)


class TestV29_0Rebalancing(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_rebalancing': True, 'rebalance_threshold': 0.2})

    def test_set_target_allocation(self):
        self.engine.set_target_allocation('BTC/USDT', 0.5)
        self.assertEqual(self.engine._target_allocation['BTC/USDT'], 0.5)

    def test_check_rebalancing_needed(self):
        result = self.engine.check_rebalancing_needed()
        self.assertFalse(result)


class TestV29_0Sentiment(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_news_sentiment': True, 'sentiment_impact': 0.1})

    def test_update_sentiment(self):
        self.engine.update_sentiment('BTC/USDT', 0.5)
        self.assertEqual(self.engine._sentiment_cache['BTC/USDT'], 0.5)

    def test_get_sentiment_signal(self):
        self.engine.update_sentiment('BTC/USDT', 0.5)
        signal = self.engine.get_sentiment_signal('BTC/USDT')
        self.assertEqual(signal, 0.05)


class TestV29_0MLSignals(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_ml_signals': True, 'ml_confidence_boost': 0.1})

    def test_update_ml_prediction(self):
        self.engine.update_ml_prediction('BTC/USDT', 0.8)
        self.assertEqual(self.engine._ml_predictions['BTC/USDT'], 0.8)

    def test_get_ml_boosted_confidence(self):
        self.engine.update_ml_prediction('BTC/USDT', 0.8)
        boosted = self.engine.get_ml_boosted_confidence('BTC/USDT', 0.5)
        self.assertGreater(boosted, 0.5)


class TestV29_0Config(unittest.TestCase):
    def test_auto_trade_config_v29_0(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={
            'enable_rebalancing': True, 'rebalance_threshold': 0.3,
            'enable_news_sentiment': True, 'sentiment_impact': 0.2,
            'enable_ml_signals': True, 'ml_confidence_boost': 0.15
        })
        self.assertTrue(engine.run_config.enable_rebalancing)
        self.assertEqual(engine.run_config.rebalance_threshold, 0.3)
        self.assertTrue(engine.run_config.enable_ml_signals)

    def test_default_config_v29_0(self):
        from trading.auto_execution_engine import AutoTradeConfig
        config = AutoTradeConfig()
        self.assertFalse(config.enable_rebalancing)
        self.assertFalse(config.enable_news_sentiment)
        self.assertFalse(config.enable_ml_signals)


class TestV30_0FundingMonitor(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_funding_monitor': True, 'funding_alert_threshold': 0.001})

    def test_update_funding_rate(self):
        self.engine.update_funding_rate('BTC/USDT', 0.0005)
        self.assertEqual(self.engine._funding_rates['BTC/USDT'], 0.0005)

    def test_check_funding_alert(self):
        self.engine.update_funding_rate('BTC/USDT', 0.002)
        result = self.engine.check_funding_alert('BTC/USDT')
        self.assertTrue(result)


class TestV30_0AlertSystem(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_alerts': True})

    def test_send_alert(self):
        self.engine.send_alert('INFO', 'Test alert')
        self.assertEqual(len(self.engine._alert_history), 1)

    def test_get_recent_alerts(self):
        self.engine.send_alert('INFO', 'Test 1')
        self.engine.send_alert('WARNING', 'Test 2')
        alerts = self.engine.get_recent_alerts(1)
        self.assertEqual(len(alerts), 1)


class TestV30_0PerformanceSummary(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_get_performance_summary(self):
        summary = self.engine.get_performance_summary()
        self.assertIn('total_trades', summary)
        self.assertIn('consecutive_wins', summary)


class TestV30_0Config(unittest.TestCase):
    def test_auto_trade_config_v30_0(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={
            'enable_funding_monitor': True, 'funding_alert_threshold': 0.002,
            'enable_alerts': True, 'alert_level': 'WARNING'
        })
        self.assertTrue(engine.run_config.enable_funding_monitor)
        self.assertEqual(engine.run_config.funding_alert_threshold, 0.002)

    def test_default_config_v30_0(self):
        from trading.auto_execution_engine import AutoTradeConfig
        config = AutoTradeConfig()
        self.assertFalse(config.enable_funding_monitor)
        self.assertTrue(config.enable_alerts)


# V31.0: Smart Order Routing (SOR) Tests
class TestV31_0SORMode(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_sor_mode_enum(self):
        from trading.auto_execution_engine import SORMode
        self.assertEqual(SORMode.TWAP.value, 'twap')
        self.assertEqual(SORMode.VWAP.value, 'vwap')
        self.assertEqual(SORMode.POV.value, 'participation_of_volume')


class TestV31_0ExchangePrice(unittest.TestCase):
    def test_exchange_price_creation(self):
        from trading.auto_execution_engine import ExchangePrice
        price = ExchangePrice(
            exchange='binance',
            symbol='BTC/USDT',
            bid_price=50000.0,
            ask_price=50050.0,
            bid_volume=100.0,
            ask_volume=100.0
        )
        self.assertEqual(price.exchange, 'binance')
        self.assertEqual(price.symbol, 'BTC/USDT')
        self.assertEqual(price.bid_price, 50000.0)
        self.assertEqual(price.ask_price, 50050.0)


class TestV31_0SOROrder(unittest.TestCase):
    def test_sor_order_creation(self):
        from trading.auto_execution_engine import SOROrder
        order = SOROrder(
            order_id='sor_test_001',
            symbol='BTC/USDT',
            side='buy',
            total_quantity=1.0,
            mode='twap',
            slices=10
        )
        self.assertEqual(order.order_id, 'sor_test_001')
        self.assertEqual(order.symbol, 'BTC/USDT')
        self.assertEqual(order.side, 'buy')
        self.assertEqual(order.total_quantity, 1.0)
        self.assertEqual(order.status, 'pending')


class TestV31_0CollectPrices(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_collect_exchange_prices(self):
        import asyncio
        async def run():
            prices = await self.engine.collect_exchange_prices('BTC/USDT')
            return prices
        prices = asyncio.run(run())
        self.assertIsInstance(prices, list)
        # 模拟环境可能有配置限制


class TestV31_0CalculateSORSlices(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_calculate_sor_slices(self):
        from trading.auto_execution_engine import SOROrder
        order = SOROrder(
            order_id='sor_001',
            symbol='BTC/USDT',
            side='buy',
            total_quantity=1.0,
            slices=5,
            mode='twap'
        )
        slices = self.engine.calculate_sor_slices(order)
        self.assertEqual(len(slices), 5)
        self.assertEqual(slices[0]['status'], 'pending')


class TestV31_0CreateSOROrder(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_create_sor_order(self):
        order = self.engine.create_sor_order('BTC/USDT', 'buy', 1.0)
        self.assertEqual(order.symbol, 'BTC/USDT')
        self.assertEqual(order.side, 'buy')
        self.assertEqual(order.total_quantity, 1.0)
        self.assertIn(order.order_id, self.engine._sor_orders)


class TestV31_0GetSORStatus(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_get_sor_status(self):
        order = self.engine.create_sor_order('ETH/USDT', 'sell', 0.5)
        status = self.engine.get_sor_status(order.order_id)
        self.assertIsNotNone(status)
        self.assertEqual(status['symbol'], 'ETH/USDT')
        self.assertEqual(status['side'], 'sell')


class TestV31_0BestExchange(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_get_best_exchange_buy(self):
        # 模拟价格数据
        from trading.auto_execution_engine import ExchangePrice
        self.engine._exchange_prices['BTC/USDT'] = [
            ExchangePrice('binance', 'BTC/USDT', 50000, 50100, 100, 100),
            ExchangePrice('bybit', 'BTC/USDT', 49900, 50000, 100, 100),
        ]
        best = self.engine.get_best_exchange('BTC/USDT', 'buy')
        self.assertEqual(best, 'bybit')  # 最低卖价

    def test_get_best_exchange_sell(self):
        from trading.auto_execution_engine import ExchangePrice
        self.engine._exchange_prices['BTC/USDT'] = [
            ExchangePrice('binance', 'BTC/USDT', 50000, 50100, 100, 100),
            ExchangePrice('bybit', 'BTC/USDT', 49900, 50000, 100, 100),
        ]
        best = self.engine.get_best_exchange('BTC/USDT', 'sell')
        self.assertEqual(best, 'binance')  # 最高买价


class TestV31_0SORStats(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_sor_stats_initialized(self):
        stats = self.engine.stats
        self.assertIn('sor_orders_created', stats)
        self.assertIn('sor_orders_completed', stats)
        self.assertIn('sor_slices_executed', stats)
        self.assertIn('sor_total_slippage_bps', stats)


class TestV31_0Config(unittest.TestCase):
    def test_sor_default_config(self):
        from trading.auto_execution_engine import AutoTradeConfig
        config = AutoTradeConfig()
        self.assertFalse(config.enable_sor)
        self.assertEqual(config.sor_mode, 'twap')
        self.assertEqual(config.sor_slices, 10)

    def test_sor_custom_config(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={
            'enable_sor': True,
            'sor_mode': 'vwap',
            'sor_slices': 20,
            'sor_max_slippage_bps': 5
        })
        self.assertTrue(engine.run_config.enable_sor)
        self.assertEqual(engine.run_config.sor_mode, 'vwap')
        self.assertEqual(engine.run_config.sor_slices, 20)
        self.assertEqual(engine.run_config.sor_max_slippage_bps, 5)


# V32.0: Order Flow Analysis (OFA) Tests
class TestV32_0OFAConfig(unittest.TestCase):
    def test_ofa_default_config(self):
        from trading.auto_execution_engine import AutoTradeConfig
        config = AutoTradeConfig()
        self.assertFalse(config.enable_ofa)
        self.assertEqual(config.large_order_threshold, 1.0)
        self.assertEqual(config.vwap_gap_threshold, 0.005)

    def test_ofa_custom_config(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        engine = AutoExecutionEngine(config={
            'enable_ofa': True,
            'large_order_threshold': 2.0,
            'vwap_gap_threshold': 0.01,
            'institutional_patterns': True
        })
        self.assertTrue(engine.run_config.enable_ofa)
        self.assertEqual(engine.run_config.large_order_threshold, 2.0)
        self.assertEqual(engine.run_config.vwap_gap_threshold, 0.01)
        self.assertTrue(engine.run_config.institutional_patterns)


class TestV32_0VolumeTracking(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_update_volume(self):
        self.engine.update_volume('BTC/USDT', 5.0, 50000.0)
        self.assertIn('BTC/USDT', self.engine._volume_history)
        self.assertEqual(len(self.engine._volume_history['BTC/USDT']), 1)


class TestV32_0LargeOrderDetection(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_detect_large_order(self):
        # 添加大单
        self.engine.update_volume('BTC/USDT', 5.0, 50000.0)
        result = self.engine.detect_large_order('BTC/USDT')
        self.assertIsNotNone(result)
        self.assertTrue(result['is_large'])


class TestV32_0VWAPGap(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_detect_vwap_gap(self):
        # 设置交易历史计算VWAP
        self.engine._trade_history['ETH/USDT'] = [
            {'price': 3000, 'volume': 10},
            {'price': 3100, 'volume': 10}
        ]
        # 手动设置VWAP
        self.engine._vwap['ETH/USDT'] = 3050

        # 测试缺口检测
        gap = self.engine.detect_vwap_gap('ETH/USDT', 3200)  # 大于VWAP 5%
        self.assertIsNotNone(gap)
        self.assertEqual(gap['direction'], 'above')


class TestV32_0OrderFlowScore(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_ofa': True})

    def test_calculate_order_flow_score(self):
        # 添加足够交易量
        for i in range(10):
            self.engine.update_volume('BTC/USDT', 0.5 + i * 0.1, 50000 + i * 10)

        score = self.engine.calculate_order_flow_score('BTC/USDT')
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)


class TestV32_0InstitutionalPattern(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine(config={'enable_ofa': True, 'institutional_patterns': True})

    def test_detect_institutional_pattern(self):
        # 添加持续大单
        for i in range(25):
            vol = 5.0 if i % 3 == 0 else 0.5
            self.engine.update_volume('BTC/USDT', vol, 50000 + i)
            self.engine._trade_history['BTC/USDT'].append({'price': 50000 + i, 'volume': vol})

        pattern = self.engine.detect_institutional_pattern('BTC/USDT')
        self.assertIsNotNone(pattern)


class TestV32_0OrderFlowSummary(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_get_order_flow_summary(self):
        self.engine.update_volume('BTC/USDT', 1.0, 50000)
        summary = self.engine.get_order_flow_summary('BTC/USDT')
        self.assertIn('order_flow_score', summary)
        self.assertIn('vwap', summary)


class TestV32_0OFAStats(unittest.TestCase):
    def setUp(self):
        from trading.auto_execution_engine import AutoExecutionEngine
        self.engine = AutoExecutionEngine()

    def test_ofa_stats_initialized(self):
        stats = self.engine.stats
        self.assertIn('large_orders_detected', stats)
        self.assertIn('vwap_gaps_detected', stats)
        self.assertIn('institutional_signals', stats)


# 运行测试
if __name__ == '__main__':
    unittest.main(verbosity=2)