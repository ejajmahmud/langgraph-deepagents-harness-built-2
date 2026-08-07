"""Arbitrage engine for detecting and executing arbitrage opportunities."""

import asyncio
import uuid
from typing import Optional

import pandas as pd

from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    ArbitrageType,
    OrderSide,
    Position,
    PositionStatus,
    TradingConfig,
    TradingPair,
)


class ArbitrageEngine:
    """Arbitrage engine for detecting and managing arbitrage positions.

    Coordinates market analysis and risk management to identify and execute
    profitable arbitrage opportunities.
    """

    def __init__(self, config: TradingConfig) -> None:
        """Initialize the arbitrage engine.

        Args:
            config: Trading configuration.
        """
        self.config = config
        self.positions: list[Position] = []
        self.opportunities: list[ArbitrageOpportunity] = []
        self._running = False

    def add_position(self, position: Position) -> None:
        """Add a new position.

        Args:
            position: Position to add.
        """
        self.positions.append(position)

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        pnl: float,
    ) -> Optional[Position]:
        """Close a position.

        Args:
            position_id: Position ID to close.
            exit_price: Exit price.
            pnl: Profit/loss.

        Returns:
            Updated position if found.
        """
        for position in self.positions:
            if position.id == position_id:
                position.status = PositionStatus.CLOSED
                position.current_price = exit_price
                position.pnl = pnl
                position.closed_at = pd.Timestamp.now()
                return position
        return None

    def get_open_positions(self) -> list[Position]:
        """Get all open positions.

        Returns:
            List of open positions.
        """
        return [p for p in self.positions if p.status == PositionStatus.OPEN]

    def get_total_pnl(self) -> float:
        """Get total profit/loss from all positions.

        Returns:
            Total PnL.
        """
        return sum(p.pnl for p in self.positions)

    def create_position(
        self,
        opportunity: ArbitrageOpportunity,
        size: float,
        entry_price: float,
    ) -> Position:
        """Create a position from an opportunity.

        Args:
            opportunity: The arbitrage opportunity.
            size: Position size.
            entry_price: Entry price.

        Returns:
            New position.
        """
        return Position(
            id=str(uuid.uuid4()),
            arbitrage_type=opportunity.arbitrage_type,
            trading_pairs=opportunity.trading_pairs,
            entry_price=entry_price,
            current_price=entry_price,
            size=size,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=pd.Timestamp.now(),
        )

    def update_position_prices(
        self, market_prices: dict[str, float]
    ) -> list[Position]:
        """Update position prices and check exit conditions.

        Args:
            market_prices: Current market prices {symbol: price}.

        Returns:
            Positions that should be closed.
        """
        to_close = []

        for position in self.get_open_positions():
            # Get the main trading pair symbol
            if not position.trading_pairs:
                continue

            main_pair = position.trading_pairs[0]
            symbol = main_pair.symbol

            if symbol in market_prices:
                position.current_price = market_prices[symbol]

        return to_close

    def get_performance_metrics(self) -> dict:
        """Get performance metrics for the arbitrage engine.

        Returns:
            Dictionary of performance metrics.
        """
        closed_positions = [
            p for p in self.positions if p.status == PositionStatus.CLOSED
        ]

        if not closed_positions:
            return {
                "total_positions": 0,
                "open_positions": len(self.get_open_positions()),
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
            }

        wins = [p for p in closed_positions if p.pnl > 0]
        losses = [p for p in closed_positions if p.pnl <= 0]

        return {
            "total_positions": len(closed_positions),
            "open_positions": len(self.get_open_positions()),
            "total_pnl": self.get_total_pnl(),
            "win_rate": len(wins) / len(closed_positions) if closed_positions else 0,
            "avg_profit": sum(p.pnl for p in wins) / len(wins) if wins else 0.0,
            "avg_loss": sum(p.pnl for p in losses) / len(losses) if losses else 0.0,
            "by_type": {
                t.value: len(
                    [p for p in closed_positions if p.arbitrage_type == t]
                )
                for t in ArbitrageType
            },
        }

    def get_positions_summary(self) -> dict:
        """Get positions summary."""
        open_positions = self.get_open_positions()
        closed_positions = [
            p for p in self.positions if p.status == PositionStatus.CLOSED
        ]

        return {
            "total": len(self.positions),
            "open": len(open_positions),
            "closed": len(closed_positions),
            "open_pnl": sum(p.pnl for p in open_positions),
            "closed_pnl": sum(p.pnl for p in closed_positions),
            "by_type": {
                t.value: len(
                    [p for p in open_positions if p.arbitrage_type == t]
                )
                for t in ArbitrageType
            },
        }


