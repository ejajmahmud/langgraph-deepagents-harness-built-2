"""V61.0 低风险套利交易系统 - 增强版

V61.0 新增功能:
1. Live Trading Mode - 实盘交易模式
2. API Key Management - API 密钥安全管理
3. Trade History Persistence - 交易历史持久化
4. Advanced Order Types - 高级订单类型 (OCO, STOP_LIMIT, TRAILING_STOP)
5. Low-Risk Arbitrage Strategies - 低风险套利策略增强
6. Adaptive Learning - 自适应学习

创建时间: 2026-05-08
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from deepagents_crypto_trading.types import (
    ArbitrageType,
    Exchange,
    OrderSide,
    OrderType,
    Position,
    PositionStatus,
    TradingConfig,
    TradingPair,
)

logger = logging.getLogger(__name__)


class LiveTradingMode(Enum):
    """实盘交易模式"""
    PAPER = "paper"  # 模拟交易
    LIVE = "live"  # 实盘交易
    BACKTEST = "backtest"  # 回测模式


class OrderTimeInForce(Enum):
    """订单有效期"""
    GTC = "good_till_cancel"  # 取消前有效
    IOC = "immediate_or_cancel"  # 立即成交或取消
    FOK = "fill_or_kill"  # 全部成交或取消
    GTD = "good_till_date"  # 指定日期前有效


class AdvancedOrderType(Enum):
    """高级订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"
    OCO = "one_cancels_other"  # 二选一订单
    TRAILING_STOP = "trailing_stop"


@dataclass
class APIKeyConfig:
    """API 密钥配置"""
    exchange: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None  # Coinbase 需要
    testnet: bool = True
    enabled: bool = True


