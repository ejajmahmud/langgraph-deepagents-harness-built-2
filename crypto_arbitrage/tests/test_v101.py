"""
V101.0 Test Suite - Real Trading API, Performance Dashboard & Risk Management
======================================================================

Tests for:
- RealTradingAPI
- PerformanceDashboardV101
- RiskManagerV101
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v101_real_trading import (
    ExchangeAPIType,
    DashboardMetricType,
    RiskCheckType,
    OrderTypeV101,
    OrderSideV101,
    OrderStatusV101,
    PositionSideV101,
    TradingModeV101,
    RiskLevelV101,
    AlertSeverityV101,
    TickerData,
    OrderBookData,
    OrderBookLevel,
    OrderV101,
    PositionV101,
    RiskLimit,
    RiskAssessment,
    DashboardConfig,
    RealTradingAPI,
    PerformanceDashboardV101,
    RiskManagerV101,
    get_real_trading_api,
    get_performance_dashboard,
    get_risk_manager,
)


def test_real_trading_api():
    """Test Real Trading API"""
    print("=== Testing RealTradingAPI ===")

    api = get_real_trading_api()

    # Test connect
    result = api.connect()
    print(f"  [PASS] connect: {result}")
    assert result == True

    # Test is_connected
    connected = api.is_connected()
    print(f"  [PASS] is_connected: {connected}")
    assert connected == True

    # Test get_ticker
    ticker = api.get_ticker("BTCUSDT")
    print(f"  [PASS] get_ticker: symbol={ticker.symbol}, bid={ticker.bid:.2f}")
    assert ticker is not None
    assert ticker.symbol == "BTCUSDT"

    # Test get_order_book
    order_book = api.get_order_book("BTCUSDT")
    print(f"  [PASS] get_order_book: spread={order_book.get_spread():.2f}")
    assert order_book is not None
    assert order_book.get_spread() > 0

    # Test create_order
    order_id = api.create_order("BTCUSDT", OrderSideV101.BUY, OrderTypeV101.MARKET, 0.001)
    order = api.get_order(order_id)
    print(f"  [PASS] create_order: order_id={order.order_id}")
    assert order is not None

    # Test cancel_order
    result = api.cancel_order(order_id)
    print(f"  [PASS] cancel_order: {result}")
    assert result == True

    # Test update_position
    api.update_position("BTCUSDT", PositionSideV101.LONG, 0.5, 45000, 46000)
    position = api.get_position("BTCUSDT")
    print(f"  [PASS] update_position: pnl={position.unrealized_pnl:.2f}")
    assert position is not None

    # Test get_balance
    balance = api.get_balance()
    print(f"  [PASS] get_balance: equity={balance['total_equity']:.2f}")
    assert balance['total_equity'] > 0

    print(f"[PASS] RealTradingAPI")
    return True


def test_performance_dashboard():
    """Test Performance Dashboard"""
    print("=== Testing PerformanceDashboardV101 ===")

    dashboard = get_performance_dashboard()

    # Test add_snapshot
    dashboard.add_snapshot(
        equity=105000,
        daily_pnl=5000,
        open_positions=3,
        closed_trades=15,
        win_rate=0.6
    )
    print(f"  [PASS] add_snapshot: equity=105000")

    # Test add more snapshots
    dashboard.add_snapshot(
        equity=110000,
        daily_pnl=5000,
        open_positions=2,
        closed_trades=20,
        win_rate=0.65
    )
    print(f"  [PASS] add more snapshots")

    # Test get_dashboard_data
    data = dashboard.get_dashboard_data()
    print(f"  [PASS] get_dashboard_data: equity={data['equity']}, win_rate={data['win_rate']:.2f}")
    assert data['equity'] > 0
    assert 'win_rate' in data

    # Test create_widget
    widget_id = dashboard.create_widget("chart", "Equity Curve")
    print(f"  [PASS] create_widget: {widget_id}")
    assert widget_id is not None

    # Test calculate_sharpe
    sharpe = dashboard.calculate_sharpe()
    print(f"  [PASS] calculate_sharpe: {sharpe:.2f}")

    print(f"[PASS] PerformanceDashboardV101")
    return True


def test_risk_manager():
    """Test Risk Manager"""
    print("=== Testing RiskManagerV101 ===")

    risk_mgr = get_risk_manager()

    # Test set_limit
    risk_mgr.set_limit(RiskCheckType.POSITION_LIMIT, 50000)
    limit = risk_mgr.get_limit(RiskCheckType.POSITION_LIMIT)
    print(f"  [PASS] set_limit: {limit.value}")
    assert limit.value == 50000

    # Test update_position
    pos = PositionV101(
        symbol="BTCUSDT",
        side=PositionSideV101.LONG,
        quantity=1.0,
        entry_price=45000,
        current_price=46000
    )
    risk_mgr.update_position("BTCUSDT", pos)
    print(f"  [PASS] update_position: added BTCUSDT")

    # Test calculate_total_exposure
    exposure = risk_mgr.calculate_total_exposure()
    print(f"  [PASS] calculate_total_exposure: {exposure:.2f}")
    assert exposure > 0

    # Test calculate_leverage
    leverage = risk_mgr.calculate_leverage()
    print(f"  [PASS] calculate_leverage: {leverage:.2f}")
    assert leverage > 0

    # Test calculate_var
    var = risk_mgr.calculate_var()
    print(f"  [PASS] calculate_var: {var:.2f}")
    assert var > 0

    # Test check_risk
    assessment = risk_mgr.check_risk()
    print(f"  [PASS] check_risk: level={assessment.risk_level.value}, score={assessment.score:.2f}")
    assert assessment.risk_level in [RiskLevelV101.LOW, RiskLevelV101.HIGH, RiskLevelV101.CRITICAL]

    # Test can_trade
    can_trade, reason = risk_mgr.can_trade("ETHUSDT", 0.5, 3000)
    print(f"  [PASS] can_trade: {can_trade}, reason={reason}")

    print(f"[PASS] RiskManagerV101")
    return True


def test_order_book_analysis():
    """Test Order Book Analysis"""
    print("=== Testing OrderBookData ===")

    import random
    # Create prices with actual spread
    base = 40000
    bids = [OrderBookLevel(price=base - (i+1) * 1, quantity=random.uniform(0.1, 5)) for i in range(10)]
    asks = [OrderBookLevel(price=base + (i+1) * 1, quantity=random.uniform(0.1, 5)) for i in range(10)]

    order_book = OrderBookData(symbol="BTCUSDT", bids=bids, asks=asks)

    spread = order_book.get_spread()
    print(f"  [PASS] get_spread: {spread:.2f}")
    assert spread > 0

    mid_price = order_book.get_mid_price()
    print(f"  [PASS] get_mid_price: {mid_price:.2f}")
    assert mid_price == base

    depth = order_book.get_depth(5)
    print(f"  [PASS] get_depth: bid_volume={depth['bid_volume']:.2f}, imbalance={depth['imbalance']:.2f}")
    assert 'imbalance' in depth

    print(f"[PASS] OrderBookData")
    return True


def test_risk_limits():
    """Test Risk Limits"""
    print("=== Testing RiskLimits ===")

    limit = RiskLimit(
        limit_type=RiskCheckType.POSITION_LIMIT,
        value=100000,
        current_value=50000,
        severity=AlertSeverityV101.WARNING
    )

    is_breached = limit.is_breached()
    print(f"  [PASS] is_breached: {is_breached}")
    assert is_breached == False

    limit.current_value = 110000
    is_breached = limit.is_breached()
    print(f"  [PASS] is_breached after update: {is_breached}")
    assert is_breached == True

    print(f"[PASS] RiskLimits")
    return True


def test_position_calculations():
    """Test Position Calculations"""
    print("=== Testing PositionV101 ===")

    pos = PositionV101(
        symbol="BTCUSDT",
        side=PositionSideV101.LONG,
        quantity=1.0,
        entry_price=45000,
        current_price=46000,
        leverage=3.0
    )

    pnl = pos.calculate_pnl()
    print(f"  [PASS] calculate_pnl: {pnl:.2f}")
    assert pnl == 1000

    roi = pos.calculate_roi()
    print(f"  [PASS] calculate_roi: {roi:.4f}")
    assert roi > 0

    # Test short
    pos_short = PositionV101(
        symbol="BTCUSDT",
        side=PositionSideV101.SHORT,
        quantity=1.0,
        entry_price=45000,
        current_price=46000
    )
    pnl_short = pos_short.calculate_pnl()
    print(f"  [PASS] short pnl: {pnl_short:.2f}")
    assert pnl_short == -1000

    print(f"[PASS] PositionV101")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("V101.0 Test Suite - Real Trading API / Dashboard / Risk")
    print("=" * 60)

    tests = [
        ("RealTradingAPI", test_real_trading_api),
        ("PerformanceDashboardV101", test_performance_dashboard),
        ("RiskManagerV101", test_risk_manager),
        ("OrderBookAnalysis", test_order_book_analysis),
        ("RiskLimits", test_risk_limits),
        ("PositionCalculations", test_position_calculations),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("=== ALL TESTS PASSED ===")
        return True
    else:
        print("=== SOME TESTS FAILED ===")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)