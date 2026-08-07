"""测试自适应风险管理器 (AdaptiveRiskManager)

测试 V3.9 迭代中的自适应风险管理器核心功能：
1. 数据结构测试 (RiskLevel, MarketData, RiskMetrics, RiskParameters, RiskProfile)
2. 市场风险计算器测试
3. 流动性风险评估器测试
4. 执行风险评估器测试
5. 系统风险评估器测试
6. 自适应风险管理器主类测试
7. 集成测试

运行方式:
    python tests/test_adaptive_risk_manager.py
"""

import asyncio
import sys
import os
import threading
from collections import deque
from datetime import datetime
from typing import TypedDict
from unittest.mock import Mock, AsyncMock, patch, MagicMock
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
    MarketRiskCalculator,
    LiquidityRiskAssessor,
    ExecutionRiskEvaluator,
    SystemRiskMonitor,
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

def test_risk_level_enum():
    """测试风险级别枚举"""
    print_header("数据结构测试: RiskLevel 枚举")

    passed = True
    passed &= assert_is_instance(RiskLevel.LOW, RiskLevel, "RiskLevel.LOW 是 RiskLevel 实例")
    passed &= assert_is_instance(RiskLevel.MEDIUM, RiskLevel, "RiskLevel.MEDIUM 是 RiskLevel 实例")
    passed &= assert_is_instance(RiskLevel.HIGH, RiskLevel, "RiskLevel.HIGH 是 RiskLevel 实例")
    passed &= assert_is_instance(RiskLevel.CRITICAL, RiskLevel, "RiskLevel.CRITICAL 是 RiskLevel 实例")

    passed &= assert_equal(RiskLevel.LOW.value, "low", "RiskLevel.LOW 值为 'low'")
    passed &= assert_equal(RiskLevel.MEDIUM.value, "medium", "RiskLevel.MEDIUM 值为 'medium'")
    passed &= assert_equal(RiskLevel.HIGH.value, "high", "RiskLevel.HIGH 值为 'high'")
    passed &= assert_equal(RiskLevel.CRITICAL.value, "critical", "RiskLevel.CRITICAL 值为 'critical'")

    print_test("RiskLevel 枚举测试", passed)
    return passed


def test_market_data():
    """测试市场数据结构"""
    print_header("数据结构测试: MarketData")

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000.0,
        volatility=0.02,
        order_book_depth={"bids": 100000, "asks": 100000},
        timestamp=1234567890.0
    )

    passed = True
    passed &= assert_equal(market_data.symbol, "BTC/USDT", "symbol 正确")
    passed &= assert_equal(market_data.price, 50000.0, "price 正确")
    passed &= assert_equal(market_data.volume, 1000.0, "volume 正确")
    passed &= assert_equal(market_data.volatility, 0.02, "volatility 正确")
    passed &= assert_equal(market_data.timestamp, 1234567890.0, "timestamp 正确")
    passed &= assert_equal(market_data.order_book_depth["bids"], 100000, "order_book_depth.bids 正确")

    print_test("MarketData 结构测试", passed)
    return passed


def test_risk_metrics():
    """测试风险指标结构"""
    print_header("数据结构测试: RiskMetrics")

    metrics = RiskMetrics(
        market_risk=0.3,
        liquidity_risk=0.2,
        execution_risk=0.15,
        system_risk=0.1,
        overall_risk_score=0.25,
        risk_level=RiskLevel.MEDIUM
    )

    passed = True
    passed &= assert_equal(metrics.market_risk, 0.3, "market_risk 正确")
    passed &= assert_equal(metrics.liquidity_risk, 0.2, "liquidity_risk 正确")
    passed &= assert_equal(metrics.execution_risk, 0.15, "execution_risk 正确")
    passed &= assert_equal(metrics.system_risk, 0.1, "system_risk 正确")
    passed &= assert_equal(metrics.overall_risk_score, 0.25, "overall_risk_score 正确")
    passed &= assert_equal(metrics.risk_level, RiskLevel.MEDIUM, "risk_level 正确")

    print_test("RiskMetrics 结构测试", passed)
    return passed


