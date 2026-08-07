"""
智能告警系统 V2.5

基于动态阈值和异常检测的智能告警系统。
支持动态阈值调整、异常检测、告警聚类和预测。

核心功能：
1. 动态阈值告警
2. 异常检测告警
3. 告警优先级评估
4. 告警聚类
5. 告警预测
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntelligentAlerting:
    """智能告警系统

    基于历史数据和机器学习，实现动态阈值和异常检测。
    """

    def __init__(self, storage, config):
        """初始化智能告警系统

        Args:
            storage: 统一存储实例
            config: 配置管理器实例
        """
        self.storage = storage
        self.config = config
        self._enabled = True
        self._alert_history: List[Dict] = []
        self._alert_clusters: Dict[str, List[Dict]] = defaultdict(list)
        self._dynamic_thresholds: Dict[str, Dict] = {}
        self._baseline_cache: Dict[str, List[float]] = defaultdict(list)
        self._cache_ttl = 3600  # 缓存1小时

        # 告警配置
        self.alert_config = config.get_monitoring_config()
        self.thresholds = self.alert_config.get("performance_thresholds", {})

        logger.info("智能告警系统初始化成功")

    def enable(self):
        """启用智能告警"""
        self._enabled = True
        logger.info("智能告警已启用")

    def disable(self):
        """禁用智能告警"""
        self._enabled = False
        logger.info("智能告警已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

    # ---------------------- 动态阈值检测 ----------------------

    def check_dynamic_threshold(
        self,
        metric_name: str,
        current_value: float,
        historical_data: List[float],
        std_deviation: float = 2.5
    ) -> Dict[str, Any]:
        """检查动态阈值

        Args:
            metric_name: 指标名称
            current_value: 当前值
            historical_data: 历史数据
            std_deviation: 标准差倍数（默认2.5σ）

        Returns:
            检测结果
            {
                "is_alert": bool,
                "threshold": float,
                "deviation": float,
                "severity": str,
                "message": str
            }
        """
        if len(historical_data) < 10:
            # 数据不足，使用静态阈值
            return self._check_static_threshold(metric_name, current_value)

        # 计算统计指标
        mean = sum(historical_data) / len(historical_data)
        variance = sum((x - mean) ** 2 for x in historical_data) / len(historical_data)
        std = variance ** 0.5

        # 动态阈值 = 均值 ± 标准差倍数
        upper_threshold = mean + std_deviation * std
        lower_threshold = max(0, mean - std_deviation * std)

        # 计算偏离度
        if current_value > upper_threshold:
            deviation = (current_value - upper_threshold) / std
            is_alert = True
            message = f"{metric_name} 超过动态上限 {upper_threshold:.2f}"
        elif current_value < lower_threshold:
            deviation = (lower_threshold - current_value) / std
            is_alert = True
            message = f"{metric_name} 低于动态下限 {lower_threshold:.2f}"
        else:
            deviation = 0
            is_alert = False
            message = f"{metric_name} 正常 ({current_value:.2f})"

        # 严重程度
        if deviation > 3.0:
            severity = "critical"
        elif deviation > 2.0:
            severity = "high"
        elif deviation > 1.0:
            severity = "medium"
        else:
            severity = "low"

        # 缓存动态阈值
        self._dynamic_thresholds[metric_name] = {
            "upper": upper_threshold,
            "lower": lower_threshold,
            "mean": mean,
            "std": std,
            "updated_at": datetime.now().isoformat()
        }

        return {
            "is_alert": is_alert,
            "threshold": upper_threshold if current_value > mean else lower_threshold,
            "deviation": deviation,
            "severity": severity,
            "message": message,
            "metric_name": metric_name,
            "current_value": current_value,
            "baseline": mean,
            "detection_time": datetime.now().isoformat()
        }

    def _check_static_threshold(self, metric_name: str, current_value: float) -> Dict[str, Any]:
        """检查静态阈值（后备方案）"""
        threshold = self.thresholds.get(metric_name)

        if threshold is None:
            return {
                "is_alert": False,
                "message": f"{metric_name} 无静态阈值配置",
                "severity": "info"
            }

        if isinstance(threshold, (int, float)):
            is_alert = current_value > threshold
            message = f"{metric_name} 超过阈值 {threshold}"
        elif isinstance(threshold, dict):
            max_threshold = threshold.get("max")
            min_threshold = threshold.get("min")

            if max_threshold and current_value > max_threshold:
                is_alert = True
                message = f"{metric_name} 超过最大阈值 {max_threshold}"
            elif min_threshold and current_value < min_threshold:
                is_alert = True
                message = f"{metric_name} 低于最小阈值 {min_threshold}"
            else:
                is_alert = False
                message = f"{metric_name} 正常"
        else:
            is_alert = False
            message = f"{metric_name} 阈值配置错误"

        return {
            "is_alert": is_alert,
            "message": message,
            "severity": "medium" if is_alert else "info",
            "metric_name": metric_name,
            "current_value": current_value
        }

    # ---------------------- 异常检测 ----------------------

    def detect_anomalies(
        self,
        metric_name: str,
        current_value: float,
        historical_data: List[float],
        window_size: int = 50
    ) -> Dict[str, Any]:
        """检测异常值

        Args:
            metric_name: 指标名称
            current_value: 当前值
            historical_data: 历史数据
            window_size: 移动窗口大小

        Returns:
            异常检测结果
        """
        if len(historical_data) < window_size:
            return {
                "is_anomaly": False,
                "confidence": 0.0,
                "message": f"历史数据不足（需要{window_size}个数据点）"
            }

        # 1. Z-Score检测
        window = historical_data[-window_size:]
        window_mean = sum(window) / len(window)
        window_std = (sum((x - window_mean) ** 2 for x in window) / len(window)) ** 0.5

        if window_std > 0:
            z_score = (current_value - window_mean) / window_std
        else:
            z_score = 0

        # 2. 移动平均检测
        ma = sum(window) / len(window)
        ma_deviation = abs(current_value - ma) / ma if ma > 0 else 0

        # 3. 突变检测（与前一个值比较）
        if len(historical_data) > 0:
            previous_value = historical_data[-1]
            change_rate = abs(current_value - previous_value) / previous_value if previous_value > 0 else 0
        else:
            change_rate = 0

        # 综合判断
        is_z_score_anomaly = abs(z_score) > 3.0
        is_ma_anomaly = ma_deviation > 0.5  # 偏离移动平均50%以上
        is_change_anomaly = change_rate > 0.3  # 突变30%以上

        anomaly_count = sum([is_z_score_anomaly, is_ma_anomaly, is_change_anomaly])
        is_anomaly = anomaly_count >= 2  # 至少2个指标检测到异常

        # 置信度（基于异常指标数量）
        confidence = min(0.95, anomaly_count / 3 * 0.95 + 0.3)

        # 异常类型
        anomaly_types = []
        if is_z_score_anomaly:
            anomaly_types.append("统计异常（Z-Score）")
        if is_ma_anomaly:
            anomaly_types.append("趋势异常（移动平均）")
        if is_change_anomaly:
            anomaly_types.append("突变异常（变化率）")

        # 严重程度
        if anomaly_count == 3:
            severity = "critical"
        elif anomaly_count == 2:
            severity = "high"
        else:
            severity = "medium"

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "z_score": z_score,
            "ma_deviation": ma_deviation,
            "change_rate": change_rate,
            "anomaly_types": anomaly_types,
            "severity": severity,
            "message": f"{metric_name} 检测到异常：{', '.join(anomaly_types)}" if is_anomaly else f"{metric_name} 正常",
            "detection_time": datetime.now().isoformat()
        }

    # ---------------------- 告警生成和管理 ----------------------

    def generate_alert(
        self,
        alert_type: str,
        metric_name: str,
        severity: str,
        message: str,
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成告警

        Args:
            alert_type: 告警类型 (threshold, anomaly, performance, risk)
            metric_name: 指标名称
            severity: 严重程度 (low, medium, high, critical)
            message: 告警消息
            details: 详细信息

        Returns:
            告警对象
        """
        alert_id = f"{alert_type}_{metric_name}_{datetime.now().timestamp()}"

        alert = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "metric_name": metric_name,
            "severity": severity,
            "message": message,
            "details": details or {},
            "created_at": datetime.now().isoformat(),
            "acknowledged": False,
            "resolved": False,
            "cluster_id": None
        }

        # 添加到历史记录
        self._alert_history.append(alert)

        # 告警聚类
        cluster_id = self._cluster_alert(alert)
        alert["cluster_id"] = cluster_id

        # 记录到Memo0
        self._record_alert_to_memo0(alert)

        logger.warning(f"告警生成: {severity.upper()} - {message}")

        return alert

    def _cluster_alert(self, alert: Dict) -> str:
        """告警聚类

        将相似的告警分组到同一个cluster中。

        Args:
            alert: 告警对象

        Returns:
            cluster_id
        """
        alert_type = alert["alert_type"]
        metric_name = alert["metric_name"]
        severity = alert["severity"]

        # 简单聚类规则：相同类型 + 相同指标 + 相同严重程度 = 同一cluster
        cluster_key = f"{alert_type}_{metric_name}_{severity}"

        # 检查是否已有相似cluster（最近5分钟内的）
        recent_threshold = datetime.now() - timedelta(minutes=5)

        for cluster_id, cluster_alerts in self._alert_clusters.items():
            if not cluster_alerts:
                continue

            last_alert = cluster_alerts[-1]
            last_time = datetime.fromisoformat(last_alert["created_at"])

            if last_time < recent_threshold:
                # cluster太旧，忽略
                continue

            # 检查相似性
            last_key = f"{last_alert['alert_type']}_{last_alert['metric_name']}_{last_alert['severity']}"
            if last_key == cluster_key:
                # 加入现有cluster
                self._alert_clusters[cluster_id].append(alert)
                return cluster_id

        # 创建新cluster
        new_cluster_id = f"cluster_{datetime.now().timestamp()}"
        self._alert_clusters[new_cluster_id] = [alert]

        return new_cluster_id

    def _record_alert_to_memo0(self, alert: Dict):
        """将告警记录到Memo0"""
        content = f"""
[告警] {alert['created_at']}

告警ID: {alert['alert_id']}
告警类型: {alert['alert_type']}
指标名称: {alert['metric_name']}
严重程度: {alert['severity'].upper()}

告警消息:
{alert['message']}

详细信息:
{json.dumps(alert.get('details', {}), indent=2, ensure_ascii=False)}

Cluster ID: {alert.get('cluster_id', 'N/A')}
""".strip()

        self.storage.add_knowledge(
            category="alert",
            content=content,
            metadata={
                "alert_id": alert["alert_id"],
                "alert_type": alert["alert_type"],
                "metric_name": alert["metric_name"],
                "severity": alert["severity"],
                "created_at": alert["created_at"]
            }
        )

    # ---------------------- 告警预测 ----------------------

    def predict_alerts(
        self,
        metric_name: str,
        current_trend: List[float],
        forecast_horizon: int = 5
    ) -> Dict[str, Any]:
        """预测未来告警

        基于当前趋势，预测未来是否可能触发告警。

        Args:
            metric_name: 指标名称
            current_trend: 当前趋势数据（最近的值）
            forecast_horizon: 预测步数

        Returns:
            预测结果
        """
        if len(current_trend) < 10:
            return {
                "prediction": "unknown",
                "confidence": 0.0,
                "message": "趋势数据不足，无法预测"
            }

        # 1. 简单线性趋势预测
        recent_values = current_trend[-10:]
        slope = (recent_values[-1] - recent_values[0]) / len(recent_values)

        # 2. 预测未来值
        predicted_values = []
        for i in range(1, forecast_horizon + 1):
            predicted = recent_values[-1] + slope * i
            predicted_values.append(max(0, predicted))  # 避免负值

        # 3. 检查预测值是否超过阈值
        threshold_data = self._dynamic_thresholds.get(metric_name)
        if threshold_data:
            upper_threshold = threshold_data.get("upper")
            lower_threshold = threshold_data.get("lower")
        else:
            # 使用静态阈值
            threshold = self.thresholds.get(metric_name)
            if isinstance(threshold, (int, float)):
                upper_threshold = threshold
                lower_threshold = 0
            elif isinstance(threshold, dict):
                upper_threshold = threshold.get("max")
                lower_threshold = threshold.get("min")
            else:
                upper_threshold = None
                lower_threshold = None

        predicted_alerts = []
        for i, predicted in enumerate(predicted_values):
            if upper_threshold and predicted > upper_threshold:
                predicted_alerts.append({
                    "step": i + 1,
                    "predicted_value": predicted,
                    "threshold": upper_threshold,
                    "direction": "exceed_upper"
                })
            elif lower_threshold and predicted < lower_threshold:
                predicted_alerts.append({
                    "step": i + 1,
                    "predicted_value": predicted,
                    "threshold": lower_threshold,
                    "direction": "below_lower"
                })

        # 4. 生成预测结论
        if not predicted_alerts:
            prediction = "normal"
            message = f"预测未来{forecast_horizon}步{metric_name}正常"
            confidence = 0.7
        else:
            earliest_alert = predicted_alerts[0]
            prediction = "alert_expected"
            message = f"预计{earliest_alert['step']}步后{metric_name}将{earliest_alert['direction']}阈值"
            confidence = 0.6 + (len(predicted_alerts) / forecast_horizon) * 0.3

        return {
            "prediction": prediction,
            "confidence": confidence,
            "message": message,
            "predicted_values": predicted_values,
            "predicted_alerts": predicted_alerts,
            "slope": slope,
            "prediction_time": datetime.now().isoformat()
        }

    # ---------------------- 告警统计和分析 ----------------------

    def get_alert_statistics(
        self,
        time_range: str = "24h"
    ) -> Dict[str, Any]:
        """获取告警统计

        Args:
            time_range: 时间范围 (1h, 6h, 24h, 7d, 30d)

        Returns:
            统计信息
        """
        # 时间过滤
        time_threshold = self._get_time_threshold(time_range)
        filtered_alerts = [
            a for a in self._alert_history
            if datetime.fromisoformat(a["created_at"]) >= time_threshold
        ]

        # 基础统计
        total_alerts = len(filtered_alerts)
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        by_metric = defaultdict(int)
        acknowledged_count = sum(1 for a in filtered_alerts if a["acknowledged"])
        resolved_count = sum(1 for a in filtered_alerts if a["resolved"])

        for alert in filtered_alerts:
            by_severity[alert["severity"]] += 1
            by_type[alert["alert_type"]] += 1
            by_metric[alert["metric_name"]] += 1

        # Cluster统计
        active_clusters = 0
        for cluster_id, cluster_alerts in self._alert_clusters.items():
            last_alert = cluster_alerts[-1]
            if not last_alert["resolved"]:
                active_clusters += 1

        return {
            "time_range": time_range,
            "total_alerts": total_alerts,
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "by_metric": dict(by_metric),
            "acknowledged_count": acknowledged_count,
            "resolved_count": resolved_count,
            "acknowledgment_rate": acknowledged_count / total_alerts if total_alerts > 0 else 0,
            "resolution_rate": resolved_count / total_alerts if total_alerts > 0 else 0,
            "active_clusters": active_clusters,
            "generated_at": datetime.now().isoformat()
        }

    def _get_time_threshold(self, time_range: str) -> datetime:
        """获取时间阈值"""
        now = datetime.now()

        if time_range == "1h":
            return now - timedelta(hours=1)
        elif time_range == "6h":
            return now - timedelta(hours=6)
        elif time_range == "24h":
            return now - timedelta(hours=24)
        elif time_range == "7d":
            return now - timedelta(days=7)
        elif time_range == "30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)

    def get_active_alerts(self) -> List[Dict]:
        """获取活跃告警（未解决的告警）"""
        return [a for a in self._alert_history if not a["resolved"]]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警

        Args:
            alert_id: 告警ID

        Returns:
            是否成功
        """
        for alert in self._alert_history:
            if alert["alert_id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_at"] = datetime.now().isoformat()
                logger.info(f"告警已确认: {alert_id}")
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警

        Args:
            alert_id: 告警ID

        Returns:
            是否成功
        """
        for alert in self._alert_history:
            if alert["alert_id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.now().isoformat()
                logger.info(f"告警已解决: {alert_id}")
                return True
        return False

    # ---------------------- 批量检测接口 ----------------------

    def check_all_metrics(
        self,
        metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[Dict]]:
        """批量检测所有指标

        Args:
            metrics: 指标字典
            {
                "metric_name": {
                    "current_value": float,
                    "historical_data": List[float],
                    "type": str  # threshold, anomaly
                }
            }

        Returns:
            检测结果
            {
                "alerts": List[Dict],
                "anomalies": List[Dict],
                "predictions": List[Dict]
            }
        """
        results = {
            "alerts": [],
            "anomalies": [],
            "predictions": []
        }

        for metric_name, metric_data in metrics.items():
            current_value = metric_data.get("current_value")
            historical_data = metric_data.get("historical_data", [])
            metric_type = metric_data.get("type", "threshold")

            if metric_type == "threshold":
                # 动态阈值检测
                threshold_result = self.check_dynamic_threshold(
                    metric_name,
                    current_value,
                    historical_data
                )

                if threshold_result["is_alert"]:
                    alert = self.generate_alert(
                        alert_type="threshold",
                        metric_name=metric_name,
                        severity=threshold_result["severity"],
                        message=threshold_result["message"],
                        details=threshold_result
                    )
                    results["alerts"].append(alert)

                # 预测
                prediction = self.predict_alerts(metric_name, historical_data[-10:])
                if prediction["prediction"] == "alert_expected":
                    results["predictions"].append(prediction)

            elif metric_type == "anomaly":
                # 异常检测
                anomaly_result = self.detect_anomalies(
                    metric_name,
                    current_value,
                    historical_data
                )

                results["anomalies"].append(anomaly_result)

                if anomaly_result["is_anomaly"]:
                    alert = self.generate_alert(
                        alert_type="anomaly",
                        metric_name=metric_name,
                        severity=anomaly_result["severity"],
                        message=anomaly_result["message"],
                        details=anomaly_result
                    )
                    results["alerts"].append(alert)

        return results


# ---------------------- 便捷函数 ----------------------

_intelligent_alerting: Optional[IntelligentAlerting] = None


def get_intelligent_alerting() -> Optional[IntelligentAlerting]:
    """获取智能告警系统实例（全局单例）

    Returns:
        IntelligentAlerting 实例，如果未初始化则返回 None
    """
    return _intelligent_alerting


def initialize_intelligent_alerting(storage, config) -> IntelligentAlerting:
    """初始化智能告警系统

    Args:
        storage: 统一存储实例
        config: 配置管理器实例

    Returns:
        IntelligentAlerting 实例
    """
    global _intelligent_alerting

    if _intelligent_alerting is None:
        _intelligent_alerting = IntelligentAlerting(storage, config)

    return _intelligent_alerting
