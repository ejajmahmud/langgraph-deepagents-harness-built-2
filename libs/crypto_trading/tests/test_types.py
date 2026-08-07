"""Tests for the crypto trading system types."""

import pandas as pd
import pytest

from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    ArbitrageType,
    Exchange,
    OrderSide,
    OrderType,
    Position,
    PositionStatus,
    Price,
    RiskConfig,
    TradingConfig,
    TradingPair,
)


class TestExchange:
    """Tests for Exchange enum."""

    def test_exchange_values(self) -> None:
        """Test exchange values."""
        assert Exchange.BINANCE.value == "binance"
        assert Exchange.COINBASE.value == "coinbase"
        assert Exchange.BYBIT.value == "bybit"
        assert Exchange.OKX.value == "okx"
        assert Exchange.KRAKEN.value == "kraken"


class TestTradingPair:
    """Tests for TradingPair."""

    def test_symbol_property(self) -> None:
        """Test symbol property."""
        pair = TradingPair(base="BTC", quote="USDT", exchange=Exchange.BINANCE)
        assert pair.symbol == "BTCUSDT"

    def test_symbol_property_eth(self) -> None:
        """Test symbol property for ETH."""
        pair = TradingPair(base="ETH", quote="USDT", exchange=Exchange.BINANCE)
        assert pair.symbol == "ETHUSDT"


class TestPrice:
    """Tests for Price."""

    def test_price_creation(self) -> None:
        """Test price creation."""
        timestamp = pd.Timestamp.now()
        price = Price(
            symbol="BTCUSDT",
            price=67500.0,
            volume_24h=10_000_000.0,
            timestamp=timestamp,
            exchange=Exchange.BINANCE,
        )
        assert price.symbol == "BTCUSDT"
        assert price.price == 67500.0
        assert price.exchange == Exchange.BINANCE


class TestPosition:
    """Tests for Position."""

    def test_position_creation(self) -> None:
        """Test position creation."""
        now = pd.Timestamp.now()
        position = Position(
            id="test-123",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[
                TradingPair(base="BTC", quote="USDT", exchange=Exchange.BINANCE)
            ],
            entry_price=67000.0,
            current_price=67000.0,
            size=0.1,
            side=OrderSide.BUY,
            status=PositionStatus.OPEN,
            pnl=0.0,
            opened_at=now,
        )
        assert position.id == "test-123"
        assert position.status == PositionStatus.OPEN
        assert position.arbitrage_type == ArbitrageType.TRIANGULAR


class TestRiskConfig:
    """Tests for RiskConfig."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = RiskConfig()
        assert config.max_position_size_pct == 0.1
        assert config.max_daily_loss_pct == 0.05
        assert config.max_exposure_pct == 0.25
        assert config.stop_loss_pct == 0.02
        assert config.take_profit_pct == 0.05
        assert config.min_confidence == 0.7
        assert config.min_profit_pct == 0.005


class TestTradingConfig:
    """Tests for TradingConfig."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = TradingConfig()
        assert config.initial_capital == 10000.0
        assert config.check_interval_seconds == 5
        assert len(config.enabled_exchanges) == 3
        assert config.enabled_exchanges[0] == Exchange.BINANCE

    def test_post_init(self) -> None:
        """Test post init."""
        config = TradingConfig()
        assert ArbitrageType.TRIANGULAR in config.enabled_strategies
        assert ArbitrageType.CROSS_EXCHANGE in config.enabled_strategies


class TestArbitrageOpportunity:
    """Tests for ArbitrageOpportunity."""

    def test_opportunity_creation(self) -> None:
        """Test opportunity creation."""
        opportunity = ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=[
                TradingPair(base="BTC", quote="USDT", exchange=Exchange.BINANCE)
            ],
            expected_profit_pct=1.5,
            required_capital=5000.0,
            estimated_duration_seconds=30,
            risk_level=0.3,
            confidence=0.8,
            exchanges=[Exchange.BINANCE],
        )
        assert opportunity.expected_profit_pct == 1.5
        assert opportunity.confidence == 0.8
        assert opportunity.arbitrage_type == ArbitrageType.TRIANGULAR