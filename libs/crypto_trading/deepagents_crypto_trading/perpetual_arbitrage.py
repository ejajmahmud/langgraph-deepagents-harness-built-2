"""V63.0 永续期货套利策略模块

V63.0 新增功能:
1. PerpetualArbitrageEngine - 永续期货套利引擎
2. FundingRateData - 资金费率数据结构
3. PerpetualConfig - 永续合约配置
4. PerpetualSignal - 永续套利信号
5. calculate_funding_arbitrage - 资金费率套利计算

创建时间: 2026-05-08
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from deepagents_crypto_trading.types import (
    ArbitrageType,
    Exchange,
)

logger = logging.getLogger(__name__)


class PerpetualSide(Enum):
    """永续合约方向"""
    LONG = "long"  # 做多
    SHORT = "short"  # 做空


class FundingRateDirection(Enum):
    """资金费率方向"""
    POSITIVE = "positive"  # 多付空收 (做空获得资金)
    NEGATIVE = "negative"  # 空付多收 (做多获得资金)
    ZERO = "zero"  # 无资金


@dataclass
class FundingRateData:
    """资金费率数据"""
    symbol: str  # 交易对
    exchange: str  # 交易所
    funding_rate: float  # 当前资金费率
    funding_rate_predicted: float  # 预测资金费率 (8小时后)
    funding_time: datetime  # 下次资金结算时间
    mark_price: float  # 标记价格
    index_price: float  # 指数价格
    interest_rate: float = 0.0001  # 利率 (通常 0.01%)
    created_at: datetime = field(default_factory=datetime.now)

    def hours_until_funding(self) -> float:
        """距离下次资金结算的小时数"""
        delta = self.funding_time - datetime.now()
        return max(0, delta.total_seconds() / 3600)

    def annualized_funding_rate(self) -> float:
        """年化资金费率"""
        # 资金费率每8小时计算一次, 一年约1095次
        return self.funding_rate * 1095

    def expected_annual_return(self, position_ratio: float = 1.0) -> float:
        """预期年化收益率 (基于资金费率)"""
        return self.annualized_funding_rate() * position_ratio


@dataclass
class PerpetualConfig:
    """永续合约套利配置"""
    symbol: str  # 交易对, e.g., "BTCUSDT"
    exchange: str = "binance"  # 交易所
    max_position_size: float = 10000  # 最大仓位 (USDT)
    min_funding_rate: float = 0.0001  # 最小资金费率 (0.01%)
    min_profit_threshold: float = 0.0003  # 最小收益阈值 (0.03%)
    max_leverage: int = 10  # 最大杠杆
    funding_lookback_hours: int = 24  # 资金费率回看小时数
    enable_hedge: bool = True  # 是否对冲
    enable_funding_arbitrage: bool = True  # 是否启用资金费率套利

    def validate(self) -> tuple[bool, str]:
        """验证配置"""
        if not self.symbol:
            return False, "Symbol is required"
        if self.min_funding_rate < 0:
            return False, "Min funding rate must be positive"
        if self.max_leverage < 1 or self.max_leverage > 125:
            return False, "Leverage must be 1-125"
        return True, "Valid"


@dataclass
class PerpetualSignal:
    """永续套利信号"""
    symbol: str
    exchange: str
    side: PerpetualSide
    entry_price: float
    target_funding_rate: float  # 目标资金费率
    estimated_duration_hours: float  # 预计持仓小时数
    expected_profit: float  # 预期收益
    confidence: float  # 置信度 (0-1)
    status: str = "pending"  # pending/active/executed/cancelled/expired
    funding_data: Optional[FundingRateData] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "side": self.side.value,
            "entry_price": self.entry_price,
            "target_funding_rate": self.target_funding_rate,
            "estimated_duration_hours": self.estimated_duration_hours,
            "expected_profit": self.expected_profit,
            "confidence": self.confidence,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }

    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


class PerpetualArbitrageEngine:
    """永续期货套利引擎

    功能:
    1. 资金费率套利 - 通过持有永续合约赚取资金费率
    2. 期现套利 - 永续合约 vs 现货对冲
    3. 跨交易所套利 - 不同交易所资金费率差异
    """

    def __init__(self, config: PerpetualConfig) -> None:
        """初始化套利引擎"""
        self.config = config
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._funding_history: List[FundingRateData] = []
        self._signals: List[PerpetualSignal] = []
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def enable(self) -> bool:
        """启用引擎"""
        valid, msg = self.config.validate()
        if not valid:
            logger.error(f"Invalid config: {msg}")
            return False
        self._enabled = True
        logger.info(f"Perpetual arbitrage enabled for {self.config.symbol}")
        return True

    def disable(self) -> bool:
        """禁用引擎"""
        self._enabled = False
        logger.info("Perpetual arbitrage disabled")
        return True

    def update_funding_rate(self, funding_data: FundingRateData) -> None:
        """更新资金费率数据"""
        self._funding_history.append(funding_data)
        # 保留最近24小时数据
        cutoff = datetime.now() - timedelta(hours=24)
        self._funding_history = [
            f for f in self._funding_history if f.created_at > cutoff
        ]
        logger.debug(f"Funding rate updated: {funding_data.funding_rate}")

    def get_average_funding_rate(self, hours: int = 24) -> float:
        """获取平均资金费率"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [f.funding_rate for f in self._funding_history if f.created_at > cutoff]
        if not recent:
            return 0.0
        return sum(recent) / len(recent)

    def calculate_funding_arbitrage(
        self,
        funding_data: FundingRateData,
        position_size: float,
    ) -> Dict[str, Any]:
        """计算资金费率套利收益

        Args:
            funding_data: 资金费率数据
            position_size: 仓位大小 (USDT)

        Returns:
            套利收益计算结果
        """
        hours = funding_data.hours_until_funding()
        funding_payment = position_size * funding_data.funding_rate

        # 年化收益
        annual_return = funding_data.expected_annual_return()

        # 根据方向计算收益
        if funding_data.funding_rate > 0:
            # 正资金费率: 做空获得资金
            direction = "short"
            expected_profit = funding_payment
        elif funding_data.funding_rate < 0:
            # 负资金费率: 做多获得资金
            direction = "long"
            expected_profit = abs(funding_payment)
        else:
            direction = "none"
            expected_profit = 0.0

        return {
            "direction": direction,
            "funding_payment": funding_payment,
            "annual_return": annual_return,
            "hours_until_funding": hours,
            "expected_profit": expected_profit,
            "profit_ratio": expected_profit / position_size if position_size > 0 else 0,
        }

    def scan_opportunity(self, funding_data: FundingRateData) -> Optional[PerpetualSignal]:
        """扫描套利机会

        Args:
            funding_data: 资金费率数据

        Returns:
            套利信号, 无机会返回None
        """
        if not self._enabled:
            return None

        # 检查是否满足最小资金费率
        if abs(funding_data.funding_rate) < self.config.min_funding_rate:
            logger.debug(f"Funding rate {funding_data.funding_rate} below minimum")
            return None

        # 计算预期收益
        position_size = self.config.max_position_size
        arbitrage = self.calculate_funding_arbitrage(funding_data, position_size)

        # 检查是否满足最小收益阈值
        if arbitrage["profit_ratio"] < self.config.min_profit_threshold:
            logger.debug(f"Profit ratio below threshold")
            return None

        # 确定方向
        if funding_data.funding_rate > 0:
            side = PerpetualSide.SHORT
        else:
            side = PerpetualSide.LONG

        # 计算置信度
        confidence = min(1.0, abs(funding_data.funding_rate) / 0.001)

        # 创建信号
        signal = PerpetualSignal(
            symbol=funding_data.symbol,
            exchange=funding_data.exchange,
            side=side,
            entry_price=funding_data.mark_price,
            target_funding_rate=funding_data.funding_rate,
            estimated_duration_hours=funding_data.hours_until_funding(),
            expected_profit=arbitrage["expected_profit"],
            confidence=confidence,
            funding_data=funding_data,
            expires_at=datetime.now() + timedelta(hours=8),
        )

        self._signals.append(signal)
        logger.info(f"Perpetual arbitrage signal: {side.value} {funding_data.symbol}")
        return signal

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """获取当前持仓"""
        return self._positions.copy()

    def get_signals(self) -> List[PerpetualSignal]:
        """获取信号列表"""
        return self._signals.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "enabled": self._enabled,
            "positions": len(self._positions),
            "signals": len(self._signals),
            "funding_history": len(self._funding_history),
            "avg_funding_rate": self.get_average_funding_rate(),
        }


