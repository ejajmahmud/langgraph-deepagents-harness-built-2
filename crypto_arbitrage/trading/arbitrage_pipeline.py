"""套利交易管道 V16.6

完整编排套利交易生命周期：扫描 → 知识过滤 → 风险检查 → 执行 → 持仓跟踪 → 知识双向桥接 → 持久化。
桥接 V16.2 KnowledgeDrivenArbitrageScanner 与现有 ExecutionEngine/PositionManager。
V16.6新增：双向知识桥接 + 知识驱动信号过滤 + 管道状态持久化。

核心能力：
1. 管道编排 — Scanner → Knowledge Filter → Risk Gate → Execution → Position → Knowledge Bridge 全链路
2. 风险门控 — 自动评估机会风险等级，低置信度/高波动自动拒绝
3. 模拟/实盘切换 — simulation 模式用模拟执行，live 模式对接真实交易所
4. 持仓跟踪 — 每笔套利开仓/平仓记录，实时 P&L 计算
5. 知识闭环 — 每笔交易结果自动写入知识库，驱动后续决策
6. 批量回测 — 支持 N 轮连续扫描+执行模拟，输出统计报告
7. [V16.4] 统计套利 — StatisticalArbEngine集成，自动配对发现+信号生成
8. [V16.4] 自适应风控 — AdaptiveRiskGate根据知识库动态调整参数
9. [V16.5] 资金费率套利 — FundingRateEngine集成，delta中性费率收益
10. [V16.5] 组合风控 — PortfolioRiskManager跨策略统一风控
11. [V16.5] 异步管道 — run_pipeline_async非阻塞执行
12. [V16.6] 双向知识桥 — TradingKnowledgeBridge读写双向知识流
13. [V16.6] 信号过滤 — KnowledgeDrivenSignalFilter基于历史知识过滤信号
14. [V16.6] 状态持久化 — PipelineStatePersistence重启恢复

架构位置:
    CcxtPriceFeed ─→ PriceHistoryManager ─→ StatisticalArbEngine ─┐
                    ─→ KnowledgeDrivenArbitrageScanner ───────────┤
                    ─→ FundingRateEngine ─────────────────────────┤
                                                                   ↓
                                                         ArbitragePipeline V16.6
                                                                   ↕
                    Memo0 Knowledge Base ←── PortfolioRiskManager ─┤
                    TradingKnowledgeBridge ←── KnowledgeSignalFilter┤
                    PipelineStatePersistence ←─────────────────────┘

创建时间：2026-05-05
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PipelineMode(Enum):
    """管道运行模式"""
    SIMULATION = "simulation"
    LIVE = "live"


class PipelineStage(Enum):
    """管道阶段"""
    SCANNING = "scanning"
    RISK_GATING = "risk_gating"
    EXECUTING = "executing"
    POSITION_TRACKING = "position_tracking"
    KNOWLEDGE_RECORDING = "knowledge_recording"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineResult:
    """管道执行结果"""
    pipeline_id: str
    stage: PipelineStage
    opportunities_scanned: int = 0
    opportunities_passed_risk: int = 0
    opportunities_executed: int = 0
    positions_opened: int = 0
    positions_closed: int = 0
    knowledge_entries: int = 0
    total_realized_pnl: float = 0.0
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    # V16.4 统计套利字段
    stat_arb_pairs_scanned: int = 0
    stat_arb_signals: int = 0
    stat_arb_positions_opened: int = 0
    stat_arb_positions_closed: int = 0
    stat_arb_pnl: float = 0.0
    # V16.5 资金费率字段
    funding_rate_opportunities: int = 0
    funding_rate_signals: int = 0
    funding_rate_positions_opened: int = 0
    funding_rate_positions_closed: int = 0
    funding_rate_pnl: float = 0.0
    # V16.5 组合风控字段
    portfolio_risk_actions: int = 0
    portfolio_risk_rejections: int = 0
    # V16.6 知识桥接字段
    knowledge_context_applied: bool = False
    signals_filtered: int = 0
    signals_filtered_reasons: List[str] = field(default_factory=list)
    knowledge_reads: int = 0
    knowledge_writes: int = 0
    state_persisted: bool = False


@dataclass
class PositionRecord:
    """持仓记录"""
    position_id: str
    opportunity_id: str
    arbitrage_type: str
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    quantity: float
    expected_profit_pct: float
    actual_profit_pct: float = 0.0
    status: str = "open"
    opened_at: float = 0.0
    closed_at: float = 0.0
    knowledge_recorded: bool = False


class AdaptiveRiskGate:
    """自适应风控门控 V16.4

    根据知识库中的历史交易数据动态调整风控参数。
    """

    def __init__(self, knowledge_storage=None, config: Optional[Dict[str, Any]] = None):
        """初始化自适应风控

        Args:
            knowledge_storage: 知识存储实例
            config: 配置字典
        """
        self._knowledge = knowledge_storage
        self.config = config or {}

        # 基准参数
        self._base_confidence = self.config.get("min_confidence_to_execute", 0.65)
        self._base_profit = self.config.get("min_profit_to_execute", 0.05)
        self._base_max_positions = self.config.get("max_positions", 10)

        # 自适应参数（当前生效值）
        self.current_confidence = self._base_confidence
        self.current_profit = self._base_profit
        self.current_max_positions = self._base_max_positions

        # 调整历史
        self._adjustment_history: List[Dict[str, Any]] = []
        self._last_adjustment_time = 0.0
        self._adjustment_interval = self.config.get("adjustment_interval_sec", 300.0)

    def update_from_knowledge(self) -> Dict[str, Any]:
        """从知识库学习并调整参数

        Returns:
            调整结果
        """
        if self._knowledge is None:
            return {"adjusted": False, "reason": "no_knowledge"}

        now = time.time()
        if now - self._last_adjustment_time < self._adjustment_interval:
            return {"adjusted": False, "reason": "too_frequent"}

        try:
            # 搜索最近的执行结果
            results = self._knowledge.search_memories("arbitrage_execution", top_k=20)
            stat_results = self._knowledge.search_memories("stat_arb_result", top_k=20)

            all_results = results + stat_results

            if len(all_results) < 5:
                return {"adjusted": False, "reason": "insufficient_data"}

            # 统计胜率
            wins = sum(
                1 for r in all_results
                if "profitable" in r.get("memory", "").lower() or
                   "profit" in r.get("memory", "").lower()
            )
            losses = sum(
                1 for r in all_results
                if "loss" in r.get("memory", "").lower() and
                   "profitable" not in r.get("memory", "").lower()
            )

            total = wins + losses
            win_rate = wins / total if total > 0 else 0.5

            adjustments = {}

            # 胜率高 → 放宽限制
            if win_rate > 0.7:
                self.current_confidence = max(0.4, self._base_confidence - 0.1)
                self.current_profit = max(0.02, self._base_profit * 0.8)
                self.current_max_positions = self._base_max_positions + 2
                adjustments["direction"] = "relaxed"
            # 胜率低 → 收紧限制
            elif win_rate < 0.4:
                self.current_confidence = min(0.85, self._base_confidence + 0.1)
                self.current_profit = self._base_profit * 1.5
                self.current_max_positions = max(3, self._base_max_positions - 2)
                adjustments["direction"] = "tightened"
            else:
                # 正常范围 → 恢复基准
                self.current_confidence = self._base_confidence
                self.current_profit = self._base_profit
                self.current_max_positions = self._base_max_positions
                adjustments["direction"] = "baseline"

            adjustments.update({
                "win_rate": win_rate,
                "total_trades": total,
                "confidence": self.current_confidence,
                "min_profit": self.current_profit,
                "max_positions": self.current_max_positions,
            })

            self._adjustment_history.append({
                "timestamp": now,
                "adjustments": adjustments
            })
            self._last_adjustment_time = now

            return {"adjusted": True, **adjustments}

        except Exception as e:
            return {"adjusted": False, "reason": str(e)}

    def get_current_params(self) -> Dict[str, Any]:
        """获取当前风控参数

        Returns:
            当前参数字典
        """
        return {
            "min_confidence": self.current_confidence,
            "min_profit_pct": self.current_profit,
            "max_positions": self.current_max_positions,
            "adjustment_count": len(self._adjustment_history),
        }


class ArbitragePipeline:
    """套利交易管道 V16.6

    编排完整的套利交易生命周期，连接各核心组件。
    V16.6增强：双向知识桥接 + 知识驱动信号过滤 + 管道状态持久化。
    """

    def __init__(
        self,
        scanner=None,
        knowledge_storage=None,
        config: Optional[Dict[str, Any]] = None,
        stat_arb_engine=None,
        price_history_manager=None,
        adaptive_risk_gate=None,
        funding_rate_engine=None,
        portfolio_risk_manager=None,
        knowledge_bridge=None,
        signal_filter=None,
        state_persistence=None
    ):
        """初始化套利交易管道

        Args:
            scanner: KnowledgeDrivenArbitrageScanner 实例
            knowledge_storage: Memo0/Mock 知识存储实例
            config: 配置字典
            stat_arb_engine: StatisticalArbEngine 实例 (V16.4)
            price_history_manager: PriceHistoryManager 实例 (V16.4)
            adaptive_risk_gate: AdaptiveRiskGate 实例 (V16.4)
            funding_rate_engine: FundingRateEngine 实例 (V16.5)
            portfolio_risk_manager: PortfolioRiskManager 实例 (V16.5)
            knowledge_bridge: TradingKnowledgeBridge 实例 (V16.6)
            signal_filter: KnowledgeDrivenSignalFilter 实例 (V16.6)
            state_persistence: PipelineStatePersistence 实例 (V16.6)
        """
        self._scanner = scanner
        self._knowledge = knowledge_storage
        self.config = config or {}

        # V16.4 新组件
        self._stat_arb_engine = stat_arb_engine
        self._price_history = price_history_manager
        self._adaptive_risk = adaptive_risk_gate

        # V16.5 新组件
        self._funding_rate_engine = funding_rate_engine
        self._portfolio_risk = portfolio_risk_manager

        # V16.6 新组件
        self._knowledge_bridge = knowledge_bridge
        self._signal_filter = signal_filter
        self._state_persistence = state_persistence

        # 管道参数
        self.mode = PipelineMode(
            self.config.get("mode", "simulation")
        )
        self.max_positions = self.config.get("max_positions", 10)
        self.max_single_trade_usd = self.config.get("max_single_trade_usd", 1000.0)
        self.min_confidence_to_execute = self.config.get("min_confidence_to_execute", 0.65)
        self.min_profit_to_execute = self.config.get("min_profit_to_execute", 0.05)
        self.auto_execute = self.config.get("auto_execute", True)
        self.knowledge_feedback = self.config.get("knowledge_feedback", True)

        # V16.4 统计套利开关
        self.enable_stat_arb = self.config.get("enable_stat_arb", True)
        self.enable_adaptive_risk = self.config.get("enable_adaptive_risk", True)

        # V16.5 资金费率套利开关
        self.enable_funding_rate = self.config.get("enable_funding_rate", True)
        self.enable_portfolio_risk = self.config.get("enable_portfolio_risk", True)

        # V16.6 知识桥接和信号过滤开关
        self.enable_knowledge_bridge = self.config.get("enable_knowledge_bridge", True)
        self.enable_signal_filter = self.config.get("enable_signal_filter", True)
        self.enable_state_persistence = self.config.get("enable_state_persistence", True)

        # 持仓管理
        self.positions: Dict[str, PositionRecord] = {}
        self.closed_positions: List[PositionRecord] = []

        # 统计数据
        self.total_pipelines = 0
        self.total_opportunities_found = 0
        self.total_opportunities_executed = 0
        self.total_positions_opened = 0
        self.total_positions_closed = 0
        self.total_realized_pnl = 0.0
        self.total_fees_paid = 0.0

        # V16.4 统计套利统计
        self.total_stat_arb_signals = 0
        self.total_stat_arb_positions = 0
        self.total_stat_arb_pnl = 0.0

        # V16.5 资金费率统计
        self.total_funding_rate_signals = 0
        self.total_funding_rate_positions = 0
        self.total_funding_rate_pnl = 0.0
        self.total_portfolio_risk_rejections = 0

        # V16.6 知识桥接统计
        self.total_signals_filtered = 0
        self.total_knowledge_reads = 0
        self.total_knowledge_writes = 0

        # 管道历史
        self.pipeline_history: List[PipelineResult] = []
        self.max_history = 200

        logger.info(
            f"套利交易管道 V16.6 初始化: "
            f"mode={self.mode.value}, "
            f"max_positions={self.max_positions}, "
            f"stat_arb={'ON' if self.enable_stat_arb else 'OFF'}, "
            f"funding_rate={'ON' if self.enable_funding_rate else 'OFF'}, "
            f"portfolio_risk={'ON' if self.enable_portfolio_risk else 'OFF'}, "
            f"knowledge_bridge={'ON' if self.enable_knowledge_bridge else 'OFF'}, "
            f"signal_filter={'ON' if self.enable_signal_filter else 'OFF'}, "
            f"state_persist={'ON' if self.enable_state_persistence else 'OFF'}"
        )

    def _get_scanner(self):
        """延迟获取扫描器"""
        if self._scanner is not None:
            return self._scanner
        try:
            from strategies.knowledge_driven_arbitrage_scanner import get_arbitrage_scanner
            self._scanner = get_arbitrage_scanner()
            return self._scanner
        except Exception as e:
            logger.error(f"获取扫描器失败: {e}")
            return None

    def _get_knowledge(self):
        """延迟获取知识存储"""
        if self._knowledge is not None:
            return self._knowledge
        try:
            from storage.mem0_storage import get_mem0_storage
            storage = get_mem0_storage()
            if storage is None:
                from storage.mem0_mock_storage import create_mock_mem0_storage
                storage = create_mock_mem0_storage({
                    "user_id": "crypto-arbitrage-user",
                    "agent_id": "arbitrage-pipeline-v16-3"
                })
            self._knowledge = storage
            return storage
        except Exception:
            try:
                from storage.mem0_mock_storage import create_mock_mem0_storage
                storage = create_mock_mem0_storage({
                    "user_id": "crypto-arbitrage-user",
                    "agent_id": "arbitrage-pipeline-v16-3"
                })
                self._knowledge = storage
                return storage
            except Exception as e:
                logger.error(f"获取知识存储失败: {e}")
                return None

    def run_pipeline(self) -> PipelineResult:
        """执行完整的套利交易管道

        流程：扫描 → [统计套利扫描] → 风险检查 → 执行 → 持仓 → 知识记录

        Returns:
            管道执行结果
        """
        start_time = time.time()
        pipeline_id = f"pipe_{uuid.uuid4().hex[:12]}"

        result = PipelineResult(
            pipeline_id=pipeline_id,
            stage=PipelineStage.SCANNING
        )

        logger.info(f"[Pipeline:{pipeline_id}] 开始执行管道 V16.6")

        try:
            # Stage 0: 自适应风控参数更新 (V16.4)
            if self.enable_adaptive_risk and self._adaptive_risk:
                self._update_adaptive_risk_params()

            # Stage 0.5: 知识上下文加载 (V16.6)
            if self.enable_knowledge_bridge:
                self._stage_load_knowledge_context(result)

            # Stage 1: 扫描
            scan_result = self._stage_scan(result)
            if scan_result is None:
                result.stage = PipelineStage.FAILED
                result.errors.append("扫描阶段失败")
                return self._finalize_pipeline(result, start_time)

            # Stage 1.5: 统计套利扫描 (V16.4)
            if self.enable_stat_arb:
                self._stage_stat_arb_scan(result)

            # Stage 1.6: 资金费率套利扫描 (V16.5)
            if self.enable_funding_rate:
                self._stage_funding_rate_scan(result)

            # Stage 2: 风险门控
            gated_opportunities = self._stage_risk_gate(result, scan_result)
            if not gated_opportunities and result.stat_arb_positions_opened == 0:
                result.stage = PipelineStage.COMPLETED
                logger.info(f"[Pipeline:{pipeline_id}] 无机会通过风险门控")
                return self._finalize_pipeline(result, start_time)

            # Stage 2.5: 知识驱动信号过滤 (V16.6)
            if self.enable_signal_filter and gated_opportunities:
                gated_opportunities = self._stage_signal_filter(result, gated_opportunities)

            # Stage 3: 执行
            if gated_opportunities:
                execution_results = self._stage_execute(result, gated_opportunities)

                # Stage 4: 持仓跟踪
                self._stage_position_tracking(result, execution_results)

                # Stage 5: 知识记录
                self._stage_knowledge_recording(result, execution_results)

            result.stage = PipelineStage.COMPLETED
            logger.info(
                f"[Pipeline:{pipeline_id}] 管道完成: "
                f"扫描={result.opportunities_scanned}, "
                f"通过风控={result.opportunities_passed_risk}, "
                f"执行={result.opportunities_executed}, "
                f"统计套利信号={result.stat_arb_signals}, "
                f"盈亏={result.total_realized_pnl:.4f}%"
            )

            # Stage 6: 知识桥接写入 (V16.6)
            if self.enable_knowledge_bridge:
                self._stage_knowledge_bridge_write(result)

            # Stage 7: 状态持久化 (V16.6)
            if self.enable_state_persistence:
                self._stage_persist_state(result)

        except Exception as e:
            result.stage = PipelineStage.FAILED
            result.errors.append(str(e))
            logger.error(f"[Pipeline:{pipeline_id}] 管道异常: {e}")

        return self._finalize_pipeline(result, start_time)

    def _stage_scan(self, result: PipelineResult):
        """阶段1: 扫描套利机会"""
        scanner = self._get_scanner()
        if scanner is None:
            result.errors.append("扫描器不可用")
            return None

        try:
            scan_result = scanner.full_scan()
            result.opportunities_scanned = scan_result.opportunities_found
            self.total_opportunities_found += scan_result.opportunities_found

            result.details["scan_id"] = scan_result.scan_id
            result.details["scan_duration_ms"] = scan_result.scan_duration_ms
            result.details["raw_opportunities"] = len(scan_result.all_opportunities)

            logger.info(
                f"扫描完成: {scan_result.opportunities_found} 个机会, "
                f"{scan_result.profitable_opportunities} 个盈利"
            )
            return scan_result

        except Exception as e:
            result.errors.append(f"扫描失败: {e}")
            logger.error(f"扫描阶段失败: {e}")
            return None

    def _update_adaptive_risk_params(self) -> None:
        """V16.4: 更新自适应风控参数"""
        try:
            result = self._adaptive_risk.update_from_knowledge()
            if result.get("adjusted"):
                params = self._adaptive_risk.get_current_params()
                self.min_confidence_to_execute = params["min_confidence"]
                self.min_profit_to_execute = params["min_profit_pct"]
                self.max_positions = params["max_positions"]
                logger.info(
                    f"自适应风控调整: confidence={params['min_confidence']:.2f}, "
                    f"profit={params['min_profit_pct']:.4f}%, "
                    f"direction={result.get('direction', 'unknown')}"
                )
        except Exception as e:
            logger.warning(f"自适应风控更新失败: {e}")

    def _stage_stat_arb_scan(self, result: PipelineResult) -> None:
        """V16.4: 统计套利扫描阶段

        运行StatisticalArbEngine扫描+执行统计套利信号。

        Args:
            result: 管道结果
        """
        engine = self._get_stat_arb_engine()
        if engine is None:
            return

        try:
            scan_result = engine.run_full_scan(exchange="binance")

            result.stat_arb_pairs_scanned = scan_result.get("pairs_scanned", 0)
            result.stat_arb_signals = scan_result.get("signals_generated", 0)
            result.stat_arb_positions_opened = scan_result.get("positions_opened", 0)
            result.stat_arb_positions_closed = scan_result.get("positions_closed", 0)

            # 统计已关闭持仓的P&L
            for pos in engine.closed_positions:
                if pos.status == "closed":
                    result.stat_arb_pnl += pos.realized_pnl_usd

            # 更新全局统计
            self.total_stat_arb_signals += result.stat_arb_signals
            self.total_stat_arb_positions += result.stat_arb_positions_opened
            self.total_stat_arb_pnl += result.stat_arb_pnl

            logger.info(
                f"统计套利阶段: "
                f"配对={result.stat_arb_pairs_scanned}, "
                f"信号={result.stat_arb_signals}, "
                f"开仓={result.stat_arb_positions_opened}, "
                f"平仓={result.stat_arb_positions_closed}"
            )

        except Exception as e:
            result.errors.append(f"统计套利扫描失败: {e}")
            logger.warning(f"统计套利阶段失败: {e}")

    def _get_stat_arb_engine(self):
        """V16.4: 延迟获取统计套利引擎"""
        if self._stat_arb_engine is not None:
            return self._stat_arb_engine
        try:
            from strategies.statistical_arb_engine import get_statistical_arb_engine
            self._stat_arb_engine = get_statistical_arb_engine({
                "position_size_usd": self.max_single_trade_usd,
                "max_positions": max(2, self.max_positions // 3),
            })
            return self._stat_arb_engine
        except Exception as e:
            logger.debug(f"统计套利引擎不可用: {e}")
            return None

    def _get_funding_rate_engine(self):
        """V16.5: 延迟获取资金费率引擎"""
        if self._funding_rate_engine is not None:
            return self._funding_rate_engine
        try:
            from strategies.funding_rate_engine import get_funding_rate_engine
            self._funding_rate_engine = get_funding_rate_engine({
                "position_size_usd": self.max_single_trade_usd,
                "max_total_positions": max(2, self.max_positions // 4),
            })
            return self._funding_rate_engine
        except Exception as e:
            logger.debug(f"资金费率引擎不可用: {e}")
            return None

    def _get_portfolio_risk(self):
        """V16.5: 延迟获取组合风控"""
        if self._portfolio_risk is not None:
            return self._portfolio_risk
        try:
            from trading.portfolio_risk_manager import get_portfolio_risk_manager
            self._portfolio_risk = get_portfolio_risk_manager({
                "max_total_exposure_usd": self.max_single_trade_usd * self.max_positions,
                "max_single_position_usd": self.max_single_trade_usd,
                "max_positions_total": self.max_positions,
            })
            return self._portfolio_risk
        except Exception as e:
            logger.debug(f"组合风控不可用: {e}")
            return None

    def _get_knowledge_bridge(self):
        """V16.6: 延迟获取知识桥接器"""
        if self._knowledge_bridge is not None:
            return self._knowledge_bridge
        try:
            from trading.trading_knowledge_bridge import get_trading_knowledge_bridge
            self._knowledge_bridge = get_trading_knowledge_bridge(
                knowledge_storage=self._knowledge
            )
            return self._knowledge_bridge
        except Exception as e:
            logger.debug(f"知识桥接器不可用: {e}")
            return None

    def _get_signal_filter(self):
        """V16.6: 延迟获取信号过滤器"""
        if self._signal_filter is not None:
            return self._signal_filter
        try:
            from trading.knowledge_signal_filter import get_knowledge_signal_filter
            bridge = self._get_knowledge_bridge()
            self._signal_filter = get_knowledge_signal_filter(
                knowledge_bridge=bridge
            )
            return self._signal_filter
        except Exception as e:
            logger.debug(f"信号过滤器不可用: {e}")
            return None

    def _get_state_persistence(self):
        """V16.6: 延迟获取状态持久化"""
        if self._state_persistence is not None:
            return self._state_persistence
        try:
            from trading.pipeline_state_persistence import get_pipeline_persistence
            self._state_persistence = get_pipeline_persistence()
            return self._state_persistence
        except Exception as e:
            logger.debug(f"状态持久化不可用: {e}")
            return None

    def _stage_load_knowledge_context(self, result: PipelineResult) -> None:
        """V16.6: 加载知识上下文

        从知识库加载市场上下文，用于辅助决策。

        Args:
            result: 管道结果
        """
        bridge = self._get_knowledge_bridge()
        if bridge is None:
            return

        try:
            context = bridge.get_market_context()
            result.knowledge_context_applied = context.confidence > 0.1
            result.knowledge_reads += 1
            self.total_knowledge_reads += 1

            if context.confidence > 0.1:
                # 根据上下文调整管道参数
                if context.recent_win_rate < 0.3:
                    # 近期胜率低，收紧风控
                    self.min_confidence_to_execute = min(
                        0.85, self.min_confidence_to_execute + 0.05
                    )
                    logger.info(
                        f"知识上下文: 胜率低({context.recent_win_rate:.1%})，"
                        f"收紧置信度至{self.min_confidence_to_execute:.2f}"
                    )
                elif context.recent_win_rate > 0.7:
                    # 近期胜率高，适当放宽
                    self.min_confidence_to_execute = max(
                        0.5, self.min_confidence_to_execute - 0.05
                    )
                    logger.info(
                        f"知识上下文: 胜率高({context.recent_win_rate:.1%})，"
                        f"放宽置信度至{self.min_confidence_to_execute:.2f}"
                    )

                if context.circuit_breaker_count > 2:
                    logger.warning(
                        f"知识上下文: 近期{context.circuit_breaker_count}次熔断，"
                        f"建议降低仓位"
                    )

            logger.info(
                f"知识上下文加载: conf={context.confidence:.2f}, "
                f"win_rate={context.recent_win_rate:.1%}"
            )

        except Exception as e:
            result.errors.append(f"知识上下文加载失败: {e}")
            logger.warning(f"知识上下文加载失败: {e}")

    def _stage_signal_filter(
        self,
        result: PipelineResult,
        opportunities: list
    ) -> list:
        """V16.6: 知识驱动信号过滤

        Args:
            result: 管道结果
            opportunities: 通过风控的机会列表

        Returns:
            过滤后的机会列表
        """
        signal_filter = self._get_signal_filter()
        if signal_filter is None:
            return opportunities

        filtered = []
        for opp in opportunities:
            # 将机会转换为信号过滤参数
            filter_result = signal_filter.filter_signal(
                signal_type=getattr(opp, 'arbitrage_type', type('', (), {'value': 'cross_exchange'})()).value
                if hasattr(opp, 'arbitrage_type') else 'cross_exchange',
                symbol=getattr(opp, 'symbol', 'UNKNOWN'),
                exchange=getattr(opp, 'buy_exchange', 'unknown'),
                side="buy",
                confidence=getattr(opp, 'confidence_score', 0.5),
                size_usd=self.max_single_trade_usd
            )

            if filter_result.action.value in ("pass", "reduce_confidence", "reduce_size"):
                # 调整置信度
                if hasattr(opp, 'confidence_score'):
                    opp.confidence_score = filter_result.adjusted_confidence
                filtered.append(opp)
            else:
                result.signals_filtered += 1
                result.signals_filtered_reasons.extend(filter_result.reasons[:2])

        self.total_signals_filtered += result.signals_filtered
        logger.info(
            f"信号过滤: {len(opportunities)} → {len(filtered)} | "
            f"过滤={result.signals_filtered}"
        )

        return filtered

    def _stage_knowledge_bridge_write(self, result: PipelineResult) -> None:
        """V16.6: 知识桥接写入

        将交易结果和风控事件写入知识库。

        Args:
            result: 管道结果
        """
        bridge = self._get_knowledge_bridge()
        if bridge is None:
            return

        try:
            # 记录交易结果
            for pos in self.closed_positions:
                if not pos.knowledge_recorded:
                    bridge.record_trade_result(
                        strategy=pos.arbitrage_type,
                        symbol=pos.symbol,
                        exchange=pos.buy_exchange,
                        pnl_pct=pos.actual_profit_pct,
                        pnl_usd=pos.actual_profit_pct * pos.quantity * pos.buy_price / 100,
                        outcome="profitable" if pos.actual_profit_pct > 0 else "loss"
                    )
                    pos.knowledge_recorded = True
                    result.knowledge_writes += 1

            # 记录管道结果摘要
            if result.total_realized_pnl != 0:
                bridge.save_pipeline_state({
                    "pipeline_id": result.pipeline_id,
                    "total_pnl": result.total_realized_pnl,
                    "positions_closed": result.positions_closed,
                    "stat_arb_pnl": result.stat_arb_pnl,
                    "funding_rate_pnl": result.funding_rate_pnl,
                })
                result.knowledge_writes += 1

            self.total_knowledge_writes += result.knowledge_writes

            # 刷新桥接器缓冲区
            bridge._flush_perf_buffer()

            logger.info(f"知识桥接写入: {result.knowledge_writes} 条")

        except Exception as e:
            result.errors.append(f"知识桥接写入失败: {e}")
            logger.warning(f"知识桥接写入失败: {e}")

    def _stage_persist_state(self, result: PipelineResult) -> None:
        """V16.6: 持久化管道状态

        Args:
            result: 管道结果
        """
        persistence = self._get_state_persistence()
        if persistence is None:
            return

        try:
            # 保存管道结果历史
            persistence.save_pipeline_result(
                pipeline_id=result.pipeline_id,
                stage=result.stage.value,
                opportunities_scanned=result.opportunities_scanned,
                opportunities_executed=result.opportunities_executed,
                positions_opened=result.positions_opened,
                positions_closed=result.positions_closed,
                realized_pnl=result.total_realized_pnl,
                execution_time_ms=result.execution_time_ms,
                errors=result.errors[:5],
            )

            # 保存管道统计
            from trading.pipeline_state_persistence import PersistedPipelineStats
            stats = PersistedPipelineStats(
                total_pipelines=self.total_pipelines,
                total_opportunities_found=self.total_opportunities_found,
                total_opportunities_executed=self.total_opportunities_executed,
                total_positions_opened=self.total_positions_opened,
                total_positions_closed=self.total_positions_closed,
                total_realized_pnl=self.total_realized_pnl,
                total_stat_arb_pnl=self.total_stat_arb_pnl,
                total_funding_rate_pnl=self.total_funding_rate_pnl,
                total_portfolio_risk_rejections=self.total_portfolio_risk_rejections,
            )
            persistence.save_pipeline_stats(stats)

            # 保存风控状态
            prisk = self._get_portfolio_risk()
            if prisk:
                persistence.save_risk_state(
                    peak_nav=prisk._peak_nav,
                    total_realized_pnl=prisk._total_realized_pnl,
                    circuit_breaker_active=prisk._circuit_breaker_active,
                    circuit_breaker_reason=prisk._circuit_breaker_reason,
                    circuit_breaker_since=prisk._circuit_breaker_since,
                    total_position_count=len(prisk._positions)
                )

            result.state_persisted = True
            logger.info("管道状态已持久化")

        except Exception as e:
            result.errors.append(f"状态持久化失败: {e}")
            logger.warning(f"状态持久化失败: {e}")

    def _stage_funding_rate_scan(self, result: PipelineResult) -> None:
        """V16.5: 资金费率套利扫描阶段

        运行FundingRateEngine扫描+执行资金费率套利。

        Args:
            result: 管道结果
        """
        engine = self._get_funding_rate_engine()
        if engine is None:
            return

        try:
            scan_result = engine.run_full_scan()

            result.funding_rate_opportunities = scan_result.get("opportunities_found", 0)
            result.funding_rate_signals = scan_result.get("signals_generated", 0)
            result.funding_rate_positions_opened = scan_result.get("positions_opened", 0)
            result.funding_rate_positions_closed = scan_result.get("positions_closed", 0)

            # 统计已关闭持仓的P&L
            for pos in engine.closed_positions:
                if pos.status == "closed":
                    result.funding_rate_pnl += pos.realized_pnl_usd

            # V16.5: 注册到组合风控
            if self.enable_portfolio_risk:
                prisk = self._get_portfolio_risk()
                if prisk:
                    for pos_id, pos in engine.positions.items():
                        if pos.status == "open":
                            prisk.register_position(
                                strategy="funding_rate",
                                symbol=pos.symbol,
                                exchange=pos.exchange,
                                side=pos.side.value,
                                quantity=pos.quantity,
                                value_usd=pos.position_value_usd,
                                strategy_position_id=pos.position_id
                            )

            # 更新全局统计
            self.total_funding_rate_signals += result.funding_rate_signals
            self.total_funding_rate_positions += result.funding_rate_positions_opened
            self.total_funding_rate_pnl += result.funding_rate_pnl

            logger.info(
                f"资金费率阶段: "
                f"机会={result.funding_rate_opportunities}, "
                f"信号={result.funding_rate_signals}, "
                f"开仓={result.funding_rate_positions_opened}, "
                f"平仓={result.funding_rate_positions_closed}"
            )

        except Exception as e:
            result.errors.append(f"资金费率扫描失败: {e}")
            logger.warning(f"资金费率阶段失败: {e}")

    def _stage_risk_gate(
        self,
        result: PipelineResult,
        scan_result
    ) -> list:
        """阶段2: 风险门控

        过滤掉低置信度、低利润、风险过高的机会。

        Args:
            result: 管道结果
            scan_result: 扫描结果

        Returns:
            通过风控的机会列表
        """
        result.stage = PipelineStage.RISK_GATING

        gated = []
        for opp in scan_result.all_opportunities:
            # 检查置信度
            if opp.confidence_score < self.min_confidence_to_execute:
                logger.debug(
                    f"机会 {opp.opportunity_id} 置信度过低: "
                    f"{opp.confidence_score:.2f} < {self.min_confidence_to_execute}"
                )
                continue

            # 检查净利润
            if opp.net_profit_pct < self.min_profit_to_execute:
                logger.debug(
                    f"机会 {opp.opportunity_id} 利润过低: "
                    f"{opp.net_profit_pct:.4f}% < {self.min_profit_to_execute}%"
                )
                continue

            # 检查持仓数量限制
            if len(self.positions) >= self.max_positions:
                logger.debug("持仓数量已达上限，跳过")
                continue

            # 检查重复持仓（同币种同类型）
            duplicate = any(
                p.symbol == opp.symbol and
                p.arbitrage_type == opp.arbitrage_type.value and
                p.status == "open"
                for p in self.positions.values()
            )
            if duplicate:
                logger.debug(f"重复持仓: {opp.symbol} {opp.arbitrage_type.value}")
                continue

            gated.append(opp)

        result.opportunities_passed_risk = len(gated)
        logger.info(f"风险门控: {len(scan_result.all_opportunities)} → {len(gated)} 个通过")
        return gated

    def _stage_execute(
        self,
        result: PipelineResult,
        opportunities: list
    ) -> List[Dict[str, Any]]:
        """阶段3: 执行套利交易

        Args:
            result: 管道结果
            opportunities: 通过风控的机会列表

        Returns:
            执行结果列表
        """
        result.stage = PipelineStage.EXECUTING

        execution_results = []
        for opp in opportunities:
            exec_result = self._execute_single_opportunity(opp)
            execution_results.append(exec_result)

            if exec_result.get("success"):
                result.opportunities_executed += 1
                self.total_opportunities_executed += 1
            else:
                result.errors.append(
                    f"执行失败 {opp.opportunity_id}: "
                    f"{exec_result.get('error', 'unknown')}"
                )

        return execution_results

    def _execute_single_opportunity(self, opp) -> Dict[str, Any]:
        """执行单个套利机会

        Args:
            opp: ArbitrageOpportunity 实例

        Returns:
            执行结果字典
        """
        logger.info(
            f"执行套利: {opp.arbitrage_type.value} | "
            f"{opp.symbol} | "
            f"buy={opp.buy_exchange} sell={opp.sell_exchange} | "
            f"net={opp.net_profit_pct:.4f}%"
        )

        try:
            if self.mode == PipelineMode.SIMULATION:
                return self._simulate_execution(opp)
            else:
                return self._live_execution(opp)
        except Exception as e:
            return {"success": False, "error": str(e), "opportunity_id": opp.opportunity_id}

    def _simulate_execution(self, opp) -> Dict[str, Any]:
        """模拟执行套利

        Args:
            opp: 套利机会

        Returns:
            模拟执行结果
        """
        import random

        # 模拟交易量（基于 max_single_trade_usd）
        quantity = self.max_single_trade_usd / opp.buy_price

        # 模拟滑点（±0.05%）
        actual_buy_price = opp.buy_price * (1 + random.uniform(-0.0005, 0.0005))
        actual_sell_price = opp.sell_price * (1 + random.uniform(-0.0005, 0.0005))

        # 计算实际利润
        actual_spread_pct = (actual_sell_price - actual_buy_price) / actual_buy_price * 100
        total_fee_pct = (
            opp.fee_breakdown.get("buy_taker_fee", 0.1) +
            opp.fee_breakdown.get("sell_taker_fee", 0.1) +
            opp.fee_breakdown.get("slippage_total", 0.04) +
            opp.fee_breakdown.get("withdrawal_fee", 0.05) +
            opp.fee_breakdown.get("extra_leg_fee", 0)
        )
        actual_profit_pct = actual_spread_pct - total_fee_pct

        # 执行结果
        pnl_usd = quantity * actual_buy_price * (actual_profit_pct / 100)
        success = actual_profit_pct > 0

        # 立即平仓（套利特性：同时买卖）
        result = {
            "success": success,
            "opportunity_id": opp.opportunity_id,
            "arbitrage_type": opp.arbitrage_type.value,
            "symbol": opp.symbol,
            "buy_exchange": opp.buy_exchange,
            "sell_exchange": opp.sell_exchange,
            "buy_price": actual_buy_price,
            "sell_price": actual_sell_price,
            "quantity": quantity,
            "expected_profit_pct": opp.net_profit_pct,
            "actual_profit_pct": actual_profit_pct,
            "pnl_usd": pnl_usd,
            "fees_usd": quantity * actual_buy_price * (total_fee_pct / 100),
            "execution_mode": "simulation"
        }

        logger.info(
            f"模拟执行{'成功' if success else '失败'}: "
            f"expected={opp.net_profit_pct:.4f}% "
            f"actual={actual_profit_pct:.4f}% "
            f"pnl=${pnl_usd:.4f}"
        )

        return result

    def _live_execution(self, opp) -> Dict[str, Any]:
        """实盘执行套利（预留接口）

        Args:
            opp: 套利机会

        Returns:
            执行结果
        """
        # 实盘模式需要对接真实交易所 API
        logger.warning("实盘模式尚未对接真实交易所，降级为模拟执行")
        return self._simulate_execution(opp)

    def _stage_position_tracking(
        self,
        result: PipelineResult,
        execution_results: List[Dict[str, Any]]
    ) -> None:
        """阶段4: 持仓跟踪

        Args:
            result: 管道结果
            execution_results: 执行结果列表
        """
        result.stage = PipelineStage.POSITION_TRACKING

        for exec_res in execution_results:
            if not exec_res.get("success"):
                continue

            position = PositionRecord(
                position_id=f"pos_{uuid.uuid4().hex[:8]}",
                opportunity_id=exec_res["opportunity_id"],
                arbitrage_type=exec_res["arbitrage_type"],
                symbol=exec_res["symbol"],
                buy_exchange=exec_res["buy_exchange"],
                sell_exchange=exec_res["sell_exchange"],
                buy_price=exec_res["buy_price"],
                sell_price=exec_res["sell_price"],
                quantity=exec_res["quantity"],
                expected_profit_pct=exec_res["expected_profit_pct"],
                actual_profit_pct=exec_res["actual_profit_pct"],
                status="closed",
                opened_at=time.time(),
                closed_at=time.time()
            )

            # 套利交易通常立即平仓（同时买卖），所以直接标记为closed
            self.closed_positions.append(position)
            self.total_positions_closed += 1
            self.total_realized_pnl += exec_res.get("pnl_usd", 0)
            result.total_realized_pnl += exec_res.get("pnl_usd", 0)
            result.positions_closed += 1

            logger.info(
                f"持仓记录: {position.position_id} | "
                f"{position.symbol} | "
                f"profit={position.actual_profit_pct:.4f}% | "
                f"pnl=${exec_res.get('pnl_usd', 0):.4f}"
            )

    def _stage_knowledge_recording(
        self,
        result: PipelineResult,
        execution_results: List[Dict[str, Any]]
    ) -> None:
        """阶段5: 知识记录

        将每笔执行结果写入知识库，形成反馈闭环。

        Args:
            result: 管道结果
            execution_results: 执行结果列表
        """
        result.stage = PipelineStage.KNOWLEDGE_RECORDING

        knowledge = self._get_knowledge()
        if not knowledge:
            logger.warning("知识存储不可用，跳过知识记录")
            return

        for exec_res in execution_results:
            try:
                # 记录执行结果到知识库
                success = exec_res.get("success", False)
                arb_type = exec_res.get("arbitrage_type", "unknown")
                symbol = exec_res.get("symbol", "unknown")
                actual_pnl = exec_res.get("actual_profit_pct", 0)
                expected_pnl = exec_res.get("expected_profit_pct", 0)
                mode = exec_res.get("execution_mode", "unknown")

                outcome = "profitable" if actual_pnl > 0 else "loss"
                content = (
                    f"[arbitrage_execution] {arb_type} | "
                    f"{symbol} | "
                    f"expected={expected_pnl:.4f}% | "
                    f"actual={actual_pnl:.4f}% | "
                    f"outcome={outcome} | "
                    f"mode={mode} | "
                    f"buy={exec_res.get('buy_exchange', '?')} | "
                    f"sell={exec_res.get('sell_exchange', '?')}"
                )

                knowledge.add_memory(content)
                result.knowledge_entries += 1

                # 同时用 add_knowledge 接口记录（带分类）
                knowledge.add_knowledge(
                    category="execution_result",
                    content=(
                        f"{arb_type} {symbol}: "
                        f"expected {expected_pnl:.4f}% → actual {actual_pnl:.4f}% "
                        f"({outcome})"
                    ),
                    metadata={
                        "arbitrage_type": arb_type,
                        "symbol": symbol,
                        "profit_pct": actual_pnl,
                        "success": success
                    }
                )

            except Exception as e:
                logger.warning(f"知识记录失败: {e}")

        logger.info(f"知识记录完成: {result.knowledge_entries} 条")

    def _finalize_pipeline(
        self,
        result: PipelineResult,
        start_time: float
    ) -> PipelineResult:
        """完成管道执行，更新统计

        Args:
            result: 管道结果
            start_time: 开始时间

        Returns:
            最终管道结果
        """
        result.execution_time_ms = (time.time() - start_time) * 1000
        self.total_pipelines += 1

        # 添加到历史
        self.pipeline_history.append(result)
        if len(self.pipeline_history) > self.max_history:
            self.pipeline_history = self.pipeline_history[-self.max_history:]

        return result

    def run_batch(self, rounds: int = 5, interval_sec: float = 1.0) -> List[PipelineResult]:
        """批量运行管道

        Args:
            rounds: 运行轮数
            interval_sec: 每轮间隔秒数

        Returns:
            管道结果列表
        """
        results = []
        for i in range(rounds):
            logger.info(f"===== 批量执行 第 {i+1}/{rounds} 轮 =====")
            result = self.run_pipeline()
            results.append(result)
            if i < rounds - 1 and interval_sec > 0:
                time.sleep(interval_sec)
        return results

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """获取管道统计

        Returns:
            统计数据字典
        """
        success_pipelines = sum(
            1 for r in self.pipeline_history
            if r.stage == PipelineStage.COMPLETED
        )

        avg_pnl = (
            self.total_realized_pnl / self.total_positions_closed
            if self.total_positions_closed > 0 else 0.0
        )

        avg_profit_pct = 0.0
        if self.closed_positions:
            avg_profit_pct = sum(
                p.actual_profit_pct for p in self.closed_positions
            ) / len(self.closed_positions)

        win_rate = 0.0
        if self.closed_positions:
            wins = sum(1 for p in self.closed_positions if p.actual_profit_pct > 0)
            win_rate = wins / len(self.closed_positions)

        return {
            "version": "V16.6",
            "total_pipelines": self.total_pipelines,
            "success_pipelines": success_pipelines,
            "pipeline_success_rate": (
                success_pipelines / self.total_pipelines
                if self.total_pipelines > 0 else 0.0
            ),
            "total_opportunities_found": self.total_opportunities_found,
            "total_opportunities_executed": self.total_opportunities_executed,
            "execution_rate": (
                self.total_opportunities_executed / self.total_opportunities_found
                if self.total_opportunities_found > 0 else 0.0
            ),
            "total_positions_opened": self.total_positions_opened,
            "total_positions_closed": self.total_positions_closed,
            "total_realized_pnl": self.total_realized_pnl,
            "avg_pnl_per_trade": avg_pnl,
            "avg_profit_pct": avg_profit_pct,
            "win_rate": win_rate,
            "mode": self.mode.value,
            "active_positions": len(self.positions),
            "config": {
                "max_positions": self.max_positions,
                "max_single_trade_usd": self.max_single_trade_usd,
                "min_confidence_to_execute": self.min_confidence_to_execute,
                "min_profit_to_execute": self.min_profit_to_execute,
                "auto_execute": self.auto_execute,
                "knowledge_feedback": self.knowledge_feedback,
            },
            # V16.4 统计套利统计
            "stat_arb": {
                "total_signals": self.total_stat_arb_signals,
                "total_positions": self.total_stat_arb_positions,
                "total_pnl": self.total_stat_arb_pnl,
                "enabled": self.enable_stat_arb,
            },
            # V16.5 资金费率统计
            "funding_rate": {
                "total_signals": self.total_funding_rate_signals,
                "total_positions": self.total_funding_rate_positions,
                "total_pnl": self.total_funding_rate_pnl,
                "enabled": self.enable_funding_rate,
            },
            "adaptive_risk": {
                "enabled": self.enable_adaptive_risk,
                "params": (
                    self._adaptive_risk.get_current_params()
                    if self._adaptive_risk else None
                ),
            },
            # V16.5 组合风控
            "portfolio_risk": {
                "enabled": self.enable_portfolio_risk,
                "dashboard": (
                    self._portfolio_risk.get_risk_dashboard()
                    if self._portfolio_risk else None
                ),
            },
            # V16.6 知识桥接
            "knowledge_bridge": {
                "enabled": self.enable_knowledge_bridge,
                "total_reads": self.total_knowledge_reads,
                "total_writes": self.total_knowledge_writes,
                "total_signals_filtered": self.total_signals_filtered,
            },
        }

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的管道执行历史

        Args:
            limit: 返回数量

        Returns:
            历史记录列表
        """
        history = []
        for result in self.pipeline_history[-limit:]:
            history.append({
                "pipeline_id": result.pipeline_id,
                "stage": result.stage.value,
                "opportunities_scanned": result.opportunities_scanned,
                "opportunities_passed_risk": result.opportunities_passed_risk,
                "opportunities_executed": result.opportunities_executed,
                "positions_closed": result.positions_closed,
                "total_realized_pnl": result.total_realized_pnl,
                "knowledge_entries": result.knowledge_entries,
                "execution_time_ms": result.execution_time_ms,
                "errors": result.errors[:3],
            })
        history.reverse()
        return history


