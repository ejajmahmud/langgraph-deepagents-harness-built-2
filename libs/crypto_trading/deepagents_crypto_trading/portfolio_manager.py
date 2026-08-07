"""Portfolio Manager - Investment Portfolio Management.

Manages crypto investment portfolio with positions, P&L tracking, and rebalancing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from deepagents_crypto_trading.types import Position, PositionStatus, TradingPair


class RebalanceStrategy(Enum):
    """Portfolio rebalancing strategies."""
    THRESHOLD = "threshold"  # Rebalance when drift exceeds threshold
    TIME_BASED = "time_based"  # Rebalance on schedule
    VOLATILITY = "volatility"  # Rebalance based on volatility
    TARGET = "target"  # Maintain target allocation


class PortfolioMetric(Enum):
    """Portfolio metric types."""
    TOTAL_VALUE = "total_value"
    DAILY_PNL = "daily_pnl"
    TOTAL_PNL = "total_pnl"
    RETURN_PCT = "return_pct"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"


@dataclass
class PortfolioPosition:
    """Portfolio position with additional tracking."""
    trading_pair: TradingPair
    quantity: float
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    allocation_pct: float = 0.0
    updated_at: float = field(default_factory=time.time)

    @property
    def value(self) -> float:
        """Current position value."""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost basis."""
        return self.quantity * self.avg_entry_price

    def update_price(self, price: float) -> None:
        """Update current price and recalculate P&L."""
        prev_price = self.current_price
        self.current_price = price
        self.unrealized_pnl = (price - self.avg_entry_price) * self.quantity
        self.updated_at = time.time()


@dataclass
class PortfolioAllocation:
    """Target portfolio allocation."""
    trading_pair: TradingPair
    target_pct: float
    min_pct: float = 0.0
    max_pct: float = 100.0
    rebalance_threshold: float = 0.05  # 5% drift threshold


@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a point in time."""
    timestamp: float
    total_value: float
    total_cost: float
    unrealized_pnl: float
    realized_pnl: float
    positions: list[PortfolioPosition]
    allocation_drift: float = 0.0

    @property
    def total_pnl(self) -> float:
        """Total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def return_pct(self) -> float:
        """Return percentage."""
        if self.total_cost > 0:
            return (self.total_pnl / self.total_cost) * 100
        return 0.0


@dataclass
class PortfolioConfig:
    """Portfolio configuration."""
    base_currency: str = "USDT"
    max_position_size_pct: float = 25.0  # Max 25% in single position
    rebalance_strategy: RebalanceStrategy = RebalanceStrategy.THRESHOLD
    rebalance_threshold: float = 0.05  # 5% drift triggers rebalance
    min_trade_value: float = 10.0  # Minimum trade value
    target_volatility: float = 0.15  # Target 15% volatility


