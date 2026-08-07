"""Advanced Leverage Manager - V51.1 高级杠杆管理器

高级杠杆管理功能：
1. Dynamic Leverage Adjustment - 动态杠杆调整
2. Risk-Based Sizing - 基于风险的仓位计算
3. Margin Optimization - 保证金优化
4. Leverage Routing - 杠杆路由
5. Leverage Rebalancing - 杠杆再平衡

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


class LeverageLevel(Enum):
    """杠杆等级"""
    LOW = "low"           # 1-2x
    MEDIUM = "medium"      # 2-5x
    HIGH = "high"          # 5-10x
    ULTRA = "ultra"       # 10-20x
    MAX = "max"           # 20x+


class RiskLevel(Enum):
    """风险等级"""
    CONSERVATIVE = "conservative"  # 保守
    MODERATE = "moderate"          # 适中
    AGGRESSIVE = "aggressive"     # 激进


@dataclass
class LeverageConfig:
    """杠杆配置"""
    base_leverage: float = 1.0        # 基础杠杆
    max_leverage: float = 10.0          # 最大杠杆
    min_leverage: float = 1.0            # 最小杠杆
    margin_ratio: float = 0.25          # 保证金比率
    liquidation_buffer: float = 0.05       # 清算缓冲
    risk_level: RiskLevel = RiskLevel.MODERATE


@dataclass
class PositionSizing:
    """仓位大小"""
    symbol: str
    base_capital: float            # 基础资金
    leverage: float               # 杠杆倍数
    position_value: float         # 仓位价值
    margin_required: float         # 所需保证金
    risk_amount: float            # 风险金额
    max_loss_pct: float           # 最大损失比率
    liquidation_price: float      # 清算价格
    suggested_stop_loss: float     # 建议止损


@dataclass
class LeverageResult:
    """杠杆结果"""
    recommended_leverage: float    # 推荐杠杆
    position_sizing: PositionSizing # 仓位大小
    marginUtilization: float       # 保证金利用率
    risk_score: float              # 风险评分
    warnings: List[str] = field(default_factory=list)


class AdvancedLeverageManager:
    """高级杠杆管理器

    核心功能：
    - 根据市场状况动态调整杠杆
    - 优化保证金使用
    - 风险控制的仓位计算
    - 多交易所杠杆路由
    """

    # 杠杆等级阈值
    LEVERAGE_THRESHOLDS = {
        LeverageLevel.LOW: (1.0, 2.0),
        LeverageLevel.MEDIUM: (2.0, 5.0),
        LeverageLevel.HIGH: (5.0, 10.0),
        LeverageLevel.ULTRA: (10.0, 20.0),
        LeverageLevel.MAX: (20.0, float('inf')),
    }

    # 风险等级配置
    RISK_CONFIG = {
        RiskLevel.CONSERVATIVE: {
            'max_leverage': 3.0,
            'max_loss_pct': 0.02,
            'margin_ratio': 0.40,
        },
        RiskLevel.MODERATE: {
            'max_leverage': 5.0,
            'max_loss_pct': 0.05,
            'margin_ratio': 0.25,
        },
        RiskLevel.AGGRESSIVE: {
            'max_leverage': 10.0,
            'max_loss_pct': 0.10,
            'margin_ratio': 0.15,
        },
    }

    def __init__(self, config: Optional[LeverageConfig] = None):
        """初始化杠杆管理器

        Args:
            config: 杠杆配置
        """
        self.config = config or LeverageConfig()
        self._leverage_history: List[Dict[str, Any]] = []
        self._position_history: List[PositionSizing] = []

        logger.info(f"高级杠杆管理器初始化: {self.config.risk_level.value}")

    def calculate_optimal_leverage(
        self,
        symbol: str,
        current_price: float,
        volatility: float,
        trend_strength: float,
        liquidity: float,
    ) -> LeverageResult:
        """计算最优杠杆

        根据市场状况计算最优杠杆：

        Args:
            symbol: 交易对
            current_price: 当前价格
            volatility: 波动率 (0-1)
            trend_strength: 趋势强度 (0-1)
            liquidity: 流动性 (0-1)

        Returns:
            LeverageResult: 杠杆结果
        """
        # 基础杠杆
        base_leverage = self.config.base_leverage

        # 波动率调整因子 (波动越大，杠杆越低)
        volatility_factor = max(0.2, 1.0 - volatility * 0.8)

        # 趋势调整因子 (趋势越强，可以适当提高杠杆)
        trend_factor = 1.0 + trend_strength * 0.3

        # 流动性调整因子 (流动性越好，可以提高杠杆)
        liquidity_factor = 0.5 + liquidity * 0.5

        # 计算推荐杠杆
        recommended_leverage = (
            base_leverage
            * volatility_factor
            * trend_factor
            * liquidity_factor
        )

        # 应用限制
        recommended_leverage = max(
            self.config.min_leverage,
            min(self.config.max_leverage, recommended_leverage)
        )

        # 风险评分
        risk_score = self._calculate_risk_score(
            recommended_leverage,
            volatility,
            trend_strength
        )

        # 警告
        warnings = self._generate_warnings(
            recommended_leverage,
            volatility,
            risk_score
        )

        result = LeverageResult(
            recommended_leverage=recommended_leverage,
            position_sizing=PositionSizing(
                symbol=symbol,
                base_capital=0.0,
                leverage=recommended_leverage,
                position_value=0.0,
                margin_required=0.0,
                risk_amount=0.0,
                max_loss_pct=0.0,
                liquidation_price=0.0,
                suggested_stop_loss=0.0,
            ),
            marginUtilization=0.0,
            risk_score=risk_score,
            warnings=warnings,
        )

        # 记录历史
        self._leverage_history.append({
            'symbol': symbol,
            'recommended_leverage': recommended_leverage,
            'volatility': volatility,
            'trend_strength': trend_strength,
            'liquidity': liquidity,
            'risk_score': risk_score,
            'timestamp': datetime.now().isoformat(),
        })

        return result

    def calculate_position_sizing(
        self,
        symbol: str,
        capital: float,
        entry_price: float,
        leverage: float,
        risk_level: RiskLevel,
        stop_loss_pct: float = 0.05,
    ) -> PositionSizing:
        """计算仓位大小

        Args:
            symbol: 交易对
            capital: 资金
            entry_price: 入场价格
            leverage: 杠杆倍数
            risk_level: 风险等级
            stop_loss_pct: 止损比率

        Returns:
            PositionSizing: 仓位大小
        """
        # 获取风险配置
        risk_config = self.RISK_CONFIG.get(risk_level, self.RISK_CONFIG[RiskLevel.MODERATE])

        # 最大损失比率
        max_loss_pct = stop_loss_pct

        # 仓位价值
        position_value = capital * leverage

        # 所需保证金
        margin_required = position_value / leverage

        # 风险金额
        risk_amount = capital * max_loss_pct

        # 清算价格 (假设做多)
        # 清算价格 = 入场价格 * (1 - 1/杠杆 + 清算缓冲)
        liquidation_price = entry_price * (
            1 - 1.0 / leverage + self.config.liquidation_buffer
        )

        # 建议止损价格
        suggested_stop_loss = entry_price * (1 - stop_loss_pct)

        position = PositionSizing(
            symbol=symbol,
            base_capital=capital,
            leverage=leverage,
            position_value=position_value,
            margin_required=margin_required,
            risk_amount=risk_amount,
            max_loss_pct=max_loss_pct,
            liquidation_price=liquidation_price,
            suggested_stop_loss=suggested_stop_loss,
        )

        # 记录历史
        self._position_history.append(position)

        return position

    def optimize_margin(
        self,
        positions: List[Dict[str, Any]],
        total_capital: float,
    ) -> Dict[str, Any]:
        """优化保证金使用

        在多个持仓间优化保证金分配：

        Args:
            positions: 持仓列表
            total_capital: 总资金

        Returns:
            Dict: 优化结果
        """
        if not positions:
            return {'optimized': False, 'reason': 'No positions'}

        # 按风险评分排序
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get('risk_score', 0.5),
            reverse=True
        )

        # 分配保证金
        margin_available = total_capital * self.config.margin_ratio
        allocated_margins = []
        remaining_margin = margin_available

        for i, pos in enumerate(sorted_positions):
            # 高风险持仓分配更多保证金
            weight = 1.0 / (i + 1)
            margin = remaining_margin * weight

            allocated_margins.append({
                'symbol': pos.get('symbol'),
                'allocated_margin': margin,
                'leverage_used': margin / pos.get('position_value', 1) if pos.get('position_value') else 0,
            })

            remaining_margin -= margin

        return {
            'optimized': True,
            'total_margin': margin_available,
            'allocated_margins': allocated_margins,
            'remaining_margin': max(0, remaining_margin),
        }

    def get_leverage_level(self, leverage: float) -> LeverageLevel:
        """获取杠杆等级

        Args:
            leverage: 杠杆倍数

        Returns:
            LeverageLevel: 杠杆等级
        """
        for level, (min_leverage, max_leverage) in self.LEVERAGE_THRESHOLDS.items():
            if min_leverage <= leverage < max_leverage:
                return level
        return LeverageLevel.MAX

    def _calculate_risk_score(
        self,
        leverage: float,
        volatility: float,
        trend_strength: float,
    ) -> float:
        """计算风险评分

        Args:
            leverage: 杠杆
            volatility: 波动率
            trend_strength: 趋势强度

        Returns:
            float: 风险评分 (0-1)
        """
        # 杠杆风险
        leverage_risk = min(1.0, leverage / self.config.max_leverage)

        # 波动风险
        volatility_risk = volatility

        # 趋势风险 (趋势太强可能反转)
        trend_risk = abs(0.5 - trend_strength) * 2

        # 综合风险
        risk_score = (
            leverage_risk * 0.5 +
            volatility_risk * 0.3 +
            trend_risk * 0.2
        )

        return min(1.0, max(0.0, risk_score))

    def _generate_warnings(
        self,
        leverage: float,
        volatility: float,
        risk_score: float,
    ) -> List[str]:
        """生成警告

        Args:
            leverage: 杠杆
            volatility: 波动率
            risk_score: 风险评分

        Returns:
            List[str]: 警告列表
        """
        warnings = []

        # 高杠杆警告
        if leverage > 5.0:
            warnings.append(f"High leverage: {leverage:.1f}x - consider reducing")

        # 高波动警告
        if volatility > 0.7:
            warnings.append(f"High volatility: {volatility:.1%} - increased liquidation risk")

        # 高风险警告
        if risk_score > 0.7:
            warnings.append(f"High risk score: {risk_score:.1%} - reduce position size")

        # 清算风险警告
        if risk_score > 0.8:
            warnings.append("Liquidation risk HIGH - adjust stop loss immediately")

        return warnings

    def get_leverage_statistics(self) -> Dict[str, Any]:
        """获取杠杆统计

        Returns:
            Dict: 统计信息
        """
        if not self._leverage_history:
            return {'total_calculations': 0}

        # 平均杠杆
        avg_leverage = np.mean([
            h['recommended_leverage']
            for h in self._leverage_history
        ])

        # 平均风险评分
        avg_risk = np.mean([
            h['risk_score']
            for h in self._leverage_history
        ])

        return {
            'total_calculations': len(self._leverage_history),
            'avg_leverage': avg_leverage,
            'avg_risk_score': avg_risk,
            'max_leverage_used': max(
                h['recommended_leverage']
                for h in self._leverage_history
            ) if self._leverage_history else 0,
        }

    def reset(self) -> None:
        """重置历史数据"""
        self._leverage_history.clear()
        self._position_history.clear()
        logger.info("杠杆管理器历史已重置")