def test_risk_parameters():
    """测试风险参数结构"""
    print_header("数据结构测试: RiskParameters")

    params = RiskParameters(
        max_position_size=1000.0,
        stop_loss_pct=2.0,
        leverage_ratio=1.0,
        max_daily_loss=500.0,
        max_total_exposure=5000.0
    )

    passed = True
    passed &= assert_equal(params.max_position_size, 1000.0, "max_position_size 正确")
    passed &= assert_equal(params.stop_loss_pct, 2.0, "stop_loss_pct 正确")
    passed &= assert_equal(params.leverage_ratio, 1.0, "leverage_ratio 正确")
    passed &= assert_equal(params.max_daily_loss, 500.0, "max_daily_loss 正确")
    passed &= assert_equal(params.max_total_exposure, 5000.0, "max_total_exposure 正确")

    print_test("RiskParameters 结构测试", passed)
    return passed


def test_risk_profile():
    """测试风险配置文件结构"""
    print_header("数据结构测试: RiskProfile")

    metrics = RiskMetrics(
        market_risk=0.3,
        liquidity_risk=0.2,
        execution_risk=0.15,
        system_risk=0.1,
        overall_risk_score=0.25,
        risk_level=RiskLevel.MEDIUM
    )

    params = RiskParameters(
        max_position_size=1000.0,
        stop_loss_pct=2.0,
        leverage_ratio=1.0,
        max_daily_loss=500.0,
        max_total_exposure=5000.0
    )

    profile = RiskProfile(
        metrics=metrics,
        parameters=params,
        timestamp=1234567890.0,
        recommendations=["建议减少仓位", "关注流动性"]
    )

    passed = True
    passed &= assert_is_instance(profile.metrics, RiskMetrics, "metrics 是 RiskMetrics 实例")
    passed &= assert_is_instance(profile.parameters, RiskParameters, "parameters 是 RiskParameters 实例")
    passed &= assert_equal(profile.timestamp, 1234567890.0, "timestamp 正确")
    passed &= assert_equal(len(profile.recommendations), 2, "recommendations 数量正确")
    passed &= assert_equal(profile.recommendations[0], "建议减少仓位", "recommendations[0] 正确")

    print_test("RiskProfile 结构测试", passed)
    return passed


# ==================== MarketRiskCalculator 测试 ====================

def test_market_risk_calculator_normal_market():
    """测试正常市场条件下的市场风险计算"""
    print_header("MarketRiskCalculator: 正常市场条件")

    calculator = MarketRiskCalculator()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.01,  # 低波动率
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    risk_score = calculator.calculate_market_risk(market_data)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score < 0.4, "正常市场风险分数应较低 (<0.4)")

    print_test(f"正常市场风险计算 (得分: {risk_score:.3f})", passed)
    return passed


def test_market_risk_calculator_high_volatility():
    """测试高波动率市场下的市场风险计算"""
    print_header("MarketRiskCalculator: 高波动率市场")

    calculator = MarketRiskCalculator()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.08,  # 高波动率
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    risk_score = calculator.calculate_market_risk(market_data)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score > 0.6, "高波动率市场风险分数应较高 (>0.6)")

    print_test(f"高波动率市场风险计算 (得分: {risk_score:.3f})", passed)
    return passed


def test_market_risk_calculator_extreme_volatility():
    """测试极端波动率市场下的市场风险计算"""
    print_header("MarketRiskCalculator: 极端波动率市场")

    calculator = MarketRiskCalculator()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.20,  # 极端波动率
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    risk_score = calculator.calculate_market_risk(market_data)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score > 0.8, "极端波动率市场风险分数应很高 (>0.8)")

    print_test(f"极端波动率市场风险计算 (得分: {risk_score:.3f})", passed)
    return passed


# ==================== LiquidityRiskAssessor 测试 ====================

