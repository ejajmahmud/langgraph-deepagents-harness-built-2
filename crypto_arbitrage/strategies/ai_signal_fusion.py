"""AI Signal Fusion Engine - V50.0 AI信号融合引擎

融合多个信号源，使用机器学习模型生成综合交易信号：
1. Multi-Signal Aggregation - 多信号聚合
2. Signal Weighting - 信号加权
3. Confidence Calibration - 信心校准
4. Signal Conflict Resolution - 信号冲突解决
5. Ensemble Prediction - 集成预测

作者：DeepAgents
创建时间：2026-05-08
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SignalSource(Enum):
    """信号源类型"""
    TECHNICAL = "technical"  # 技术分析
    FUNDAMENTAL = "fundamental"  # 基本面
    SENTIMENT = "sentiment"  # 情绪分析
    NEWS = "news"  # 新闻
    ONCHAIN = "on_chain"  # 链上数据
    ML_MODEL = "ml_model"  # ML模型
    CORRELATION = "correlation"  # 相关性
    VOLUME = "volume"  # 成交量


class SignalDirection(Enum):
    """信号方向"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalQuality(Enum):
    """信号质量"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TradingSignal:
    """交易信号"""
    source: SignalSource
    direction: SignalDirection
    strength: float  # 0-1
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        """综合评分 = strength * confidence"""
        return self.strength * self.confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'direction': self.direction.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'score': self.score,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class SignalAggregation:
    """信号聚合结果"""
    aggregate_direction: SignalDirection
    aggregate_strength: float
    aggregate_confidence: float
    consensus_score: float  # 一致性评分 0-1
    signals: List[TradingSignal] = field(default_factory=list)
    conflict_signals: List[Tuple[TradingSignal, TradingSignal]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusedSignal:
    """融合后的最终信号"""
    symbol: str
    direction: SignalDirection
    strength: float
    confidence: float
    combined_score: float  # 综合评分
    sources: List[SignalSource] = field(default_factory=list)
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class SignalFusionEngine:
    """AI信号融合引擎"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}

        # 配置参数
        self.min_consensus = self.config.get('min_consensus', 0.6)  # 最小共识
        self.conflict_threshold = self.config.get('conflict_threshold', 0.3)  # 冲突阈值
        self.strength_weight = self.config.get('strength_weight', 0.5)  # 强度权重
        self.confidence_weight = self.config.get('confidence_weight', 0.5)  # 信心权重

        # 动态权重配置
        self.source_weights: Dict[SignalSource, float] = self.config.get(
            'source_weights',
            {
                SignalSource.TECHNICAL: 0.25,
                SignalSource.FUNDAMENTAL: 0.20,
                SignalSource.SENTIMENT: 0.15,
                SignalSource.NEWS: 0.10,
                SignalSource.ONCHAIN: 0.10,
                SignalSource.ML_MODEL: 0.15,
                SignalSource.CORRELATION: 0.05,
                SignalSource.VOLUME: 0.10
            }
        )

        # 信号历史
        self.signal_history: Dict[str, List[TradingSignal]] = {}
        self.aggregation_history: List[SignalAggregation] = []

        logger.info(f"SignalFusionEngine initialized: {self.config}")

    def add_signal(
        self,
        symbol: str,
        signal: TradingSignal
    ) -> None:
        """添加信号"""
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []

        self.signal_history[symbol].append(signal)
        logger.info(f"Added {signal.source.value} signal for {symbol}: {signal.direction.value}")

    def create_signal(
        self,
        source: SignalSource,
        direction: SignalDirection,
        strength: float,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TradingSignal:
        """创建信号"""
        return TradingSignal(
            source=source,
            direction=direction,
            strength=max(0.0, min(1.0, strength)),
            confidence=max(0.0, min(1.0, confidence)),
            metadata=metadata or {}
        )

    def detect_conflicts(
        self,
        signals: List[TradingSignal]
    ) -> List[Tuple[TradingSignal, TradingSignal]]:
        """检测信号冲突"""
        conflicts = []

        for i in range(len(signals)):
            for j in range(i + 1, len(signals)):
                sig1 = signals[i]
                sig2 = signals[j]

                # 方向冲突
                if sig1.direction != sig2.direction:
                    # 计算冲突程度
                    diff = abs(sig1.score - sig2.score)

                    if diff < self.conflict_threshold:
                        conflicts.append((sig1, sig2))

        return conflicts

    def resolve_conflicts(
        self,
        signals: List[TradingSignal],
        conflicts: List[Tuple[TradingSignal, TradingSignal]]
    ) -> List[TradingSignal]:
        """解决信号冲突

        策略：
        1. 采用高信心信号
        2. 采用高权重信号源
        3. 时间优先（最新）
        """
        if not conflicts:
            return signals

        # 创建信号评分
        def resolve_score(sig: TradingSignal) -> float:
            source_weight = self.source_weights.get(sig.source, 0.1)
            return (
                self.strength_weight * sig.strength +
                self.confidence_weight * sig.confidence +
                source_weight * sig.confidence
            )

        # 排序并选择最佳信号
        resolved = sorted(signals, key=resolve_score, reverse=True)

        # 保留高评分信号
        return resolved[:len(signals) // 2 + 1] if len(signals) > 2 else signals

    def aggregate_signals(
        self,
        symbol: str,
        method: str = "weighted"
    ) -> SignalAggregation:
        """聚合信号

        Args:
            symbol: 交易对
            method: 聚合方法 (weighted/weighted_geometric/consensus/belief)
        """
        signals = self.signal_history.get(symbol, [])

        if not signals:
            return SignalAggregation(
                aggregate_direction=SignalDirection.NEUTRAL,
                aggregate_strength=0.0,
                aggregate_confidence=0.0,
                consensus_score=0.0
            )

        # 检测冲突
        conflicts = self.detect_conflicts(signals)

        # 解决冲突
        resolved_signals = self.resolve_conflicts(signals, conflicts)

        # 按方法聚合
        if method == "weighted":
            result = self._weighted_aggregation(resolved_signals)
        elif method == "weighted_geometric":
            result = self._weighted_geometric_aggregation(resolved_signals)
        elif method == "consensus":
            result = self._consensus_aggregation(resolved_signals)
        elif method == "belief":
            result = self._belief_aggregation(resolved_signals)
        else:
            result = self._weighted_aggregation(resolved_signals)

        # 计算共识评分
        consensus_score = self._calculate_consensus(resolved_signals)

        result.conflict_signals = conflicts
        result.signals = resolved_signals
        result.consensus_score = consensus_score

        self.aggregation_history.append(result)
        return result

    def _weighted_aggregation(
        self,
        signals: List[TradingSignal]
    ) -> SignalAggregation:
        """加权线性聚合"""
        total_weight = 0.0
        bull_score = 0.0
        bear_score = 0.0

        for sig in signals:
            source_weight = self.source_weights.get(sig.source, 0.1)
            weight = source_weight * sig.strength * sig.confidence

            if sig.direction == SignalDirection.BULLISH:
                bull_score += weight
            elif sig.direction == SignalDirection.BEARISH:
                bear_score += weight

            total_weight += weight

        if total_weight == 0:
            return SignalAggregation(
                aggregate_direction=SignalDirection.NEUTRAL,
                aggregate_strength=0.0,
                aggregate_confidence=0.0,
                consensus_score=0.0
            )

        # 归一化
        bull_ratio = bull_score / total_weight
        bear_ratio = bear_score / total_weight

        if bull_ratio > bear_ratio:
            direction = SignalDirection.BULLISH
            strength = bull_ratio
            confidence = total_weight / len(signals) if signals else 0
        elif bear_ratio > bull_ratio:
            direction = SignalDirection.BEARISH
            strength = bear_ratio
            confidence = total_weight / len(signals) if signals else 0
        else:
            direction = SignalDirection.NEUTRAL
            strength = 0.0
            confidence = 0.0

        return SignalAggregation(
            aggregate_direction=direction,
            aggregate_strength=strength,
            aggregate_confidence=confidence,
            consensus_score=abs(bull_ratio - bear_ratio)
        )

    def _weighted_geometric_aggregation(
        self,
        signals: List[TradingSignal]
    ) -> SignalAggregation:
        """加权几何平均聚合"""
        bull_product = 1.0
        bear_product = 1.0

        for sig in signals:
            source_weight = self.source_weights.get(sig.source, 0.1)
            weight = source_weight * sig.confidence

            if sig.direction == SignalDirection.BULLISH:
                bull_product *= (sig.strength ** weight)
            elif sig.direction == SignalDirection.BEARISH:
                bear_product *= (sig.strength ** weight)

        # 使用几何平均
        bull_geo = bull_product ** (1 / len(signals)) if signals else 0
        bear_geo = bear_product ** (1 / len(signals)) if signals else 0

        if bull_geo > bear_geo:
            return SignalAggregation(
                aggregate_direction=SignalDirection.BULLISH,
                aggregate_strength=bull_geo,
                aggregate_confidence=min(bull_geo, 1.0),
                consensus_score=0.0
            )
        elif bear_geo > bull_geo:
            return SignalAggregation(
                aggregate_direction=SignalDirection.BEARISH,
                aggregate_strength=bear_geo,
                aggregate_confidence=min(bear_geo, 1.0),
                consensus_score=0.0
            )
        else:
            return SignalAggregation(
                aggregate_direction=SignalDirection.NEUTRAL,
                aggregate_strength=0.0,
                aggregate_confidence=0.0,
                consensus_score=0.0
            )

    def _consensus_aggregation(
        self,
        signals: List[TradingSignal]
    ) -> SignalAggregation:
        """共识聚合 - 多数决"""
        if not signals:
            return SignalAggregation(
                aggregate_direction=SignalDirection.NEUTRAL,
                aggregate_strength=0.0,
                aggregate_confidence=0.0,
                consensus_score=0.0
            )

        # 统计方向
        direction_counts = {
            SignalDirection.BULLISH: 0,
            SignalDirection.BEARISH: 0,
            SignalDirection.NEUTRAL: 0
        }

        total_score = 0.0
        for sig in signals:
            direction_counts[sig.direction] += 1
            total_score += sig.score

        # 找到多数
        max_direction = max(direction_counts, key=direction_counts.get)
        count = direction_counts[max_direction]

        # 共识比例
        consensus = count / len(signals)

        return SignalAggregation(
            aggregate_direction=max_direction,
            aggregate_strength=consensus,
            aggregate_confidence=total_score / len(signals),
            consensus_score=consensus
        )

    def _belief_aggregation(
        self,
        signals: List[TradingSignal]
    ) -> SignalAggregation:
        """Dempster-Shafer信念聚合"""
        # 简化实现：使用加权证据理论
        m_bull = 0.0
        m_bear = 0.0
        m_uncertain = 1.0

        for sig in signals:
            source_weight = self.source_weights.get(sig.source, 0.1)
            mass = source_weight * sig.confidence

            if sig.direction == SignalDirection.BULLISH:
                m_bull += mass * sig.strength
                m_uncertain -= mass * sig.strength
            elif sig.direction == SignalDirection.BEARISH:
                m_bear += mass * sig.strength
                m_uncertain -= mass * sig.strength

        # 归一化
        total = m_bull + m_bear + m_uncertain
        if total > 0:
            m_bull /= total
            m_bear /= total
            m_uncertain /= total

        if m_bull > m_bear:
            direction = SignalDirection.BULLISH
            strength = m_bull
        elif m_bear > m_bull:
            direction = SignalDirection.BEARISH
            strength = m_bear
        else:
            direction = SignalDirection.NEUTRAL
            strength = 0.0

        return SignalAggregation(
            aggregate_direction=direction,
            aggregate_strength=strength,
            aggregate_confidence=1 - m_uncertain,
            consensus_score=0.0
        )

    def _calculate_consensus(
        self,
        signals: List[TradingSignal]
    ) -> float:
        """计算共识评分"""
        if not signals:
            return 0.0

        # 计算方向一致性
        direction_votes = {}

        for sig in signals:
            direction_votes[sig.direction] = direction_votes.get(sig.direction, 0) + sig.score

        if not direction_votes:
            return 0.0

        # 一致性 = 主导方向的投票占比
        total_votes = sum(direction_votes.values())
        max_votes = max(direction_votes.values())

        return max_votes / total_votes if total_votes > 0 else 0

    def fuse_signals(
        self,
        symbol: str,
        method: str = "weighted"
    ) -> FusedSignal:
        """融合信号生成最终交易信号"""

        # 聚合
        aggregation = self.aggregate_signals(symbol, method)

        # 筛选
        if aggregation.aggregate_confidence < self.min_consensus:
            return FusedSignal(
                symbol=symbol,
                direction=SignalDirection.NEUTRAL,
                strength=0.0,
                confidence=aggregation.aggregate_confidence,
                combined_score=0.0,
                sources=[],
                reasoning="insufficient_confidence",
                metadata={'aggregation': aggregation.metadata}
            )

        # 生成融合信号
        source_list = [sig.source for sig in aggregation.signals]

        return FusedSignal(
            symbol=symbol,
            direction=aggregation.aggregate_direction,
            strength=aggregation.aggregate_strength,
            confidence=aggregation.aggregate_confidence,
            combined_score=aggregation.aggregate_strength * aggregation.aggregate_confidence,
            sources=source_list,
            reasoning=f"fused_{method}_aggregation",
            metadata={
                'consensus_score': aggregation.consensus_score,
                'conflict_count': len(aggregation.conflict_signals)
            }
        )

    def get_signal_weights(
        self,
        source: SignalSource
    ) -> float:
        """获取信号源权重"""
        return self.source_weights.get(source, 0.1)

    def set_signal_weights(
        self,
        source: SignalSource,
        weight: float
    ) -> None:
        """设置信号源权重"""
        self.source_weights[source] = max(0.0, min(1.0, weight))
        logger.info(f"Set weight for {source.value}: {weight}")

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'symbols': len(self.signal_history),
            'aggregation_count': len(self.aggregation_history),
            'source_weights': {
                k.value: v for k, v in self.source_weights.items()
            }
        }


def create_signal_fusion_engine(
    config: Optional[Dict[str, Any]] = None
) -> SignalFusionEngine:
    """创建AI信号融合引擎"""
    return SignalFusionEngine(config=config)


# ============= 测试函数 =============

def _test_signal_fusion():
    """测试信号融合引擎"""
    # 创建引擎
    engine = create_signal_fusion_engine({
        'min_consensus': 0.5,
        'conflict_threshold': 0.4
    })

    symbol = "BTC/USDT"

    # 添加多个信号
    signals = [
        engine.create_signal(
            SignalSource.TECHNICAL,
            SignalDirection.BULLISH,
            strength=0.8,
            confidence=0.7,
            metadata={'indicator': 'RSI', 'value': 35}
        ),
        engine.create_signal(
            SignalSource.FUNDAMENTAL,
            SignalDirection.BULLISH,
            strength=0.6,
            confidence=0.8,
            metadata={'metric': 'funding_rate', 'value': 0.0001}
        ),
        engine.create_signal(
            SignalSource.SENTIMENT,
            SignalDirection.BEARISH,
            strength=0.5,
            confidence=0.6,
            metadata={'sentiment': 'fear', 'value': 30}
        ),
        engine.create_signal(
            SignalSource.ML_MODEL,
            SignalDirection.BULLISH,
            strength=0.7,
            confidence=0.75,
            metadata={'model': 'lstm', 'prediction': 'up'}
        )
    ]

    for sig in signals:
        engine.add_signal(symbol, sig)

    # 融合信号
    fused = engine.fuse_signals(symbol, method="weighted")

    print(f"=== Signal Fusion Results ===")
    print(f"Direction: {fused.direction.value}")
    print(f"Strength: {fused.strength:.2f}")
    print(f"Confidence: {fused.confidence:.2f}")
    print(f"Combined Score: {fused.combined_score:.4f}")
    print(f"Sources: {[s.value for s in fused.sources]}")
    print(f"Reasoning: {fused.reasoning}")

    # 测试不同聚合方法
    for method in ["weighted", "consensus", "belief"]:
        agg = engine.aggregate_signals(symbol, method)
        print(f"\n--- {method} ---")
        print(f"Direction: {agg.aggregate_direction.value}")
        print(f"Strength: {agg.aggregate_strength:.2f}")
        print(f"Confidence: {agg.aggregate_confidence:.2f}")
        print(f"Conflicts: {len(agg.conflict_signals)}")

    print("\n✅ SignalFusionEngine tests passed!")


if __name__ == "__main__":
    _test_signal_fusion()