# 全局管道实例
_pipeline: Optional[ArbitragePipeline] = None


def get_arbitrage_pipeline(
    config: Optional[Dict[str, Any]] = None
) -> ArbitragePipeline:
    """获取全局套利管道实例

    Args:
        config: 配置字典

    Returns:
        套利管道实例
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = ArbitragePipeline(config)
    return _pipeline


def create_arbitrage_pipeline(
    scanner=None,
    knowledge_storage=None,
    config: Optional[Dict[str, Any]] = None,
    stat_arb_engine=None,
    price_history_manager=None,
    adaptive_risk_gate=None,
    funding_rate_engine=None,
    portfolio_risk_manager=None,
    knowledge_bridge=None,
    signal_filter=None,
    state_persistence=None
) -> ArbitragePipeline:
    """创建新的套利管道实例

    Args:
        scanner: 扫描器实例
        knowledge_storage: 知识存储实例
        config: 配置字典
        stat_arb_engine: 统计套利引擎实例 (V16.4)
        price_history_manager: 价格历史管理器实例 (V16.4)
        adaptive_risk_gate: 自适应风控实例 (V16.4)
        funding_rate_engine: 资金费率引擎实例 (V16.5)
        portfolio_risk_manager: 组合风控实例 (V16.5)
        knowledge_bridge: 知识桥接器实例 (V16.6)
        signal_filter: 信号过滤器实例 (V16.6)
        state_persistence: 状态持久化实例 (V16.6)

    Returns:
        套利管道实例
    """
    return ArbitragePipeline(
        scanner=scanner,
        knowledge_storage=knowledge_storage,
        config=config,
        stat_arb_engine=stat_arb_engine,
        price_history_manager=price_history_manager,
        adaptive_risk_gate=adaptive_risk_gate,
        funding_rate_engine=funding_rate_engine,
        portfolio_risk_manager=portfolio_risk_manager,
        knowledge_bridge=knowledge_bridge,
        signal_filter=signal_filter,
        state_persistence=state_persistence
    )


async def run_pipeline_async(
    pipeline: Optional[ArbitragePipeline] = None,
    config: Optional[Dict[str, Any]] = None,
    callback=None
) -> PipelineResult:
    """V16.5: 异步运行管道

    在后台线程中运行管道，不阻塞事件循环。

    Args:
        pipeline: 管道实例（None则创建新的）
        config: 配置（仅在创建新管道时使用）
        callback: 完成回调 callback(result)

    Returns:
        管道结果
    """
    import concurrent.futures

    if pipeline is None:
        pipeline = ArbitragePipeline(config)

    loop = asyncio.get_event_loop()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, pipeline.run_pipeline)

    if callback:
        try:
            callback(result)
        except Exception as e:
            logger.error(f"管道回调异常: {e}")

    return result


async def run_batch_async(
    rounds: int = 5,
    interval_sec: float = 1.0,
    pipeline: Optional[ArbitragePipeline] = None,
    config: Optional[Dict[str, Any]] = None
) -> List[PipelineResult]:
    """V16.5: 异步批量运行管道

    Args:
        rounds: 轮数
        interval_sec: 间隔秒
        pipeline: 管道实例
        config: 配置

    Returns:
        结果列表
    """
    if pipeline is None:
        pipeline = ArbitragePipeline(config)

    results = []
    for i in range(rounds):
        result = await run_pipeline_async(pipeline)
        results.append(result)
        if i < rounds - 1 and interval_sec > 0:
            await asyncio.sleep(interval_sec)

    return results