def test_liquidity_risk_assessor_high_liquidity():
    """测试高流动性下的风险评估"""
    print_header("LiquidityRiskAssessor: 高流动性市场")

    assessor = LiquidityRiskAssessor()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=10000000.0,  # 高成交量
        volatility=0.01,
        order_book_depth={"bids": 5000000, "asks": 5000000},  # 深度订单簿
        timestamp=1234567890.0
    )

    risk_score = assessor.assess_liquidity_risk(market_data)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score < 0.3, "高流动性市场风险分数应较低 (<0.3)")

    print_test(f"高流动性风险评估 (得分: {risk_score:.3f})", passed)
    return passed


def test_liquidity_risk_assessor_low_liquidity():
    """测试低流动性下的风险评估"""
    print_header("LiquidityRiskAssessor: 低流动性市场")

    assessor = LiquidityRiskAssessor()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=10000.0,  # 低成交量
        volatility=0.01,
        order_book_depth={"bids": 5000, "asks": 5000},  # 浅订单簿
        timestamp=1234567890.0
    )

    risk_score = assessor.assess_liquidity_risk(market_data)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score > 0.7, "低流动性市场风险分数应较高 (>0.7)")

    print_test(f"低流动性风险评估 (得分: {risk_score:.3f})", passed)
    return passed


# ==================== ExecutionRiskEvaluator 测试 ====================

def test_execution_risk_evaluator_normal():
    """测试正常执行条件下的风险"""
    print_header("ExecutionRiskEvaluator: 正常执行条件")

    evaluator = ExecutionRiskEvaluator()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.01,
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    position_size = 1000.0  # 小仓位
    risk_score = evaluator.evaluate_execution_risk(market_data, position_size)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score < 0.4, "正常执行条件风险分数应较低 (<0.4)")

    print_test(f"正常执行风险评估 (得分: {risk_score:.3f})", passed)
    return passed


def test_execution_risk_evaluator_large_position():
    """测试大仓位执行风险"""
    print_header("ExecutionRiskEvaluator: 大仓位")

    evaluator = ExecutionRiskEvaluator()

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.01,
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    position_size = 100000.0  # 大仓位
    risk_score = evaluator.evaluate_execution_risk(market_data, position_size)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score > 0.5, "大仓位执行风险分数应较高 (>0.5)")

    print_test(f"大仓位执行风险评估 (得分: {risk_score:.3f})", passed)
    return passed


# ==================== SystemRiskMonitor 测试 ====================

def test_system_risk_monitor_normal():
    """测试正常系统状态"""
    print_header("SystemRiskMonitor: 正常系统状态")

    monitor = SystemRiskMonitor()

    system_state = {
        "api_latency": 100.0,  # 低延迟
        "error_rate": 0.0,  # 无错误
        "connection_stable": True,
        "memory_usage": 0.5,  # 正常内存使用
        "cpu_usage": 0.3  # 正常 CPU 使用
    }

    risk_score = monitor.monitor_system_risk(system_state)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score < 0.3, "正常系统状态风险分数应较低 (<0.3)")

    print_test(f"正常系统状态风险评估 (得分: {risk_score:.3f})", passed)
    return passed


def test_system_risk_monitor_degraded():
    """测试系统降级状态"""
    print_header("SystemRiskMonitor: 系统降级状态")

    monitor = SystemRiskMonitor()

    system_state = {
        "api_latency": 2000.0,  # 高延迟
        "error_rate": 0.15,  # 高错误率
        "connection_stable": False,
        "memory_usage": 0.9,  # 高内存使用
        "cpu_usage": 0.95  # 高 CPU 使用
    }

    risk_score = monitor.monitor_system_risk(system_state)

    passed = True
    passed &= assert_in_range(risk_score, 0.0, 1.0, "风险分数在 0-1 范围内")
    passed &= assert_true(risk_score > 0.7, "系统降级状态风险分数应较高 (>0.7)")

    print_test(f"系统降级状态风险评估 (得分: {risk_score:.3f})", passed)
    return passed


# ==================== AdaptiveRiskManager 集成测试 ====================

async def test_adaptive_risk_manager_initialization():
    """测试自适应风险管理器初始化"""
    print_header("AdaptiveRiskManager: 初始化")

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

    passed = True
    passed &= assert_is_instance(manager, AdaptiveRiskManager, "manager 是 AdaptiveRiskManager 实例")
    passed &= assert_true(manager is not None, "manager 不为 None")

    print_test("AdaptiveRiskManager 初始化测试", passed)
    return passed


