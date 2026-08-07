"""Order management system for cryptocurrency trading."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderTimeInForce(str, Enum):
    """Order time in force."""

    GTC = "good_till_cancelled"
    IOC = "immediate_or_cancel"
    FOK = "fill_or_kill"
    GTT = "good_till_time"


@dataclass
class Order:
    """Order data."""

    id: str
    symbol: str
    side: str  # buy/sell
    order_type: str  # market/limit
    quantity: float
    price: Optional[float] = None
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    time_in_force: OrderTimeInForce = OrderTimeInForce.GTC
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    fee: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def remaining_quantity(self) -> float:
        """Get remaining quantity."""
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        """Check if fully filled."""
        return self.filled_quantity >= self.quantity

    @property
    def fill_percentage(self) -> float:
        """Get fill percentage."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100


@dataclass
class OrderBook:
    """Order book for a trading pair."""

    symbol: str
    bids: list[dict] = field(default_factory=list)  # price, quantity
    asks: list[dict] = field(default_factory=list)  # price, quantity
    last_update: datetime = field(default_factory=datetime.now)


class OrderManager:
    """Order management system.

    Manages order lifecycle including creation, execution, tracking,
    and reconciliation.
    """

    def __init__(self) -> None:
        """Initialize order manager."""
        self.orders: dict[str, Order] = {}
        self.order_history: list[Order] = []
        self._order_books: dict[str, OrderBook] = {}

    def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        metadata: Optional[dict] = None,
    ) -> Order:
        """Create a market order.

        Args:
            symbol: Trading symbol.
            side: Order side (buy/sell).
            quantity: Order quantity.
            metadata: Optional metadata.

        Returns:
            Created order.
        """
        return self._create_order(
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=quantity,
            metadata=metadata,
        )

    def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: OrderTimeInForce = OrderTimeInForce.GTC,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> Order:
        """Create a limit order.

        Args:
            symbol: Trading symbol.
            side: Order side (buy/sell).
            quantity: Order quantity.
            price: Limit price.
            time_in_force: Time in force.
            expires_at: Expiration time.
            metadata: Optional metadata.

        Returns:
            Created order.
        """
        return self._create_order(
            symbol=symbol,
            side=side,
            order_type="limit",
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            expires_at=expires_at,
            metadata=metadata,
        )

    def _create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: OrderTimeInForce = OrderTimeInForce.GTC,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> Order:
        """Create an order.

        Args:
            symbol: Trading symbol.
            side: Order side.
            order_type: Order type.
            quantity: Order quantity.
            price: Limit price (for limit orders).
            time_in_force: Time in force.
            expires_at: Expiration time.
            metadata: Optional metadata.

        Returns:
            Created order.
        """
        order = Order(
            id=f"ord_{uuid.uuid4().hex[:12]}",
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self.orders[order.id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID.

        Args:
            order_id: Order ID.

        Returns:
            Order if found.
        """
        return self.orders.get(order_id)

    def update_order(
        self,
        order_id: str,
        filled_quantity: Optional[float] = None,
        average_fill_price: Optional[float] = None,
        status: Optional[OrderStatus] = None,
    ) -> Optional[Order]:
        """Update order fill information.

        Args:
            order_id: Order ID.
            filled_quantity: Filled quantity.
            average_fill_price: Average fill price.
            status: New status.

        Returns:
            Updated order or None.
        """
        order = self.orders.get(order_id)
        if not order:
            return None

        if filled_quantity is not None:
            order.filled_quantity = filled_quantity

        if average_fill_price is not None:
            order.average_fill_price = average_fill_price

        if status is not None:
            order.status = status

        order.updated_at = datetime.now()

        if order.is_filled:
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            self.order_history.append(order)

        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Order ID.

        Returns:
            True if cancelled.
        """
        order = self.orders.get(order_id)
        if not order:
            return False

        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            return False

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        self.order_history.append(order)
        return True

    def get_pending_orders(self, symbol: Optional[str] = None) -> list[Order]:
        """Get pending orders.

        Args:
            symbol: Filter by symbol (optional).

        Returns:
            List of pending orders.
        """
        pending = [
            o for o in self.orders.values()
            if o.status == OrderStatus.PENDING
        ]

        if symbol:
            pending = [o for o in pending if o.symbol == symbol]

        return pending

    def get_orders_by_status(
        self, status: OrderStatus
    ) -> list[Order]:
        """Get orders by status.

        Args:
            status: Order status to filter.

        Returns:
            List of orders.
        """
        return [o for o in self.orders.values() if o.status == status]

    def get_order_statistics(self) -> dict:
        """Get order statistics.

        Returns:
            Dictionary of order statistics.
        """
        total = len(self.orders)
        filled = len([o for o in self.orders.values() if o.status == OrderStatus.FILLED])
        cancelled = len([o for o in self.orders.values() if o.status == OrderStatus.CANCELLED])
        pending = len([o for o in self.orders.values() if o.status == OrderStatus.PENDING])

        total_volume = sum(
            o.filled_quantity * o.average_fill_price
            for o in self.orders.values()
            if o.status == OrderStatus.FILLED and o.average_fill_price > 0
        )

        return {
            "total_orders": total,
            "filled_orders": filled,
            "cancelled_orders": cancelled,
            "pending_orders": pending,
            "fill_rate": filled / total if total > 0 else 0.0,
            "total_volume": total_volume,
            "total_fees": sum(o.fee for o in self.orders.values()),
        }

    def get_orders_summary(self) -> dict:
        """Get orders summary.

        Returns:
            Dictionary of orders summary.
        """
        by_symbol: dict[str, dict] = {}

        for order in self.orders.values():
            if order.symbol not in by_symbol:
                by_symbol[order.symbol] = {
                    "pending": 0,
                    "filled": 0,
                    "cancelled": 0,
                }

            status_key = order.status.value
            if status_key in by_symbol[order.symbol]:
                by_symbol[order.symbol][status_key] += 1

        return by_symbol


class OrderExecutionSimulator:
    """Simulates order execution for testing."""

    def __init__(self, order_manager: OrderManager) -> None:
        """Initialize simulator.

        Args:
            order_manager: Order manager to manage orders.
        """
        self.order_manager = order_manager

    async def execute_market_order(
        self,
        order_id: str,
        fill_price: float,
        fee_pct: float = 0.001,
    ) -> bool:
        """Execute a market order.

        Args:
            order_id: Order ID.
            fill_price: Fill price.
            fee_pct: Fee percentage.

        Returns:
            True if executed.
        """
        order = self.order_manager.get_order(order_id)
        if not order or order.order_type != "market":
            return False

        if order.status != OrderStatus.PENDING:
            return False

        # Calculate fee
        volume = order.quantity * fill_price
        fee = volume * fee_pct

        # Update order
        self.order_manager.update_order(
            order_id=order_id,
            filled_quantity=order.quantity,
            average_fill_price=fill_price,
            status=OrderStatus.FILLED,
        )

        # Update fee
        order.fee = fee

        return True

    async def execute_limit_order(
        self,
        order_id: str,
        fill_price: float,
        filled_quantity: float,
        fee_pct: float = 0.001,
    ) -> bool:
        """Execute a limit order.

        Args:
            order_id: Order ID.
            fill_price: Fill price.
            filled_quantity: Filled quantity.
            fee_pct: Fee percentage.

        Returns:
            True if executed.
        """
        order = self.order_manager.get_order(order_id)
        if not order or order.order_type != "limit":
            return False

        if order.status != OrderStatus.PENDING:
            return False

        # Calculate new filled quantity
        new_filled = order.filled_quantity + filled_quantity
        new_avg_price = (
            (order.filled_quantity * order.average_fill_price +
             filled_quantity * fill_price)
            / new_filled if new_filled > 0 else fill_price
        )

        # Calculate fee
        volume = filled_quantity * fill_price
        fee = volume * fee_pct

        # Update order
        status = OrderStatus.FILLED if new_filled >= order.quantity else OrderStatus.PARTIALLY_FILLED
        self.order_manager.update_order(
            order_id=order_id,
            filled_quantity=new_filled,
            average_fill_price=new_avg_price,
            status=status,
        )

        # Update fee
        order.fee += fee

        return True