class TriangularArbitrage:
    """Triangular arbitrage strategy implementation."""

    def __init__(self, config: TradingConfig) -> None:
        """Initialize triangular arbitrage strategy.

        Args:
            config: Trading configuration.
        """
        self.config = config

    def calculate_profit(
        self,
        prices: list[float],
        path: list[TradingPair],
    ) -> float:
        """Calculate profit from triangular arbitrage path.

        Args:
            prices: List of prices for each pair.
            path: Trading pairs path.

        Returns:
            Profit percentage.
        """
        if len(prices) != 3 or len(path) != 3:
            return 0.0

        # Simple triangular arb: A->B->C->A
        # Starting with 1 unit of A
        p1, p2, p3 = prices

        try:
            amount1 = 1.0 / p1  # Buy A with quote
            amount2 = amount1 * p2  # Trade A for B
            amount3 = amount2 / p3  # Trade B back for quote

            return (amount3 - 1.0) * 100
        except ZeroDivisionError:
            return 0.0

    def find_best_path(
        self,
        prices: dict[str, dict[str, float]],
    ) -> Optional[tuple[list[TradingPair], float]]:
        """Find best triangular arbitrage path.

        Args:
            prices: {exchange: {symbol: price}}.

        Returns:
            (path, profit_pct) or None.
        """
        # Common triangular paths
        paths = [
            (("BTC", "USDT"), ("BTC", "ETH"), ("ETH", "USDT")),
            (("ETH", "USDT"), ("ETH", "BTC"), ("BTC", "USDT")),
            (("SOL", "USDT"), ("SOL", "ETH"), ("ETH", "USDT")),
        ]

        best_profit = 0.0
        best_path: Optional[list[TradingPair]] = None

        for exchange, exchange_prices in prices.items():
            for path in paths:
                # Get prices for this path
                path_prices = []
                for base, quote in path:
                    symbol = f"{base}{quote}"
                    if symbol in exchange_prices:
                        path_prices.append(exchange_prices[symbol])
                    else:
                        break

                if len(path_prices) != 3:
                    continue

                # Calculate profit
                profit = self.calculate_profit(
                    path_prices,
                    [
                        TradingPair(base=p[0], quote=p[1], exchange=exchange)
                        for p in path
                    ],
                )

                if profit > best_profit:
                    best_profit = profit
                    best_path = [
                        TradingPair(base=p[0], quote=p[1], exchange=exchange)
                        for p in path
                    ]

        if best_path:
            return (best_path, best_profit)
        return None


class CrossExchangeArbitrage:
    """Cross-exchange arbitrage strategy implementation."""

    def __init__(self, config: TradingConfig) -> None:
        """Initialize cross-exchange arbitrage strategy.

        Args:
            config: Trading configuration.
        """
        self.config = config

    def calculate_profit(
        self,
        buy_exchange_price: float,
        sell_exchange_price: float,
    ) -> float:
        """Calculate profit from cross-exchange arbitrage.

        Args:
            buy_exchange_price: Price on buy exchange.
            sell_exchange_price: Price on sell exchange.

        Returns:
            Profit percentage.
        """
        if buy_exchange_price <= 0 or sell_exchange_price <= 0:
            return 0.0

        return ((sell_exchange_price - buy_exchange_price) / buy_exchange_price) * 100

    def find_opportunity(
        self,
        prices: dict[str, dict[str, float]],
    ) -> Optional[tuple[TradingPair, TradingPair, float]]:
        """Find cross-exchange arbitrage opportunity.

        Args:
            prices: {symbol: {exchange: price}}.

        Returns:
            (buy_pair, sell_pair, profit_pct) or None.
        """
        best_profit = 0.0
        best_buy: Optional[TradingPair] = None
        best_sell: Optional[TradingPair] = None

        for symbol, exchange_prices in prices.items():
            if len(exchange_prices) < 2:
                continue

            # Find max difference
            exchanges = list(exchange_prices.keys())
            buy_exchange = min(
                exchanges, key=lambda e: exchange_prices[e]  # type: ignore
            )
            sell_exchange = max(
                exchanges, key=lambda e: exchange_prices[e]  # type: ignore
            )

            buy_price = exchange_prices[buy_exchange]
            sell_price = exchange_prices[sell_exchange]

            profit = self.calculate_profit(buy_price, sell_price)

            if profit > best_profit:
                best_profit = profit
                base = symbol.replace("USDT", "")
                best_buy = TradingPair(base=base, quote="USDT", exchange=buy_exchange)
                best_sell = TradingPair(
                    base=base, quote="USDT", exchange=sell_exchange
                )

        if best_buy and best_sell:
            return (best_buy, best_sell, best_profit)
        return None