class PortfolioManager:
    """Manages investment portfolio with positions and rebalancing.

    Features:
    - Position tracking with real-time P&L
    - Target allocation management
    - Automated rebalancing
    - Performance metrics
    """

    def __init__(self, config: Optional[PortfolioConfig] = None) -> None:
        """Initialize portfolio manager.

        Args:
            config: Portfolio configuration.
        """
        self.config = config or PortfolioConfig()
        self._positions: dict[str, PortfolioPosition] = {}
        self._target_allocations: dict[str, PortfolioAllocation] = {}
        self._snapshots: list[PortfolioSnapshot] = []
        self._initial_value: float = 0.0
        self._realized_pnl: float = 0.0

    def set_initial_value(self, value: float) -> None:
        """Set initial portfolio value.

        Args:
            value: Initial value in base currency.
        """
        self._initial_value = value

    def set_target_allocation(
        self,
        trading_pair: TradingPair,
        target_pct: float,
        min_pct: float = 0.0,
        max_pct: float = 100.0,
    ) -> None:
        """Set target allocation for a trading pair.

        Args:
            trading_pair: Trading pair symbol.
            target_pct: Target allocation percentage.
            min_pct: Minimum allocation percentage.
            max_pct: Maximum allocation percentage.
        """
        self._target_allocations[trading_pair.symbol] = PortfolioAllocation(
            trading_pair=trading_pair,
            target_pct=target_pct,
            min_pct=min_pct,
            max_pct=max_pct,
        )

    def add_position(
        self,
        trading_pair: TradingPair,
        quantity: float,
        avg_entry_price: float,
        current_price: float = 0.0,
    ) -> PortfolioPosition:
        """Add or update a position.

        Args:
            trading_pair: Trading pair.
            quantity: Position quantity.
            avg_entry_price: Average entry price.
            current_price: Current market price.

        Returns:
            The portfolio position.
        """
        symbol = trading_pair.symbol
        if symbol in self._positions:
            # Update existing position
            pos = self._positions[symbol]
            total_quantity = pos.quantity + quantity
            if total_quantity > 0:
                pos.avg_entry_price = (
                    pos.cost_basis + quantity * avg_entry_price
                ) / total_quantity
            pos.quantity = total_quantity
            pos.update_price(current_price or avg_entry_price)
        else:
            # Create new position
            self._positions[symbol] = PortfolioPosition(
                trading_pair=trading_pair,
                quantity=quantity,
                avg_entry_price=avg_entry_price,
                current_price=current_price or avg_entry_price,
            )

        self._update_allocations()
        return self._positions[symbol]

    def close_position(
        self,
        trading_pair: TradingPair,
        quantity: float,
        exit_price: float,
    ) -> float:
        """Close (reduce) a position and realize P&L.

        Args:
            trading_pair: Trading pair to close.
            quantity: Quantity to close.
            exit_price: Exit price.

        Returns:
            Realized P&L.
        """
        symbol = trading_pair.symbol
        if symbol not in self._positions:
            return 0.0

        pos = self._positions[symbol]
        close_qty = min(quantity, pos.quantity)

        # Calculate realized P&L
        realized = (exit_price - pos.avg_entry_price) * close_qty
        self._realized_pnl += realized
        pos.realized_pnl += realized

        # Update quantity
        pos.quantity -= close_qty
        if pos.quantity <= 0:
            del self._positions[symbol]
        else:
            pos.update_price(exit_price)

        self._update_allocations()
        return realized

    def update_price(self, trading_pair: TradingPair, price: float) -> None:
        """Update current price for a position.

        Args:
            trading_pair: Trading pair.
            price: Current price.
        """
        symbol = trading_pair.symbol
        if symbol in self._positions:
            self._positions[symbol].update_price(price)

    def should_rebalance(self) -> bool:
        """Check if portfolio should be rebalanced.

        Returns:
            True if rebalancing is needed.
        """
        if not self._target_allocations:
            return False

        for symbol, pos in self._positions.items():
            if symbol in self._target_allocations:
                target = self._target_allocations[symbol]
                drift = abs(pos.allocation_pct - target.target_pct)
                if drift > self.config.rebalance_threshold:
                    return True
        return False

    def get_rebalance_orders(self) -> list[dict]:
        """Get orders needed to rebalance portfolio.

        Returns:
            List of rebalance orders (symbol, side, quantity).
        """
        orders = []
        total_value = self.get_total_value()

        if total_value <= 0:
            return orders

        for symbol, target in self._target_allocations.items():
            current_alloc = self._positions.get(symbol)
            current_pct = current_alloc.allocation_pct if current_alloc else 0.0
            drift = target.target_pct - current_pct

            # Skip if within threshold
            if abs(drift) < self.config.rebalance_threshold:
                continue

            target_value = total_value * (target.target_pct / 100)
            current_value = total_value * (current_pct / 100)
            diff_value = target_value - current_value

            if diff_value < -self.config.min_trade_value:
                # Need to sell
                if current_alloc and current_alloc.current_price > 0:
                    qty = abs(diff_value) / current_alloc.current_price
                    orders.append({
                        "symbol": symbol,
                        "side": "sell",
                        "quantity": qty,
                        "reason": f"rebalance {current_pct:.1f}% -> {target.target_pct:.1f}%",
                    })
            elif diff_value > self.config.min_trade_value:
                # Need to buy
                orders.append({
                    "symbol": symbol,
                    "side": "buy",
                    "value": diff_value,
                    "reason": f"rebalance {current_pct:.1f}% -> {target.target_pct:.1f}%",
                })

        return orders

    def get_total_value(self) -> float:
        """Get total portfolio value.

        Returns:
            Total value in base currency.
        """
        return sum(pos.value for pos in self._positions.values())

    def get_total_cost(self) -> float:
        """Get total cost basis.

        Returns:
            Total cost basis.
        """
        return sum(pos.cost_basis for pos in self._positions.values())

    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L.

        Returns:
            Unrealized P&L.
        """
        return sum(pos.unrealized_pnl for pos in self._positions.values())

    def get_realized_pnl(self) -> float:
        """Get total realized P&L.

        Returns:
            Realized P&L.
        """
        return self._realized_pnl

    def get_daily_pnl(self) -> float:
        """Get daily P&L (from snapshots).

        Returns:
            Daily P&L.
        """
        if len(self._snapshots) >= 2:
            return self._snapshots[-1].total_pnl - self._snapshots[-2].total_pnl
        return self.get_total_pnl()

    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized).

        Returns:
            Total P&L.
        """
        return self.get_realized_pnl() + self.get_unrealized_pnl()

    def get_return_pct(self) -> float:
        """Get return percentage.

        Returns:
            Return percentage.
        """
        cost = self.get_total_cost()
        if cost > 0:
            return (self.get_total_pnl() / cost) * 100
        return 0.0

    def create_snapshot(self) -> PortfolioSnapshot:
        """Create a portfolio snapshot.

        Returns:
            Portfolio snapshot.
        """
        snapshot = PortfolioSnapshot(
            timestamp=time.time(),
            total_value=self.get_total_value(),
            total_cost=self.get_total_cost(),
            unrealized_pnl=self.get_unrealized_pnl(),
            realized_pnl=self.get_realized_pnl(),
            positions=list(self._positions.values()),
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_positions(self) -> list[PortfolioPosition]:
        """Get all positions.

        Returns:
            List of positions.
        """
        return list(self._positions.values())

    def get_positions_summary(self) -> dict:
        """Get positions summary.

        Returns:
            Dictionary of positions summary.
        """
        return {
            "total_value": self.get_total_value(),
            "total_cost": self.get_total_cost(),
            "unrealized_pnl": self.get_unrealized_pnl(),
            "realized_pnl": self.get_realized_pnl(),
            "total_pnl": self.get_total_pnl(),
            "return_pct": self.get_return_pct(),
            "position_count": len(self._positions),
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "value": pos.value,
                    "allocation_pct": pos.allocation_pct,
                    "unrealized_pnl": pos.unrealized_pnl,
                }
                for symbol, pos in self._positions.items()
            },
        }

    def _update_allocations(self) -> None:
        """Update position allocation percentages."""
        total_value = self.get_total_value()
        if total_value <= 0:
            for pos in self._positions.values():
                pos.allocation_pct = 0.0
            return

        for pos in self._positions.values():
            pos.allocation_pct = (pos.value / total_value) * 100

    def get_performance_metrics(self) -> dict:
        """Get portfolio performance metrics.

        Returns:
            Dictionary of performance metrics.
        """
        return {
            "total_value": self.get_total_value(),
            "total_cost": self.get_total_cost() or self._initial_value,
            "unrealized_pnl": self.get_unrealized_pnl(),
            "realized_pnl": self.get_realized_pnl(),
            "total_pnl": self.get_total_pnl(),
            "return_pct": self.get_return_pct(),
            "daily_pnl": self.get_daily_pnl(),
            "positions": len(self._positions),
            "snapshots": len(self._snapshots),
        }


# Type aliases for common use
__all__ = [
    "PortfolioManager",
    "PortfolioPosition",
    "PortfolioAllocation",
    "PortfolioSnapshot",
    "PortfolioConfig",
    "RebalanceStrategy",
    "PortfolioMetric",
]