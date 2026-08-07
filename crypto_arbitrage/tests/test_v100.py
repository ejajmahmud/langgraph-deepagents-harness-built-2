"""
V100.0 Test Suite - Production Deployment & Advanced Order Types
============================================================

测试V100.0的生产部署和高级订单功能

版本: 4.6.0
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v100_production import (
    StageName, AdvancedOrderType, AssetType, RebalanceTrigger,
    DeploymentStatus, OrderContingencyType,
    DeploymentStage, DeploymentPipeline,
    StopLimitOrder, TrailingStopParameters, AdvancedOrderV100,
    AssetPosition, MultiAssetPortfolio, RebalanceConfig,
    DeploymentPipelineManager, AdvancedOrderManager, MultiAssetManager,
    get_deployment_manager, get_advanced_order_manager, get_multi_asset_manager,
    initialize_deployment_manager, initialize_advanced_order_manager,
    initialize_multi_asset_manager
)


def test_deployment_pipeline():
    """测试部署流水线"""
    print("\n=== Testing DeploymentPipeline ===")

    manager = initialize_deployment_manager()

    # 创建流水线
    pipeline_id = manager.create_pipeline("main_deployment")
    print(f"  Pipeline created: {pipeline_id}")

    # 执行流水线
    result = manager.execute_pipeline(pipeline_id)
    print(f"  Pipeline executed: {result}")

    # 获取状态
    status = manager.get_status()
    print(f"  Status: {status}")

    return True


def test_advanced_orders():
    """测试高级订单"""
    print("\n=== Testing AdvancedOrderManager ===")

    manager = initialize_advanced_order_manager()

    # 创建OTO订单
    primary = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.1,
        "price": 50000
    }
    contingent = {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "quantity": 0.1,
        "price": 55000
    }
    oto_id = manager.create_oto_order(primary, contingent)
    print(f"  OTO order created: {oto_id}")

    # 创建OCO订单
    order1 = {"symbol": "ETHUSDT", "side": "BUY", "quantity": 1.0, "price": 3000}
    order2 = {"symbol": "ETHUSDT", "side": "SELL", "quantity": 1.0, "price": 3500}
    oco_id = manager.create_oco_order(order1, order2)
    print(f"  OCO order created: {oco_id}")

    # 创建追踪止损
    params = TrailingStopParameters(
        trail_distance=500,
        activation_price=48000
    )
    ts_id = manager.create_trailing_stop("BNBUSDT", "BUY", 1.0, params)
    print(f"  Trailing stop created: {ts_id}")

    # 获取待执行订单
    pending = manager.get_pending_orders()
    print(f"  Pending orders: {len(pending)}")

    return True


def test_multi_asset_portfolio():
    """测试多资产组合"""
    print("\n=== Testing MultiAssetManager ===")

    manager = initialize_multi_asset_manager()

    # 创建组合
    portfolio_id = manager.create_portfolio("diversified")
    print(f"  Portfolio created: {portfolio_id}")

    # 添加资产
    manager.add_asset(portfolio_id, AssetType.CRYPTO, "BTC", 0.5, 50000)
    manager.add_asset(portfolio_id, AssetType.CRYPTO, "ETH", 10, 3000)
    print(f"  Assets added: BTC, ETH")

    # 获取组合摘要
    summary = manager.get_portfolio_summary(portfolio_id)
    print(f"  Total value: ${summary['total_value']:,.2f}" if summary.get("total_value") else "")
    print(f"  Positions: {summary.get('positions_count')}")

    # 再平衡
    weights = {"BTC": 0.6, "ETH": 0.4}
    rebalanced = manager.rebalance_portfolio(portfolio_id, weights)
    print(f"  Rebalanced: {len(rebalanced.get('adjustments', {}))} assets")

    return True


def test_asset_position():
    """测试资产持仓"""
    print("\n=== Testing AssetPosition ===")

    position = AssetPosition(
        asset_type=AssetType.CRYPTO,
        symbol="BTC",
        quantity=1.0,
        avg_price=45000,
        current_price=50000
    )

    pnl = position.calculate_pnl()
    print(f"  Position PnL: ${pnl:.2f}")

    return True


def test_trailing_stop_order():
    """测试追踪止损订单"""
    print("\n=== Testing TrailingStopParameters ===")

    params = TrailingStopParameters(
        trail_distance=200,
        trail_percentage=2.0,
        activation_price=48000
    )

    order = AdvancedOrderV100(
        order_id="test_ts_001",
        order_type=AdvancedOrderType.STOP_LIMIT_TRAILING,
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.1,
        trailing_params=params
    )

    print(f"  Order type: {order.order_type.value}")
    print(f"  Trail distance: {params.trail_distance}")

    return True


def test_advanced_order_types():
    """测试高级订单类型枚举"""
    print("\n=== Testing AdvancedOrderType Enum ===")

    for order_type in AdvancedOrderType:
        print(f"  {order_type.value}")

    return True


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("V100.0 Test Suite - Production Deployment & Advanced Orders")
    print("="*60)

    tests = [
        ("DeploymentPipeline", test_deployment_pipeline),
        ("AdvancedOrders", test_advanced_orders),
        ("MultiAssetPortfolio", test_multi_asset_portfolio),
        ("AssetPosition", test_asset_position),
        ("TrailingStopOrder", test_trailing_stop_order),
        ("AdvancedOrderTypes", test_advanced_order_types),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
                print(f"\n[PASS] {name}")
        except Exception as e:
            failed += 1
            print(f"\n[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n=== ALL TESTS PASSED ===")
    else:
        print(f"\n=== FAILURES: {failed} tests ===")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)