async def test_adaptive_risk_manager_assess_overall_risk():
    """测试整体风险评估"""
    print_header("AdaptiveRiskManager: 整体风险评估")

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

    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.02,
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    risk_profile = await manager.assess_overall_risk(market_data)

    passed = True
    passed &= assert_is_instance(risk_profile, RiskProfile, "risk_profile 是 RiskProfile 实例")
    passed &= assert_is_instance(risk_profile.metrics, RiskMetrics, "metrics 是 RiskMetrics 实例")
    passed &= assert_is_instance(risk_profile.parameters, RiskParameters, "parameters 是 RiskParameters 实例")
    passed &= assert_in_range(risk_profile.metrics.overall_risk_score, 0.0, 1.0,
                              "overall_risk_score 在 0-1 范围内")
    passed &= assert_true(len(risk_profile.recommendations) > 0, "有风险建议")

    print_test(f"整体风险评估 (总风险: {risk_profile.metrics.overall_risk_score:.3f}, "
              f"级别: {risk_profile.metrics.risk_level.value})", passed)
    return passed


async def test_adaptive_risk_manager_get_adapted_parameters():
    """测试获取自适应调整后的参数"""
    print_header("AdaptiveRiskManager: 获取自适应调整后的参数")

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

    current_params = RiskParameters(
        max_position_size=1000.0,
        stop_loss_pct=2.0,
        leverage_ratio=1.0,
        max_daily_loss=500.0,
        max_total_exposure=5000.0
    )

    adapted_params = await manager.get_adapted_parameters(current_params)

    passed = True
    passed &= assert_is_instance(adapted_params, RiskParameters, "adapted_params 是 RiskParameters 实例")
    passed &= assert_true(adapted_params.max_position_size > 0, "max_position_size > 0")
    passed &= assert_true(adapted_params.stop_loss_pct > 0, "stop_loss_pct > 0")

    print_test(f"获取自适应参数 (max_position_size: {adapted_params.max_position_size:.2f}, "
              f"stop_loss_pct: {adapted_params.stop_loss_pct:.2f}%)", passed)
    return passed


async def test_adaptive_risk_manager_high_risk_scenario():
    """测试高风险场景下的参数调整"""
    print_header("AdaptiveRiskManager: 高风险场景")

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

    # 高风险市场数据
    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=10000.0,  # 低流动性
        volatility=0.10,  # 高波动率
        order_book_depth={"bids": 5000, "asks": 5000},  # 浅订单簿
        timestamp=1234567890.0
    )

    risk_profile = await manager.assess_overall_risk(market_data)

    current_params = RiskParameters(
        max_position_size=1000.0,
        stop_loss_pct=2.0,
        leverage_ratio=1.0,
        max_daily_loss=500.0,
        max_total_exposure=5000.0
    )

    adapted_params = await manager.get_adapted_parameters(current_params)

    passed = True
    passed &= assert_is_instance(risk_profile, RiskProfile, "risk_profile 是 RiskProfile 实例")
    passed &= assert_true(risk_profile.metrics.overall_risk_score > 0.6,
                         "高风险场景 overall_risk_score > 0.6")
    passed &= assert_true(adapted_params.max_position_size < current_params.max_position_size,
                         "高风险场景应降低仓位大小")
    passed &= assert_true(adapted_params.stop_loss_pct >= current_params.stop_loss_pct,
                         "高风险场景应增加或保持止损比例")

    print_test(f"高风险场景测试 (总风险: {risk_profile.metrics.overall_risk_score:.3f}, "
              f"仓位调整: {adapted_params.max_position_size:.2f} -> {current_params.max_position_size:.2f})",
              passed)
    return passed


