"""
V99.0 Test Suite - Production Integration & Live Trading
========================================================

测试V99.0的生产集成和实盘交易功能

版本: 4.5.0
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.v99_production import (
    DeploymentTier, HealthStatus, ServiceState,
    ExecutionModeV99, ConnectionStatus,
    ProductionConfigV99, ServiceHealth, DeploymentMetrics,
    ExchangeConnection, TradingSession, OrderBatch,
    ProductionManager, DeploymentValidator, ServiceRegistry,
    LiveExchangeManager, SessionManager, BatchExecutor,
    get_production_manager, get_live_exchange_manager, get_session_manager,
    initialize_production_manager, initialize_live_exchange_manager,
    initialize_session_manager
)


def test_production_config():
    """测试生产配置"""
    print("\n=== Testing ProductionConfig ===")

    # 测试有效配置
    config = ProductionConfigV99(
        tier=DeploymentTier.PRODUCTION,
        health_check_interval=60
    )
    assert config.validate() == True
    print(f"  Production config valid: {config.validate()}")

    # 测试无效配置
    bad_config = ProductionConfigV99(health_check_interval=5)
    assert bad_config.validate() == False
    print(f"  Bad config invalid: {not bad_config.validate()}")

    return True


def test_production_manager():
    """测试生产管理器"""
    print("\n=== Testing ProductionManager ===")

    manager = initialize_production_manager()
    assert manager is not None

    # 测试启动
    result = manager.start()
    assert result == True
    print(f"  Start result: {result}")

    # 注册服务
    health = ServiceHealth(
        service_name="trading_engine",
        status=HealthStatus.HEALTHY,
        uptime_seconds=3600,
        response_time_ms=25.5
    )
    manager.register_service("trading_engine", health)
    print(f"  Service registered: trading_engine")

    # 检查健康
    check = manager.check_health("trading_engine")
    print(f"  Health check: {check.status.value}")

    # 测试状态
    status = manager.get_status()
    print(f"  Status: {status}")

    # 记录指标
    metrics = DeploymentMetrics(
        uptime_percentage=99.9,
        avg_response_time_ms=30.0,
        request_count=1000,
        error_rate=0.001
    )
    manager.record_metrics(metrics)
    print(f"  Metrics recorded")

    return True


def test_live_exchange_manager():
    """测试实时交易所管理器"""
    print("\n=== Testing LiveExchangeManager ===")

    manager = initialize_live_exchange_manager()

    # 添加交易所
    assert manager.add_exchange("binance", testnet=True) == True
    assert manager.add_exchange("okx", testnet=False) == True
    print(f"  Exchanges added: binance, okx")

    # 连接交易所
    assert manager.connect("binance") == True
    conn = manager.get_connection("binance")
    print(f"  Binance connected: {conn.status.value if conn else 'error'}")
    print(f"  Latency: {conn.latency_ms:.1f}ms" if conn else "")

    # 获取状态
    status = manager.get_status()
    print(f"  Status: {status}")

    return True


def test_session_manager():
    """测试会话管理器"""
    print("\n=== Testing SessionManager ===")

    manager = initialize_session_manager()

    # 创建会话
    session_id = manager.create_session("binance", ExecutionModeV99.PAPER)
    print(f"  Session created: {session_id[:30]}...")

    # 获取当前会话
    session = manager.get_current_session()
    print(f"  Current session mode: {session.mode.value}" if session else "")

    # 更新盈亏
    manager.update_pnl(session_id, 100.5)
    session = manager.get_session(session_id)
    print(f"  PnL updated: ${session.pnl:.2f}" if session else "")

    # 关闭会话
    manager.close_session(session_id)
    session = manager.get_session(session_id)
    print(f"  Session closed: {session.status}" if session else "")

    return True


def test_batch_executor():
    """测试批次执行器"""
    print("\n=== Testing BatchExecutor ===")

    executor = BatchExecutor(max_batch_size=5)

    # 创建订单
    orders = [
        {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.01},
        {"symbol": "ETHUSDT", "side": "BUY", "quantity": 0.1},
    ]

    batch_id = executor.create_batch(orders)
    print(f"  Batch created: {batch_id}")

    # 执行批次
    result = executor.execute_batch(batch_id)
    print(f"  Batch executed: {result}")

    return True


def test_service_registry():
    """测试服务注册表"""
    print("\n=== Testing ServiceRegistry ===")

    registry = ServiceRegistry()

    # 注册服务
    health = ServiceHealth(
        service_name="api_server",
        status=HealthStatus.HEALTHY
    )
    registry.register(health)
    print(f"  Service registered: api_server")

    # 获取健康摘要
    summary = registry.get_health_summary()
    print(f"  Health summary: {summary}")

    # 列出所有服务
    services = registry.list_all()
    print(f"  Total services: {len(services)}")

    return True


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("V99.0 Test Suite - Production Integration & Live Trading")
    print("="*60)

    tests = [
        ("ProductionConfig", test_production_config),
        ("ProductionManager", test_production_manager),
        ("LiveExchangeManager", test_live_exchange_manager),
        ("SessionManager", test_session_manager),
        ("BatchExecutor", test_batch_executor),
        ("ServiceRegistry", test_service_registry),
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