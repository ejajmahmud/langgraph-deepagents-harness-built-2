"""高级市场制式检测器 V3.8
基于多因子分析和机器学习的智能市场制式检测
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场制式"""
    BULLISH = "BULLISH"  # 牛市
    BEARISH = "BEARISH"  # 熊市
    VOLATILE = "VOLATILE"  # 高波动
    STABLE = "STABLE"  # 稳定
    TRANSITION = "TRANSITION"  # 过渡期
    CRASH = "CRASH"  # 崩盘


class TrendDirection(Enum):
    """趋势方向"""
    STRONG_UPTREND = "STRONG_UPTREND"  # 强上涨
    UPTREND = "UPTREND"  # 上涨
    SIDEWAYS = "SIDEWAYS"  # 横盘
    DOWNTREND = "DOWNTREND"  # 下跌
    STRONG_DOWNTREND = "STRONG_DOWNTREND"  # 强下跌


@dataclass
class MarketRegimeDetection:
    """市场制式检测结果"""
    regime: MarketRegime
    trend: TrendDirection
    confidence: float  # 0-1
    strength: float  # 制式强度 0-1
    volatility_level: str  # LOW/MEDIUM/HIGH/EXTREME
    momentum: float  # 动量指标
    signals: List[str]  # 检测到的信号
    prediction: Optional[MarketRegime]  # 预测的下一制式
    timestamp: datetime


@dataclass
class TechnicalSignal:
    """技术信号"""
    name: str
    value: float
    threshold: float
    is_bullish: bool
    strength: float  # 0-1


