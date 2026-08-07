"""Signal Quality Scorer - V23.0 信号质量评分器

多因子风险评分系统，综合评估信号质量。

核心功能：
1. Multi-Factor Scoring — 多因子评分
2. Risk-Adjusted Scoring — 风险调整
3. Historical Performance — 历史表现
4. Market Regime Detection — 市场状态检测
5. Signal Confidence — 信号置信度计算

创建时间：2026-05-06 05:05
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SignalRating(Enum):
    """信号评级"""
    A_PLUS = "A+"   # 卓越
    A = "A"        # 优秀
    B_PLUS = "B+"  # 良好
    B = "B"        # 一般
    C = "C"        # 谨慎
    D = "D"        # 不推荐


class ScoringFactor(Enum):
    """评分因子"""
    HISTORICAL_PERFORMANCE = "historical_performance"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    SPREAD = "spread"
    CORRELATION = "correlation"
    MARKET_REGIME = "market_regime"
    RISK_REWARD = "risk_reward"
    CONFIDENCE = "confidence"


@dataclass
class SignalScore:
    """信号评分"""
    rating: SignalRating
    total_score: float  # 0-100
    breakdown: Dict[str, float] = field(default_factory=dict)
    risk_adjusted_score: float = 0.0
    confidence: float = 0.0
    recommendation: str = "execute"
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rating': self.rating.value,
            'total_score': self.total_score,
            'breakdown': self.breakdown,
            'risk_adjusted_score': self.risk_adjusted_score,
            'confidence': self.confidence,
            'recommendation': self.recommendation,
            'reasons': self.reasons,
            'warnings': self.warnings
        }


@dataclass
class ScoredSignal:
    """已评分信号"""
    signal_id: str
    symbol: str
    action: str
    entry_price: float
    target_price: float
    stop_loss: float
    score: SignalScore
    timestamp: float = field(default_factory=time.time)


class SignalQualityScorer:
    """信号质量评分器

    多因子风险评分系统。
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        portfolio_analytics=None,
        risk_manager=None
    ):
        """初始化评分器

        Args:
            config: 配置字典
            portfolio_analytics: 投资组合分析器
            risk_manager: 风险管理器
        """
        self.config = config or {}
        self.portfolio_analytics = portfolio_analytics
        self.risk_manager = risk_manager

        # 评分权重
        self.factor_weights = self.config.get('factor_weights', {
            'historical_performance': 0.25,
            'volatility': 0.15,
            'liquidity': 0.15,
            'spread': 0.10,
            'correlation': 0.10,
            'market_regime': 0.10,
            'risk_reward': 0.15,
        })

        # 评分阈值
        self.score_thresholds = self.config.get('score_thresholds', {
            'A_PLUS': 90,
            'A': 80,
            'B_PLUS': 70,
            'B': 60,
            'C': 50,
        })

        # 最小置信度
        self.min_confidence = self.config.get('min_confidence', 0.5)
        self.min_score = self.config.get('min_score', 60)

        # 信号历史
        self.signal_history: List[ScoredSignal] = []
        self.max_history = 500

    # ---------------------- 核心评分 ----------------------

    def score_signal(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        target_price: float,
        stop_loss: float,
        historical_stats: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None
    ) -> SignalScore:
        """评分信号

        Args:
            symbol: 交易对
            action: 动作 (buy/sell)
            entry_price: 入场价
            target_price: 目标价
            stop_loss: 止损价
            historical_stats: 历史统计数据
            market_data: 市场数据

        Returns:
            信号评分
        """
        # 计算各因子分数
        breakdown = {}

        # 1. 历史表现分
        breakdown['historical_performance'] = self._score_historical(
            historical_stats
        )

        # 2. 波动率分
        breakdown['volatility'] = self._score_volatility(
            market_data
        )

        # 3. 流动性分
        breakdown['liquidity'] = self._score_liquidity(
            market_data
        )

        # 4. 价差分
        breakdown['spread'] = self._score_spread(
            market_data
        )

        # 5. 相关性分
        breakdown['correlation'] = self._score_correlation(
            historical_stats
        )

        # 6. 市场状态分
        breakdown['market_regime'] = self._score_market_regime(
            market_data
        )

        # 7. 风险回报分
        breakdown['risk_reward'] = self._score_risk_reward(
            entry_price,
            target_price,
            stop_loss
        )

        # 计算总分
        total_score = self._calculate_weighted_score(breakdown)

        # 获取评级
        rating = self._get_rating(total_score)

        # 计算风险调整分
        risk_adjusted = self._calculate_risk_adjusted_score(
            total_score,
            breakdown
        )

        # 计算置信度
        confidence = self._calculate_confidence(
            total_score,
            breakdown
        )

        # 生成原因和警告
        reasons, warnings = self._generate_feedback(
            rating,
            breakdown
        )

        # 确定推荐
        recommendation = self._get_recommendation(
            total_score,
            confidence,
            rating
        )

        # 创建评分
        score = SignalScore(
            rating=rating,
            total_score=total_score,
            breakdown=breakdown,
            risk_adjusted_score=risk_adjusted,
            confidence=confidence,
            recommendation=recommendation,
            reasons=reasons,
            warnings=warnings
        )

        return score

    # ---------------------- 评分因子 ----------------------

    def _score_historical(
        self,
        stats: Optional[Dict[str, Any]]
    ) -> float:
        """历史表现评分"""
        if not stats:
            # 使用投资组合分析器
            if self.portfolio_analytics:
                metrics = self.portfolio_analytics.get_metrics()
                win_rate = metrics.win_rate

                if win_rate >= 0.6:
                    return 90
                elif win_rate >= 0.5:
                    return 75
                elif win_rate >= 0.4:
                    return 60
                else:
                    return 40

            return 50  # 默认

        # 从stats计算
        win_rate = stats.get('win_rate', 0.5)
        profit_factor = stats.get('profit_factor', 1.0)

        score = (win_rate * 50) + (min(profit_factor / 3, 1) * 50)
        return max(0, min(100, score))

    def _score_volatility(self, data: Optional[Dict[str, Any]]) -> float:
        """波动率评分"""
        if not data:
            return 50

        volatility = data.get('volatility', 0.05)

        # 低波动率 = 高分
        if volatility <= 0.02:
            return 90
        elif volatility <= 0.05:
            return 70
        elif volatility <= 0.10:
            return 50
        elif volatility <= 0.15:
            return 30
        else:
            return 15

    def _score_liquidity(self, data: Optional[Dict[str, Any]]) -> float:
        """流动性评分"""
        if not data:
            return 50

        volume = data.get('volume_24h', 0)
        if not volume:
            return 30

        # 高流动性 = 高分
        if volume >= 1_000_000_000:  # 10亿+
            return 95
        elif volume >= 100_000_000:  # 1亿+
            return 80
        elif volume >= 10_000_000:    # 1000万+
            return 60
        elif volume >= 1_000_000:     # 100万+
            return 40
        else:
            return 20

    def _score_spread(self, data: Optional[Dict[str, Any]]) -> float:
        """价差评分"""
        if not data:
            return 50

        spread = data.get('spread_pct', 0.1)

        # 小价差 = 高分
        if spread <= 0.05:
            return 90
        elif spread <= 0.1:
            return 75
        elif spread <= 0.2:
            return 60
        elif spread <= 0.5:
            return 40
        else:
            return 20

    def _score_correlation(self, stats: Optional[Dict[str, Any]]) -> float:
        """相关性评分"""
        if not stats:
            return 50

        correlation = stats.get('correlation', 0.5)

        # 低相关性 = 高分
        if abs(correlation) <= 0.2:
            return 90
        elif abs(correlation) <= 0.4:
            return 75
        elif abs(correlation) <= 0.6:
            return 60
        else:
            return 40

    def _score_market_regime(self, data: Optional[Dict[str, Any]]) -> float:
        """市场状态评分"""
        if not data:
            return 50

        regime = data.get('market_regime', 'neutral')

        if regime == 'trending':
            return 75
        elif regime == 'volatile':
            return 40
        elif regime == 'range_bound':
            return 60
        elif regime == 'quiet':
            return 70
        else:
            return 50

    def _score_risk_reward(
        self,
        entry_price: float,
        target_price: float,
        stop_loss: float
    ) -> float:
        """风险回报评分"""
        if entry_price <= 0 or stop_loss <= 0:
            return 0

        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)

        if risk <= 0:
            return 0

        ratio = reward / risk

        if ratio >= 3:
            return 95
        elif ratio >= 2:
            return 80
        elif ratio >= 1.5:
            return 65
        elif ratio >= 1:
            return 50
        elif ratio >= 0.5:
            return 30
        else:
            return 15

    # ---------------------- 辅助计算 ----------------------

    def _calculate_weighted_score(
        self,
        breakdown: Dict[str, float]
    ) -> float:
        """计算加权分数"""
        total = 0.0

        for factor, score in breakdown.items():
            weight = self.factor_weights.get(factor, 0.1)
            total += score * weight

        return total

    def _get_rating(self, score: float) -> SignalRating:
        """获取评级"""
        if score >= self.score_thresholds['A_PLUS']:
            return SignalRating.A_PLUS
        elif score >= self.score_thresholds['A']:
            return SignalRating.A
        elif score >= self.score_thresholds['B_PLUS']:
            return SignalRating.B_PLUS
        elif score >= self.score_thresholds['B']:
            return SignalRating.B
        elif score >= self.score_thresholds['C']:
            return SignalRating.C
        else:
            return SignalRating.D

    def _calculate_risk_adjusted_score(
        self,
        total: float,
        breakdown: Dict[str, float]
    ) -> float:
        """计算风险调整分数"""
        # 波动率惩罚
        vol_score = breakdown.get('volatility', 50)
        vol_penalty = (100 - vol_score) * 0.1

        # 市场状态惩罚
        regime_score = breakdown.get('market_regime', 50)
        regime_penalty = (50 - regime_score) * 0.05

        adjusted = total - vol_penalty - regime_penalty
        return max(0, min(100, adjusted))

    def _calculate_confidence(
        self,
        total: float,
        breakdown: Dict[str, float]
    ) -> float:
        """计算置信度"""
        # 基于数据完整性调整
        data_factors = sum(1 for v in breakdown.values() if v > 0)
        completeness = data_factors / len(breakdown)

        # 基于分数调整
        score_factor = total / 100

        confidence = (completeness * 0.5) + (score_factor * 0.5)
        return max(0, min(1, confidence))

    def _generate_feedback(
        self,
        rating: SignalRating,
        breakdown: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        """生成反馈"""
        reasons = []
        warnings = []

        # 生成原因
        if breakdown.get('historical_performance', 0) >= 80:
            reasons.append("历史表现优秀")
        elif breakdown.get('historical_performance', 0) < 50:
            warnings.append("历史表现不佳")

        if breakdown.get('volatility', 0) >= 70:
            reasons.append("波动率低")
        elif breakdown.get('volatility', 0) < 30:
            warnings.append("波动率高")

        if breakdown.get('liquidity', 0) >= 70:
            reasons.append("流动性好")
        elif breakdown.get('liquidity', 0) < 40:
            warnings.append("流动性不足")

        if breakdown.get('risk_reward', 0) >= 80:
            reasons.append("风险回报比优秀")

        if breakdown.get('market_regime', 0) < 40:
            warnings.append("市场状态不佳")

        return reasons, warnings

    def _get_recommendation(
        self,
        score: float,
        confidence: float,
        rating: SignalRating
    ) -> str:
        """获取推荐"""
        if rating in [SignalRating.A_PLUS, SignalRating.A]:
            if confidence >= self.min_confidence:
                return "execute"
            else:
                return "evaluate"

        elif rating == SignalRating.B_PLUS:
            if score >= self.min_score and confidence >= 0.6:
                return "execute"
            else:
                return "watch"

        elif rating == SignalRating.B:
            return "watch"

        else:
            return "skip"

    # ---------------------- 信号记录 ----------------------

    def record_scored_signal(
        self,
        signal: ScoredSignal
    ) -> None:
        """记录已评分信号"""
        self.signal_history.append(signal)
        if len(self.signal_history) > self.max_history:
            self.signal_history.pop(0)

    def get_signal_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取信号历史"""
        signals = self.signal_history[-limit:]
        return [
            {
                'signal_id': s.signal_id,
                'symbol': s.symbol,
                'action': s.action,
                'score': s.score.to_dict(),
                'timestamp': s.timestamp
            }
            for s in signals
        ]

    # ---------------------- 统计 ----------------------

    @property
    def total_signals(self) -> int:
        """总信号数"""
        return len(self.signal_history)