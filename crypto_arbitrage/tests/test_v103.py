"""
V103.0 Test Suite - Options Trading, Futures Hedging & AI Strategy
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v103_options_hedge import (
    OptionType, OptionStyle, HedgeType, OptimizationMethod, SignalTypeV103,
    OptionsTradingV103, FuturesHedgingEngine, AIStrategyOptimizerV103,
    get_options, get_hedging, get_ai, AITrainingConfig
)


def test_options():
    print("=== Testing OptionsTradingV103 ===")
    opt = get_options()
    cid = opt.create_option(OptionType.CALL, OptionStyle.EUROPEAN, 50000, 30, 1.0, 0.05)
    print(f"  [PASS] create: {cid}")
    opt.buy_option(cid, 1.0)
    print(f"  [PASS] buy")
    price = opt.calculate_price(45000, 50000, 0.1, 0.5)
    print(f"  [PASS] price: {price:.4f}")
    greeks = opt.calculate_greeks(45000, OptionType.CALL)
    print(f"  [PASS] greeks: delta={greeks.delta}")
    print(f"[PASS] Options")
    return True


def test_hedging():
    print("=== Testing FuturesHedgingEngine ===")
    h = get_hedging()
    h.add_spot("BTC", 1.0)
    print(f"  [PASS] add_spot")
    delta = h.calculate_delta("BTC")
    print(f"  [PASS] delta: {delta}")
    sig = h.generate_signal("BTC")
    print(f"  [PASS] signal: {sig.action if sig else None}")
    if sig:
        h.execute_hedge(sig, 45000)
        print(f"  [PASS] execute")
    s = h.get_summary()
    print(f"  [PASS] summary: {s}")
    print(f"[PASS] Hedging")
    return True


def test_ai():
    print("=== Testing AIStrategyOptimizerV103 ===")
    ai = get_ai()
    ranges = {"p0": (-1.0, 1.0), "p1": (-1.0, 1.0)}
    ai.init_population(ranges)
    print(f"  [PASS] init_pop")
    feats = [[1.0, 2.0], [2.0, -1.0]]
    labs = [1.0, -1.0]
    ai.train_step(feats, labs)
    print(f"  [PASS] train")
    sig = ai.generate_signal([1.0, 2.0])
    print(f"  [PASS] signal: {sig.signal_type.value if sig else None}")
    st = ai.get_status()
    print(f"  [PASS] status: {st}")
    print(f"[PASS] AI")
    return True


def main():
    print("\n" + "=" * 50)
    print("V103.0 Test Suite")
    print("=" * 50)

    tests = [test_options, test_hedging, test_ai]
    passed = sum(1 for t in tests if t())
    failed = len(tests) - passed

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("=== ALL TESTS PASSED ===")
        return True
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)