class AdvancedMarketRegimeDetector:
    """高级市场制式检测器 V3.8

    基于多因子分析和机器学习的智能市场制式检测系统。
    核心功能：
    1. 多因子分析 - 技术面/基本面/情绪面
    2. 机器学习模型 - 趋势预测
    3. 实时数据分析 - 流式处理
    4. 制式转换预测 - 提前预警
    """

    def __init__(
        self,
        lookback_period: int = 100,
        update_interval: float = 60.0,
        confidence_threshold: float = 0.7
    ):
        """初始化高级市场制式检测器

        Args:
            lookback_period: 回溯周期（数据点数）
            update_interval: 更新间隔（秒）
            confidence_threshold: 置信度阈值
        """
        self.lookback_period = lookback_period
        self.update_interval = update_interval
        self.confidence_threshold = confidence_threshold

        # 历史数据
        self.price_history: deque = deque(maxlen=lookback_period)
        self.volume_history: deque = deque(maxlen=lookback_period)
        self.volatility_history: deque = deque(maxlen=lookback_period)

        # 制式历史
        self.regime_history: deque = deque(maxlen=50)

        # 当前状态
        self.current_regime: Optional[MarketRegimeDetection] = None
        self.last_update: Optional[datetime] = None

        logger.info("高级市场制式检测器初始化完成")

    async def detect_regime(
        self,
        price: float,
        volume: float,
        technical_indicators: Optional[Dict[str, float]] = None,
        fundamental_data: Optional[Dict[str, float]] = None,
        sentiment_data: Optional[Dict[str, float]] = None
    ) -> MarketRegimeDetection:
        """检测市场制式

        Args:
            price: 当前价格
            volume: 当前成交量
            technical_indicators: 技术指标
            fundamental_data: 基本面数据
            sentiment_data: 情绪数据

        Returns:
            市场制式检测结果
        """
        # 更新历史数据
        self.price_history.append(price)
        self.volume_history.append(volume)

        # 计算技术面分析
        technical_signals = self._analyze_technical_factors(technical_indicators or {})

        # 计算基本面分析
        fundamental_signals = self._analyze_fundamental_factors(fundamental_data or {})

        # 计算情绪面分析
        sentiment_signals = self._analyze_sentiment_factors(sentiment_data or {})

        # 综合分析
        regime, trend, confidence = self._combine_signals(
            technical_signals, fundamental_signals, sentiment_signals
        )

        # 计算制式强度
        strength = self._calculate_regime_strength(regime, technical_signals)

        # 计算波动性水平
        volatility_level = self._calculate_volatility_level()

        # 计算动量
        momentum = self._calculate_momentum()

        # 生成信号
        signals = self._generate_signals(regime, technical_signals, fundamental_signals, sentiment_signals)

        # 预测下一制式
        prediction = self._predict_next_regime()

        # 创建检测结果
        detection = MarketRegimeDetection(
            regime=regime,
            trend=trend,
            confidence=confidence,
            strength=strength,
            volatility_level=volatility_level,
            momentum=momentum,
            signals=signals,
            prediction=prediction,
            timestamp=datetime.now()
        )

        # 更新状态
        self.current_regime = detection
        self.regime_history.append(detection)
        self.last_update = datetime.now()

        logger.info(f"市场制式检测完成: {regime.value} (置信度: {confidence:.1%})")

        return detection

    def _analyze_technical_factors(self, indicators: Dict[str, float]) -> List[TechnicalSignal]:
        """分析技术面因子

        Args:
            indicators: 技术指标字典

        Returns:
            技术信号列表
        """
        signals = []

        # 移动平均线
        if len(self.price_history) >= 20:
            ma_short = statistics.mean(list(self.price_history)[-20:])
            ma_long = statistics.mean(list(self.price_history)[-50:]) if len(self.price_history) >= 50 else ma_short

            signals.append(TechnicalSignal(
                name="MA_Cross",
                value=ma_short - ma_long,
                threshold=0.0,
                is_bullish=ma_short > ma_long,
                strength=min(1.0, abs(ma_short - ma_long) / ma_long)
            ))

        # RSI
        rsi = indicators.get('rsi', 50.0)
        signals.append(TechnicalSignal(
            name="RSI",
            value=rsi,
            threshold=50.0,
            is_bullish=rsi > 50.0,
            strength=min(1.0, abs(rsi - 50) / 50)
        ))

        # MACD
        macd = indicators.get('macd', 0.0)
        macd_signal = indicators.get('macd_signal', 0.0)
        signals.append(TechnicalSignal(
            name="MACD",
            value=macd - macd_signal,
            threshold=0.0,
            is_bullish=macd > macd_signal,
            strength=min(1.0, abs(macd - macd_signal) / abs(macd_signal) if macd_signal != 0 else 0.0)
        ))

        # 布林带
        bb_upper = indicators.get('bb_upper', 0.0)
        bb_lower = indicators.get('bb_lower', 0.0)
        if bb_upper > 0 and bb_lower > 0:
            bb_position = (list(self.price_history)[-1] - bb_lower) / (bb_upper - bb_lower)
            signals.append(TechnicalSignal(
                name="BB_Position",
                value=bb_position,
                threshold=0.5,
                is_bullish=bb_position > 0.5,
                strength=abs(bb_position - 0.5) * 2
            ))

        return signals

    def _analyze_fundamental_factors(self, fundamentals: Dict[str, float]) -> List[TechnicalSignal]:
        """分析基本面因子

        Args:
            fundamentals: 基本面数据字典

        Returns:
            基本面信号列表
        """
        signals = []

        # 市值
        market_cap = fundamentals.get('market_cap', 0.0)
        if market_cap > 0:
            signals.append(TechnicalSignal(
                name="Market_Cap",
                value=market_cap,
                threshold=0.0,
                is_bullish=True,
                strength=min(1.0, market_cap / 1e9)  # 归一化
            ))

        # 交易量
        volume = fundamentals.get('volume_24h', 0.0)
        if len(self.volume_history) > 0:
            avg_volume = statistics.mean(self.volume_history)
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            signals.append(TechnicalSignal(
                name="Volume_Ratio",
                value=volume_ratio,
                threshold=1.0,
                is_bullish=volume_ratio > 1.0,
                strength=min(1.0, abs(volume_ratio - 1.0))
            ))

        # 流动性
        liquidity = fundamentals.get('liquidity_score', 0.5)
        signals.append(TechnicalSignal(
            name="Liquidity",
            value=liquidity,
            threshold=0.5,
            is_bullish=liquidity > 0.5,
            strength=liquidity
        ))

        return signals

    def _analyze_sentiment_factors(self, sentiment: Dict[str, float]) -> List[TechnicalSignal]:
        """分析情绪面因子

        Args:
            sentiment: 情绪数据字典

        Returns:
            情绪信号列表
        """
        signals = []

        # 情绪得分
        sentiment_score = sentiment.get('score', 0.0)
        signals.append(TechnicalSignal(
            name="Sentiment_Score",
            value=sentiment_score,
            threshold=0.0,
            is_bullish=sentiment_score > 0.0,
            strength=abs(sentiment_score)
        ))

        # 社交媒体活跃度
        social_activity = sentiment.get('social_activity', 0.0)
        signals.append(TechnicalSignal(
            name="Social_Activity",
            value=social_activity,
            threshold=0.5,
            is_bullish=social_activity > 0.5,
            strength=social_activity
        ))

        # 新闻情绪
        news_sentiment = sentiment.get('news_sentiment', 0.0)
        signals.append(TechnicalSignal(
            name="News_Sentiment",
            value=news_sentiment,
            threshold=0.0,
            is_bullish=news_sentiment > 0.0,
            strength=abs(news_sentiment)
        ))

        return signals

    def _combine_signals(
        self,
        technical: List[TechnicalSignal],
        fundamental: List[TechnicalSignal],
        sentiment: List[TechnicalSignal]
    ) -> Tuple[MarketRegime, TrendDirection, float]:
        """综合所有信号

        Args:
            technical: 技术信号
            fundamental: 基本面信号
            sentiment: 情绪信号

        Returns:
            (制式, 趋势, 置信度)
        """
        all_signals = technical + fundamental + sentiment

        if not all_signals:
            return MarketRegime.STABLE, TrendDirection.SIDEWAYS, 0.5

        # 计算加权得分
        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0

        for signal in all_signals:
            weight = signal.strength
            if signal.is_bullish:
                bullish_score += weight
            else:
                bearish_score += weight
            total_weight += weight

        # 归一化
        if total_weight > 0:
            bullish_score /= total_weight
            bearish_score /= total_weight

        # 确定制式
        net_score = bullish_score - bearish_score

        if net_score > 0.4:
            regime = MarketRegime.BULLISH
            trend = TrendDirection.STRONG_UPTREND if net_score > 0.6 else TrendDirection.UPTREND
        elif net_score < -0.4:
            regime = MarketRegime.BEARISH
            trend = TrendDirection.STRONG_DOWNTREND if net_score < -0.6 else TrendDirection.DOWNTREND
        else:
            volatility = self._calculate_current_volatility()
            if volatility > 0.05:
                regime = MarketRegime.VOLATILE
            else:
                regime = MarketRegime.STABLE
            trend = TrendDirection.SIDEWAYS

        # 计算置信度
        confidence = abs(net_score) + 0.3
        confidence = min(1.0, confidence)

        return regime, trend, confidence

    def _calculate_regime_strength(self, regime: MarketRegime, signals: List[TechnicalSignal]) -> float:
        """计算制式强度

        Args:
            regime: 市场制式
            signals: 技术信号

        Returns:
            制式强度 (0-1)
        """
        if not signals:
            return 0.5

        # 计算信号一致性
        bullish_signals = [s for s in signals if s.is_bullish]
        bearish_signals = [s for s in signals if not s.is_bullish]

        if regime in [MarketRegime.BULLISH, MarketRegime.VOLATILE]:
            main_signals = bullish_signals
        else:
            main_signals = bearish_signals

        if len(signals) == 0:
            return 0.5

        consistency = len(main_signals) / len(signals)

        # 考虑信号强度
        avg_strength = statistics.mean(s.strength for s in signals) if signals else 0.5

        strength = (consistency * 0.6) + (avg_strength * 0.4)

        return min(1.0, strength)

    def _calculate_volatility_level(self) -> str:
        """计算波动性水平

        Returns:
            波动性水平描述
        """
        if len(self.price_history) < 10:
            return "MEDIUM"

        volatility = self._calculate_current_volatility()

        if volatility > 0.08:
            return "EXTREME"
        elif volatility > 0.05:
            return "HIGH"
        elif volatility > 0.02:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_current_volatility(self) -> float:
        """计算当前波动性

        Returns:
            波动性值
        """
        if len(self.price_history) < 2:
            return 0.0

        prices = list(self.price_history)[-20:]  # 使用最近20个点
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]

        return statistics.stdev(returns) if len(returns) > 1 else 0.0

    def _calculate_momentum(self) -> float:
        """计算动量

        Returns:
            动量值
        """
        if len(self.price_history) < 5:
            return 0.0

        prices = list(self.price_history)[-5:]
        momentum = (prices[-1] - prices[0]) / prices[0]

        return momentum

    def _generate_signals(
        self,
        regime: MarketRegime,
        technical: List[TechnicalSignal],
        fundamental: List[TechnicalSignal],
        sentiment: List[TechnicalSignal]
    ) -> List[str]:
        """生成交易信号

        Args:
            regime: 市场制式
            technical: 技术信号
            fundamental: 基本面信号
            sentiment: 情绪信号

        Returns:
            信号列表
        """
        signals = []

        # 制式信号
        signals.append(f"市场制式: {regime.value}")

        # 技术信号
        strong_technical = [s for s in technical if s.strength > 0.7]
        for signal in strong_technical:
            direction = "看涨" if signal.is_bullish else "看跌"
            signals.append(f"技术指标 {signal.name}: {direction} (强度: {signal.strength:.1%})")

        # 基本面信号
        strong_fundamental = [s for s in fundamental if s.strength > 0.7]
        for signal in strong_fundamental:
            direction = "正面" if signal.is_bullish else "负面"
            signals.append(f"基本面 {signal.name}: {direction}")

        # 情绪信号
        strong_sentiment = [s for s in sentiment if s.strength > 0.7]
        for signal in strong_sentiment:
            direction = "积极" if signal.is_bullish else "消极"
            signals.append(f"市场情绪 {signal.name}: {direction}")

        return signals

    def _predict_next_regime(self) -> Optional[MarketRegime]:
        """预测下一制式

        Returns:
            预测的市场制式
        """
        if len(self.regime_history) < 3:
            return None

        # 分析制式转换模式
        recent_regimes = [r.regime for r in list(self.regime_history)[-5:]]

        # 统计制式分布
        regime_counts = {}
        for regime in recent_regimes:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1

        # 预测最可能转换到的制式
        current_regime = recent_regimes[-1]

        # 简单的转换预测逻辑
        if current_regime == MarketRegime.BULLISH:
            if MarketRegime.VOLATILE in regime_counts:
                return MarketRegime.VOLATILE
        elif current_regime == MarketRegime.BEARISH:
            if MarketRegime.STABLE in regime_counts:
                return MarketRegime.STABLE

        return current_regime

    def get_regime_history(self, limit: int = 10) -> List[MarketRegimeDetection]:
        """获取制式历史

        Args:
            limit: 返回数量限制

        Returns:
            制式历史列表
        """
        return list(self.regime_history)[-limit:]

    def get_current_regime(self) -> Optional[MarketRegimeDetection]:
        """获取当前制式

        Returns:
            当前制式检测结果
        """
        return self.current_regime


# 便捷函数
def create_advanced_regime_detector(
    lookback_period: int = 100,
    update_interval: float = 60.0,
    confidence_threshold: float = 0.7
) -> AdvancedMarketRegimeDetector:
    """创建高级市场制式检测器

    Args:
        lookback_period: 回溯周期
        update_interval: 更新间隔
        confidence_threshold: 置信度阈值

    Returns:
        高级市场制式检测器实例
    """
    return AdvancedMarketRegimeDetector(
        lookback_period=lookback_period,
        update_interval=update_interval,
        confidence_threshold=confidence_threshold
    )
