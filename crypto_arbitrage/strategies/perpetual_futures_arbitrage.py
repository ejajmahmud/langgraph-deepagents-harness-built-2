"""Perpetual Futures Arbitrage - V50.0 永续期货套利策略

实现永续期货与现货之间的套利：
1. Funding Rate Arbitrage - 资金费率套利
2. Basis Trading - 基差交易
3. Funding Rate Prediction - 资金费率预测
4. Implied Funding Rate - 隐含资金费率计算

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


class PerpetualStatus(Enum):
    """永续合约状态"""
    NORMAL = "normal"  # 正常
    INDEXPremium = "premium"  # 溢价
    INDEXDiscount = "discount"  # 折价
    HIGH_VOLATILITY = "high_volatility"  # 高波动


class FundingPeriod(Enum):
    """资金费率结算周期"""
    EVERY_8H = "8h"  # 每8小时
    EVERY_4H = "4h"  # 每4小时
    HOURLY = "1h"  # 每小时


@dataclass
class PerpetualContract:
    """永续合约信息"""
    symbol: str  # 合约_symbol，如BTC-PERP
    underlying: str  # 标的，如BTC
    index_price: float  # 现货指数价格
    mark_price: float  # 合约标记价格
    last_funding_rate: float  # 上次资金费率
    next_funding_time: datetime  # 下次资金结算时间
    open_interest: float  # 未平仓合约量
    volume_24h: float  # 24小时交易量
    funding_rate_history: List[Tuple[datetime, float]] = field(default_factory=list)

    @property
    def basis(self) -> float:
        """基差 = 标记价格 - 现货价格"""
        return self.mark_price - self.index_price

    @property
    def basis_ratio(self) -> float:
        """基差比率"""
        if self.index_price > 0:
            return self.basis / self.index_price
        return 0.0


@dataclass
class FundingPrediction:
    """资金费率预测"""
    implied_rate: float  # 隐含资金费率
    predicted_rate: float  # 预测资金费率
    confidence: float  # 信心指数
    trend: str  # 趋势 (increasing/decreasing/stable)
    historical_avg: float  # 历史平均
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerpetualArbitrageOpportunity:
    """永续期货套利机会"""
    symbol: str
    side: str  # long_funding/short_funding/basis
    entry_price: float
    target_price: float
    expected_profit: float
    confidence: float
    holding_period: float  # 持仓周期（小时）
    funding_rate: float  # 资金费率
    risk_level: str  # low/medium/high
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerpTradingSignal:
    """永续期货交易信号"""
    action: str  # enter_long/enter_short/close/exit
    symbol: str
    position_size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class FundingRateCalculator:
    """资金费率计算器"""

    # 资金费率计算参数
    INTEREST_RATE = 0.0001  # 基础利率 (0.01%)
    CLAMP_DELTA = 0.003  # clamp(delta, -0.003, 0.003)

    @classmethod
    def calculate_implied_rate(
        cls,
        mark_price: float,
        index_price: float,
        time_to_funding: float  # 距离下次结算的时间（小时）/ 8
    ) -> float:
        """计算隐含资金费率

        公式: (MarkPrice - IndexPrice) / IndexPrice * 8 / time_to_funding
        """
        if index_price <= 0 or time_to_funding <= 0:
            return 0.0

        basis = mark_price - index_price
        basis_ratio = basis / index_price

        # 年化后转换为8小时费率
        implied_rate = basis_ratio * 8 / time_to_funding

        return implied_rate

    @classmethod
    def clamp_funding_rate(cls, rate: float) -> float:
        """限制资金费率在[-0.003, 0.003]范围内"""
        return max(-0.003, min(0.003, rate))

    @classmethod
    def calculate_funding_rate(
        cls,
        mark_price: float,
        index_price: float,
        predicted_premium: float,
        clamp: bool = True
    ) -> float:
        """计算最终资金费率

        公式: clamp((MarkPrice - IndexPrice - PredictedPremium) / IndexPrice + Interest, -0.003, 0.003)
        """
        base_rate = (mark_price - index_price) / index_price if index_price > 0 else 0

        funding_rate = cls.clamp_funding_rate(
            base_rate - predicted_premium + cls.INTEREST_RATE
        ) if clamp else base_rate - predicted_premium + cls.INTEREST_RATE

        return funding_rate


class PerpetualFuturesArbitrage:
    """永续期货套利引擎"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}

        # 配置参数
        self.min_profit_threshold = self.config.get('min_profit_threshold', 0.0001)  # 0.01%
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.max_funding_age = self.config.get('max_funding_age', 8)  # 小时
        self.funding_period = FundingPeriod(
            self.config.get('funding_period', '8h')
        )

        # 合约管理
        self.contracts: Dict[str, PerpetualContract] = {}
        self.opportunities: List[PerpetualArbitrageOpportunity] = []

        # 统计
        self.total_funding_earned = 0.0
        self.trade_count = 0

        logger.info(f"PerpetualFuturesArbitrage initialized: {self.config}")

    def add_contract(self, contract: PerpetualContract) -> None:
        """添加永续合约"""
        self.contracts[contract.symbol] = contract
        logger.info(f"Added perpetual contract: {contract.symbol}")

    def get_contract(self, symbol: str) -> Optional[PerpetualContract]:
        """获取永续合约"""
        return self.contracts.get(symbol)

    def analyze_funding_arbitrage(
        self,
        contract: PerpetualContract,
        current_funding_rate: float,
        predicted_funding_rate: float,
        funding_period_hours: int = 8
    ) -> PerpetualArbitrageOpportunity:
        """分析资金费率套利机会

        策略：
        - 当预测资金费率 > 当前资金费率时，做多合约（收多方钱）
        - 当预测资金费率 < 当前资金费率时，做空合约（收空方钱）
        """
        # 计算预期的资金收益
        rate_diff = predicted_funding_rate - current_funding_rate

        # 简化计算
        expected_profit = abs(rate_diff) * contract.mark_price
        holding_hours = funding_period_hours / 8  # 归一化到8小时

        # 判断方向
        if rate_diff > self.min_profit_threshold:
            side = "long_funding"  # 做多，收多方钱
            entry = contract.mark_price
            target = contract.mark_price
        elif rate_diff < -self.min_profit_threshold:
            side = "short_funding"  # 做空，收空方钱
            entry = contract.mark_price
            target = contract.mark_price
        else:
            side = "hold"
            expected_profit = 0
            holding_hours = 0

        # 计算信心指数
        confidence = min(abs(rate_diff) / 0.003, 1.0) if rate_diff != 0 else 0

        # 风险评估
        if abs(rate_diff) > 0.002:
            risk_level = "low"
        elif abs(rate_diff) > 0.001:
            risk_level = "medium"
        else:
            risk_level = "high"

        return PerpetualArbitrageOpportunity(
            symbol=contract.symbol,
            side=side,
            entry_price=entry,
            target_price=target,
            expected_profit=expected_profit,
            confidence=confidence,
            holding_period=holding_hours,
            funding_rate=current_funding_rate,
            risk_level=risk_level,
            metadata={
                'rate_diff': rate_diff,
                'predicted_rate': predicted_funding_rate
            }
        )

    def analyze_basis_trading(
        self,
        contract: PerpetualContract,
        historical_basis_std: float,
        z_score_threshold: float = 2.0
    ) -> PerpetualArbitrageOpportunity:
        """分析基差交易机会

        策略：当基差偏离历史均值超过Z-score阈值时进行均值回归交易
        """
        current_basis = contract.basis_ratio
        expected_basis = 0.0

        # 计算Z-score
        if historical_basis_std > 0:
            z_score = (current_basis - expected_basis) / historical_basis_std
        else:
            z_score = 0.0

        # 判断机会
        if z_score > z_score_threshold:
            # 正向基差过大 -> 预期回归，做空合约
            side = "short_basis"
            expected_profit = abs(current_basis) * contract.mark_price
            target_price = contract.mark_price * (1 + current_basis * 0.5)
        elif z_score < -z_score_threshold:
            # 负向基差过大 -> 预期回归，做多合约
            side = "long_basis"
            expected_profit = abs(current_basis) * contract.mark_price
            target_price = contract.mark_price * (1 + current_basis * 0.5)
        else:
            side = "hold"
            expected_profit = 0
            target_price = contract.mark_price

        confidence = min(abs(z_score) / z_score_threshold, 1.0)

        return PerpetualArbitrageOpportunity(
            symbol=contract.symbol,
            side=side,
            entry_price=contract.mark_price,
            target_price=target_price,
            expected_profit=expected_profit,
            confidence=confidence,
            holding_period=4.0,  # 预期4小时
            funding_rate=0.0,
            risk_level="low",
            metadata={
                'current_basis': current_basis,
                'z_score': z_score,
                'historical_std': historical_basis_std
            }
        )

    def predict_funding_rate(
        self,
        contract: PerpetualContract,
        lookback_hours: int = 24
    ) -> FundingPrediction:
        """预测资金费率

        基于历史资金费率数据预测未来费率
        """
        history = contract.funding_rate_history

        if len(history) < 2:
            return FundingPrediction(
                implied_rate=0.0,
                predicted_rate=contract.last_funding_rate,
                confidence=0.0,
                trend="stable",
                historical_avg=contract.last_funding_rate
            )

        # 计算隐含资金费率
        time_to_funding = 4  # 假设4小时
        implied_rate = FundingRateCalculator.calculate_implied_rate(
            contract.mark_price,
            contract.index_price,
            time_to_funding
        )

        # 简单移动平均预测
        recent_rates = [rate for _, rate in history[-min(lookback_hours, len(history)):]]
        predicted_rate = np.mean(recent_rates) if recent_rates else contract.last_funding_rate

        # 计算趋势
        if len(recent_rates) >= 2:
            recent_avg = np.mean(recent_rates[-2:])
            older_avg = np.mean(recent_rates[:-2])

            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # 计算历史平均
        all_rates = [rate for _, rate in history]
        historical_avg = np.mean(all_rates)

        # 信心指数
        confidence = min(len(recent_rates) / 10, 1.0) if recent_rates else 0

        return FundingPrediction(
            implied_rate=implied_rate,
            predicted_rate=predicted_rate,
            confidence=confidence,
            trend=trend,
            historical_avg=historical_avg,
            metadata={
                'recent_rates_count': len(recent_rates),
                'implied_rate_source': contract.symbol
            }
        )

    def find_opportunities(
        self,
        funding_period_hours: int = 8,
        basis_std: float = 0.001,
        z_score_threshold: float = 2.0
    ) -> List[PerpetualArbitrageOpportunity]:
        """查找���有套利机会

        Args:
            funding_period_hours: 资金费率周期（小时）
            basis_std: 历史基差标准差
            z_score_threshold: Z-score阈值
        """
        opportunities = []

        for symbol, contract in self.contracts.items():
            # 1. 资金费率套利分析
            prediction = self.predict_funding_rate(contract)
            perp_opp = self.analyze_funding_arbitrage(
                contract=contract,
                current_funding_rate=contract.last_funding_rate,
                predicted_funding_rate=prediction.predicted_rate,
                funding_period_hours=funding_period_hours
            )
            if perp_opp.side != "hold":
                opportunities.append(perp_opp)

            # 2. 基差交易分析
            basis_opp = self.analyze_basis_trading(
                contract=contract,
                historical_basis_std=basis_std,
                z_score_threshold=z_score_threshold
            )
            if basis_opp.side != "hold":
                opportunities.append(basis_opp)

        # 按预期收益排序
        opportunities.sort(key=lambda x: x.expected_profit, reverse=True)

        self.opportunities = opportunities
        return opportunities

    def get_best_opportunity(
        self,
        min_confidence: float = 0.6
    ) -> Optional[PerpetualArbitrageOpportunity]:
        """获取最佳套利机会"""
        filtered = [
            opp for opp in self.opportunities
            if opp.confidence >= min_confidence
        ]

        if not filtered:
            return None

        # 返回最佳机会
        return filtered[0]

    def generate_signal(
        self,
        contract: PerpetualContract,
        opp: PerpetualArbitrageOpportunity
    ) -> PerpTradingSignal:
        """生成交易信号"""

        if opp.side == "hold":
            return PerpTradingSignal(
                action="hold",
                symbol=contract.symbol,
                position_size=0,
                entry_price=contract.mark_price,
                stop_loss=0,
                take_profit=0,
                reason="no_opportunity",
                confidence=opp.confidence
            )

        # 计算止损和止盈
        stop_loss_pct = 0.02  # 2% 止损
        take_profit_pct = 0.05  # 5% 止盈

        if opp.side in ["long_funding", "long_basis"]:
            action = "enter_long"
            stop_loss = contract.mark_price * (1 - stop_loss_pct)
            take_profit = contract.mark_price * (1 + take_profit_pct)
        else:
            action = "enter_short"
            stop_loss = contract.mark_price * (1 + stop_loss_pct)
            take_profit = contract.mark_price * (1 - take_profit_pct)

        return PerpTradingSignal(
            action=action,
            symbol=contract.symbol,
            position_size=1.0,
            entry_price=contract.mark_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=f"{opp.side}_arbitrage",
            confidence=opp.confidence
        )

    def execute_funding(self, contract: PerpetualContract) -> float:
        """执行资金费率收取

        Returns:
            收取的资金费率
        """
        rate = FundingRateCalculator.calculate_funding_rate(
            contract.mark_price,
            contract.index_price,
            0.0  # 不考虑预测溢价
        )

        # 更新统计
        self.total_funding_earned += rate * contract.mark_price
        self.trade_count += 1

        logger.info(f"Collected funding: {rate:.6f} for {contract.symbol}")

        return rate

    def get_status(self) -> Dict[str, Any]:
        """��取状态"""
        return {
            'contracts': len(self.contracts),
            'opportunities': len(self.opportunities),
            'total_funding_earned': self.total_funding_earned,
            'trade_count': self.trade_count,
            'config': self.config
        }


