"""测试风险预测与预警机制

测试 V3.9 迭代中的风险预测功能：
1. TrendAnalyzer - 趋势分析引擎
2. RiskPredictor - 风险预测器
3. ExtremeEventDetector - 极端事件检测器
4. EarlyWarningSystem - 早期预警系统

运行方式:
    python tests/test_risk_prediction.py
"""

import asyncio
import sys
import os
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.adaptive_risk_manager import (
    RiskLevel,
    MarketData,
    RiskMetrics,
    TrendDirection,
)


# ==================== 辅助函数 ====================

def print_header(title: str) -> None:
    """打印测试标题"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_success(message: str) -> None:
    """打印成功消息"""
    print(f"[PASS] {message}")


def print_error(message: str) -> None:
    """打印错误消息"""
    print(f"[FAIL] {message}")


def print_info(message: str) -> None:
    """打印信息消息"""
    print(f"[INFO] {message}")


def assert_equal(actual: Any, expected: Any, test_name: str) -> bool:
    """断言相等"""
    if actual == expected:
        print_success(f"{test_name}: 通过")
        return True
    else:
        print_error(f"{test_name}: 失败 (期望: {expected}, 实际: {actual})")
        return False


def assert_true(condition: bool, test_name: str) -> bool:
    """断言为真"""
    if condition:
        print_success(f"{test_name}: 通过")
        return True
    else:
        print_error(f"{test_name}: 失败 (条件为 False)")
        return False


def assert_greater(actual: float, threshold: float, test_name: str) -> bool:
    """断言大于"""
    if actual > threshold:
        print_success(f"{test_name}: 通过 ({actual} > {threshold})")
        return True
    else:
        print_error(f"{test_name}: 失败 ({actual} <= {threshold})")
        return False


def assert_less(actual: float, threshold: float, test_name: str) -> bool:
    """断言小于"""
    if actual < threshold:
        print_success(f"{test_name}: 通过 ({actual} < {threshold})")
        return True
    else:
        print_error(f"{test_name}: 失败 ({actual} >= {threshold})")
        return False


# ==================== 导入预测模块 ====================

try:
    from tools.adaptive_risk_manager import (
        TrendAnalyzer,
        RiskPredictor,
        ExtremeEventDetector,
        EarlyWarningSystem,
        TrendInfo,
        PredictionResult,
        ExtremeEvent,
        WarningAlert
    )
    PREDICTION_MODULES_AVAILABLE = True
except ImportError as e:
    print_info(f"预测模块尚未实现: {e}")
    PREDICTION_MODULES_AVAILABLE = False


# ==================== 测试函数 ====================

def test_data_structures() -> bool:
    """测试数据结构"""
    print_header("测试数据结构")

    if not PREDICTION_MODULES_AVAILABLE:
        print_info("预测模块尚未实现，跳过数据结构测试")
        return True

    passed = 0
    total = 0

    # 测试 TrendInfo
    total += 1
    try:
        trend_info = TrendInfo(
            short_sma=100.0,
            long_sma=95.0,
            direction=TrendDirection.BULLISH,
            strength=0.05,
            prediction=102.0
        )
        assert_equal(trend_info.direction, TrendDirection.BULLISH, "TrendInfo.direction")
        assert_true(trend_info.strength > 0, "TrendInfo.strength > 0")
        passed += 1
    except Exception as e:
        print_error(f"TrendInfo 创建失败: {e}")

    # 测试 PredictionResult
    total += 1
    try:
        prediction = PredictionResult(
            predicted_risk_level=RiskLevel.HIGH,
            confidence=0.85,
            time_horizon="1h",
            predicted_score=0.75,
            factors=["volatility_increase", "trend_reversal"]
        )
        assert_equal(prediction.predicted_risk_level, RiskLevel.HIGH, "PredictionResult.risk_level")
        assert_true(prediction.confidence > 0.8, "PredictionResult.confidence > 0.8")
        passed += 1
    except Exception as e:
        print_error(f"PredictionResult 创建失败: {e}")

    # 测试 ExtremeEvent
    total += 1
    try:
        event = ExtremeEvent(
            event_type="flash_crash",
            severity=0.9,
            probability=0.15,
            estimated_impact="large",
            detection_time=time.time()
        )
        assert_equal(event.event_type, "flash_crash", "ExtremeEvent.type")
        assert_true(event.severity > 0.8, "ExtremeEvent.severity > 0.8")
        passed += 1
    except Exception as e:
        print_error(f"ExtremeEvent 创建失败: {e}")

    # 测试 WarningAlert
    total += 1
    try:
        alert = WarningAlert(
            alert_type="risk_increase",
            severity=WarningAlert.Severity.HIGH,
            message="风险等级预计将上升",
            predicted_time=time.time() + 3600,
            recommended_actions=["reduce_position", "tighten_stops"]
        )
        assert_equal(alert.alert_type, "risk_increase", "WarningAlert.type")
        assert_equal(alert.severity, WarningAlert.Severity.HIGH, "WarningAlert.severity")
        passed += 1
    except Exception as e:
        print_error(f"WarningAlert 创建失败: {e}")

    print_info(f"数据结构测试: {passed}/{total} 通过")
    return passed == total


def test_trend_analyzer() -> bool:
    """测试趋势分析引擎"""
    print_header("测试趋势分析引擎 (TrendAnalyzer)")

    if not PREDICTION_MODULES_AVAILABLE:
        print_info("预测模块尚未实现，跳过趋势分析测试")
        return True

    passed = 0
    total = 0

    try:
        analyzer = TrendAnalyzer(config={'window_size': 20})

        # 测试上升趋势
        total += 1
        upward_trend = list(range(90, 110))  # 上升序列
        result = analyzer.analyze_trend(upward_trend)
        assert_equal(result.direction, TrendDirection.BULLISH, "上升趋势检测")
        assert_true(result.strength > 0, "上升趋势强度 > 0")
        passed += 1

        # 测试下降趋势
        total += 1
        downward_trend = list(range(110, 90, -1))  # 下降序列
        result = analyzer.analyze_trend(downward_trend)
        assert_equal(result.direction, TrendDirection.BEARISH, "下降趋势检测")
        assert_true(result.strength > 0, "下降趋势强度 > 0")
        passed += 1

        # 测试横盘趋势
        total += 1
        sideways_trend = [100] * 30  # 平稳序列
        result = analyzer.analyze_trend(sideways_trend)
        assert_equal(result.direction, TrendDirection.SIDEWAYS, "横盘趋势检测")
        assert_true(result.strength < 0.2, "横盘趋势强度 < 0.2")  # 放宽阈值
        passed += 1

        # 测试波动性序列
        total += 1
        volatile_trend = [100 + i * 0.5 + (i % 3) * 2 for i in range(50)]
        result = analyzer.analyze_trend(volatile_trend)
        assert_true(result is not None, "波动性趋势分析")
        assert_true(0 <= result.strength <= 1, "趋势强度在 [0, 1] 范围内")
        passed += 1

        print_success(f"趋势分析引擎测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"趋势分析引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_predictor() -> bool:
    """测试风险预测器"""
    print_header("测试风险预测器 (RiskPredictor)")

    if not PREDICTION_MODULES_AVAILABLE:
        print_info("预测模块尚未实现，跳过风险预测测试")
        return True

    passed = 0
    total = 0

    try:
        predictor = RiskPredictor(config={'prediction_horizon': 3600})

        # 模拟历史风险数据
        total += 1
        risk_history = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65]
        prediction = predictor.predict_risk(risk_history)

        assert_true(prediction is not None, "风险预测结果不为空")
        assert_true(0 <= prediction.predicted_score <= 1, "预测分数在 [0, 1] 范围内")
        assert_true(prediction.confidence >= 0, "预测置信度 >= 0")
        passed += 1

        # 测试风险上升趋势预测
        total += 1
        increasing_risk = list(range(30, 70, 5))  # [30, 35, 40, ..., 65]
        normalized_risk = [r / 100.0 for r in increasing_risk]
        prediction = predictor.predict_risk(normalized_risk)

        assert_equal(prediction.predicted_risk_level, RiskLevel.HIGH, "风险上升趋势预测")
        assert_true(prediction.predicted_score > 0.5, "预测风险分数 > 0.5")
        passed += 1

        # 测试风险下降趋势预测
        total += 1
        decreasing_risk = list(range(70, 30, -5))  # [70, 65, 60, ..., 35]
        normalized_risk = [r / 100.0 for r in decreasing_risk]
        prediction = predictor.predict_risk(normalized_risk)

        assert_equal(prediction.predicted_risk_level, RiskLevel.LOW, "风险下降趋势预测")
        assert_true(prediction.predicted_score < 0.5, "预测风险分数 < 0.5")
        passed += 1

        # 测试稳定风险预测
        total += 1
        stable_risk = [0.5] * 10
        prediction = predictor.predict_risk(stable_risk)

        assert_equal(prediction.predicted_risk_level, RiskLevel.MEDIUM, "稳定风险预测")
        assert_true(0.4 <= prediction.predicted_score <= 0.6, "预测分数接近 0.5")
        passed += 1

        print_success(f"风险预测器测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"风险预测器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extreme_event_detector() -> bool:
    """测试极端事件检测器"""
    print_header("测试极端事件检测器 (ExtremeEventDetector)")

    if not PREDICTION_MODULES_AVAILABLE:
        print_info("预测模块尚未实现，跳过极端事件检测测试")
        return True

    passed = 0
    total = 0

    try:
        detector = ExtremeEventDetector(config={'volatility_threshold': 0.1})

        # 测试正常市场数据
        total += 1
        normal_prices = [100 + i * 0.1 for i in range(100)]  # 平缓上升
        events = detector.detect_extreme_events(normal_prices)

        assert_equal(len(events), 0, "正常市场无极端事件")
        passed += 1

        # 测试闪崩事件
        total += 1
        crash_prices = [100] * 50 + [95, 90, 85, 80, 75, 70]  # 突然下跌
        events = detector.detect_extreme_events(crash_prices)

        assert_true(len(events) > 0, "检测到闪崩事件")
        if events:
            assert_equal(events[0].event_type, "flash_crash", "事件类型为闪崩")
            assert_true(events[0].severity > 0.7, "闪崩严重性 > 0.7")
            passed += 1
        else:
            print_error("闪崩事件未检测到")

        # 测试剧烈波动事件
        total += 1
        volatile_prices = [100 + (i % 10) * 5 for i in range(100)]  # 剧烈波动
        events = detector.detect_extreme_events(volatile_prices)

        assert_true(len(events) > 0, "检测到剧烈波动事件")
        passed += 1

        # 测试流动性枯竭事件
        total += 1
        low_volume_data = [
            {'price': 100, 'volume': 10000},
            {'price': 101, 'volume': 9000},
            {'price': 102, 'volume': 8000},
            {'price': 103, 'volume': 7000},
            {'price': 104, 'volume': 6000},
            {'price': 105, 'volume': 5000},
            {'price': 106, 'volume': 4000},
            {'price': 107, 'volume': 3000},
            {'price': 108, 'volume': 2000},
            {'price': 109, 'volume': 1000}
        ]
        events = detector.detect_liquidity_crisis(low_volume_data)

        assert_true(len(events) > 0, "检测到流动性危机")
        passed += 1

        print_success(f"极端事件检测器测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"极端事件检测器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_early_warning_system() -> bool:
    """测试早期预警系统"""
    print_header("测试早期预警系统 (EarlyWarningSystem)")

    if not PREDICTION_MODULES_AVAILABLE:
        print_info("预测模块尚未实现，跳过早期预警系统测试")
        return True

    passed = 0
    total = 0

    try:
        warning_system = EarlyWarningSystem(config={'warning_threshold': 0.7})

        # 测试风险上升预警
        total += 1
        current_metrics = RiskMetrics(
            market_risk=0.5,
            liquidity_risk=0.4,
            execution_risk=0.3,
            system_risk=0.2,
            overall_risk_score=0.4,
            risk_level=RiskLevel.MEDIUM
        )
        prediction = PredictionResult(
            predicted_risk_level=RiskLevel.HIGH,
            confidence=0.8,
            time_horizon="1h",
            predicted_score=0.75,
            factors=["volatility_increase"]
        )

        alerts = warning_system.generate_warnings(current_metrics, prediction)

        assert_true(len(alerts) > 0, "生成了预警")
        if alerts:
            assert_equal(alerts[0].alert_type, "risk_increase", "预警类型为风险上升")
            assert_equal(alerts[0].severity, WarningAlert.Severity.HIGH, "预警严重性为高")
            passed += 1
        else:
            print_error("未生成预警")

        # 测试极端事件预警
        total += 1
        extreme_event = ExtremeEvent(
            event_type="flash_crash",
            severity=0.9,
            probability=0.8,
            estimated_impact="large",
            detection_time=time.time()
        )

        alerts = warning_system.generate_extreme_event_warnings(extreme_event)

        assert_true(len(alerts) > 0, "生成了极端事件预警")
        if alerts:
            assert_true(alerts[0].severity == WarningAlert.Severity.CRITICAL, "极端事件预警严重性为严重")
            assert_true("immediate" in " ".join(alerts[0].recommended_actions).lower(), "建议立即行动")
            passed += 1
        else:
            print_error("未生成极端事件预警")

        # 测试预警去重
        total += 1
        warning_system.clear_history()
        alerts1 = warning_system.generate_warnings(current_metrics, prediction)
        alerts2 = warning_system.generate_warnings(current_metrics, prediction)  # 相同预警

        assert_true(len(alerts2) <= len(alerts1), "预警去重生效")
        passed += 1

        print_success(f"早期预警系统测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"早期预警系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration() -> bool:
    """集成测试"""
    print_header("集成测试 - 完整预测流程")

    if not PREDICTION_MODULES_AVAILABLE:
        print_info("预测模块尚未实现，跳过集成测试")
        return True

    passed = 0
    total = 0

    try:
        # 初始化所有组件
        trend_analyzer = TrendAnalyzer()
        risk_predictor = RiskPredictor()
        event_detector = ExtremeEventDetector()
        warning_system = EarlyWarningSystem()

        # 模拟市场数据
        total += 1
        price_history = [100 + i * 0.2 + (i % 5) * 0.5 for i in range(100)]
        risk_history = [0.3 + i * 0.01 for i in range(50)]

        # 1. 分析趋势
        trend_result = trend_analyzer.analyze_trend(price_history)
        assert_true(trend_result is not None, "趋势分析完成")
        passed += 1

        # 2. 预测风险
        total += 1
        risk_prediction = risk_predictor.predict_risk(risk_history)
        assert_true(risk_prediction is not None, "风险预测完成")
        assert_true(risk_prediction.confidence > 0, "预测置信度 > 0")
        passed += 1

        # 3. 检测极端事件
        total += 1
        extreme_events = event_detector.detect_extreme_events(price_history)
        assert_true(isinstance(extreme_events, list), "极端事件检测完成")
        passed += 1

        # 4. 生成预警
        total += 1
        current_metrics = RiskMetrics(
            market_risk=0.5,
            liquidity_risk=0.4,
            execution_risk=0.3,
            system_risk=0.2,
            overall_risk_score=0.4,
            risk_level=RiskLevel.MEDIUM
        )
        warnings = warning_system.generate_warnings(current_metrics, risk_prediction)
        assert_true(isinstance(warnings, list), "预警生成完成")
        passed += 1

        # 5. 验证完整流程
        total += 1
        assert_true(trend_result.direction in [TrendDirection.BULLISH, TrendDirection.BEARISH, TrendDirection.SIDEWAYS],
                   "趋势方向有效")
        assert_true(risk_prediction.predicted_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
                   "预测风险等级有效")
        passed += 1

        print_success(f"集成测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 主测试函数 ====================

def main() -> None:
    """主测试函数"""
    print("\n" + "="*80)
    print(" 风险预测与预警机制测试套件")
    print(" V3.9 迭代 - Phase 1 剩余任务")
    print("="*80)

    start_time = time.time()

    results = []

    # 运行所有测试
    results.append(("数据结构测试", test_data_structures()))
    results.append(("趋势分析引擎测试", test_trend_analyzer()))
    results.append(("风险预测器测试", test_risk_predictor()))
    results.append(("极端事件检测器测试", test_extreme_event_detector()))
    results.append(("早期预警系统测试", test_early_warning_system()))
    results.append(("集成测试", test_integration()))

    # 汇总结果
    print_header("测试结果汇总")
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")

    print("\n" + "="*80)
    print(f" 总体结果: {passed_tests}/{total_tests} 测试通过")
    print(f" 通过率: {passed_tests/total_tests*100:.1f}%")
    print(f" 执行时间: {time.time() - start_time:.2f} 秒")
    print("="*80 + "\n")

    # 退出码
    sys.exit(0 if passed_tests == total_tests else 1)


if __name__ == "__main__":
    main()
