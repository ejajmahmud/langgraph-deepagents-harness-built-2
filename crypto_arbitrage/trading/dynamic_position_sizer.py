"""Dynamic Position Sizer - V22.0 动态仓位管理器

根据实时性能和市场状况动态调整仓位大小。

核心功能：
1. Kelly Criterion — 基于胜率动态计算最优仓位
2. Drawdown Adjusted — 回撤时自动减仓
3. Volatility Adjusted — 波动率调整
4. Performance Based — 基于近期表现调整
5. Risk Limits — 动态风险限制

创建时间：2026-05-06 04:35
"""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SizingStrategy(Enum):
    """仓位策略"""
    FIXED = "fixed"
    KELLY = "kelly"
    HALF_KELLY = "half_kelly"
    Fractions_KELLY = "fractional_kelly"
    VOLATILITY = "volatility"
    DRAWDOWN = "drawdown"
    ADAPTIVE = "adaptive"


@dataclass
class PositionSizeResult:
    """仓位计算结果"""
    recommended_size: float
    base_size: float
    multiplier: float
    strategy: str
    confidence: float
    reason: str
    kelly_pct: float = 0.0
    drawdown_factor: float = 1.0
    volatility_factor: float = 1.0
    performance_factor: float = 1.0


class DynamicPositionSizer:
    """动态仓位管理器

    根据实时性能和市场状况动态调整仓位大小。
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        portfolio_analytics=None
    ):
        """初始化动态仓位管理器

        Args:
            config: 配置字典
            portfolio_analytics: 投资组合分析器实例
        """
        self.config = config or {}
        self.portfolio_analytics = portfolio_analytics

        # 基础配置
        self.base_position_size = self.config.get('base_position_size', 1000.0)
        self.max_position_size = self.config.get('max_position_size', 10000.0)
        self.min_position_size = self.config.get('min_position_size', 100.0)

        # Kelly配置
        self.kelly_fraction = self.config.get('kelly_fraction', 0.5)  # 半Kelly
        self.max_kelly_pct = self.config.get('max_kelly_pct', 0.25)  # 最大25%

        # 回撤配置
        self.drawdown_reduction_levels = self.config.get('drawdown_reduction_levels', {
            5.0: 0.8,    # 5%回撤 → 80%仓位
            10.0: 0.6,   # 10%回撤 → 60%仓位
            15.0: 0.4,   # 15%回撤 → 40%仓位
            20.0: 0.2,   # 20%回撤 → 20%仓位
        })

        # 波动率配置
        self.volatility_reduction_levels = self.config.get('volatility_reduction_levels', {
            0.02: 1.0,    # 2%波动率 → 100%
            0.05: 0.8,    # 5%波动率 → 80%
            0.10: 0.6,   # 10%波动率 → 60%
            0.15: 0.4,    # 15%波动率 → 40%
        })

        # 胜率配置
        self.win_rate_thresholds = self.config.get('win_rate_thresholds', {
            0.3: 0.5,   # 30%胜率 → 50%仓位
            0.4: 0.7,   # 40%胜率 → 70%仓位
            0.5: 0.9,   # 50%胜率 → 90%仓位
            0.6: 1.0,   # 60%胜率 → 100%仓位
        })

        # 默认策略
        self.default_strategy = SizingStrategy(
            self.config.get('default_strategy', 'adaptive')
        )

        # 统计
        self.calculation_history: List[PositionSizeResult] = []
        self.max_history = 100

    # ---------------------- 核心计算 ----------------------

    def calculate_position_size(
        self,
        strategy: str = "adaptive",
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        current_drawdown: Optional[float] = None,
        volatility: Optional[float] = None,
        confidence: float = 0.5,
        timestamp: Optional[float] = None
    ) -> PositionSizeResult:
        """计算推荐仓位

        Args:
            strategy: 策略类型
            win_rate: 胜率 (0-1)
            avg_win: 平均盈利
            avg_loss: 平均亏损（绝对值）
            current_drawdown: 当前回撤百分比
            volatility: 波动率
            confidence: 信号置信度
            timestamp: 时间戳

        Returns:
            仓位计算结果
        """
        ts = timestamp or time.time()

        # 获取性能数据
        if self.portfolio_analytics and not win_rate:
            metrics = self.portfolio_analytics.get_metrics()
            win_rate = metrics.win_rate
            avg_win = metrics.avg_win or 100.0
            avg_loss = abs(metrics.avg_loss) or 50.0

        # 默认值
        win_rate = win_rate or 0.5
        avg_win = avg_win or 100.0
        avg_loss = avg_loss or 50.0

        # 获取回撤
        if self.portfolio_analytics and current_drawdown is None:
            current_drawdown = self.portfolio_analytics.calculate_current_drawdown()

        current_drawdown = current_drawdown or 0.0

        # 计算各因素
        kelly_pct = self._calculate_kelly(win_rate, avg_win, avg_loss)
        drawdown_factor = self._calculate_drawdown_factor(current_drawdown)
        volatility_factor = self._calculate_volatility_factor(volatility or 0.02)
        performance_factor = self._calculate_performance_factor(win_rate)

        # 计算最终仓位
        base_size = self.base_position_size

        if strategy == "fixed":
            multiplier = 1.0
            reason = "Fixed position size"

        elif strategy == "kelly":
            kelly_frac = min(kelly_pct, self.max_kelly_pct)
            multiplier = kelly_frac * 100  # 转换为倍数
            reason = f"KellyCriterion: {kelly_pct*100:.1f}%"

        elif strategy == "half_kelly":
            kelly_frac = min(kelly_pct * self.kelly_fraction, self.max_kelly_pct)
            multiplier = kelly_frac * 100
            reason = f"HalfKelly: {kelly_pct*50:.1f}%"

        elif strategy == "fractional_kelly":
            kelly_frac = min(kelly_pct * self.kelly_fraction, self.max_kelly_pct)
            multiplier = kelly_frac * 100
            reason = f"FractionalKelly: {kelly_pct*100*self.kelly_fraction:.1f}%"

        elif strategy == "volatility":
            multiplier = volatility_factor
            reason = f"Volatility: {volatility_factor:.2f}x"

        elif strategy == "drawdown":
            multiplier = drawdown_factor
            reason = f"Drawdown: {drawdown_factor:.2f}x at {current_drawdown:.1f}%"

        elif strategy == "adaptive":
            # 综合所有因素
            multiplier = (
                min(kelly_pct * 2, 1.0) *
                drawdown_factor *
                volatility_factor *
                performance_factor
            )
            multiplier = max(multiplier, 0.1)  # 最小10%
            reason = f"Adaptive: Kelly*{drawdown_factor:.1f}*{volatility_factor:.1f}*{performance_factor:.1f}"

        else:
            multiplier = 1.0
            reason = "Unknown strategy, using fixed"

        # 应用置信度
        multiplier *= (0.5 + confidence * 0.5)

        # 计算最终仓位
        recommended_size = base_size * multiplier
        recommended_size = max(
            self.min_position_size,
            min(self.max_position_size, recommended_size)
        )

        # 创建结果
        result = PositionSizeResult(
            recommended_size=recommended_size,
            base_size=base_size,
            multiplier=multiplier,
            strategy=strategy,
            confidence=confidence,
            reason=reason,
            kelly_pct=kelly_pct,
            drawdown_factor=drawdown_factor,
            volatility_factor=volatility_factor,
            performance_factor=performance_factor
        )

        # 记录历史
        self._record_calculation(result)

        return result

    # ---------------------- Kelly Criterion ----------------------

    def _calculate_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """计算Kelly百分比

        Kelly = W - (1-W)/R
        其中 R = avg_win / avg_loss

        Args:
            win_rate: 胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损

        Returns:
            Kelly百分比
        """
        if avg_loss <= 0:
            return 0.0

        win = win_rate
        loss_rate = 1.0 - win_rate
        ratio = avg_win / avg_loss

        if ratio <= 0:
            return 0.0

        kelly = win - (loss_rate / ratio)

        return max(0.0, min(kelly, self.max_kelly_pct))

    # ---------------------- Drawdown Factor ----------------------

    def _calculate_drawdown_factor(self, drawdown: float) -> float:
        """计算回撤因子

        Args:
            drawdown: 回撤百分比

        Returns:
            仓位因子
        """
        # 按阈值递减
        sorted_levels = sorted(self.drawdown_reduction_levels.items(), reverse=True)

        for threshold, factor in sorted_levels:
            if drawdown >= threshold:
                return factor

        return 1.0  # 无回撤

    # ---------------------- Volatility Factor ----------------------

    def _calculate_volatility_factor(self, volatility: float) -> float:
        """计算波动率因子

        Args:
            volatility: 波动率

        Returns:
            仓位因子
        """
        if volatility is None or volatility <= 0:
            return 1.0

        sorted_levels = sorted(self.volatility_reduction_levels.items(), reverse=True)

        for threshold, factor in sorted_levels:
            if volatility >= threshold:
                return factor

        return 1.0

    # ---------------------- Performance Factor ----------------------

    def _calculate_performance_factor(self, win_rate: float) -> float:
        """计算性能因子

        Args:
            win_rate: 胜率

        Returns:
            仓位因子
        """
        sorted_levels = sorted(self.win_rate_thresholds.items())

        result = 0.5  # 默认
        for threshold, factor in sorted_levels:
            if win_rate >= threshold:
                result = factor

        return result

    # ---------------------- 辅助方法 ----------------------

    def _record_calculation(self, result: PositionSizeResult) -> None:
        """记录计算结果"""
        self.calculation_history.append(result)
        if len(self.calculation_history) > self.max_history:
            self.calculation_history.pop(0)

    def get_recommended_strategy(self) -> str:
        """获取推荐策略

        基于当前状态返回最佳策略
        """
        if not self.portfolio_analytics:
            return "fixed"

        metrics = self.portfolio_analytics.get_metrics()

        # 高回撤 - 使用drawdown策略
        if metrics.current_drawdown > 15:
            return "drawdown"

        # 高胜率 - 使用kelly
        if metrics.win_rate > 0.6:
            return "adaptive"

        # 中等 - 使用adaptive
        return "adaptive"

    # ---------------------- 统计属性 ----------------------

    @property
    def total_calculations(self) -> int:
        """总计算次数"""
        return len(self.calculation_history)

    @property
    def average_size(self) -> float:
        """平均仓位"""
        if not self.calculation_history:
            return self.base_position_size

        return sum(r.recommended_size for r in self.calculation_history) / len(
            self.calculation_history
        )