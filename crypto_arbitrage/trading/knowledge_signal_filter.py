"""知识驱动信号过滤器 V16.6

基于历史知识库中的交易数据，对交易信号进行二次过滤：
1. 历史胜率过滤 — 跳过历史胜率低的币种/交易所/策略组合
2. 近期亏损回避 — 近期连续亏损时降低仓位或拒绝信号
3. 时段性能过滤 — 根据不同时段的历史表现加权
4. 信号去重 — 避免短时间内重复发出相同信号

与TradingKnowledgeBridge协作，通过知识库历史数据提升信号质量。

架构位置:
    Signal Source (Scanner/Engine)
           ↓
    KnowledgeDrivenSignalFilter V16.6  ←── TradingKnowledgeBridge
           ↓ (过滤/加权后的信号)
    ArbitragePipeline V16.6

创建时间：2026-05-05
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FilterAction(Enum):
    """过滤动作"""
    PASS = "pass"                  # 通过
    REDUCE_CONFIDENCE = "reduce"   # 降低置信度
    REDUCE_SIZE = "reduce_size"    # 降低仓位
    REJECT = "reject"              # 拒绝
    DELAY = "delay"                # 延迟（去重冷却期）


@dataclass
class FilterResult:
    """过滤结果"""
    action: FilterAction
    original_confidence: float
    adjusted_confidence: float
    original_size_usd: float
    adjusted_size_usd: float
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalFingerprint:
    """信号指纹（用于去重）"""
    signal_type: str
    symbol: str
    exchange: str
    side: str

    def __hash__(self):
        return hash((self.signal_type, self.symbol, self.exchange, self.side))

    def __eq__(self, other):
        if not isinstance(other, SignalFingerprint):
            return False
        return (
            self.signal_type == other.signal_type and
            self.symbol == other.symbol and
            self.exchange == other.exchange and
            self.side == other.side
        )


class KnowledgeDrivenSignalFilter:
    """知识驱动信号过滤器 V16.6

    基于知识库中的历史数据，对交易信号进行多维度过滤和加权。
    """

    def __init__(
        self,
        knowledge_bridge=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化信号过滤器

        Args:
            knowledge_bridge: TradingKnowledgeBridge实例
            config: 配置字典
        """
        self._bridge = knowledge_bridge
        self.config = config or {}

        # 过滤参数
        self.min_symbol_win_rate = self.config.get("min_symbol_win_rate", 0.3)
        self.min_strategy_win_rate = self.config.get("min_strategy_win_rate", 0.25)
        self.max_recent_losses = self.config.get("max_recent_losses", 3)
        self.dedup_cooldown_sec = self.config.get("dedup_cooldown_sec", 60.0)
        self.confidence_decay_per_loss = self.config.get(
            "confidence_decay_per_loss", 0.1
        )
        self.size_reduction_factor = self.config.get("size_reduction_factor", 0.5)

        # 启用/禁用过滤器
        self.enable_history_filter = self.config.get("enable_history_filter", True)
        self.enable_loss_avoidance = self.config.get("enable_loss_avoidance", True)
        self.enable_dedup = self.config.get("enable_dedup", True)
        self.enable_symbol_filter = self.config.get("enable_symbol_filter", True)

        # 信号去重缓存
        self._recent_signals: Dict[SignalFingerprint, float] = {}

        # 近期亏损追踪
        self._recent_losses: List[Dict[str, Any]] = []

        # 统计
        self.total_signals_received = 0
        self.total_signals_passed = 0
        self.total_signals_reduced = 0
        self.total_signals_rejected = 0
        self.total_signals_delayed = 0
        self.filter_reasons: Dict[str, int] = defaultdict(int)

        logger.info(
            f"知识驱动信号过滤器 V16.6 初始化: "
            f"history={'ON' if self.enable_history_filter else 'OFF'}, "
            f"loss_avoid={'ON' if self.enable_loss_avoidance else 'OFF'}, "
            f"dedup={'ON' if self.enable_dedup else 'OFF'}"
        )

    def _get_bridge(self):
        """延迟获取知识桥接器"""
        if self._bridge is not None:
            return self._bridge
        try:
            from trading.trading_knowledge_bridge import get_trading_knowledge_bridge
            self._bridge = get_trading_knowledge_bridge()
            return self._bridge
        except Exception as e:
            logger.debug(f"知识桥接器不可用: {e}")
            return None

    def filter_signal(
        self,
        signal_type: str,
        symbol: str,
        exchange: str,
        side: str,
        confidence: float,
        size_usd: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FilterResult:
        """过滤交易信号

        依次执行多维度过滤，返回过滤结果。

        Args:
            signal_type: 信号类型 (cross_exchange/triangular/statistical/funding_rate)
            symbol: 交易对
            exchange: 交易所
            side: 方向
            confidence: 原始置信度
            size_usd: 原始仓位大小
            metadata: 额外元数据

        Returns:
            过滤结果
        """
        self.total_signals_received += 1

        result = FilterResult(
            action=FilterAction.PASS,
            original_confidence=confidence,
            adjusted_confidence=confidence,
            original_size_usd=size_usd,
            adjusted_size_usd=size_usd,
        )

        # 1. 去重检查
        if self.enable_dedup:
            dedup_result = self._check_dedup(signal_type, symbol, exchange, side)
            if dedup_result is not None:
                result.action = FilterAction.DELAY
                result.reasons.append(dedup_result)
                self.total_signals_delayed += 1
                self.filter_reasons["dedup"] += 1
                return result

        # 2. 币种历史过滤
        if self.enable_symbol_filter:
            symbol_result = self._check_symbol_history(symbol)
            if symbol_result:
                result.reasons.append(symbol_result)
                # 降低置信度
                result.adjusted_confidence *= 0.8

        # 3. 策略历史过滤
        if self.enable_history_filter:
            strategy_result = self._check_strategy_history(signal_type)
            if strategy_result:
                result.reasons.append(strategy_result)
                result.adjusted_confidence *= 0.85

        # 4. 近期亏损回避
        if self.enable_loss_avoidance:
            loss_result = self._check_recent_losses(symbol, signal_type)
            if loss_result:
                result.reasons.append(loss_result)
                # 根据连续亏损数降低置信度
                recent_loss_count = self._count_recent_losses(symbol, signal_type)
                decay = 1.0 - (recent_loss_count * self.confidence_decay_per_loss)
                result.adjusted_confidence *= max(0.1, decay)

        # 5. 根据调整后的置信度决定最终动作
        if result.adjusted_confidence < 0.2:
            result.action = FilterAction.REJECT
            result.adjusted_size_usd = 0.0
            self.total_signals_rejected += 1
            self.filter_reasons["low_confidence"] += 1
        elif result.adjusted_confidence < 0.4:
            result.action = FilterAction.REDUCE_SIZE
            result.adjusted_size_usd *= self.size_reduction_factor
            self.total_signals_reduced += 1
            self.filter_reasons["reduced_size"] += 1
        elif result.adjusted_confidence < result.original_confidence * 0.8:
            result.action = FilterAction.REDUCE_CONFIDENCE
            self.total_signals_reduced += 1
            self.filter_reasons["reduced_confidence"] += 1
        else:
            self.total_signals_passed += 1

        # 记录到去重缓存
        if result.action != FilterAction.DELAY:
            fingerprint = SignalFingerprint(signal_type, symbol, exchange, side)
            self._recent_signals[fingerprint] = time.time()

        if result.reasons:
            logger.info(
                f"信号过滤: {signal_type} {symbol} → {result.action.value} | "
                f"conf={result.original_confidence:.2f}→{result.adjusted_confidence:.2f} | "
                f"reasons={'; '.join(result.reasons)}"
            )

        return result

    def notify_trade_result(
        self,
        symbol: str,
        strategy: str,
        pnl_usd: float,
        outcome: str
    ) -> None:
        """通知交易结果（用于更新近期亏损追踪）

        Args:
            symbol: 交易对
            strategy: 策略名称
            pnl_usd: 盈亏金额
            outcome: 结果
        """
        if pnl_usd < 0:
            self._recent_losses.append({
                "symbol": symbol,
                "strategy": strategy,
                "pnl_usd": pnl_usd,
                "outcome": outcome,
                "timestamp": time.time(),
            })
            # 只保留最近20个亏损记录
            if len(self._recent_losses) > 20:
                self._recent_losses = self._recent_losses[-20:]

    def _check_dedup(
        self,
        signal_type: str,
        symbol: str,
        exchange: str,
        side: str
    ) -> Optional[str]:
        """去重检查

        Returns:
            拒绝原因，None表示通过
        """
        fingerprint = SignalFingerprint(signal_type, symbol, exchange, side)
        last_seen = self._recent_signals.get(fingerprint)

        if last_seen is not None:
            elapsed = time.time() - last_seen
            if elapsed < self.dedup_cooldown_sec:
                remaining = self.dedup_cooldown_sec - elapsed
                return f"信号去重: 冷却中 {remaining:.0f}s"

        return None

    def _check_symbol_history(self, symbol: str) -> Optional[str]:
        """检查币种历史表现

        Returns:
            警告原因，None表示通过
        """
        bridge = self._get_bridge()
        if bridge is None:
            return None

        try:
            history = bridge.get_symbol_history(symbol)
            if not history or history.get("trades_found", 0) < 3:
                return None

            win_rate = history.get("win_rate", 0.5)
            if win_rate < self.min_symbol_win_rate:
                return f"币种胜率低: {symbol} {win_rate:.1%} < {self.min_symbol_win_rate:.1%}"

            return None

        except Exception as e:
            logger.debug(f"币种历史检查失败: {e}")
            return None

    def _check_strategy_history(self, strategy: str) -> Optional[str]:
        """检查策略历史表现

        Returns:
            警告原因，None表示通过
        """
        bridge = self._get_bridge()
        if bridge is None:
            return None

        try:
            insight = bridge.get_strategy_insight(strategy)
            if insight is None:
                return None

            if insight.win_rate < self.min_strategy_win_rate:
                return (
                    f"策略胜率低: {strategy} {insight.win_rate:.1%} "
                    f"< {self.min_strategy_win_rate:.1%}"
                )

            if insight.trend == "declining" and insight.recommendation == "decrease":
                return f"策略趋势下降: {strategy}"

            return None

        except Exception as e:
            logger.debug(f"策略历史检查失败: {e}")
            return None

    def _check_recent_losses(
        self,
        symbol: str,
        strategy: str
    ) -> Optional[str]:
        """检查近期亏损

        Returns:
            警告原因，None表示通过
        """
        count = self._count_recent_losses(symbol, strategy)
        if count >= self.max_recent_losses:
            return f"近期连续亏损: {count}次 ≥ {self.max_recent_losses}"
        return None

    def _count_recent_losses(
        self,
        symbol: str,
        strategy: str,
        window_sec: float = 3600.0
    ) -> int:
        """计算近期亏损次数

        Args:
            symbol: 交易对
            strategy: 策略
            window_sec: 时间窗口（秒）

        Returns:
            近期亏损次数
        """
        now = time.time()
        count = 0
        for loss in self._recent_losses:
            if now - loss["timestamp"] > window_sec:
                continue
            # 同币种或同策略的亏损
            if loss["symbol"] == symbol or loss["strategy"] == strategy:
                count += 1
        return count

    def cleanup_expired_signals(self) -> int:
        """清理过期的去重缓存条目

        Returns:
            清理数量
        """
        now = time.time()
        expired = [
            fp for fp, ts in self._recent_signals.items()
            if now - ts > self.dedup_cooldown_sec * 3
        ]
        for fp in expired:
            del self._recent_signals[fp]

        return len(expired)

    def get_filter_statistics(self) -> Dict[str, Any]:
        """获取过滤器统计

        Returns:
            统计字典
        """
        total = self.total_signals_received
        return {
            "version": "V16.6",
            "total_received": total,
            "total_passed": self.total_signals_passed,
            "total_reduced": self.total_signals_reduced,
            "total_rejected": self.total_signals_rejected,
            "total_delayed": self.total_signals_delayed,
            "pass_rate": (
                self.total_signals_passed / total if total > 0 else 0.0
            ),
            "reject_rate": (
                self.total_signals_rejected / total if total > 0 else 0.0
            ),
            "dedup_cache_size": len(self._recent_signals),
            "recent_losses_tracked": len(self._recent_losses),
            "filter_reasons": dict(self.filter_reasons),
            "config": {
                "min_symbol_win_rate": self.min_symbol_win_rate,
                "min_strategy_win_rate": self.min_strategy_win_rate,
                "max_recent_losses": self.max_recent_losses,
                "dedup_cooldown_sec": self.dedup_cooldown_sec,
            },
        }


# 全局实例
_signal_filter: Optional[KnowledgeDrivenSignalFilter] = None


def get_knowledge_signal_filter(
    knowledge_bridge=None,
    config: Optional[Dict[str, Any]] = None
) -> KnowledgeDrivenSignalFilter:
    """获取全局信号过滤器实例

    Args:
        knowledge_bridge: 知识桥接器
        config: 配置字典

    Returns:
        信号过滤器实例
    """
    global _signal_filter
    if _signal_filter is None:
        _signal_filter = KnowledgeDrivenSignalFilter(knowledge_bridge, config)
    return _signal_filter
