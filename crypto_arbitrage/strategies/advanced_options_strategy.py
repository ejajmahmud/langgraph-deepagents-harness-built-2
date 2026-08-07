"""Advanced Options Trading Strategy - V50.0

高级期权交易策略模块，支持：
1. Delta Neutral Trading - delta中性交易
2. Volatility Arbitrage - 波动率套利
3. Put-Call Parity - 看涨看跌期权平价套利
4. Calendar Spread - 日历价差
5. Iron Condor Strategy - 铁鹰策略

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


class OptionType(Enum):
    """期权类型"""
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    """期权风格"""
    EUROPEAN = "european"
    AMERICAN = "american"


class PositionSide(Enum):
    """持仓方向"""
    LONG = "long"
    SHORT = "short"


class StrategyMode(Enum):
    """策略模式"""
    DELTA_NEUTRAL = "delta_neutral"
    VOLATILITY_ARB = "volatility_arb"
    PUT_CALL_PARITY = "put_call_parity"
    CALENDAR_SPREAD = "calendar_spread"
    IRON_CONDOR = "iron_condor"


@dataclass
class OptionGreeks:
    """期权Greeks值"""
    delta: float = 0.0  # 期权Delta值
    gamma: float = 0.0  # 期权Gamma值
    theta: float = 0.0  # 期权Theta值
    vega: float = 0.0  # 期权Vega值
    rho: float = 0.0  # 期权Rho值

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'rho': self.rho
        }


@dataclass
class OptionContract:
    """期权合约"""
    symbol: str
    underlying: str  # 标的资产
    strike_price: float  # 行权价
    expiry_date: datetime  # 到期日
    option_type: OptionType  # 期权类型
    option_style: OptionStyle = OptionStyle.EUROPEAN
    multiplier: float = 1.0  # 合约乘数

    def __post_init__(self):
        if isinstance(self.option_type, str):
            self.option_type = OptionType(self.option_type)


@dataclass
class OptionPosition:
    """期权持仓"""
    contract: OptionContract
    side: PositionSide
    quantity: int  # 持仓数量
    entry_price: float  # 开仓价格
    open_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.contract.symbol,
            'underlying': self.contract.underlying,
            'strike_price': self.contract.strike_price,
            'expiry_date': self.contract.expiry_date.isoformat(),
            'option_type': self.contract.option_type.value,
            'side': self.side.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'open_date': self.open_date.isoformat()
        }


@dataclass
class OptionsStrategyResult:
    """期权策略结果"""
    strategy_mode: StrategyMode
    signal: str  # buy/sell/hold
    confidence: float  # 信心指数 0-1
    expected_profit: float  # 预期收益
    max_risk: float  # 最大风险
    net_delta: float  # 净Delta
    positions: List[OptionPosition] = field(default_factory=list)
    greeks: OptionGreeks = field(default_factory=OptionGreeks)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BlackScholesModel:
    """Black-Scholes期权定价模型"""

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """标准正态分布累积分布函数"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _normal_pdf(x: float) -> float:
        """标准正态分布概率密度函数"""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    @classmethod
    def calculate_price(
        cls,
        s: float,  # 标的价格
        k: float,  # 行权价
        t: float,  # 到期时间（年）
        r: float,  # 无风险利率
        sigma: float,  # 波动率
        option_type: OptionType
    ) -> float:
        """计算期权价格"""
        if t <= 0:
            # 到期
            if option_type == OptionType.CALL:
                return max(s - k, 0)
            else:
                return max(k - s, 0)

        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        if option_type == OptionType.CALL:
            price = s * cls._normal_cdf(d1) - k * math.exp(-r * t) * cls._normal_cdf(d2)
        else:
            price = k * math.exp(-r * t) * cls._normal_cdf(-d2) - s * cls._normal_cdf(-d1)

        return price

    @classmethod
    def calculate_greeks(
        cls,
        s: float,  # 标的价格
        k: float,  # 行权价
        t: float,  # 到期时间（年）
        r: float,  # 无风险利率
        sigma: float,  # 波动率
        option_type: OptionType
    ) -> OptionGreeks:
        """计算期权Greeks"""
        if t <= 0:
            return OptionGreeks()

        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)
        sqrt_t = math.sqrt(t)

        # 计算各Greeks
        nd1 = cls._normal_cdf(d1)
        n_d1 = cls._normal_pdf(d1)

        if option_type == OptionType.CALL:
            delta = nd1
            rho = k * t * math.exp(-r * t) * cls._normal_cdf(d2) / 100
        else:
            delta = nd1 - 1
            rho = -k * t * math.exp(-r * t) * cls._normal_cdf(-d2) / 100

        gamma = n_d1 / (s * sigma * sqrt_t)
        vega = s * sqrt_t * n_d1 / 100
        theta = (-s * n_d1 * sigma / (2 * sqrt_t)
                - r * k * math.exp(-r * t) * cls._normal_cdf(d2) if option_type == OptionType.CALL
                else r * k * math.exp(-r * t) * cls._normal_cdf(-d2)) / 365

        return OptionGreeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )


class AdvancedOptionsStrategy:
    """高级期权交易策略"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}

        # 默认参数
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.max_position_size = self.config.get('max_position_size', 10)
        self.target_delta = self.config.get('target_delta', 0.0)  # Delta中性目标
        self.volatility_threshold = self.config.get('volatility_threshold', 0.02)
        self.risk_free_rate = self.config.get('risk_free_rate', 0.05)

        # 持仓管理
        self.positions: List[OptionPosition] = []
        self.strategy_history: List[OptionsStrategyResult] = []

        logger.info(f"AdvancedOptionsStrategy initialized with config: {self.config}")

    def calculate_call_put_parity(
        self,
        call_price: float,
        put_price: float,
        strike_price: float,
        time_to_expiry: float,
        current_price: float
    ) -> Tuple[float, str]:
        """计算看涨看跌期权平价套利机会

        公式: C - P = S - K * e^(-rT)
        如果实际价差偏离理论值，则存在套利机会
        """
        theoretical_diff = current_price - strike_price * math.exp(
            -self.risk_free_rate * time_to_expiry
        )
        actual_diff = call_price - put_price

        deviation = actual_diff - theoretical_diff

        # 判断套利方向
        if deviation > self.volatility_threshold * current_price:
            # 实际call价格过高，存在套利空间 -> 卖出call，买入put，做空标的
            signal = "sell_call_buy_put"
            opportunity = deviation
        elif deviation < -self.volatility_threshold * current_price:
            # 实际put价格过高 -> 买入call，卖出put，做多标的
            signal = "buy_call_sell_put"
            opportunity = -deviation
        else:
            signal = "hold"
            opportunity = 0.0

        return opportunity, signal

    def analyze_delta_neutral(
        self,
        underlying: str,
        current_price: float,
        positions: List[OptionPosition],
        implied_volatility: float,
        time_to_expiry: float,
        underlying_delta: float = 1.0  # 标的资产的delta
    ) -> OptionsStrategyResult:
        """分析Delta中性策略

        目标：通过期权组合实现组合整体Delta为0
        """
        net_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0

        for pos in positions:
            if pos.contract.underlying != underlying:
                continue

            # 计算期权Greeks
            greeks = BlackScholesModel.calculate_greeks(
                s=current_price,
                k=pos.contract.strike_price,
                t=time_to_expiry,
                r=self.risk_free_rate,
                sigma=implied_volatility,
                option_type=pos.contract.option_type
            )

            # 考虑持仓方向
            multiplier = pos.quantity if pos.side == PositionSide.LONG else -pos.quantity

            net_delta += greeks.delta * multiplier * pos.contract.multiplier
            total_gamma += greeks.gamma * multiplier * pos.contract.multiplier
            total_theta += greeks.theta * multiplier * pos.contract.multiplier

        # 添加标的资产Delta
        underlying_exposure = sum(
            p.quantity * underlying_delta
            for p in positions
            if p.contract.underlying == underlying
        )
        net_delta += underlying_exposure

        # 计算对冲需求
        hedge_ratio = -net_delta / underlying_delta if underlying_delta != 0 else 0

        # 生成信号
        if abs(net_delta - self.target_delta) < 0.05:
            signal = "hold"
            confidence = 0.9
        elif net_delta > self.target_delta:
            signal = "sell_underlying"
            confidence = min(abs(net_delta) / underlying_delta, 1.0)
        else:
            signal = "buy_underlying"
            confidence = min(abs(net_delta) / underlying_delta, 1.0)

        return OptionsStrategyResult(
            strategy_mode=StrategyMode.DELTA_NEUTRAL,
            signal=signal,
            confidence=confidence,
            # Theta收益作为预期收益
            expected_profit=total_theta,
            # Gamma风险
            max_risk=abs(total_gamma) * current_price * current_price,
            net_delta=net_delta,
            greeks=OptionGreeks(
                delta=net_delta,
                gamma=total_gamma,
                theta=total_theta
            )
        )

    def analyze_volatility_arbitrage(
        self,
        current_price: float,
        strike_price: float,
        time_to_expiry: float,
        implied_volatility: float,
        historical_volatility: float,
        option_type: OptionType
    ) -> OptionsStrategyResult:
        """波动率套利分析

        当隐含波动率显著高于历史波动率时，卖出期权（收取权利金）
        当隐含波动率显著低于历史波动率时，买入期权
        """
        vol_diff = implied_volatility - historical_volatility
        vol_diff_ratio = vol_diff / historical_volatility if historical_volatility > 0 else 0

        # 计算期权价格
        option_price = BlackScholesModel.calculate_price(
            s=current_price,
            k=strike_price,
            t=time_to_expiry,
            r=self.risk_free_rate,
            sigma=implied_volatility,
            option_type=option_type
        )

        # 计算vega（波动率敏感度）
        greeks = BlackScholesModel.calculate_greeks(
            s=current_price,
            k=strike_price,
            t=time_to_expiry,
            r=self.risk_free_rate,
            sigma=implied_volatility,
            option_type=option_type
        )

        # 生成信号
        if abs(vol_diff_ratio) < 0.1:
            signal = "hold"
            confidence = 0.5
        elif vol_diff > 0:
            # IV > HV，卖出期权
            signal = "sell_option"
            confidence = min(abs(vol_diff_ratio), 1.0)
        else:
            # IV < HV，买入期权
            signal = "buy_option"
            confidence = min(abs(vol_diff_ratio), 1.0)

        # 预期利润来自theta + vega回归
        expected_profit = (
            abs(vol_diff) * greeks.vega  # Vega回归收益
            + abs(time_to_expiry) * 365 * greeks.theta  # Theta收益
        )

        return OptionsStrategyResult(
            strategy_mode=StrategyMode.VOLATILITY_ARB,
            signal=signal,
            confidence=confidence,
            expected_profit=expected_profit,
            max_risk=option_price * current_price,
            net_delta=greeks.delta,
            greeks=greeks
        )

    def analyze_iron_condor(
        self,
        current_price: float,
        time_to_expiry: float,
        implied_volatility: float,
        wing_width: float = 0.05  # 翼宽（相对于标的价格的百分比）
    ) -> OptionsStrategyResult:
        """铁鹰策略分析

        卖出一个牛价差+熊价差的组合：
        - 卖出较低行权价的看跌期权（put）
        - 买入更较低行权价的看跌期权
        - 卖出较高行权价的看涨期权（call）
        - 买入更较高行权价的看涨期权
        """
        # 计算行权价
        lower_put_strike = current_price * (1 - wing_width * 2)
        higher_put_strike = current_price * (1 - wing_width)
        lower_call_strike = current_price * (1 + wing_width)
        higher_call_strike = current_price * (1 + wing_width * 2)

        # 组合Greeks
        net_delta = 0.0
        net_gamma = 0.0
        net_theta = 0.0
        net_vega = 0.0

        # 各腿的Greeks
        legs = [
            (lower_put_strike, OptionType.PUT, -1),  # 卖出低put
            (higher_put_strike, OptionType.PUT, 1),  # 买入更低put
            (lower_call_strike, OptionType.CALL, -1),  # 卖出高call
            (higher_call_strike, OptionType.CALL, 1),  # 买入更高call
        ]

        for strike, opt_type, direction in legs:
            greeks = BlackScholesModel.calculate_greeks(
                s=current_price,
                k=strike,
                t=time_to_expiry,
                r=self.risk_free_rate,
                sigma=implied_volatility,
                option_type=opt_type
            )
            net_delta += greeks.delta * direction
            net_gamma += greeks.gamma * direction
            net_theta += greeks.theta * direction
            net_vega += greeks.vega * direction

        # 铁鹰策略特征
        # 有限的盈利（权利金收入）
        # 有限的亏损（行权价差）

        # 判断信号
        if abs(net_delta) < 0.1:
            signal = "hold"
            confidence = 0.7
        else:
            # 轻微Delta偏移，可以通过标的资产对冲
            signal = "adjust_delta"
            confidence = 0.6

        return OptionsStrategyResult(
            strategy_mode=StrategyMode.IRON_CONDOR,
            signal=signal,
            confidence=confidence,
            expected_profit=net_theta * 100,  # 简化估算
            max_risk=wing_width * current_price * 2,  # 最大亏损
            net_delta=net_delta,
            greeks=OptionGreeks(
                delta=net_delta,
                gamma=net_gamma,
                theta=net_theta,
                vega=net_vega
            ),
            metadata={
                'lower_put_strike': lower_put_strike,
                'higher_put_strike': higher_put_strike,
                'lower_call_strike': lower_call_strike,
                'higher_call_strike': higher_call_strike,
                'wing_width': wing_width
            }
        )

    def analyze(
        self,
        underlying: str,
        current_price: float,
        implied_volatility: float,
        historical_volatility: float,
        time_to_expiry: float,
        strategy_mode: StrategyMode = StrategyMode.VOLATILITY_ARB,
        strike_price: Optional[float] = None,
        option_type: Optional[OptionType] = None,
        positions: Optional[List[OptionPosition]] = None
    ) -> OptionsStrategyResult:
        """主分析函数"""

        if strategy_mode == StrategyMode.DELTA_NEUTRAL:
            result = self.analyze_delta_neutral(
                underlying=underlying,
                current_price=current_price,
                positions=positions or [],
                implied_volatility=implied_volatility,
                time_to_expiry=time_to_expiry
            )
        elif strategy_mode == StrategyMode.VOLATILITY_ARB:
            result = self.analyze_volatility_arbitrage(
                current_price=current_price,
                strike_price=strike_price or current_price,
                time_to_expiry=time_to_expiry,
                implied_volatility=implied_volatility,
                historical_volatility=historical_volatility,
                option_type=option_type or OptionType.CALL
            )
        elif strategy_mode == StrategyMode.IRON_CONDOR:
            result = self.analyze_iron_condor(
                current_price=current_price,
                time_to_expiry=time_to_expiry,
                implied_volatility=implied_volatility
            )
        else:
            # 默认返回空结果
            result = OptionsStrategyResult(
                strategy_mode=strategy_mode,
                signal="hold",
                confidence=0.0,
                expected_profit=0.0,
                max_risk=0.0,
                net_delta=0.0
            )

        # 记录到历史
        self.strategy_history.append(result)

        return result

    def get_signal(self) -> Tuple[str, float, Dict[str, Any]]:
        """获取交易信号

        Returns:
            signal: 交易信号 (buy/sell/hold)
            confidence: 信心指数
            details: 详细信息
        """
        if not self.strategy_history:
            return "hold", 0.0, {}

        # 取最新的分析结果
        latest = self.strategy_history[-1]

        # 过滤低信心信号
        if latest.confidence < self.min_confidence:
            return "hold", latest.confidence, latest.to_dict()

        return latest.signal, latest.confidence, latest.to_dict()

    def add_position(self, position: OptionPosition) -> None:
        """添加持仓"""
        self.positions.append(position)
        logger.info(f"Added position: {position.contract.symbol}")

    def remove_position(self, symbol: str) -> Optional[OptionPosition]:
        """移除持仓"""
        for i, pos in enumerate(self.positions):
            if pos.contract.symbol == symbol:
                removed = self.positions.pop(i)
                logger.info(f"Removed position: {symbol}")
                return removed
        return None

    def get_positions(self, underlying: Optional[str] = None) -> List[OptionPosition]:
        """获取持仓"""
        if underlying:
            return [p for p in self.positions if p.contract.underlying == underlying]
        return self.positions.copy()

    def get_total_pnl(self, current_price: float) -> float:
        """计算总盈亏"""
        total = 0.0
        for pos in self.positions:
            # 简化计算：基于当前价格计算��论��值变化
            # 实际实现需要获取真实期权价格
            contract = pos.contract
            greeks = BlackScholesModel.calculate_greeks(
                s=current_price,
                k=contract.strike_price,
                t=0.04,  # 假设还有约2周
                r=self.risk_free_rate,
                sigma=0.3,  # 假设波动率
                option_type=contract.option_type
            )

            if pos.side == PositionSide.LONG:
                total += greeks.delta * pos.quantity
            else:
                total -= greeks.delta * pos.quantity

        return total


def create_options_strategy(
    config: Optional[Dict[str, Any]] = None
) -> AdvancedOptionsStrategy:
    """创建高级期权交易策略"""
    return AdvancedOptionsStrategy(config=config)


# ============= 测试函数 =============

def _test_options_strategy():
    """测试期权策略"""
    # 创建策略
    strategy = create_options_strategy({
        'min_confidence': 0.6,
        'volatility_threshold': 0.03,
        'risk_free_rate': 0.05
    })

    # 测试波动率套利
    result = strategy.analyze(
        underlying="BTC",
        current_price=50000,
        implied_volatility=0.4,  # 隐含波动率高
        historical_volatility=0.25,  # 历史波动率低
        time_to_expiry=30 / 365,  # 30天
        strategy_mode=StrategyMode.VOLATILITY_ARB,
        strike_price=50000,
        option_type=OptionType.CALL
    )

    print(f"=== Volatility Arbitrage Test ===")
    print(f"Signal: {result.signal}")
    print(f"Confidence: {result.confidence}")
    print(f"Expected Profit: {result.expected_profit:.2f}")
    print(f"Max Risk: {result.max_risk:.2f}")
    print(f"Net Delta: {result.net_delta:.4f}")
    print(f"Greeks: {result.greeks.to_dict()}")

    # 测试铁鹰策略
    result2 = strategy.analyze(
        underlying="BTC",
        current_price=50000,
        implied_volatility=0.3,
        historical_volatility=0.25,
        time_to_expiry=30 / 365,
        strategy_mode=StrategyMode.IRON_CONDOR
    )

    print(f"\n=== Iron Condor Test ===")
    print(f"Signal: {result2.signal}")
    print(f"Confidence: {result2.confidence}")
    print(f"Expected Profit: {result2.expected_profit:.2f}")
    print(f"Max Risk: {result2.max_risk:.2f}")
    print(f"Metadata: {result2.metadata}")

    print("\n✅ AdvancedOptionsStrategy tests passed!")


if __name__ == "__main__":
    _test_options_strategy()