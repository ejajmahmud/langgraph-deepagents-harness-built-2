"""测试预测性健康监控器 (PredictiveHealthMonitor)

测试 V3.9 迭代中的预测性健康监控功能：
1. TrendAnalysisEngine - 趋势分析引擎
2. AnomalyPredictionModel - 异常预测模型
3. PreventiveActionsEngine - 主动预防引擎
4. PredictiveHealthMonitor - 预测性健康监控器主类

运行方式:
    python tests/test_predictive_health_monitor.py
"""

import sys
import os
import time
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.predictive_health_monitor import (
    TrendAnalysisEngine,
    AnomalyPredictionModel,
    PreventiveActionsEngine,
    PredictiveHealthMonitor,
    TrendDirection,
    AlertSeverity,
    AnomalyType,
    TrendInfo,
    AnomalyPrediction,
    PreventiveAction,
    HealthPrediction
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


# ==================== 测试函数 ====================

def test_data_structures() -> bool:
    """测试数据结构"""
    print_header("测试数据结构")

    passed = 0
    total = 0

    # 测试 TrendInfo
    total += 1
    try:
        trend_info = TrendInfo(
            metric_name="response_time",
            direction=TrendDirection.UP,
            strength=0.5,
            current_value=100.0,
            predicted_value=105.0,
            confidence=0.8
        )
        assert_equal(trend_info.direction, TrendDirection.UP, "TrendInfo.direction")
        assert_true(trend_info.strength >= 0 and trend_info.strength <= 1, "TrendInfo.strength in range")
        passed += 1
    except Exception as e:
        print_error(f"TrendInfo 创建失败: {e}")

    # 测试 AnomalyPrediction
    total += 1
    try:
        anomaly = AnomalyPrediction(
            anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
            confidence=0.85,
            impact_level=0.7,
            estimated_time=time.time() + 3600,
            recommended_action="优化数据库查询"
        )
        assert_equal(anomaly.anomaly_type, AnomalyType.PERFORMANCE_DEGRADATION, "AnomalyPrediction.type")
        assert_true(anomaly.confidence > 0.8, "AnomalyPrediction.confidence > 0.8")
        passed += 1
    except Exception as e:
        print_error(f"AnomalyPrediction 创建失败: {e}")

    # 测试 PreventiveAction
    total += 1
    try:
        action = PreventiveAction(
            action_type="clear_cache",
            description="清理缓存",
            priority=8,
            estimated_impact=0.6,
            execution_time=30
        )
        assert_equal(action.action_type, "clear_cache", "PreventiveAction.type")
        assert_true(1 <= action.priority <= 10, "PreventiveAction.priority in range")
        passed += 1
    except Exception as e:
        print_error(f"PreventiveAction 创建失败: {e}")

    # 测试 HealthPrediction
    total += 1
    try:
        prediction = HealthPrediction(
            overall_health_score=0.8,
            trends=[],
            anomalies=[],
            actions=[],
            timestamp=time.time()
        )
        assert_equal(prediction.overall_health_score, 0.8, "HealthPrediction.health_score")
        assert_true(0 <= prediction.overall_health_score <= 1, "HealthPrediction.score in range")
        passed += 1
    except Exception as e:
        print_error(f"HealthPrediction 创建失败: {e}")

    print_info(f"数据结构测试: {passed}/{total} 通过")
    return passed == total


def test_trend_analysis_engine() -> bool:
    """测试趋势分析引擎"""
    print_header("测试趋势分析引擎 (TrendAnalysisEngine)")

    passed = 0
    total = 0

    try:
        engine = TrendAnalysisEngine()

        # 测试正常指标分析
        total += 1
        metrics = {
            "response_time": 100.0,
            "throughput": 1000.0,
            "error_rate": 0.01
        }
        trends = engine.analyze_metrics(metrics)

        assert_true(len(trends) == 3, "分析返回3个指标趋势")
        assert_true(all(isinstance(t, TrendInfo) for t in trends.values()), "返回TrendInfo对象")
        passed += 1

        # 测试上升趋势检测
        total += 1
        for i in range(15):
            metrics["response_time"] = 100 + i * 5  # 上升
            engine.analyze_metrics(metrics)

        trends = engine.analyze_metrics({"response_time": 170.0})
        response_time_trend = trends.get("response_time")

        assert_true(response_time_trend is not None, "响应时间趋势存在")
        assert_equal(response_time_trend.direction, TrendDirection.UP, "检测到上升趋势")
        passed += 1

        # 测试性能降级预测
        total += 1
        degradation_trends = engine.predict_performance_degradation({
            "response_time": 200.0,
            "latency": 50.0,
            "error_rate": 0.02,
            "throughput": 800.0
        })

        assert_true(isinstance(degradation_trends, list), "返回列表")
        print_success(f"趋势分析引擎测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"趋势分析引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anomaly_prediction_model() -> bool:
    """测试异常预测模型"""
    print_header("测试异常预测模型 (AnomalyPredictionModel)")

    passed = 0
    total = 0

    try:
        model = AnomalyPredictionModel()

        # 测试正常指标（无异常）
        total += 1
        normal_metrics = {
            "response_time": 100.0,
            "memory_usage": 0.5,
            "error_rate": 0.01,
            "disk_usage": 0.6
        }

        # 添加一些基线数据
        for _ in range(25):
            model.predict_anomalies(normal_metrics)

        anomalies = model.predict_anomalies(normal_metrics)
        assert_true(len(anomalies) == 0, "正常指标无异常")
        passed += 1

        # 测试性能异常检测
        total += 1
        high_latency_metrics = {
            "response_time": 500.0,  # 异常高
            "memory_usage": 0.5,
            "error_rate": 0.01,
            "disk_usage": 0.6
        }

        anomalies = model.predict_anomalies(high_latency_metrics)
        assert_true(len(anomalies) > 0, "检测到性能异常")
        if anomalies:
            assert_equal(anomalies[0].anomaly_type, AnomalyType.PERFORMANCE_DEGRADATION, "异常类型正确")
            passed += 1
        else:
            print_error("未检测到预期的性能异常")

        # 测试资源异常检测
        total += 1
        high_memory_metrics = {
            "response_time": 100.0,
            "memory_usage": 0.95,  # 异常高
            "error_rate": 0.01,
            "disk_usage": 0.6
        }

        anomalies = model.predict_anomalies(high_memory_metrics)
        assert_true(len(anomalies) > 0, "检测到内存异常")
        if anomalies:
            memory_anomaly = next((a for a in anomalies if a.anomaly_type == AnomalyType.MEMORY_LEAK), None)
            assert_true(memory_anomaly is not None, "检测到内存泄漏异常")
            passed += 1
        else:
            print_error("未检测到预期的内存异常")

        # 测试错误率异常检测
        total += 1
        high_error_metrics = {
            "response_time": 100.0,
            "memory_usage": 0.5,
            "error_rate": 0.15,  # 异常高
            "disk_usage": 0.6
        }

        anomalies = model.predict_anomalies(high_error_metrics)
        assert_true(len(anomalies) > 0, "检测到错误率异常")
        if anomalies:
            error_anomaly = next((a for a in anomalies if a.anomaly_type == AnomalyType.ERROR_SPIKE), None)
            assert_true(error_anomaly is not None, "检测到错误率激增异常")
            passed += 1
        else:
            print_error("未检测到预期的错误率异常")

        # 测试性能降级检测
        total += 1
        performance_history = [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55]
        degradation = model.detect_performance_degradation(performance_history)

        assert_true(degradation is not None, "检测到性能降级")
        if degradation:
            assert_equal(degradation.anomaly_type, AnomalyType.PERFORMANCE_DEGRADATION, "降级类型正确")
            assert_true(degradation.confidence > 0.5, "降级置信度 > 0.5")
            passed += 1
        else:
            print_error("未检测到预期的性能降级")

        print_success(f"异常预测模型测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"异常预测模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preventive_actions_engine() -> bool:
    """测试主动预防引擎"""
    print_header("测试主动预防引擎 (PreventiveActionsEngine)")

    passed = 0
    total = 0

    try:
        engine = PreventiveActionsEngine()

        # 测试性能异常的预防行动
        total += 1
        performance_anomaly = AnomalyPrediction(
            anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
            confidence=0.8,
            impact_level=0.7,
            estimated_time=time.time() + 3600,
            recommended_action="优化数据库"
        )

        actions = engine.recommend_actions([performance_anomaly])
        assert_true(len(actions) > 0, "生成了预防行动")
        assert_true(any(a.action_type == "clear_cache" for a in actions), "包含清理缓存行动")
        passed += 1

        # 测试资源异常的预防行动
        total += 1
        resource_anomaly = AnomalyPrediction(
            anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
            confidence=0.9,
            impact_level=0.8,
            estimated_time=time.time() + 3600,
            recommended_action="清理磁盘"
        )

        actions = engine.recommend_actions([resource_anomaly])
        assert_true(len(actions) > 0, "生成了预防行动")
        assert_true(any(a.action_type == "clean_logs" for a in actions), "包含清理日志行动")
        passed += 1

        # 测试内存泄漏的预防行动
        total += 1
        memory_anomaly = AnomalyPrediction(
            anomaly_type=AnomalyType.MEMORY_LEAK,
            confidence=0.85,
            impact_level=0.9,
            estimated_time=time.time() + 3600,
            recommended_action="重启服务"
        )

        actions = engine.recommend_actions([memory_anomaly])
        assert_true(len(actions) > 0, "生成了预防行动")
        assert_true(any(a.action_type == "restart_service" for a in actions), "包含重启服务行动")
        assert_true(any(a.priority >= 8 for a in actions), "包含高优先级行动")
        passed += 1

        # 测试多个异常的预防行动
        total += 1
        multiple_anomalies = [
            performance_anomaly,
            resource_anomaly,
            memory_anomaly
        ]

        actions = engine.recommend_actions(multiple_anomalies)
        assert_true(len(actions) > 0, "生成了预防行动")
        assert_true(len(actions) <= 10, "行动数量限制在10个以内")
        # 验证按优先级排序
        if len(actions) >= 2:
            assert_true(actions[0].priority >= actions[1].priority, "行动按优先级排序")
            passed += 1
        else:
            print_error("行动数量不足，无法验证排序")

        print_success(f"主动预防引擎测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"主动预防引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_predictive_health_monitor() -> bool:
    """测试预测性健康监控器"""
    print_header("测试预测性健康监控器 (PredictiveHealthMonitor)")

    passed = 0
    total = 0

    try:
        monitor = PredictiveHealthMonitor()

        # 测试正常健康预测
        total += 1
        normal_metrics = {
            "response_time": 100.0,
            "throughput": 1000.0,
            "memory_usage": 0.5,
            "error_rate": 0.01,
            "disk_usage": 0.6
        }

        # 添加一些历史数据
        for _ in range(15):
            monitor.predict_health(normal_metrics)

        prediction = monitor.predict_health(normal_metrics)
        assert_true(isinstance(prediction, HealthPrediction), "返回HealthPrediction对象")
        assert_true(0 <= prediction.overall_health_score <= 1, "健康分数在有效范围内")
        assert_true(prediction.overall_health_score > 0.7, "正常状态健康分数 > 0.7")
        passed += 1

        # 测试异常状态预测
        total += 1
        abnormal_metrics = {
            "response_time": 500.0,
            "throughput": 500.0,
            "memory_usage": 0.95,
            "error_rate": 0.15,
            "disk_usage": 0.9
        }

        prediction = monitor.predict_health(abnormal_metrics)
        assert_true(prediction.overall_health_score < 0.5, "异常状态健康分数 < 0.5")
        assert_true(len(prediction.anomalies) > 0, "检测到异常")
        assert_true(len(prediction.actions) > 0, "推荐了预防行动")
        passed += 1

        # 测试预测摘要
        total += 1
        summary = monitor.get_prediction_summary()
        assert_true(summary["total_predictions"] > 0, "有预测历史")
        assert_true("average_health_score" in summary, "包含平均健康分数")
        assert_true("recent_anomalies" in summary, "包含最近异常")
        assert_true("recommended_actions" in summary, "包含推荐行动")
        passed += 1

        # 测试健康分数计算
        total += 1
        high_error_metrics = {
            "response_time": 100.0,
            "throughput": 1000.0,
            "memory_usage": 0.5,
            "error_rate": 0.3,  # 高错误率
            "disk_usage": 0.6
        }

        prediction = monitor.predict_health(high_error_metrics)
        assert_true(prediction.overall_health_score < 0.8, "高错误率降低健康分数")
        passed += 1

        print_success(f"预测性健康监控器测试: {passed}/{total} 通过")
        return passed == total

    except Exception as e:
        print_error(f"预测性健康监控器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration() -> bool:
    """集成测试"""
    print_header("集成测试 - 完整预测流程")

    passed = 0
    total = 0

    try:
        # 初始化监控器
        monitor = PredictiveHealthMonitor()

        # 模拟系统状态变化
        total += 1
        scenarios = [
            # 正常状态
            {
                "response_time": 100.0,
                "throughput": 1000.0,
                "memory_usage": 0.5,
                "error_rate": 0.01,
                "disk_usage": 0.6
            },
            # 轻微性能下降
            {
                "response_time": 150.0,
                "throughput": 900.0,
                "memory_usage": 0.6,
                "error_rate": 0.02,
                "disk_usage": 0.65
            },
            # 严重性能问题
            {
                "response_time": 400.0,
                "throughput": 500.0,
                "memory_usage": 0.85,
                "error_rate": 0.1,
                "disk_usage": 0.8
            }
        ]

        predictions = []
        for i, metrics in enumerate(scenarios):
            # 多次运行以积累历史
            for _ in range(5):
                prediction = monitor.predict_health(metrics)
            predictions.append(prediction)

        assert_true(len(predictions) == 3, "生成了3个预测")
        passed += 1

        # 验证健康分数递减
        total += 1
        assert_true(predictions[0].overall_health_score > predictions[1].overall_health_score,
                   "正常状态 > 轻微问题")
        assert_true(predictions[1].overall_health_score > predictions[2].overall_health_score,
                   "轻微问题 > 严重问题")
        passed += 1

        # 验证异常数量递增
        total += 1
        assert_true(len(predictions[0].anomalies) <= len(predictions[1].anomalies),
                   "正常状态异常 <= 轻微问题异常")
        assert_true(len(predictions[1].anomalies) <= len(predictions[2].anomalies),
                   "轻微问题异常 <= 严重问题异常")
        passed += 1

        # 验证推荐行动
        total += 1
        critical_prediction = predictions[2]
        assert_true(len(critical_prediction.actions) > 0, "严重状态有推荐行动")

        # 验证有高优先级行动
        high_priority_actions = [a for a in critical_prediction.actions if a.priority >= 8]
        assert_true(len(high_priority_actions) > 0, "有高优先级行动")
        passed += 1

        # 获取最终摘要
        total += 1
        summary = monitor.get_prediction_summary()
        assert_true(summary["total_predictions"] >= 15, "有足够的预测历史")
        assert_true(summary["average_health_score"] < 0.9, "平均健康分数反映问题")
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
    print(" 预测性健康监控器测试套件")
    print(" V3.9 迭代 - Phase 2 核心模块")
    print("="*80)

    start_time = time.time()

    results = []

    # 运行所有测试
    results.append(("数据结构测试", test_data_structures()))
    results.append(("趋势分析引擎测试", test_trend_analysis_engine()))
    results.append(("异常预测模型测试", test_anomaly_prediction_model()))
    results.append(("主动预防引擎测试", test_preventive_actions_engine()))
    results.append(("预测性健康监控器测试", test_predictive_health_monitor()))
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
