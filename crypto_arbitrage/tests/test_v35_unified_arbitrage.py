#!/usr/bin/env python
"""V35.0 测试运行器"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading.unified_arbitrage_system_v35 import (
    ArbitrageTypeV35,
    ArbitrageSignalV35,
    ArbitrageOpportunityV35,
    ExecutionResultV35,
    UnifiedArbitrageSystemV35
)


def test_all():
    """运行所有测试"""
    print("=" * 60)
    print("V35.0 统一套利系统测试")
    print("=" * 60)

    passed = 0
    failed = 0

    # 测试 1: 套利类型枚举
    try:
        assert ArbitrageTypeV35.TRIANGULAR.value == "triangular"
        assert ArbitrageTypeV35.CROSS_EXCHANGE.value == "cross_exchange"
        assert ArbitrageTypeV35.FUNDING_RATE.value == "funding_rate"
        print("[PASS] 套利类型枚举测试")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 套利类型枚举: {e}")
        failed += 1

    # 测试 2: 信号强度枚举
    try:
        assert ArbitrageSignalV35.STRONG_BUY.value == "strong_buy"
        assert ArbitrageSignalV35.BUY.value == "buy"
        assert ArbitrageSignalV35.NEUTRAL.value == "neutral"
        print("[PASS] 信号强度枚举测试")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 信号强度枚举: {e}")
        failed += 1

    # 测试 3: 创建机会数据结构
    try:
        opp = ArbitrageOpportunityV35(
            opportunity_id="test_001",
            arbitrage_type=ArbitrageTypeV35.TRIANGULAR,
            signal=ArbitrageSignalV35.BUY,
            symbol="BTC/USDT",
            exchanges=["binance"],
            entry_price=50000.0,
            exit_price=50100.0,
            expected_profit=0.2,
            confidence=0.8,
            risk_score=0.2,
            position_size=1000.0,
            stop_loss=49000.0,
            take_profit=51000.0
        )
        assert opp.opportunity_id == "test_001"
        assert opp.symbol == "BTC/USDT"
        print("[PASS] 机会数据结构测试")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 机会数据结构: {e}")
        failed += 1

    # 测试 4: 执行结果数据结构
    try:
        result = ExecutionResultV35(
            opportunity_id="test_001",
            success=True,
            executed_price=50000.0,
            executed_size=1000.0,
            actual_profit=50.0,
            slippage=0.001,
            fees=5.0
        )
        assert result.success is True
        assert result.actual_profit == 50.0
        print("[PASS] 执行结果数据结构测试")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 执行结果数据结构: {e}")
        failed += 1

    # 测试 5: 系统初始化
    try:
        config = {
            'min_profit_threshold': 0.1,
            'max_position_size': 10000.0,
            'enable_triangular': True,
            'enable_cross_exchange': True,
            'enable_funding': True,
            'risk_tolerance': 0.3
        }
        system = UnifiedArbitrageSystemV35(config)
        assert system.min_profit_threshold == 0.1
        assert system.max_position_size == 10000.0
        print("[PASS] 系统初始化测试")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 系统初始化: {e}")
        failed += 1

    # 测试 6: 统计功能
    try:
        stats = system.get_statistics()
        assert stats['version'] == 'V35.0'
        assert 'total_opportunities' in stats
        print("[PASS] 统计功能测试")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 统计功能: {e}")
        failed += 1

    # 测试 7: 过滤功能
    try:
        opportunities = [
            ArbitrageOpportunityV35(
                opportunity_id="opp_001",
                arbitrage_type=ArbitrageTypeV35.TRIANGULAR,
                signal=ArbitrageSignalV35.BUY,
                symbol="BTC/USDT",
                exchanges=["binance"],
                entry_price=50000.0,
                exit_price=50100.0,
                expected_profit=0.2,
                confidence=0.8,
                risk_score=0.2,
                position_size=1000.0,
                stop_loss=49000.0,
                take_profit=51000.0,
                ttl=30
            ),
            ArbitrageOpportunityV35(
                opportunity_id="opp_002",
                arbitrage_type=ArbitrageTypeV35.CROSS_EXCHANGE,
                signal=ArbitrageSignalV35.BUY,
                symbol="ETH/USDT",
                exchanges=["binance", "okx"],
                entry_price=3000.0,
                exit_price=3010.0,
                expected_profit=0.05,  # 太低
                confidence=0.8,
                risk_score=0.2,
                position_size=5000.0,
                stop_loss=2900.0,
                take_profit=3100.0,
                ttl=30
            )
        ]
        filtered = system.filter_opportunities(opportunities)
        assert len(filtered) >= 1
        print(f"[PASS] 过滤功能测试 ({len(filtered)}/{len(opportunities)} 通过)")
        passed += 1
    except Exception as e:
        print(f"[FAIL] 过滤功能: {e}")
        failed += 1

    # 结果总结
    print("=" * 60)
    print(f"测试结果: {passed}/{passed + failed} 通过")
    print("=" * 60)

    return passed, failed


if __name__ == "__main__":
    test_all()