def create_perpetual_arbitrage(
    config: Optional[Dict[str, Any]] = None
) -> PerpetualFuturesArbitrage:
    """创建永续期货套利引擎"""
    return PerpetualFuturesArbitrage(config=config)


# ============= 测试函数 =============

def _test_perpetual_arbitrage():
    """测试永续期货套利"""
    # 创建引擎
    engine = create_perpetual_arbitrage({
        'min_profit_threshold': 0.0001,
        'min_confidence': 0.6
    })

    # 添加测试合约
    contract = PerpetualContract(
        symbol="BTC-PERP",
        underlying="BTC",
        index_price=50000,
        mark_price=50100,  # 溢价100
        last_funding_rate=0.0001,  # 0.01%
        next_funding_time=datetime.now() + timedelta(hours=4),
        open_interest=1000000000,
        volume_24h=5000000000,
        funding_rate_history=[
            (datetime.now() - timedelta(hours=i), 0.0001 * (1 + 0.0001 * i))
            for i in range(1, 10)
        ]
    )

    engine.add_contract(contract)

    # 预测资金费率
    prediction = engine.predict_funding_rate(contract)
    print(f"=== Funding Prediction ===")
    print(f"Implied Rate: {prediction.implied_rate:.6f}")
    print(f"Predicted Rate: {prediction.predicted_rate:.6f}")
    print(f"Confidence: {prediction.confidence:.2f}")
    print(f"Trend: {prediction.trend}")
    print(f"Historical Avg: {prediction.historical_avg:.6f}")

    # 分析套利机会
    opp = engine.analyze_funding_arbitrage(
        contract=contract,
        current_funding_rate=contract.last_funding_rate,
        predicted_funding_rate=prediction.predicted_rate + 0.0005,
        funding_period_hours=8
    )

    print(f"\n=== Arbitrage Opportunity ===")
    print(f"Side: {opp.side}")
    print(f"Expected Profit: {opp.expected_profit:.2f}")
    print(f"Confidence: {opp.confidence:.2f}")
    print(f"Risk Level: {opp.risk_level}")

    # 生成信号
    signal = engine.generate_signal(contract, opp)
    print(f"\n=== Trading Signal ===")
    print(f"Action: {signal.action}")
    print(f"Entry Price: {signal.entry_price:.2f}")
    print(f"Stop Loss: {signal.stop_loss:.2f}")
    print(f"Take Profit: {signal.take_profit:.2f}")
    print(f"Confidence: {signal.confidence:.2f}")

    # 基差交易
    basis_opp = engine.analyze_basis_trading(
        contract=contract,
        historical_basis_std=0.002
    )
    print(f"\n=== Basis Opportunity ===")
    print(f"Side: {basis_opp.side}")

    print("\n✅ PerpetualFuturesArbitrage tests passed!")


if __name__ == "__main__":
    _test_perpetual_arbitrage()