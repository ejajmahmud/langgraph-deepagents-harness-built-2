"""测试动态参数调整器 (DynamicParameterAdjuster)

V3.9 迭代核心模块 - 动态参数调整功能测试

运行方式:
    python tests/test_dynamic_parameter_adjuster.py
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.adaptive_risk_manager import (
    RiskLevel,
    MarketData,
    RiskMetrics,
    RiskParameters,
    RiskProfile,
    AdaptiveRiskManager,
    TrendDirection,
    RiskThresholds,
    AdjustmentHistory,
    DynamicParameterAdjuster
)


def print_header(title: str) -> None:
    """打印测试标题"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_test(name: str, passed: bool, message: str = "") -> None:
    """打印测试结果"""
    status = "PASS" if passed else "FAIL"
    symbol = "[+]" if passed else "[-]"
    print(f"{symbol} {status} - {name}")
    if message:
        print(f"    {message}")


def assert_equal(actual: Any, expected: Any, test_name: str) -> bool:
    """断言相等"""
    if actual != expected:
        print(f"    Expected: {expected}, Got: {actual}")
        return False
    return True


def assert_true(condition: bool, test_name: str) -> bool:
    """断言为真"""
    if not condition:
        print(f"    Condition is False")
        return False
    return True


def assert_in_range(value: float, min_val: float, max_val: float, test_name: str) -> bool:
    """断言值在范围内"""
    if not (min_val <= value <= max_val):
        print(f"    Value {value} not in range [{min_val}, {max_val}]")
        return False
    return True


def assert_is_instance(obj: Any, expected_type: type, test_name: str) -> bool:
    """断言实例类型"""
    if not isinstance(obj, expected_type):
        print(f"    Expected type {expected_type}, got {type(obj)}")
        return False
    return True


# ==================== 数据结构测试 ====================

def test_trend_direction_enum():
    """测试趋势方向枚举"""
    print_header("动态参数调整器: TrendDirection 枚举")

    passed = True
    passed &= assert_is_instance(TrendDirection.BULLISH, TrendDirection, "TrendDirection.BULLISH 是 TrendDirection 实例")
    passed &= assert_is_instance(TrendDirection.BEARISH, TrendDirection, "TrendDirection.BEARISH 是 TrendDirection 实例")
    passed &= assert_is_instance(TrendDirection.SIDEWAYS, TrendDirection, "TrendDirection.SIDEWAYS 是 TrendDirection 实例")

    passed &= assert_equal(TrendDirection.BULLISH.value, "bullish", "TrendDirection.BULLISH 值为 'bullish'")
    passed &= assert_equal(TrendDirection.BEARISH.value, "bearish", "TrendDirection.BEARISH 值为 'bearish'")
    passed &= assert_equal(TrendDirection.SIDEWAYS.value, "sideways", "TrendDirection.SIDEWAYS 值为 'sideways'")

    print_test("TrendDirection 枚举测试", passed)
    return passed


def test_risk_thresholds_dataclass():
    """测试风险阈值数据类"""
    print_header("动态参数调整器: RiskThresholds 数据类")

    thresholds = RiskThresholds(
        max_drawdown=10.0,
        max_daily_loss=500.0,
        max_position_risk=0.02,
        min_liquidity_ratio=0.5
    )

    passed = True
    passed &= assert_equal(thresholds.max_drawdown, 10.0, "max_drawdown 正确")
    passed &= assert_equal(thresholds.max_daily_loss, 500.0, "max_daily_loss 正确")
    passed &= assert_equal(thresholds.max_position_risk, 0.02, "max_position_risk 正确")
    passed &= assert_equal(thresholds.min_liquidity_ratio, 0.5, "min_liquidity_ratio 正确")

    print_test("RiskThresholds 数据类测试", passed)
    return passed


