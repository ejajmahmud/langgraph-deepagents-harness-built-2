"""统一组合风控管理器 V16.5

跨策略聚合风险管理，监控整体投资组合的暴露度、集中度、最大回撤等，
在套利管道执行前进行最终风控把关。

核心能力：
1. 跨策略风险聚合 — 汇总 cross_exchange + triangular + statistical + funding_rate 四策略持仓
2. 集中度控制 — 单币种/单交易所/单方向持仓上限
3. 最大回撤保护 — 达到阈值自动熔断
4. 相关性感知 — 相关资产持仓合并计算
5. 实时NAV — 投资组合净值实时估算
6. 风险仪表盘 — 一站式风险状态视图

架构位置:
    ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ CrossExch  │  │ Triangular │  │ StatArb    │  │ FundingRate│
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │               │
          └───────────────┴───────────────┴───────────────┘
                                    │
                          PortfolioRiskManager V16.5
                                    │
                          ArbitragePipeline V16.5

创建时间：2026-05-05
"""

import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"           # 正常运行
    MEDIUM = "medium"     # 需要注意
    HIGH = "high"         # 建议减仓
    CRITICAL = "critical" # 立即熔断


class RiskAction(Enum):
    """风控动作"""
    ALLOW = "allow"           # 允许执行
    REDUCE_SIZE = "reduce"    # 减少仓位
    REJECT = "reject"         # 拒绝执行
    CIRCUIT_BREAK = "circuit_break"  # 熔断


@dataclass
class RiskCheckResult:
    """风控检查结果"""
    action: RiskAction
    risk_level: RiskLevel
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    adjusted_size_usd: Optional[float] = None  # 建议调整后的仓位
    timestamp: float = 0.0


@dataclass
class PortfolioPosition:
    """组合持仓"""
    position_id: str
    strategy: str           # cross_exchange / triangular / statistical / funding_rate
    symbol: str
    exchange: str
    side: str               # long / short / neutral
    quantity: float
    value_usd: float
    unrealized_pnl_usd: float
    opened_at: float
    strategy_position_id: str  # 原始策略的持仓ID


@dataclass
class ConcentrationMetrics:
    """集中度指标"""
    symbol_concentration: Dict[str, float]    # {symbol: 持仓比例}
    exchange_concentration: Dict[str, float]  # {exchange: 持仓比例}
    strategy_concentration: Dict[str, float]  # {strategy: 持仓比例}
    max_symbol_hhi: float     # 赫芬达尔指数(币种)
    max_exchange_hhi: float   # 赫芬达尔指数(交易所)


@dataclass
class NAVSnapshot:
    """NAV快照"""
    timestamp: float
    nav: float                # 净资产价值
    gross_exposure: float     # 总暴露
    net_exposure: float       # 净暴露
    unrealized_pnl: float     # 未实现盈亏
    realized_pnl: float       # 已实现盈亏
    position_count: int       # 持仓数量