async def test_adaptive_risk_manager_low_risk_scenario():
    """测试低风险场景下的参数调整"""
    print_header("AdaptiveRiskManager: 低风险场景")

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

    # 低风险市场数据
    market_data = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=10000000.0,  # 高流动性
        volatility=0.005,  # 低波动率
        order_book_depth={"bids": 5000000, "asks": 5000000},  # 深订单簿
        timestamp=1234567890.0
    )

    risk_profile = await manager.assess_overall_risk(market_data)

    current_params = RiskParameters(
        max_position_size=1000.0,
        stop_loss_pct=2.0,
        leverage_ratio=1.0,
        max_daily_loss=500.0,
        max_total_exposure=5000.0
    )

    adapted_params = await manager.get_adapted_parameters(current_params)

    passed = True
    passed &= assert_is_instance(risk_profile, RiskProfile, "risk_profile 是 RiskProfile 实例")
    passed &= assert_true(risk_profile.metrics.overall_risk_score < 0.4,
                         "低风险场景 overall_risk_score < 0.4")
    # 低风险场景可以保持或适度增加仓位
    passed &= assert_true(adapted_params.max_position_size > 0, "max_position_size > 0")

    print_test(f"低风险场景测试 (总风险: {risk_profile.metrics.overall_risk_score:.3f}, "
              f"仓位: {adapted_params.max_position_size:.2f})",
              passed)
    return passed


# ==================== 边界条件测试 ====================

async def test_edge_cases():
    """测试边界条件"""
    print_header("边界条件测试")

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

    # 测试零波动率
    market_data_zero_vol = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=0.0,  # 零波动率
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    # 测试极高波动率
    market_data_extreme_vol = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=1000000.0,
        volatility=1.0,  # 极高波动率
        order_book_depth={"bids": 500000, "asks": 500000},
        timestamp=1234567890.0
    )

    # 测试零流动性
    market_data_zero_liq = MarketData(
        symbol="BTC/USDT",
        price=50000.0,
        volume=0.0,  # 零成交量
        volatility=0.02,
        order_book_depth={"bids": 0, "asks": 0},  # 零订单簿深度
        timestamp=1234567890.0
    )

    passed = True

    try:
        risk_profile_1 = await manager.assess_overall_risk(market_data_zero_vol)
        passed &= assert_in_range(risk_profile_1.metrics.overall_risk_score, 0.0, 1.0,
                                  "零波动率风险分数在范围内")
    except Exception as e:
        print(f"    零波动率测试失败: {e}")
        passed = False

    try:
        risk_profile_2 = await manager.assess_overall_risk(market_data_extreme_vol)
        passed &= assert_in_range(risk_profile_2.metrics.overall_risk_score, 0.0, 1.0,
                                  "极高波动率风险分数在范围内")
    except Exception as e:
        print(f"    极高波动率测试失败: {e}")
        passed = False

    try:
        risk_profile_3 = await manager.assess_overall_risk(market_data_zero_liq)
        passed &= assert_in_range(risk_profile_3.metrics.overall_risk_score, 0.0, 1.0,
                                  "零流动性风险分数在范围内")
    except Exception as e:
        print(f"    零流动性测试失败: {e}")
        passed = False

    print_test("边界条件测试", passed)
    return passed