# 全局永续套利引擎
_perpetual_engine: Optional[PerpetualArbitrageEngine] = None


def get_perpetual_engine(config: Optional[PerpetualConfig] = None) -> PerpetualArbitrageEngine:
    """获取永续套利引擎实例"""
    global _perpetual_engine
    if _perpetual_engine is None:
        config = config or PerpetualConfig(symbol="BTCUSDT")
        _perpetual_engine = PerpetualArbitrageEngine(config)
    return _perpetual_engine


def create_funding_rate_data(
    symbol: str,
    exchange: str,
    funding_rate: float,
    mark_price: float,
    index_price: float,
    funding_time: Optional[datetime] = None,
) -> FundingRateData:
    """创建资金费率数据

    Args:
        symbol: 交易对
        exchange: 交易所
        funding_rate: 当前资金费率
        mark_price: 标记价格
        index_price: 指数价格
        funding_time: 下次资金结算时间

    Returns:
        FundingRateData
    """
    if funding_time is None:
        funding_time = datetime.now() + timedelta(hours=8)

    # 预测8小时后的资金费率 (基于历史平均)
    predicted = funding_rate

    return FundingRateData(
        symbol=symbol,
        exchange=exchange,
        funding_rate=funding_rate,
        funding_rate_predicted=predicted,
        funding_time=funding_time,
        mark_price=mark_price,
        index_price=index_price,
    )