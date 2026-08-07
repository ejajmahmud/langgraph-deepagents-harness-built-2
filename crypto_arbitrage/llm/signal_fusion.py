"""信号融合引擎

V2.6新增：融合多种信号源（LLM + 技术 + 套利 + 风险）
输出统一的交易决策和置信度评分。

信号源：
1. LLM信号 (TradingAgents): 基于多智能体LLM分析
2. 技术指标信号: 基于技术分析（RSI, MACD, 布林带等）
3. 套利信号: 基于套利机会检测
4. 风险信号: 基于风险评估和风险事件

融合策略：
- 加权平均（可配置权重）
- 置信度加权
- 分歧检测和警告
- 动态权重调整（基于历史表现）
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SignalFusionEngine:
    """信号融合引擎

    融合多种信号源，输出统一的交易决策和置信度评分。
    """

    def __init__(self):
        """初始化信号融合引擎"""
        self.signal_sources = ["llm", "technical", "arbitrage", "risk"]

        # 默认权重配置
        self.default_weights = {
            "llm": 0.35,        # LLM信号权重
            "technical": 0.25,   # 技术指标权重
            "arbitrage": 0.25,   # 套利信号权重
            "risk": 0.15         # 风险信号权重
        }

        # 历史表现追踪（用于动态权重调整）
        self.historical_performance = {
            "llm": {"correct": 0, "total": 0, "accuracy": 0.5},
            "technical": {"correct": 0, "total": 0, "accuracy": 0.5},
            "arbitrage": {"correct": 0, "total": 0, "accuracy": 0.5},
            "risk": {"correct": 0, "total": 0, "accuracy": 0.5}
        }

        logger.info("SignalFusionEngine initialized")

    def fuse_signals(
        self,
        llm_signal: Optional[Dict[str, Any]] = None,
        technical_signal: Optional[Dict[str, Any]] = None,
        arbitrage_signal: Optional[Dict[str, Any]] = None,
        risk_signal: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None,
        use_dynamic_weights: bool = False
    ) -> Dict[str, Any]:
        """融合多种信号源

        Args:
            llm_signal: LLM信号 (TradingAgents输出)
                格式: {"signal": "BUY", "score": 100, "confidence": 0.9, ...}
            technical_signal: 技术指标信号
                格式: {"signal": "BUY", "score": 100, "confidence": 0.8, ...}
            arbitrage_signal: 套利信号
                格式: {"signal": "BUY", "score": 100, "confidence": 0.7, ...}
            risk_signal: 风险信号
                格式: {"signal": "HOLD", "score": 50, "confidence": 0.9, ...}
            weights: 自定义权重，格式: {"llm": 0.3, "technical": 0.3, ...}
            use_dynamic_weights: 是否使用动态权重（基于历史表现）

        Returns:
            融合结果字典，包含：
            - fused_signal: 融合后的信号 (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL)
            - fused_score: 融合后的评分 (0-100)
            - confidence: 置信度 (0-1)
            - divergence: 信号分歧度 (0-1)
            - warnings: 警告列表
            - breakdown: 各信号源贡献明细
        """
        # 归一化权重
        if weights is None:
            weights = self.default_weights.copy()

        # 使用动态权重
        if use_dynamic_weights:
            weights = self._calculate_dynamic_weights(weights)

        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            weights = self.default_weights.copy()

        # 收集有效信号
        signals = {
            "llm": llm_signal,
            "technical": technical_signal,
            "arbitrage": arbitrage_signal,
            "risk": risk_signal
        }

        # 过滤无效信号
        valid_signals = {
            k: v for k, v in signals.items()
            if v is not None and "score" in v and v["confidence"] > 0
        }

        if not valid_signals:
            # 无有效信号，返回中性结果
            return {
                "fused_signal": "HOLD",
                "fused_score": 50,
                "confidence": 0.0,
                "divergence": 0.0,
                "warnings": ["No valid signals available"],
                "breakdown": {}
            }

        # 计算加权评分
        fused_score = 0
        total_confidence = 0
        breakdown = {}

        for source, signal in valid_signals.items():
            weight = weights.get(source, 0)
            score = signal["score"]
            confidence = signal["confidence"]

            # 置信度加权
            weighted_score = score * weight * confidence
            fused_score += weighted_score
            total_confidence += weight * confidence

            breakdown[source] = {
                "signal": signal["signal"],
                "score": score,
                "confidence": confidence,
                "weight": weight,
                "contribution": weighted_score
            }

        # 归一化融合评分
        if total_confidence > 0:
            fused_score = fused_score / total_confidence
        else:
            fused_score = sum(v["score"] for v in valid_signals.values()) / len(valid_signals)

        # 限制评分范围
        fused_score = max(0, min(100, fused_score))

        # 将评分转换为信号
        fused_signal = self._interpret_fused_score(fused_score)

        # 计算分歧度
        divergence = self._detect_divergence(list(valid_signals.values()))

        # 生成警告
        warnings = self._generate_warnings(valid_signals, divergence)

        return {
            "fused_signal": fused_signal,
            "fused_score": fused_score,
            "confidence": min(total_confidence, 1.0),
            "divergence": divergence,
            "warnings": warnings,
            "breakdown": breakdown
        }

    def _interpret_fused_score(self, score: float) -> str:
        """将融合评分解释为信号

        Args:
            score: 融合评分 (0-100)

        Returns:
            交易信号 (BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL)
        """
        if score >= 85:
            return "BUY"
        elif score >= 65:
            return "OVERWEIGHT"
        elif score >= 35:
            return "HOLD"
        elif score >= 15:
            return "UNDERWEIGHT"
        else:
            return "SELL"

    def _detect_divergence(self, signals: List[Dict[str, Any]]) -> float:
        """检测信号分歧度

        计算各信号之间的分歧程度。

        Args:
            signals: 信号列表

        Returns:
            分歧度 (0-1)，1表示高度分歧
        """
        if len(signals) < 2:
            return 0.0

        scores = [s["score"] for s in signals]
        mean_score = sum(scores) / len(scores)

        # 计算方差
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # 归一化分歧度 (最大方差为2500，当score分别为0和100时)
        max_variance = 2500
        divergence = min(variance / max_variance, 1.0)

        return divergence

    def _generate_warnings(
        self,
        signals: Dict[str, Dict[str, Any]],
        divergence: float
    ) -> List[str]:
        """生成警告信息

        Args:
            signals: 信号字典
            divergence: 分歧度

        Returns:
            警告列表
        """
        warnings = []

        # 高分歧警告
        if divergence > 0.7:
            warnings.append("High signal divergence detected")
        elif divergence > 0.5:
            warnings.append("Moderate signal divergence detected")

        # 风险信号警告
        if "risk" in signals:
            risk_signal = signals["risk"]
            if risk_signal["signal"] in ["UNDERWEIGHT", "SELL"]:
                warnings.append("Risk assessment suggests caution")

        # 低置信度警告
        low_confidence_signals = [
            k for k, v in signals.items()
            if v["confidence"] < 0.5
        ]
        if len(low_confidence_signals) > len(signals) / 2:
            warnings.append("Multiple low-confidence signals")

        return warnings

    def _calculate_dynamic_weights(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """计算动态权重（基于历史表现）

        Args:
            base_weights: 基础权重

        Returns:
            动态调整后的权重
        """
        dynamic_weights = base_weights.copy()

        # 基于历史准确率调整权重
        for source, perf in self.historical_performance.items():
            if source in dynamic_weights and perf["total"] > 10:
                # 准确率 > 0.6时增加权重，< 0.4时减少权重
                accuracy = perf["accuracy"]
                if accuracy > 0.6:
                    adjustment_factor = 1.0 + (accuracy - 0.6)
                elif accuracy < 0.4:
                    adjustment_factor = 0.8 + (accuracy - 0.4) * 0.5
                else:
                    adjustment_factor = 1.0

                dynamic_weights[source] *= adjustment_factor

        return dynamic_weights

    def update_performance(
        self,
        source: str,
        is_correct: bool
    ) -> None:
        """更新信号源历史表现

        Args:
            source: 信号源名称 (llm/technical/arbitrage/risk)
            is_correct: 是否预测正确
        """
        if source not in self.historical_performance:
            return

        perf = self.historical_performance[source]
        perf["total"] += 1
        if is_correct:
            perf["correct"] += 1
        perf["accuracy"] = perf["correct"] / perf["total"]

        logger.info(
            f"Updated performance for {source}: "
            f"{perf['correct']}/{perf['total']} "
            f"({perf['accuracy']:.2%})"
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """获取历史表现报告

        Returns:
            表现报告字典
        """
        return {
            "source_performance": self.historical_performance,
            "default_weights": self.default_weights
        }

    def reset_performance_tracking(self) -> None:
        """重置历史表现追踪"""
        for source in self.historical_performance:
            self.historical_performance[source] = {
                "correct": 0,
                "total": 0,
                "accuracy": 0.5
            }
        logger.info("Performance tracking reset")


def create_signal_fusion_engine() -> SignalFusionEngine:
    """工厂函数：创建信号融合引擎

    Returns:
        SignalFusionEngine实例
    """
    return SignalFusionEngine()


def get_default_weights() -> Dict[str, float]:
    """获取默认权重配置

    Returns:
        默认权重字典
    """
    engine = SignalFusionEngine()
    return engine.default_weights.copy()