# ==================== 主测试函数 ====================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print(" 自适应风险管理器 (AdaptiveRiskManager) 测试套件")
    print(" V3.9 迭代 - TDD 开发")
    print("="*80)

    results = []

    # 数据结构测试
    results.append(("RiskLevel 枚举", test_risk_level_enum()))
    results.append(("MarketData 结构", test_market_data()))
    results.append(("RiskMetrics 结构", test_risk_metrics()))
    results.append(("RiskParameters 结构", test_risk_parameters()))
    results.append(("RiskProfile 结构", test_risk_profile()))

    # MarketRiskCalculator 测试
    results.append(("MarketRiskCalculator - 正常市场", test_market_risk_calculator_normal_market()))
    results.append(("MarketRiskCalculator - 高波动率", test_market_risk_calculator_high_volatility()))
    results.append(("MarketRiskCalculator - 极端波动率", test_market_risk_calculator_extreme_volatility()))

    # LiquidityRiskAssessor 测试
    results.append(("LiquidityRiskAssessor - 高流动性", test_liquidity_risk_assessor_high_liquidity()))
    results.append(("LiquidityRiskAssessor - 低流动性", test_liquidity_risk_assessor_low_liquidity()))

    # ExecutionRiskEvaluator 测试
    results.append(("ExecutionRiskEvaluator - 正常", test_execution_risk_evaluator_normal()))
    results.append(("ExecutionRiskEvaluator - 大仓位", test_execution_risk_evaluator_large_position()))

    # SystemRiskMonitor 测试
    results.append(("SystemRiskMonitor - 正常", test_system_risk_monitor_normal()))
    results.append(("SystemRiskMonitor - 降级", test_system_risk_monitor_degraded()))

    # AdaptiveRiskManager 集成测试
    results.append(("AdaptiveRiskManager - 初始化", await test_adaptive_risk_manager_initialization()))
    results.append(("AdaptiveRiskManager - 整体风险评估", await test_adaptive_risk_manager_assess_overall_risk()))
    results.append(("AdaptiveRiskManager - 获取自适应参数", await test_adaptive_risk_manager_get_adapted_parameters()))
    results.append(("AdaptiveRiskManager - 高风险场景", await test_adaptive_risk_manager_high_risk_scenario()))
    results.append(("AdaptiveRiskManager - 低风险场景", await test_adaptive_risk_manager_low_risk_scenario()))

    # 边界条件测试
    results.append(("边界条件测试", await test_edge_cases()))

    # 打印汇总
    print_header("测试汇总")

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[+]" if result else "[-]"
        print(f"{symbol} {status} - {name}")

    print("\n" + "="*80)
    print(f" 测试结果: {passed_tests}/{total_tests} 通过")
    print(f" 成功率: {passed_tests/total_tests*100:.1f}%")
    print("="*80)

    if failed_tests > 0:
        print(f"\n {failed_tests} 个测试失败，请检查实现")
        return False
    else:
        print("\n 所有测试通过!")
        return True


# ==================== 严重问题修复测试 ====================

def test_price_history_thread_safety():
    """测试 _price_history 的线程安全性"""
    print_header("线程安全测试: _price_history 使用 deque")

    calculator = MarketRiskCalculator()

    # 验证 _price_history 是线程安全的 deque 类型
    passed = True
    passed &= assert_is_instance(calculator._price_history, deque,
                                 "_price_history 应该是 deque 类型")
    passed &= assert_is_instance(calculator._price_history.maxlen, int,
                                 "deque 应该有 maxlen 属性")
    passed &= assert_equal(calculator._price_history.maxlen, 100,
                          "deque maxlen 应该是 100")

    # 测试多线程环境下的安全性
    results = []
    def append_prices():
        for i in range(50):
            calculator._price_history.append(50000.0 + i)
        results.append(len(calculator._price_history))

    threads = []
    for _ in range(4):
        t = threading.Thread(target=append_prices)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 验证 deque 的自动截断功能
    passed &= assert_true(len(calculator._price_history) <= 100,
                         "deque 长度不应超过 maxlen")
    # 所有线程结果都应该在限制范围内（因为使用了 deque(maxlen=100)）
    # results 存储的是每个线程完成时的 deque 长度，应该都 <= 100
    if results:
        passed &= assert_true(all(r <= 100 for r in results), "所有线程结果都在限制范围内")

    print_test("_price_history 线程安全测试", passed)
    return passed


def test_error_history_memory_leak_prevention():
    """测试 _error_history 的内存泄漏防护"""
    print_header("资源泄漏测试: _error_history 使用 deque(maxlen=100)")

    monitor = SystemRiskMonitor()

    # 验证 _error_history 是 deque 类型且有 maxlen
    passed = True
    passed &= assert_is_instance(monitor._error_history, deque,
                                 "_error_history 应该是 deque 类型")
    passed &= assert_is_instance(monitor._error_history.maxlen, int,
                                 "deque 应该有 maxlen 属性")
    passed &= assert_equal(monitor._error_history.maxlen, 100,
                          "deque maxlen 应该是 100")

    # 测试自动截断功能
    for i in range(150):
        monitor._error_history.append(True)

    passed &= assert_true(len(monitor._error_history) <= 100,
                         "_error_history 长度不应超过 maxlen")
    passed &= assert_equal(len(monitor._error_history), 100,
                          "超出 maxlen 时应该被截断")

    print_test("_error_history 内存泄漏防护测试", passed)
    return passed


