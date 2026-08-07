"""
V102.0 Test Suite - Market Making, Liquidity Pool & Cross-Exchange
=============================================================

Tests for:
- MarketMakingEngine
- LiquidityPoolV102
- CrossExchangeEnhanced
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v102_market_making import (
    MarketMakingMode,
    PoolStatus,
    RoutingStrategy,
    OrderStatusV102,
    SideV102,
    PoolSource,
    PriceSource,
    MarketQuote,
    MakerOrder,
    PoolPosition,
    SwapQuote,
    ExchangePrice,
    MarketMakingEngine,
    LiquidityPoolV102,
    CrossExchangeEnhanced,
    get_market_making_engine,
    get_liquidity_pool,
    create_liquidity_pool,
    get_cross_exchange,
)


def test_market_making_engine():
    """Test Market Making Engine"""
    print("=== Testing MarketMakingEngine ===")

    engine = get_market_making_engine()

    # Test start/stop
    result = engine.start()
    print(f"  [PASS] start: {result}")
    assert result == True

    active = engine.is_active()
    print(f"  [PASS] is_active: {active}")
    assert active == True

    # Test spread config
    engine.set_spread_config(0.0005, 0.005, 0.001)
    print(f"  [PASS] set_spread_config")

    # Test inventory config
    engine.set_inventory_config(1.0, 0.5)
    print(f"  [PASS] set_inventory_config")

    # Test generate quotes
    bid, ask = engine.generate_quotes(45000)
    print(f"  [PASS] generate_quotes: bid={bid.price:.2f}, ask={ask.price:.2f}")
    assert ask.price > bid.price

    # Test submit quote
    quote_id = engine.submit_quote(bid)
    print(f"  [PASS] submit_quote: {quote_id}")

    # Test fill order
    result = engine.fill_order(quote_id, 0.5)
    print(f"  [PASS] fill_order: {result}")
    assert result == True

    # Test get inventory
    inventory = engine.get_inventory()
    print(f"  [PASS] get_inventory: {inventory}")

    # Test rebalance check
    needs = engine.needs_rebalance()
    print(f"  [PASS] needs_rebalance: {needs}")

    # Test rebalance
    delta, price = engine.rebalance(45000)
    print(f"  [PASS] rebalance: delta={delta}, price={price}")

    # Test stats
    stats = engine.get_stats()
    print(f"  [PASS] get_stats: revenue={stats['total_revenue']:.2f}")

    engine.stop()
    print(f"[PASS] MarketMakingEngine")
    return True


def test_liquidity_pool():
    """Test Liquidity Pool"""
    print("=== Testing LiquidityPoolV102 ===")

    pool_id = create_liquidity_pool("ETH", "USDC", PoolSource.UNISWAP)
    print(f"  [PASS] create_liquidity_pool: {pool_id}")

    pool = get_liquidity_pool(pool_id)
    assert pool is not None

    # Test add liquidity
    liq = pool.add_liquidity(10, 20000)
    print(f"  [PASS] add_liquidity: {liq:.2f}")
    assert liq > 0

    # Test get TVL
    tvl = pool.get_tvl()
    print(f"  [PASS] get_tvl: {tvl:.2f}")
    assert tvl > 0

    # Test swap quote
    quote = pool.get_swap_quote(1, "ETH")
    print(f"  [PASS] get_swap_quote: amount_out={quote.amount_out:.2f}")
    assert quote is not None

    # Test execute swap
    result = pool.execute_swap(quote)
    print(f"  [PASS] execute_swap: {result}")
    assert result == True

    # Test depth
    depth = pool.get_depth(3)
    print(f"  [PASS] get_depth: bid_depths={len(depth['bid_depths'])}")
    assert len(depth['bid_depths']) == 3

    # Test status
    status = pool.get_status()
    print(f"  [PASS] get_status: tvl={status['tvl']:.2f}")
    assert status['tvl'] > 0

    print(f"[PASS] LiquidityPoolV102")
    return True


def test_cross_exchange():
    """Test Cross Exchange"""
    print("=== Testing CrossExchangeEnhanced ===")

    ce = get_cross_exchange()

    # Test add prices
    ce.add_price(PriceSource.BINANCE, "BTCUSDT", 44000, 44050, 1000)
    ce.add_price(PriceSource.OKX, "BTCUSDT", 44010, 44060, 800)
    ce.add_price(PriceSource.BYBIT, "BTCUSDT", 44020, 44070, 600)
    print(f"  [PASS] add_prices")

    # Test aggregated price
    agg = ce.get_aggregated_price("BTCUSDT")
    print(f"  [PASS] get_aggregated_price: best_bid={agg.best_bid:.2f}, best_ask={agg.best_ask:.2f}")
    assert agg is not None

    # Test best price
    source, price = ce.get_best_price("BTCUSDT", SideV102.BID)
    print(f"  [PASS] get_best_price: source={source.value}, price={price:.2f}")

    # Test routing decision
    decision = ce.get_routing_decision("BTCUSDT", SideV102.BID, 1.0)
    print(f"  [PASS] get_routing_decision: source={decision.source.value}, total_cost={decision.total_cost:.2f}")
    assert decision is not None

    # Test savings
    savings = ce.calculate_savings("BTCUSDT", 1.0)
    print(f"  [PASS] calculate_savings: {savings}")
    assert 'savings' in savings

    # Test performance
    perf = ce.get_performance()
    print(f"  [PASS] get_performance: total_routes={perf['total_routes']}")
    assert perf['total_routes'] > 0

    print(f"[PASS] CrossExchangeEnhanced")
    return True


def test_market_quote():
    """Test Market Quote"""
    print("=== Testing MarketQuote ===")

    quote = MarketQuote.create("BTCUSDT", 45000, 0.001)
    print(f"  [PASS] create: mid={quote.mid_price:.2f}, spread={quote.spread:.2f}")
    assert quote.spread > 0
    assert quote.mid_price == 45000

    print(f"[PASS] MarketQuote")
    return True


def test_maker_order():
    """Test Maker Order"""
    print("=== Testing MakerOrder ===")

    order = MakerOrder(
        order_id="test_001",
        symbol="BTCUSDT",
        side=SideV102.BID,
        price=44000,
        quantity=1.0
    )

    print(f"  [PASS] create: {order.order_id}")
    assert order.filled == 0.0

    # Mock fill half
    order.filled = 0.5
    fill_rate = order.fill_rate()
    print(f"  [PASS] fill_rate: {fill_rate:.2f}")
    assert fill_rate == 0.5

    is_filled = order.is_filled()
    print(f"  [PASS] is_filled: {is_filled}")
    assert is_filled == False

    print(f"[PASS] MakerOrder")
    return True


def test_pool_position():
    """Test Pool Position"""
    print("=== Testing PoolPosition ===")

    pos = PoolPosition(
        token_a="ETH",
        token_b="USDC",
        reserve_a=10,
        reserve_b=20000,
        liquidity=447.21
    )

    print(f"  [PASS] create: liquidity={pos.liquidity:.2f}")
    assert pos.liquidity > 0

    print(f"[PASS] PoolPosition")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("V102.0 Test Suite - Market Making / Liquidity / Cross-Exchange")
    print("=" * 60)

    tests = [
        ("MarketMakingEngine", test_market_making_engine),
        ("LiquidityPoolV102", test_liquidity_pool),
        ("CrossExchangeEnhanced", test_cross_exchange),
        ("MarketQuote", test_market_quote),
        ("MakerOrder", test_maker_order),
        ("PoolPosition", test_pool_position),
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
            import traceback
            traceback.print_exc()
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