def test_adjustment_history_dataclass():
    """测试调整历史数据类"""
    print_header("动态参数调整器: AdjustmentHistory 数据类")

    history = AdjustmentHistory(
        timestamp=1234567890.0,
        original_value=1000.0,
        adjusted_value=800.0,
        adjustment_reason="高风险市场条件",
        risk_score=0.75
    )

    passed = True
    passed &= assert_equal(history.timestamp, 1234567890.0, "timestamp 正确")
    passed &= assert_equal(history.original_value, 1000.0, "original_value 正确")
    passed &= assert_equal(history.adjusted_value, 800.0, "adjusted_value 正确")
    passed &= assert_equal(history.adjustment_reason, "高风险市场条件", "adjustment_reason 正确")
    passed &= assert_equal(history.risk_score, 0.75, "risk_score 正确")

    print_test("AdjustmentHistory 数据类测试", passed)
    return passed


# ==================== DynamicParameterAdjuster 测试 ====================

async def test_dynamic_parameter_adjuster_initialization():
    """测试动态参数调整器初始化"""
    print_header("DynamicParameterAdjuster: 初始化")

    config = {
        "max_adjustment_factor": 0.5,
        "min_adjustment_factor": 0.1,
        "smooth_transition": True
    }

    adjuster = DynamicParameterAdjuster(config)

    passed = True
    passed &= assert_is_instance(adjuster, DynamicParameterAdjuster, "adjuster 是 DynamicParameterAdjuster 实例")
    passed &= assert_true(adjuster is not None, "adjuster 不为 None")

    print_test("DynamicParameterAdjuster 初始化测试", passed)
    return passed


async def test_adjust_risk_thresholds_high_risk():
    """测试高风险场景下的风险阈值调整"""
    print_header("DynamicParameterAdjuster: 高风险阈值调整")

    adjuster = DynamicParameterAdjuster({})

    current_thresholds = RiskThresholds(
        max_drawdown=10.0,
        max_daily_loss=500.0,
        max_position_risk=0.02,
        min_liquidity_ratio=0.5
    )

    metrics = RiskMetrics(
        market_risk=0.85,
        liquidity_risk=0.70,
        execution_risk=0.60,
        system_risk=0.30,
        overall_risk_score=0.80,
        risk_level=RiskLevel.HIGH
    )

    risk_profile = RiskProfile(
        metrics=metrics,
        parameters=RiskParameters(
            max_position_size=1000.0,
            stop_loss_pct=2.0,
            leverage_ratio=1.0,
            max_daily_loss=500.0,
            max_total_exposure=5000.0
        ),
        timestamp=1234567890.0
    )

    adjusted_thresholds = await adjuster.adjust_risk_thresholds(current_thresholds, risk_profile)

    passed = True
    passed &= assert_is_instance(adjusted_thresholds, RiskThresholds, "adjusted_thresholds 是 RiskThresholds 实例")
    passed &= assert_true(adjusted_thresholds.max_drawdown < current_thresholds.max_drawdown,
                         "高风险场景应降低最大回撤阈值")
    passed &= assert_true(adjusted_thresholds.max_daily_loss < current_thresholds.max_daily_loss,
                         "高风险场景应降低最大日亏损阈值")
    passed &= assert_true(adjusted_thresholds.max_position_risk < current_thresholds.max_position_risk,
                         "高风险场景应降低最大仓位风险")
    passed &= assert_true(adjusted_thresholds.min_liquidity_ratio > current_thresholds.min_liquidity_ratio,
                         "高风险场景应提高最小流动性比率")

    print_test(f"高风险阈值调整 (回撤: {current_thresholds.max_drawdown:.1f}% -> {adjusted_thresholds.max_drawdown:.1f}%)",
              passed)
    return passed