def test_order_book_depth_typed_dict():
    """测试 order_book_depth 使用 TypedDict"""
    print_header("类型注解测试: order_book_depth 使用 TypedDict")

    # 验证 TypedDict 存在并且正确定义
    passed = True

    try:
        from tools.adaptive_risk_manager import OrderBookDepth
        passed &= assert_is_instance(OrderBookDepth.__annotations__, dict,
                                     "OrderBookDepth 应该有类型注解")

        # 测试有效的 order_book_depth
        valid_depth = {"bids": 100000, "asks": 100000}
        market_data = MarketData(
            symbol="BTC/USDT",
            price=50000.0,
            volume=1000.0,
            volatility=0.02,
            order_book_depth=valid_depth,
            timestamp=1234567890.0
        )
        passed &= assert_true(market_data.order_book_depth == valid_depth,
                             "MarketData 可以接受有效的 order_book_depth")

        # 测试有效的键
        assessor = LiquidityRiskAssessor()
        depth_risk = assessor._calculate_depth_risk(valid_depth)
        passed &= assert_in_range(depth_risk, 0.0, 1.0,
                                "深度风险应该在有效范围内")

    except ImportError:
        print("    OrderBookDepth TypedDict 尚未定义")
        passed = False

    print_test("order_book_depth TypedDict 测试", passed)
    return passed


def test_magic_numbers_removed():
    """测试魔法数字是否已被提取为常量"""
    print_header("代码质量测试: 魔法数字已提取为常量")

    passed = True

    # 检查 MarketRiskCalculator 是否有类常量
    market_calc = MarketRiskCalculator()
    required_constants = [
        'DEFAULT_VOLATILITY_WEIGHT',
        'DEFAULT_PRICE_CHANGE_WEIGHT',
        'DEFAULT_LOW_VOLATILITY_THRESHOLD',
        'DEFAULT_HIGH_VOLATILITY_THRESHOLD',
        'MAX_HISTORY_LENGTH',
        'MIN_HISTORY_LENGTH',
        'EXTREME_VOLATILITY_THRESHOLD',
        'TREND_RISK_MULTIPLIER',
        'EXTREME_VOLATILITY_WEIGHT',
        'HIGH_VOLATILITY_WEIGHT'
    ]

    for const_name in required_constants:
        if not hasattr(market_calc.__class__, const_name):
            print(f"    缺少常量: {const_name}")
            passed = False

    # 检查 LiquidityRiskAssessor 是否有类常量
    liquidity_assessor = LiquidityRiskAssessor()
    required_constants_liquidity = [
        'DEFAULT_VOLUME_WEIGHT',
        'DEFAULT_DEPTH_WEIGHT',
        'LOW_VOLUME_THRESHOLD',
        'LOW_DEPTH_THRESHOLD',
        'HIGH_VOLUME_MULTIPLIER',
        'HIGH_DEPTH_MULTIPLIER'
    ]

    for const_name in required_constants_liquidity:
        if not hasattr(liquidity_assessor.__class__, const_name):
            print(f"    缺少常量: {const_name}")
            passed = False

    # 检查 ExecutionRiskEvaluator 是否有类常量
    execution_evaluator = ExecutionRiskEvaluator()
    required_constants_execution = [
        'DEFAULT_LIQUIDITY_WEIGHT',
        'DEFAULT_POSITION_WEIGHT',
        'DEFAULT_VOLATILITY_WEIGHT',
        'LARGE_POSITION_THRESHOLD',
        'MIN_POSITION_RATIO',
        'MAX_POSITION_RATIO',
        'POSITION_RATIO_THRESHOLDS'
    ]

    for const_name in required_constants_execution:
        if not hasattr(execution_evaluator.__class__, const_name):
            print(f"    缺少常量: {const_name}")
            passed = False

    # 检查 SystemRiskMonitor 是否有类常量
    system_monitor = SystemRiskMonitor()
    required_constants_system = [
        'DEFAULT_LATENCY_WEIGHT',
        'DEFAULT_ERROR_RATE_WEIGHT',
        'DEFAULT_RESOURCE_WEIGHT',
        'DEFAULT_CONNECTION_WEIGHT',
        'HIGH_LATENCY_THRESHOLD',
        'HIGH_ERROR_RATE_THRESHOLD',
        'MAX_ERROR_HISTORY'
    ]

    for const_name in required_constants_system:
        if not hasattr(system_monitor.__class__, const_name):
            print(f"    缺少常量: {const_name}")
            passed = False

    # 检查 AdaptiveRiskManager 是否有类常量
    config = {"max_daily_loss": 500, "max_position_size": 1000, "max_total_exposure": 5000}
    manager = AdaptiveRiskManager(config)
    required_constants_manager = [
        'RISK_WEIGHT_MARKET',
        'RISK_WEIGHT_LIQUIDITY',
        'RISK_WEIGHT_EXECUTION',
        'RISK_WEIGHT_SYSTEM',
        'RISK_LEVEL_THRESHOLD_LOW',
        'RISK_LEVEL_THRESHOLD_MEDIUM',
        'RISK_LEVEL_THRESHOLD_HIGH',
        'ADJUSTMENT_FACTOR_LOW_RISK',
        'ADJUSTMENT_FACTOR_MEDIUM_RISK',
        'ADJUSTMENT_FACTOR_HIGH_RISK',
        'ADJUSTMENT_FACTOR_CRITICAL_RISK',
        'STOP_LOSS_FACTOR_LOW_RISK',
        'STOP_LOSS_FACTOR_MEDIUM_RISK',
        'STOP_LOSS_FACTOR_HIGH_RISK',
        'STOP_LOSS_FACTOR_CRITICAL_RISK',
        'MIN_POSITION_SIZE',
        'MAX_STOP_LOSS_PCT',
        'LIQUIDITY_RISK_ADJUSTMENT_FACTOR'
    ]

    for const_name in required_constants_manager:
        if not hasattr(manager.__class__, const_name):
            print(f"    缺少常量: {const_name}")
            passed = False

    print_test("魔法数字提取为常量测试", passed)
    return passed