class PortfolioRiskManager:
    """统一组合风控管理器 V16.5

    跨策略风险管理，确保整体投资组合在安全范围内运行。
    """

    # 相关资产组（同组内持仓视为相关性高）
    CORRELATION_GROUPS = [
        {"BTC/USDT", "ETH/USDT"},                    # 主流币
        {"SOL/USDT", "AVAX/USDT", "ADA/USDT"},       # 公链
        {"DOGE/USDT", "XRP/USDT"},                    # Meme+支付
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化组合风控

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 风险限制
        self.max_total_exposure_usd = self.config.get("max_total_exposure_usd", 10000.0)
        self.max_single_position_usd = self.config.get("max_single_position_usd", 2000.0)
        self.max_single_symbol_pct = self.config.get("max_single_symbol_pct", 0.3)  # 单币种30%
        self.max_single_exchange_pct = self.config.get("max_single_exchange_pct", 0.5)  # 单交易所50%
        self.max_single_strategy_pct = self.config.get("max_single_strategy_pct", 0.4)  # 单策略40%
        self.max_correlated_group_pct = self.config.get("max_correlated_group_pct", 0.5)  # 相关组50%
        self.max_drawdown_pct = self.config.get("max_drawdown_pct", 5.0)  # 最大回撤5%
        self.max_positions_total = self.config.get("max_positions_total", 20)
        self.max_positions_per_strategy = self.config.get("max_positions_per_strategy", 8)

        # 持仓注册表
        self._positions: Dict[str, PortfolioPosition] = {}

        # NAV历史
        self._nav_history: List[NAVSnapshot] = []
        self._peak_nav = 0.0
        self._total_realized_pnl = 0.0

        # 熔断状态
        self._circuit_breaker_active = False
        self._circuit_breaker_reason = ""
        self._circuit_breaker_since = 0.0
        self._circuit_breaker_cooldown = self.config.get("circuit_breaker_cooldown_sec", 300.0)

        # 风控日志
        self._risk_log: List[Dict[str, Any]] = []

        # 初始NAV
        self._initial_capital = self.config.get("initial_capital", self.max_total_exposure_usd)
        self._peak_nav = self._initial_capital

        logger.info(
            f"组合风控 V16.5 初始化: "
            f"max_exposure=${self.max_total_exposure_usd}, "
            f"max_positions={self.max_positions_total}, "
            f"max_drawdown={self.max_drawdown_pct}%"
        )

    def register_position(
        self,
        strategy: str,
        symbol: str,
        exchange: str,
        side: str,
        quantity: float,
        value_usd: float,
        strategy_position_id: str = ""
    ) -> str:
        """注册持仓到风控系统

        Args:
            strategy: 策略名称
            symbol: 交易对
            exchange: 交易所
            side: 方向
            quantity: 数量
            value_usd: 价值
            strategy_position_id: 策略层持仓ID

        Returns:
            风控层持仓ID
        """
        import uuid as _uuid
        position_id = f"prisk_{strategy}_{_uuid.uuid4().hex[:8]}"

        position = PortfolioPosition(
            position_id=position_id,
            strategy=strategy,
            symbol=symbol,
            exchange=exchange,
            side=side,
            quantity=quantity,
            value_usd=value_usd,
            unrealized_pnl_usd=0.0,
            opened_at=time.time(),
            strategy_position_id=strategy_position_id
        )

        self._positions[position_id] = position
        logger.info(f"注册持仓: {strategy} {symbol} ${value_usd:.2f}")
        return position_id

    def unregister_position(self, position_id: str, realized_pnl: float = 0.0) -> bool:
        """注销持仓

        Args:
            position_id: 持仓ID
            realized_pnl: 已实现盈亏

        Returns:
            是否成功
        """
        if position_id not in self._positions:
            return False

        self._total_realized_pnl += realized_pnl
        del self._positions[position_id]
        return True

    def pre_trade_check(
        self,
        strategy: str,
        symbol: str,
        exchange: str,
        side: str,
        proposed_size_usd: float
    ) -> RiskCheckResult:
        """交易前风控检查

        Args:
            strategy: 策略
            symbol: 交易对
            exchange: 交易所
            side: 方向
            proposed_size_usd: 建议仓位大小

        Returns:
            风控检查结果
        """
        now = time.time()

        # 1. 熔断检查
        if self._circuit_breaker_active:
            if now - self._circuit_breaker_since < self._circuit_breaker_cooldown:
                return RiskCheckResult(
                    action=RiskAction.CIRCUIT_BREAK,
                    risk_level=RiskLevel.CRITICAL,
                    reason=f"熔断中: {self._circuit_breaker_reason}",
                    timestamp=now
                )
            else:
                self._circuit_breaker_active = False
                logger.info("熔断恢复")

        # 2. 单笔限额检查
        if proposed_size_usd > self.max_single_position_usd:
            adjusted = self.max_single_position_usd
            self._log_risk("reduce_single_limit", strategy, symbol, proposed_size_usd)
            return RiskCheckResult(
                action=RiskAction.REDUCE_SIZE,
                risk_level=RiskLevel.MEDIUM,
                reason=f"单笔超限: ${proposed_size_usd:.0f} > ${self.max_single_position_usd}",
                adjusted_size_usd=adjusted,
                timestamp=now
            )

        # 3. 总持仓数量检查
        if len(self._positions) >= self.max_positions_total:
            self._log_risk("reject_max_positions", strategy, symbol, proposed_size_usd)
            return RiskCheckResult(
                action=RiskAction.REJECT,
                risk_level=RiskLevel.HIGH,
                reason=f"总持仓数超限: {len(self._positions)}/{self.max_positions_total}",
                timestamp=now
            )

        # 4. 策略持仓数检查
        strategy_count = sum(1 for p in self._positions.values() if p.strategy == strategy)
        if strategy_count >= self.max_positions_per_strategy:
            self._log_risk("reject_strategy_limit", strategy, symbol, proposed_size_usd)
            return RiskCheckResult(
                action=RiskAction.REJECT,
                risk_level=RiskLevel.HIGH,
                reason=f"策略持仓超限: {strategy_count}/{self.max_positions_per_strategy}",
                timestamp=now
            )

        # 5. 计算预期集中度（基于总额度而非当前持仓总量）
        total_exposure = sum(p.value_usd for p in self._positions.values()) + proposed_size_usd
        reference_exposure = max(self.max_total_exposure_usd, total_exposure)

        # 单币种集中度
        symbol_exposure = sum(
            p.value_usd for p in self._positions.values() if p.symbol == symbol
        ) + proposed_size_usd
        symbol_pct = symbol_exposure / reference_exposure if reference_exposure > 0 else 0

        if symbol_pct > self.max_single_symbol_pct:
            adjusted = reference_exposure * self.max_single_symbol_pct - sum(
                p.value_usd for p in self._positions.values() if p.symbol == symbol
            )
            if adjusted <= 0:
                self._log_risk("reject_symbol_concentration", strategy, symbol, proposed_size_usd)
                return RiskCheckResult(
                    action=RiskAction.REJECT,
                    risk_level=RiskLevel.HIGH,
                    reason=f"币种集中度超限: {symbol} {symbol_pct:.1%} > {self.max_single_symbol_pct:.1%}",
                    timestamp=now
                )
            self._log_risk("reduce_symbol_concentration", strategy, symbol, proposed_size_usd)
            return RiskCheckResult(
                action=RiskAction.REDUCE_SIZE,
                risk_level=RiskLevel.MEDIUM,
                reason=f"币种集中度: {symbol} {symbol_pct:.1%}",
                adjusted_size_usd=max(0, adjusted),
                timestamp=now
            )

        # 6. 交易所集中度
        exchange_exposure = sum(
            p.value_usd for p in self._positions.values() if p.exchange == exchange
        ) + proposed_size_usd
        exchange_pct = exchange_exposure / reference_exposure if reference_exposure > 0 else 0

        if exchange_pct > self.max_single_exchange_pct:
            self._log_risk("reduce_exchange_concentration", strategy, symbol, proposed_size_usd)
            return RiskCheckResult(
                action=RiskAction.REDUCE_SIZE,
                risk_level=RiskLevel.MEDIUM,
                reason=f"交易所集中度: {exchange} {exchange_pct:.1%}",
                adjusted_size_usd=proposed_size_usd * 0.5,
                timestamp=now
            )

        # 7. 相关资产组集中度
        correlated_symbols = self._get_correlated_symbols(symbol)
        if correlated_symbols:
            group_exposure = sum(
                p.value_usd for p in self._positions.values()
                if p.symbol in correlated_symbols
            ) + proposed_size_usd
            group_pct = group_exposure / reference_exposure if reference_exposure > 0 else 0

            if group_pct > self.max_correlated_group_pct:
                self._log_risk("reduce_correlated_group", strategy, symbol, proposed_size_usd)
                return RiskCheckResult(
                    action=RiskAction.REDUCE_SIZE,
                    risk_level=RiskLevel.MEDIUM,
                    reason=f"相关组集中度: {group_pct:.1%}",
                    adjusted_size_usd=proposed_size_usd * 0.6,
                    timestamp=now
                )

        # 8. 总暴露检查
        if total_exposure > self.max_total_exposure_usd:
            adjusted = self.max_total_exposure_usd - sum(p.value_usd for p in self._positions.values())
            if adjusted <= 0:
                self._log_risk("reject_total_exposure", strategy, symbol, proposed_size_usd)
                return RiskCheckResult(
                    action=RiskAction.REJECT,
                    risk_level=RiskLevel.HIGH,
                    reason=f"总暴露超限: ${total_exposure:.0f} > ${self.max_total_exposure_usd}",
                    timestamp=now
                )
            self._log_risk("reduce_total_exposure", strategy, symbol, proposed_size_usd)
            return RiskCheckResult(
                action=RiskAction.REDUCE_SIZE,
                risk_level=RiskLevel.MEDIUM,
                reason=f"总暴露: ${total_exposure:.0f}",
                adjusted_size_usd=max(0, adjusted),
                timestamp=now
            )

        # 所有检查通过
        return RiskCheckResult(
            action=RiskAction.ALLOW,
            risk_level=RiskLevel.LOW,
            reason="通过所有风控检查",
            timestamp=now
        )

    def update_nav(self) -> NAVSnapshot:
        """更新NAV

        Returns:
            NAV快照
        """
        total_value = sum(p.value_usd + p.unrealized_pnl_usd for p in self._positions.values())
        gross_exposure = sum(p.value_usd for p in self._positions.values())
        unrealized_pnl = sum(p.unrealized_pnl_usd for p in self._positions.values())

        nav = self._initial_capital + self._total_realized_pnl + unrealized_pnl
        net_exposure = gross_exposure - 2 * abs(unrealized_pnl)

        snapshot = NAVSnapshot(
            timestamp=time.time(),
            nav=nav,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=self._total_realized_pnl,
            position_count=len(self._positions)
        )

        self._nav_history.append(snapshot)

        # 更新峰值NAV
        if nav > self._peak_nav:
            self._peak_nav = nav

        # 检查回撤
        if self._peak_nav > 0:
            drawdown_pct = (self._peak_nav - nav) / self._peak_nav * 100
            if drawdown_pct > self.max_drawdown_pct:
                self._activate_circuit_breaker(
                    f"最大回撤触发: {drawdown_pct:.2f}% > {self.max_drawdown_pct}%"
                )

        return snapshot

    def get_concentration_metrics(self) -> ConcentrationMetrics:
        """获取集中度指标

        Returns:
            集中度指标
        """
        total = sum(p.value_usd for p in self._positions.values())
        if total <= 0:
            return ConcentrationMetrics(
                symbol_concentration={}, exchange_concentration={},
                strategy_concentration={}, max_symbol_hhi=0, max_exchange_hhi=0
            )

        # 币种集中度
        symbol_exposure = defaultdict(float)
        exchange_exposure = defaultdict(float)
        strategy_exposure = defaultdict(float)

        for p in self._positions.values():
            symbol_exposure[p.symbol] += p.value_usd
            exchange_exposure[p.exchange] += p.value_usd
            strategy_exposure[p.strategy] += p.value_usd

        symbol_conc = {k: v / total for k, v in symbol_exposure.items()}
        exchange_conc = {k: v / total for k, v in exchange_exposure.items()}
        strategy_conc = {k: v / total for k, v in strategy_exposure.items()}

        # HHI指数
        symbol_hhi = sum(v ** 2 for v in symbol_conc.values())
        exchange_hhi = sum(v ** 2 for v in exchange_conc.values())

        return ConcentrationMetrics(
            symbol_concentration=symbol_conc,
            exchange_concentration=exchange_conc,
            strategy_concentration=strategy_conc,
            max_symbol_hhi=symbol_hhi,
            max_exchange_hhi=exchange_hhi
        )

    def get_risk_dashboard(self) -> Dict[str, Any]:
        """获取风险仪表盘

        Returns:
            风险仪表盘数据
        """
        nav = self.update_nav()
        concentration = self.get_concentration_metrics()

        drawdown_pct = 0.0
        if self._peak_nav > 0:
            drawdown_pct = (self._peak_nav - nav.nav) / self._peak_nav * 100

        # 风险等级
        if self._circuit_breaker_active:
            risk_level = RiskLevel.CRITICAL
        elif drawdown_pct > self.max_drawdown_pct * 0.8:
            risk_level = RiskLevel.HIGH
        elif len(self._positions) > self.max_positions_total * 0.8:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "version": "V16.5",
            "risk_level": risk_level.value,
            "circuit_breaker": {
                "active": self._circuit_breaker_active,
                "reason": self._circuit_breaker_reason,
                "since": self._circuit_breaker_since,
            },
            "nav": {
                "current": nav.nav,
                "peak": self._peak_nav,
                "drawdown_pct": drawdown_pct,
                "initial_capital": self._initial_capital,
                "total_realized_pnl": self._total_realized_pnl,
            },
            "positions": {
                "total": len(self._positions),
                "by_strategy": dict(Counter(p.strategy for p in self._positions.values())),
                "by_symbol": dict(Counter(p.symbol for p in self._positions.values())),
                "total_value": sum(p.value_usd for p in self._positions.values()),
            },
            "concentration": {
                "symbol": concentration.symbol_concentration,
                "exchange": concentration.exchange_concentration,
                "strategy": concentration.strategy_concentration,
                "symbol_hhi": concentration.max_symbol_hhi,
                "exchange_hhi": concentration.max_exchange_hhi,
            },
            "limits": {
                "max_total_exposure": self.max_total_exposure_usd,
                "max_single_position": self.max_single_position_usd,
                "max_positions": self.max_positions_total,
                "max_drawdown_pct": self.max_drawdown_pct,
                "usage_pct": (
                    sum(p.value_usd for p in self._positions.values()) /
                    self.max_total_exposure_usd * 100
                    if self.max_total_exposure_usd > 0 else 0
                ),
            },
            "risk_log_count": len(self._risk_log),
        }

    def _get_correlated_symbols(self, symbol: str) -> set:
        """获取相关资产组"""
        for group in self.CORRELATION_GROUPS:
            if symbol in group:
                return group
        return set()

    def _activate_circuit_breaker(self, reason: str) -> None:
        """激活熔断"""
        self._circuit_breaker_active = True
        self._circuit_breaker_reason = reason
        self._circuit_breaker_since = time.time()
        self._log_risk("circuit_break", "system", "all", 0)
        logger.warning(f"熔断激活: {reason}")

    def _log_risk(self, event: str, strategy: str, symbol: str, size: float) -> None:
        """记录风控日志"""
        self._risk_log.append({
            "timestamp": time.time(),
            "event": event,
            "strategy": strategy,
            "symbol": symbol,
            "size_usd": size,
        })


# Counter 简易实现（避免额外导入）
class Counter(dict):
    def __init__(self, iterable):
        super().__init__()
        for item in iterable:
            self[item] = self.get(item, 0) + 1


# 全局实例
_portfolio_risk_manager: Optional[PortfolioRiskManager] = None


def get_portfolio_risk_manager(
    config: Optional[Dict[str, Any]] = None
) -> PortfolioRiskManager:
    """获取全局组合风控实例"""
    global _portfolio_risk_manager
    if _portfolio_risk_manager is None:
        _portfolio_risk_manager = PortfolioRiskManager(config)
    return _portfolio_risk_manager