async def test_adjust_risk_thresholds_low_risk():
    """测试低风险场景下的风险阈值调整"""
    print_header("DynamicParameterAdjuster: 低风险阈值调整")

    adjuster = DynamicParameterAdjuster({})

    current_thresholds = RiskThresholds(
        max_drawdown=10.0,
        max_daily_loss=500.0,
        max_position_risk=0.02,
        min_liquidity_ratio=0.5
    )

    metrics = RiskMetrics(
        market_risk=0.15,
        liquidity_risk=0.10,
        execution_risk=0.10,
        system_risk=0.05,
        overall_risk_score=0.15,
        risk_level=RiskLevel.LOW
    )

    risk_profile = RiskProfile(
        metrics=metrics,
        parameters=RiskParameters(
            max_position_size=1000.0,
            stop_loss_pct=2.0,
            leverage_ratio=1.0,
            max_daily_loss=500.0,
            max_total_exposure=5000.0
        ),
        timestamp=1234567890.0
    )

    adjusted_thresholds = await adjuster.adjust_risk_thresholds(current_thresholds, risk_profile)

    passed = True
    passed &= assert_is_instance(adjusted_thresholds, RiskThresholds, "adjusted_thresholds 是 RiskThresholds 实例")
    passed &= assert_true(adjusted_thresholds.max_drawdown >= current_thresholds.max_drawdown,
                         "低风险场景应保持或放宽最大回撤阈值")
    passed &= assert_true(adjusted_thresholds.min_liquidity_ratio <= current_thresholds.min_liquidity_ratio,
                         "低风险场景应降低或保持最小流动性比率")

    print_test(f"低风险阈值调整 (回撤: {current_thresholds.max_drawdown:.1f}% -> {adjusted_thresholds.max_drawdown:.1f}%)",
              passed)
    return passed


async def test_adjust_position_size():
    """测试仓位大小调整"""
    print_header("DynamicParameterAdjuster: 仓位大小调整")

    adjuster = DynamicParameterAdjuster({})

    base_size = 1000.0
    market_conditions = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.02,
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    # 测试低风险场景
    adjusted_low = await adjuster.adjust_position_size(base_size, RiskLevel.LOW, market_conditions)
    passed = assert_true(adjusted_low >= base_size, "低风险场景应保持或增加仓位大小")

    # 测试高风险场景
    adjusted_high = await adjuster.adjust_position_size(base_size, RiskLevel.HIGH, market_conditions)
    passed &= assert_true(adjusted_high < base_size, "高风险场景应减少仓位大小")

    # 测试极高风险场景
    adjusted_critical = await adjuster.adjust_position_size(base_size, RiskLevel.CRITICAL, market_conditions)
    passed &= assert_true(adjusted_critical < adjusted_high, "极高风险场景应进一步减少仓位大小")

    print_test(f"仓位大小调整 (低: {adjusted_low:.2f}, 高: {adjusted_high:.2f}, 极高: {adjusted_critical:.2f})",
              passed)
    return passed


async def test_adjust_stop_loss():
    """测试止损水平调整"""
    print_header("DynamicParameterAdjuster: 止损水平调整")

    adjuster = DynamicParameterAdjuster({})

    current_stop_loss = 2.0

    # 测试低波动率 + 看涨趋势
    adjusted_bullish_low = await adjuster.adjust_stop_loss(current_stop_loss, 0.01, TrendDirection.BULLISH)
    passed = assert_true(adjusted_bullish_low <= current_stop_loss, "低波动+看涨应保持或降低止损")

    # 测试高波动率 + 看跌趋势
    adjusted_bearish_high = await adjuster.adjust_stop_loss(current_stop_loss, 0.08, TrendDirection.BEARISH)
    passed &= assert_true(adjusted_bearish_high >= current_stop_loss, "高波动+看跌应增加止损")

    # 测试横盘趋势
    adjusted_sideways = await adjuster.adjust_stop_loss(current_stop_loss, 0.02, TrendDirection.SIDEWAYS)
    passed &= assert_in_range(adjusted_sideways, 0.5, 10.0, "横盘止损应在合理范围内")

    print_test(f"止损调整 (看涨低波: {adjusted_bullish_low:.2f}%, 看跌高波: {adjusted_bearish_high:.2f}%, 横盘: {adjusted_sideways:.2f}%)",
              passed)
    return passed


