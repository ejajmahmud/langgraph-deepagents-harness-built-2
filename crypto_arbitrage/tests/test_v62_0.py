"""Grid Trading Strategy Tests

Tests for V62.0 Grid Trading Strategy module.
"""

import pytest
from deepagents_crypto_trading import (
    GridTradingEngine,
    GridConfig,
    GridLevel,
    GridState,
    GridOrderSide,
    GridStatistics,
    get_grid_engine,
)


def test_grid_config_validation():
    """Test grid config validation"""
    # Valid config
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    assert config.validate() is True

    # Invalid config - lower >= upper
    config_invalid = GridConfig(
        symbol="BTCUSDT",
        lower_bound=60000.0,
        upper_bound=50000.0,
    )
    assert config_invalid.validate() is False


def test_grid_engine_initialization():
    """Test grid engine initialization"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)

    assert engine.state == GridState.INACTIVE
    assert len(engine.buy_levels) > 0
    assert len(engine.sell_levels) > 0


def test_grid_start_stop():
    """Test grid start/stop"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)

    # Start
    assert engine.start() is True
    assert engine.state == GridState.ACTIVE

    # Pause
    assert engine.pause() is True
    assert engine.state == GridState.PAUSED

    # Resume
    assert engine.resume() is True
    assert engine.state == GridState.ACTIVE

    # Stop
    assert engine.stop() is True
    assert engine.state == GridState.STOPPED


def test_grid_place_order():
    """Test placing grid orders"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)
    engine.start()

    # Place buy order
    order = engine.place_buy_order(0, "buy_order_1")
    assert order is not None
    assert order.side == GridOrderSide.BUY
    assert order.status == "pending"

    # Place sell order
    order2 = engine.place_sell_order(0, "sell_order_1")
    assert order2 is not None
    assert order2.side == GridOrderSide.SELL


def test_grid_fill_order():
    """Test order fill"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)
    engine.start()

    # Place and fill buy order
    engine.place_buy_order(0, "buy_order_1")
    result = engine.fill_order("buy_order_1", 50000.0)
    assert result is True

    # Check statistics
    stats = engine.get_statistics()
    assert stats.buy_fills == 1
    assert stats.total_trades == 1


def test_grid_statistics():
    """Test grid statistics"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)
    engine.start()

    stats = engine.get_statistics()
    assert stats.total_trades == 0
    assert stats.buy_fills == 0
    assert stats.sell_fills == 0
    assert stats.total_profit == 0.0


def test_grid_get_status():
    """Test get status"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)
    engine.start()

    status = engine.get_status()
    assert status["symbol"] == "BTCUSDT"
    assert status["state"] == "active"
    assert status["lower_bound"] == 50000.0
    assert status["upper_bound"] == 60000.0


def test_grid_serialization():
    """Test grid engine serialization"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=0.01,
    )
    engine = GridTradingEngine(config)
    engine.start()

    # To dict
    data = engine.to_dict()
    assert "config" in data
    assert "state" in data

    # From dict
    engine2 = GridTradingEngine.from_dict(data)
    assert engine2.config.symbol == "BTCUSDT"


def test_get_grid_engine():
    """Test get grid engine helper"""
    config = GridConfig(
        symbol="ETHUSDT",
        lower_bound=3000.0,
        upper_bound=4000.0,
    )
    engine = get_grid_engine(config)
    assert engine is not None
    assert engine.config.symbol == "ETHUSDT"


def test_grid_profit_loss_tracking():
    """Test profit and loss tracking"""
    config = GridConfig(
        symbol="BTCUSDT",
        lower_bound=50000.0,
        upper_bound=60000.0,
        grid_count=10,
        quantity_per_grid=1.0,
    )
    engine = GridTradingEngine(config)
    engine.start()

    # Fill buy order at 50000
    engine.place_buy_order(0, "buy_1")
    engine.fill_order("buy_1", 50000.0)

    # Fill sell order at 55000 (profit)
    engine.place_sell_order(5, "sell_1")
    engine.fill_order("sell_1", 55000.0)

    stats = engine.get_statistics()
    assert stats.total_profit == 5000.0  # (55000-50000) * 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])