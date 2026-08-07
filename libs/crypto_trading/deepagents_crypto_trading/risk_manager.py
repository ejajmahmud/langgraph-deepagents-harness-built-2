"""Risk management for the crypto trading system."""

import pandas as pd
from typing import Optional

from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    Position,
    PositionStatus,
    RiskConfig,
    TradingConfig,
)


class RiskManager:
    """Risk management for cryptocurrency trading.

    Manages position sizing, stop-loss, take-profit, and exposure controls
    to minimize trading losses.
    """

    def __init__(self, config: TradingConfig) -> None:
        """Initialize risk manager.

        Args:
            config: Trading configuration.
        """
        self.config = config
        self.risk_config = config.risk_config
        self.initial_capital = config.initial_capital
        self.current_capital = config.initial_capital
        self.daily_loss = 0.0
        self.daily_reset()

    def daily_reset(self) -> None:
        """Reset daily tracking variables."""
        self.daily_loss = 0.0
        self._last_reset = pd.Timestamp.now()

    def check_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        current_positions: list[Position],
    ) -> bool:
        """Check if an opportunity passes risk checks.

        Args:
            opportunity: The arbitrage opportunity to check.
            current_positions: Current open positions.

        Returns:
            True if opportunity passes all risk checks.
        """
        # 1. Check confidence threshold
        if opportunity.confidence < self.risk_config.min_confidence:
            return False

        # 2. Check profit threshold
        if (
            opportunity.expected_profit_pct
            < self.risk_config.min_profit_pct * 100
        ):
            return False

        # 3. Check risk level
        if opportunity.risk_level > 0.5:
            return False

        # 4. Calculate position size
        position_size = self.calculate_position_size(opportunity)
        if position_size <= 0:
            return False

        # 5. Check daily loss limit
        total_pnl = sum(p.pnl for p in current_positions)
        if total_pnl < -self.risk_config.max_daily_loss_pct * self.initial_capital:
            return False

        # 6. Check total exposure
        total_exposure = sum(p.size for p in current_positions if p.status == PositionStatus.OPEN)
        if (
            total_exposure
            > self.risk_config.max_exposure_pct * self.initial_capital
        ):
            return False

        return True

    def calculate_position_size(
        self,
        opportunity: ArbitrageOpportunity,
        current_positions: Optional[list[Position]] = None,
    ) -> float:
        """Calculate position size for an opportunity.

        Args:
            opportunity: The arbitrage opportunity.
            current_positions: Current open positions (optional).

        Returns:
            Position size in quote currency.
        """
        # Available capital
        available = self.get_available_capital(current_positions or [])

        # Calculate size based on risk config
        max_by_risk = available * self.risk_config.max_position_size_pct

        # Also consider the required capital for the opportunity
        max_by_opportunity = opportunity.required_capital

        # Use the smaller of the two, but ensure minimum viable size
        size = min(max_by_risk, max_by_opportunity)

        # Enforce minimum position size
        min_size = 100.0  # Minimum $100 position

        return size if size >= min_size else 0.0

    def get_available_capital(
        self, current_positions: list[Position]
    ) -> float:
        """Get available capital for new positions.

        Args:
            current_positions: Current positions.

        Returns:
            Available capital.
        """
        used = sum(p.size for p in current_positions if p.status == PositionStatus.OPEN)
        return max(0.0, self.current_capital - used)

    def set_stop_loss(
        self, position: Position, entry_price: float
    ) -> float:
        """Calculate stop loss price for a position.

        Args:
            position: The position.
            entry_price: Entry price.

        Returns:
            Stop loss price.
        """
        return entry_price * (1 - self.risk_config.stop_loss_pct)

    def set_take_profit(
        self, position: Position, entry_price: float
    ) -> float:
        """Calculate take profit price for a position.

        Args:
            position: The position.
            entry_price: Entry price.

        Returns:
            Take profit price.
        """
        return entry_price * (1 + self.risk_config.take_profit_pct)

    def check_stop_loss(
        self, position: Position, current_price: float
    ) -> bool:
        """Check if stop loss is triggered.

        Args:
            position: The position.
            current_price: Current price.

        Returns:
            True if stop loss is triggered.
        """
        if position.status != PositionStatus.OPEN:
            return False

        if not position.stop_loss:
            return False

        # For long positions
        risk_pct = (position.entry_price - current_price) / position.entry_price

        return risk_pct >= self.risk_config.stop_loss_pct

    def check_take_profit(
        self, position: Position, current_price: float
    ) -> bool:
        """Check if take profit is triggered.

        Args:
            position: The position.
            current_price: Current price.

        Returns:
            True if take profit is triggered.
        """
        if position.status != PositionStatus.OPEN:
            return False

        if not position.take_profit:
            return False

        profit_pct = (current_price - position.entry_price) / position.entry_price

        return profit_pct >= self.risk_config.take_profit_pct

    def calculate_pnl(
        self,
        position: Position,
        exit_price: float,
        fees: float = 0.0,
    ) -> float:
        """Calculate profit/loss for a position.

        Args:
            position: The position.
            exit_price: Exit price.
            fees: Total fees paid.

        Returns:
            Profit/loss amount.
        """
        if position.side.value == "buy":
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - exit_price) * position.size

        return pnl - fees

    def update_capital(self, pnl: float) -> None:
        """Update capital after position closes.

        Args:
            pnl: Profit/loss from the trade.
        """
        self.current_capital += pnl
        self.daily_loss += pnl

    def get_risk_metrics(self) -> dict:
        """Get current risk metrics.

        Returns:
            Dictionary of risk metrics.
        """
        return {
            "current_capital": self.current_capital,
            "available_capital": self.get_available_capital([]),
            "daily_loss": self.daily_loss,
            "max_daily_loss": self.risk_config.max_daily_loss_pct * self.initial_capital,
            "max_position_pct": self.risk_config.max_position_size_pct,
            "max_exposure_pct": self.risk_config.max_exposure_pct,
            "capital_usage_pct": 1
            - (self.get_available_capital([]) / self.current_capital)
            if self.current_capital > 0
            else 0,
        }

    def reset_capital(self, new_capital: float) -> None:
        """Reset trading capital.

        Args:
            new_capital: New capital amount.
        """
        self.initial_capital = new_capital
        self.current_capital = new_capital
        self.daily_loss = 0.0