@dataclass
class AdvancedOrder:
    """高级订单数据结构"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: AdvancedOrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    trailing_distance: Optional[float] = None
    time_in_force: OrderTimeInForce = OrderTimeInForce.GTC
    status: str = "pending"
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    fee: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expire_at: Optional[datetime] = None
    client_order_id: Optional[str] = None


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    fee: float
    pnl: float = 0.0
    executed_at: datetime = field(default_factory=datetime.now)
    exchange: str = ""
    strategy: str = ""
    notes: str = ""


@dataclass
class ArbitragePosition:
    """套利持仓"""
    position_id: str
    arbitrage_type: ArbitrageType
    trading_pairs: List[TradingPair]
    entry_price: float
    current_price: float
    size: float
    side: OrderSide
    status: PositionStatus
    pnl: float
    unrealized_pnl: float
    opened_at: datetime
    closed_at: Optional[datetime] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_hold_seconds: int = 300  # 最大持有时间 5 分钟


@dataclass
class LowRiskSignal:
    """低风险��利信号"""
    signal_id: str
    arbitrage_type: ArbitrageType
    confidence: float  # 0.0 - 1.0
    expected_profit_pct: float
    risk_score: float  # 0.0 (低风险) - 1.0 (高风险)
    reasoning: str
    evidence: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class APIKeyManager:
    """API 密钥管理器

    安全地管理交易所 API 密钥
    """

    def __init__(self) -> None:
        """初始化 API 密钥管理器"""
        self._keys: Dict[str, APIKeyConfig] = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        """从环境变量加载 API 密钥"""
        # Binance
        binance_key = os.environ.get("BINANCE_API_KEY", "")
        binance_secret = os.environ.get("BINANCE_API_SECRET", "")
        if binance_key and binance_secret:
            self._keys["binance"] = APIKeyConfig(
                exchange="binance",
                api_key=binance_key,
                api_secret=binance_secret,
                testnet=os.environ.get("BINANCE_TESTNET", "true").lower() == "true",
            )

        # Coinbase
        cb_key = os.environ.get("COINBASE_API_KEY", "")
        cb_secret = os.environ.get("COINBASE_API_SECRET", "")
        cb_pass = os.environ.get("COINBASE_PASSPHRASE", "")
        if cb_key and cb_secret:
            self._keys["coinbase"] = APIKeyConfig(
                exchange="coinbase",
                api_key=cb_key,
                api_secret=cb_secret,
                passphrase=cb_pass,
            )

        # OKX
        okx_key = os.environ.get("OKX_API_KEY", "")
        okx_secret = os.environ.get("OKX_API_SECRET", "")
        if okx_key and okx_secret:
            self._keys["okx"] = APIKeyConfig(
                exchange="okx",
                api_key=okx_key,
                api_secret=okx_secret,
            )

        logger.info(f"已加载 {len(self._keys)} 个 API 密钥")

    def get_key(self, exchange: str) -> Optional[APIKeyConfig]:
        """获取 API 密钥"""
        return self._keys.get(exchange)

    def has_key(self, exchange: str) -> bool:
        """检查是否有 API 密钥"""
        key = self._keys.get(exchange)
        return key is not None and key.enabled

    def enable_exchange(self, exchange: str) -> None:
        """启用交易所"""
        if exchange in self._keys:
            self._keys[exchange].enabled = True

    def disable_exchange(self, exchange: str) -> None:
        """禁用交易所"""
        if exchange in self._keys:
            self._keys[exchange].enabled = False

    def list_enabled(self) -> List[str]:
        """列出已启用的交易所"""
        return [k for k, v in self._keys.items() if v.enabled]


class TradeHistoryManager:
    """交易历史管理器

    持久化交易历史
    """

    def __init__(self, memo_client: Optional[Any] = None) -> None:
        """初始化交易历史管理器"""
        self.memo_client = memo_client
        self._trades: List[TradeRecord] = []
        self._positions: List[ArbitragePosition] = []

    async def save_trade(self, trade: TradeRecord) -> bool:
        """保存交易记录"""
        self._trades.append(trade)

        if self.memo_client:
            try:
                await self.memo_client.save_order(
                    order_id=trade.trade_id,
                    symbol=trade.symbol,
                    side=trade.side.value,
                    order_type="market",
                    quantity=trade.quantity,
                    price=trade.price,
                    status="executed",
                    fee=trade.fee,
                )
            except Exception as e:
                logger.warning(f"保存交易记录失败: {e}")

        return True

    async def save_position(
        self,
        position: ArbitragePosition,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """保存持仓"""
        self._positions.append(position)

        if self.memo_client:
            pos = Position(
                id=position.position_id,
                arbitrage_type=position.arbitrage_type,
                trading_pairs=position.trading_pairs,
                entry_price=position.entry_price,
                current_price=position.current_price,
                size=position.size,
                side=position.side,
                status=position.status,
                pnl=position.pnl,
                opened_at=position.opened_at,  # type: ignore
                closed_at=position.closed_at,
            )
            try:
                await self.memo_client.save_trade(pos, metadata)
            except Exception as e:
                logger.warning(f"保存持仓失败: {e}")

        return True

    def get_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[TradeRecord]:
        """获取交易记录"""
        trades = self._trades

        if symbol:
            trades = [t for t in trades if t.symbol == symbol]

        return trades[-limit:]

    def get_profit_summary(self) -> Dict[str, float]:
        """获取利润摘要"""
        closed = [t for t in self._trades if t.pnl != 0]

        if not closed:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
            }

        wins = [t for t in closed if t.pnl > 0]
        losses = [t for t in closed if t.pnl < 0]

        return {
            "total_trades": len(closed),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": len(wins) / len(closed) if closed else 0.0,
            "total_pnl": sum(t.pnl for t in closed),
            "avg_profit": sum(t.pnl for t in wins) / len(wins) if wins else 0.0,
            "avg_loss": sum(t.pnl for t in losses) / len(losses) if losses else 0.0,
        }


class LowRiskArbitrageScanner:
    """低风险套利扫描器

    扫描并评估低风险套利机会
    """

    def __init__(self, config: Optional[Dict] = None) -> None:
        """初始化套利扫描器"""
        self.config = config or {}
        self.min_confidence = self.config.get("min_confidence", 0.75)
        self.max_risk_score = self.config.get("max_risk_score", 0.3)
        self.min_profit_pct = self.config.get("min_profit_pct", 0.2)
        self._scan_history: List[LowRiskSignal] = []

    def evaluate_opportunity(
        self,
        arbitrage_type: ArbitrageType,
        profit_pct: float,
        confidence: float,
        volatility: float,
        liquidity: float,
    ) -> LowRiskSignal:
        """评估套利机会

        Args:
            arbitrage_type: 套利类型
            profit_pct: 预期利润百分比
            confidence: 置信度
            volatility: 波动率
            liquidity: 流动性

        Returns:
            低风险信号
        """
        import uuid

        # 计算风险评分
        risk_score = 0.0

        # 高波动率增加风险
        if volatility > 0.5:
            risk_score += 0.3
        elif volatility > 0.3:
            risk_score += 0.15

        # 低流动性增加风险
        if liquidity < 0.3:
            risk_score += 0.3
        elif liquidity < 0.5:
            risk_score += 0.15

        # 检查是否低风险套利
        is_low_risk = (
            risk_score <= self.max_risk_score
            and confidence >= self.min_confidence
            and profit_pct >= self.min_profit_pct
        )

        reasoning = []
        if is_low_risk:
            reasoning.append("低风险套利机会")
        else:
            if risk_score > self.max_risk_score:
                reasoning.append(f"风险评分过高: {risk_score:.2f}")
            if confidence < self.min_confidence:
                reasoning.append(f"置信度过低: {confidence:.2f}")
            if profit_pct < self.min_profit_pct:
                reasoning.append(f"利润过低: {profit_pct:.2f}%")

        evidence = [
            f"预期利润: {profit_pct:.2f}%",
            f"置信度: {confidence:.2f}",
            f"风险评分: {risk_score:.2f}",
            f"波动率: {volatility:.2f}",
            f"流动性: {liquidity:.2f}",
        ]

        signal = LowRiskSignal(
            signal_id=str(uuid.uuid4()),
            arbitrage_type=arbitrage_type,
            confidence=confidence,
            expected_profit_pct=profit_pct,
            risk_score=risk_score,
            reasoning="; ".join(reasoning) if reasoning else "不适合低风险套利",
            evidence=evidence,
        )

        self._scan_history.append(signal)
        return signal

    def get_scan_stats(self) -> Dict[str, Any]:
        """获取扫描统计"""
        if not self._scan_history:
            return {
                "total_scans": 0,
                "low_risk_signals": 0,
                "avg_confidence": 0.0,
                "avg_profit": 0.0,
            }

        low_risk = [s for s in self._scan_history if s.risk_score <= self.max_risk_score]

        return {
            "total_scans": len(self._scan_history),
            "low_risk_signals": len(low_risk),
            "avg_confidence": sum(s.confidence for s in self._scan_history)
            / len(self._scan_history),
            "avg_profit": sum(s.expected_profit_pct for s in self._scan_history)
            / len(self._scan_history),
        }


class AdaptiveLearningEngine:
    """自适应学习引擎

    从历史交易中学习并优化策略
    """

    def __init__(self) -> None:
        """初始化自适应学习引擎"""
        self._performance_history: List[Dict] = []
        self._strategy_adjustments: Dict[str, float] = {}

    def recordOutcome(
        self,
        strategy: str,
        expected_profit: float,
        actual_profit: float,
    ) -> None:
        """记录交易结果"""
        adjustment = actual_profit - expected_profit
        self._performance_history.append({
            "strategy": strategy,
            "expected": expected_profit,
            "actual": actual_profit,
            "adjustment": adjustment,
            "timestamp": time.time(),
        })

    def get_strategy_adjustment(self, strategy: str) -> float:
        """获取策略调整值"""
        history = [
            h for h in self._performance_history
            if h.get("strategy") == strategy
        ]

        if not history:
            return 0.0

        # 使用滑动平均
        recent = history[-10:]
        return sum(h.get("adjustment", 0) for h in recent) / len(recent)

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self._performance_history:
            return {"status": "no_data"}

        strategies = set(h.get("strategy") for h in self._performance_history)

        return {
            "total_trades": len(self._performance_history),
            "strategies": list(strategies),
            "adjustments": {
                s: self.get_strategy_adjustment(s)
                for s in strategies
            },
        }


# 全局实例
_api_key_manager: Optional[APIKeyManager] = None
_trade_history_manager: Optional[TradeHistoryManager] = None
_arbitrage_scanner: Optional[LowRiskArbitrageScanner] = None


def get_api_key_manager() -> APIKeyManager:
    """获取 API 密钥管理器"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def get_trade_history_manager(
    memo_client: Optional[Any] = None
) -> TradeHistoryManager:
    """获取交易历史管理器"""
    global _trade_history_manager
    if _trade_history_manager is None:
        _trade_history_manager = TradeHistoryManager(memo_client)
    return _trade_history_manager


def get_arbitrage_scanner(
    config: Optional[Dict] = None
) -> LowRiskArbitrageScanner:
    """获取低风险套利扫描器"""
    global _arbitrage_scanner
    if _arbitrage_scanner is None:
        _arbitrage_scanner = LowRiskArbitrageScanner(config)
    return _arbitrage_scanner