async def test_all_critical_fixes():
    """运行所有严重问题修复测试"""
    print_header("严重问题修复测试汇总")

    results = []
    results.append(("线程安全 - _price_history", test_price_history_thread_safety()))
    results.append(("资源泄漏 - _error_history", test_error_history_memory_leak_prevention()))
    results.append(("类型注解 - TypedDict", test_order_book_depth_typed_dict()))
    results.append(("魔法数字 - 类常量", test_magic_numbers_removed()))

    # 打印汇总
    print_header("严重问题修复测试结果")

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[+]" if result else "[-]"
        print(f"{symbol} {status} - {name}")

    print("\n" + "="*80)
    print(f" 严重问题修复测试: {passed_tests}/{total_tests} 通过")
    print("="*80)

    if failed_tests > 0:
        print(f"\n {failed_tests} 个严重问题修复测试失败")
        return False
    else:
        print("\n 所有严重问题已修复!")
        return True


# ==================== 动态参数调整器测试 (TDD) ====================

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


async def test_dynamic_parameter_adjuster():
    """运行动态参数调整器所有测试"""
    print_header("动态参数调整器测试套件")

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
    print("="*80)

    if failed_tests > 0:
        print(f"\n {failed_tests} 个动态参数调整器测试失败")
        return False
    else:
        print("\n 所有动态参数调整器测试通过!")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if success:
        print("\n" + "="*80)
        print(" 运行严重问题修复测试")
        print("="*80)
        critical_fixes_success = asyncio.run(test_all_critical_fixes())
        if critical_fixes_success:
            print("\n" + "="*80)
            print(" 运行动态参数调整器测试")
            print("="*80)
            dynamic_param_success = asyncio.run(test_dynamic_parameter_adjuster())
            sys.exit(0 if dynamic_param_success else 1)
        else:
            sys.exit(1)
    sys.exit(0 if success else 1)
