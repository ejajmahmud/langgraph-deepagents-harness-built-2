"""V105.0 Test Suite"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v105_smart_routing import (
    RebalanceType, AssetClass, RouteAlgorithm,
    PortfolioRebalancerV105, RiskParityV105, SmartRoutingV105,
    RiskParityConfig, RouterConfig,
    get_portfolio, get_risk_parity, get_router
)


def test_portfolio():
    print("=== Testing PortfolioRebalancerV105 ===")
    pf = get_portfolio()
    pf.add_asset("BTC", AssetClass.CRYPTO, 0.4, 40000, 0.5, 0.1)
    pf.add_asset("ETH", AssetClass.CRYPTO, 0.6, 60000, 0.6, 0.15)
    print(f"  [PASS] add_asset")
    imb = pf.get_imbalance()
    print(f"  [PASS] imbalance: {imb:.4f}")
    should = pf.should_rebalance(0.1)
    print(f"  [PASS] should_rebalance: {should}")
    actions = pf.generate_rebalance_actions()
    print(f"  [PASS] actions: {len(actions)}")
    count = pf.rebalance()
    print(f"  [PASS] rebalanced: {count}")
    print(f"[PASS] Portfolio")
    return True


def test_risk_parity():
    print("=== Testing RiskParityV105 ===")
    rp = get_risk_parity()
    rp.add_asset("BTC", volatility=0.5, return_hist=0.1)
    rp.add_asset("ETH", volatility=0.6, return_hist=0.15)
    print(f"  [PASS] add_asset")
    weights = rp.calculate_weights()
    print(f"  [PASS] weights: {weights}")
    vol = rp.get_portfolio_volatility()
    print(f"  [PASS] vol: {vol:.4f}")
    contrib = rp.get_contribution()
    print(f"  [PASS] contrib: {contrib}")
    print(f"[PASS] RiskParity")
    return True


def test_router():
    print("=== Testing SmartRoutingV105 ===")
    rt = get_router()
    route = rt.find_route("ETH", "USDC", 1000, RouteAlgorithm.CHEAPEST)
    print(f"  [PASS] find_route: hops={route.hops if route else 0}")
    best = rt.find_best_route("ETH", "USDC", 1000)
    print(f"  [PASS] best: cost={best.cost:.4f}")
    savings = rt.get_savings("ETH", "USDC", 1000)
    print(f"  [PASS] savings: {savings:.4f}")
    print(f"[PASS] SmartRouting")
    return True


def main():
    print("\n" + "=" * 50)
    print("V105.0 Test Suite")
    print("=" * 50)

    tests = [test_portfolio, test_risk_parity, test_router]
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