async def test_optimize_leverage():
    """测试杠杆倍数优化"""
    print_header("DynamicParameterAdjuster: 杠杆倍数优化")

    adjuster = DynamicParameterAdjuster({})

    current_leverage = 2.0

    # 低风险 + 高市场稳定性
    leverage_low_risk = await adjuster.optimize_leverage(current_leverage, 0.2, 0.9)
    passed = assert_true(leverage_low_risk >= current_leverage, "低风险+高稳定性应保持或增加杠杆")

    # 高风险 + 低市场稳定性
    leverage_high_risk = await adjuster.optimize_leverage(current_leverage, 0.8, 0.3)
    passed &= assert_true(leverage_high_risk <= current_leverage, "高风险+低稳定性应降低杠杆")

    # 极端风险场景
    leverage_critical = await adjuster.optimize_leverage(5.0, 0.95, 0.2)
    passed &= assert_in_range(leverage_critical, 1.0, 3.0, "极端风险杠杆应限制在合理范围")

    print_test(f"杠杆优化 (低风险: {leverage_low_risk:.2f}x, 高风险: {leverage_high_risk:.2f}x, 极端: {leverage_critical:.2f}x)",
              passed)
    return passed


async def test_smooth_adjustment():
    """测试平滑调整机制"""
    print_header("DynamicParameterAdjuster: 平滑调整机制")

    config = {
        "smooth_transition": True,
        "max_adjustment_step": 0.3
    }

    adjuster = DynamicParameterAdjuster(config)

    base_size = 1000.0
    market_conditions = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=10000.0,  # 低流动性
        volatility=0.15,  # 高波动率
        order_book_depth={"bids": 5000, "asks": 5000},
        timestamp=1234567890.0
    )

    # 第一次调整（高风险）
    adjusted_1 = await adjuster.adjust_position_size(base_size, RiskLevel.CRITICAL, market_conditions)

    # 检查调整历史
    history = adjuster.get_adjustment_history()
    passed = assert_true(len(history) > 0, "应该记录调整历史")

    if history:
        passed &= assert_equal(history[0].original_value, base_size, "历史记录原始值正确")
        passed &= assert_is_instance(history[0], AdjustmentHistory, "历史记录是 AdjustmentHistory 实例")

    print_test(f"平滑调整机制 (原始: {base_size:.2f}, 调整后: {adjusted_1:.2f}, 历史记录: {len(history)}条)",
              passed)
    return passed


async def test_integration_with_adaptive_risk_manager():
    """测试与 AdaptiveRiskManager 的集成"""
    print_header("DynamicParameterAdjuster: 与 AdaptiveRiskManager 集成")

    config = {
        "max_daily_loss": 500,
        "max_position_size": 1000,
        "max_total_exposure": 5000,
        "max_drawdown": 10.0,
        "adaptive": {
            "volatility_threshold": 0.03,
            "liquidity_threshold": 0.5,
            "position_adjustment_factor": 0.5
        }
    }

    manager = AdaptiveRiskManager(config)
    adjuster = DynamicParameterAdjuster(config.get("adaptive", {}))

    # 创建高风险市场数据
    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=10000.0,
        volatility=0.10,
        order_book_depth={"bids": 5000, "asks": 5000},
        timestamp=1234567890.0
    )

    # 获取风险配置
    risk_profile = await manager.assess_overall_risk(market_data)

    # 调整风险阈值
    current_thresholds = RiskThresholds(
        max_drawdown=10.0,
        max_daily_loss=500.0,
        max_position_risk=0.02,
        min_liquidity_ratio=0.5
    )

    adjusted_thresholds = await adjuster.adjust_risk_thresholds(current_thresholds, risk_profile)

    # 调整仓位大小
    adjusted_position = await adjuster.adjust_position_size(
        1000.0,
        risk_profile.metrics.risk_level,
        market_data
    )

    # 调整止损
    adjusted_stop_loss = await adjuster.adjust_stop_loss(
        2.0,
        market_data.volatility,
        TrendDirection.BEARISH
    )

    # 优化杠杆
    optimized_leverage = await adjuster.optimize_leverage(
        2.0,
        risk_profile.metrics.overall_risk_score,
        0.8  # 假设市场稳定性
    )

    passed = True
    passed &= assert_is_instance(adjusted_thresholds, RiskThresholds, "风险阈值调整正确")
    passed &= assert_true(adjusted_position < 1000.0, "高风险场景仓位应减小")
    passed &= assert_true(adjusted_stop_loss > 2.0, "高风险场景止损应增大")
    passed &= assert_true(optimized_leverage <= 2.0, "高风险场景杠杆应降低")

    print_test(f"集成测试 (风险: {risk_profile.metrics.overall_risk_score:.3f}, "
              f"仓位: {adjusted_position:.2f}, "
              f"止损: {adjusted_stop_loss:.2f}%, "
              f"杠杆: {optimized_leverage:.2f}x)",
              passed)
    return passed


async def test_edge_cases_dynamic_adjuster():
    """测试动态参数调整器的边界条件"""
    print_header("DynamicParameterAdjuster: 边界条件测试")

    adjuster = DynamicParameterAdjuster({})
    market_conditions = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.02,
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    passed = True

    # 测试零基础仓位
    adjusted_zero = await adjuster.adjust_position_size(0.0, RiskLevel.LOW, market_conditions)
    passed &= assert_equal(adjusted_zero, 0.0, "零基础仓位应返回零")

    # 测试零波动率止损
    adjusted_zero_vol = await adjuster.adjust_stop_loss(2.0, 0.0, TrendDirection.BULLISH)
    passed &= assert_in_range(adjusted_zero_vol, 0.5, 10.0, "零波动率止损应在范围内")

    # 测试极端波动率止损
    adjusted_extreme_vol = await adjuster.adjust_stop_loss(2.0, 1.0, TrendDirection.BEARISH)
    passed &= assert_in_range(adjusted_extreme_vol, 0.5, 10.0, "极端波动率止损应在范围内")

    # 测试零杠杆
    leverage_zero = await adjuster.optimize_leverage(0.0, 0.5, 0.8)
    passed &= assert_equal(leverage_zero, 1.0, "零杠杆应调整为1")

    # 测试极高杠杆
    leverage_high = await adjuster.optimize_leverage(100.0, 0.9, 0.2)
    passed &= assert_in_range(leverage_high, 1.0, 5.0, "极高杠杆应限制在范围内")

    print_test("边界条件测试", passed)
    return passed


# ==================== 主测试函数 ====================

async def run_all_tests():
    """运行所有动态参数调整器测试"""
    print("\n" + "="*80)
    print(" 动态参数调整器 (DynamicParameterAdjuster) 测试套件")
    print(" V3.9 迭代 - TDD 开发")
    print("="*80)

    results = []

    # 数据结构测试
    results.append(("TrendDirection 枚举", test_trend_direction_enum()))
    results.append(("RiskThresholds 数据类", test_risk_thresholds_dataclass()))
    results.append(("AdjustmentHistory 数据类", test_adjustment_history_dataclass()))

    # DynamicParameterAdjuster 测试
    results.append(("初始化", await test_dynamic_parameter_adjuster_initialization()))
    results.append(("高风险阈值调整", await test_adjust_risk_thresholds_high_risk()))
    results.append(("低风险阈值调整", await test_adjust_risk_thresholds_low_risk()))
    results.append(("仓位大小调整", await test_adjust_position_size()))
    results.append(("止损水平调整", await test_adjust_stop_loss()))
    results.append(("杠杆倍数优化", await test_optimize_leverage()))
    results.append(("平滑调整机制", await test_smooth_adjustment()))
    results.append(("与 AdaptiveRiskManager 集成", await test_integration_with_adaptive_risk_manager()))
    results.append(("边界条件", await test_edge_cases_dynamic_adjuster()))

    # 打印汇总
    print_header("动态参数调整器测试结果")

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[+]" if result else "[-]"
        print(f"{symbol} {status} - {name}")

    print("\n" + "="*80)
    print(f" 动态参数调整器测试: {passed_tests}/{total_tests} 通过")
    print(f" 成功率: {passed_tests/total_tests*100:.1f}%")
    print("="*80)

    if failed_tests > 0:
        print(f"\n {failed_tests} 个动态参数调整器测试失败")
        return False
    else:
        print("\n 所有动态参数调整器测试通过!")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
