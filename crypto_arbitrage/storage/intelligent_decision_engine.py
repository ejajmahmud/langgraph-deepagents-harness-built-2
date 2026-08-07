"""
智能决策引擎 V2.5增强版

基于Memo0历史经验，提供AI驱动的交易决策支持。

核心功能：
1. 策略选择建议（基于历史相似条件）
2. 风险评估（学习历史风险模式）
3. 参数优化建议（分析成功案例）
4. 异常智能检测（识别市场异常）
5. 决策解释（生成可解释的决策依据）
"""

import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 线程安全锁（V5.3添加）
_decision_engine_lock = threading.Lock()


class IntelligentDecisionEngine:
    """智能决策引擎增强版

    基于Memo0存储的历史经验，提供智能决策支持。
    """

    def __init__(self, storage, auto_accumulator):
        """初始化智能决策引擎

        Args:
            storage: 统一存储实例
            auto_accumulator: 自动知识积累器实例
        """
        self.storage = storage
        self.auto_accumulator = auto_accumulator
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 缓存5分钟

        logger.info("智能决策引擎初始化成功")

    # ---------------------- 策略选择建议 ----------------------

    def recommend_strategy(
        self,
        current_market_conditions: Dict[str, Any],
        available_strategies: List[str],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """基于历史经验推荐策略

        Args:
            current_market_conditions: 当前市场条件
            {
                "volatility": float,
                "trend": str,  # rising, falling, stable
                "liquidity": str,  # high, normal, low
                "funding_rate": float,
                "spread": float
            }
            available_strategies: 可用策略列表
            top_k: 返回Top-K推荐

        Returns:
            推荐结果
            {
                "recommendations": [
                    {
                        "strategy": str,
                        "confidence": float,
                        "expected_win_rate": float,
                        "expected_profit": float,
                        "reasoning": str,
                        "historical_trades": int
                    }
                ],
                "market_analysis": {
                    "volatility_level": str,
                    "trend_strength": str,
                    "liquidity_status": str
                },
                "alternative_strategies": List[str]
            }
        """
        # 查询相似历史决策
        similar_decisions = self.auto_accumulator.query_similar_decisions(
            market_conditions=current_market_conditions,
            top_k=20
        )

        # 分析策略表现
        strategy_performance = self._analyze_strategy_performance(
            similar_decisions,
            available_strategies
        )

        # 生成推荐
        recommendations = self._generate_strategy_recommendations(
            strategy_performance,
            current_market_conditions,
            top_k
        )

        # 市场分析
        market_analysis = self._analyze_market_conditions(current_market_conditions)

        return {
            "recommendations": recommendations,
            "market_analysis": market_analysis,
            "alternative_strategies": list(set(available_strategies) - {r["strategy"] for r in recommendations}),
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_strategy_performance(
        self,
        similar_decisions: List[Dict],
        available_strategies: List[str]
    ) -> Dict[str, Dict]:
        """分析策略表现"""
        performance = {s: {"trades": [], "wins": 0, "total_profit": 0} for s in available_strategies}

        for decision in similar_decisions:
            metadata = decision.get("metadata", {})
            strategy = metadata.get("strategy")

            if strategy in performance:
                outcome = metadata.get("outcome", "")
                performance[strategy]["trades"].append(decision)

                # 记录胜率
                if "成功" in outcome or "profit" in outcome.lower():
                    performance[strategy]["wins"] += 1

                # 记录利润（如果有）
                profit = metadata.get("actual_profit")
                if profit:
                    performance[strategy]["total_profit"] += profit

        # 计算统计指标
        for strategy, data in performance.items():
            trades = data["trades"]
            if trades:
                data["trade_count"] = len(trades)
                data["win_rate"] = data["wins"] / len(trades)
                data["avg_profit"] = data["total_profit"] / len(trades)
            else:
                data["trade_count"] = 0
                data["win_rate"] = 0.0
                data["avg_profit"] = 0.0

        return performance

    def _generate_strategy_recommendations(
        self,
        performance: Dict[str, Dict],
        market_conditions: Dict[str, Any],
        top_k: int
    ) -> List[Dict]:
        """生成策略推荐"""
        # 综合评分：胜率 * 0.6 + 平均利润 * 0.4
        scored_strategies = []

        for strategy, data in performance.items():
            if data["trade_count"] > 0:
                # 归一化评分
                max_win_rate = max(d["win_rate"] for d in performance.values()) or 1.0
                max_profit = max(abs(d["avg_profit"]) for d in performance.values()) or 1.0

                win_score = data["win_rate"] / max_win_rate
                profit_score = min(data["avg_profit"], max_profit) / max_profit

                total_score = win_score * 0.6 + profit_score * 0.4

                scored_strategies.append({
                    "strategy": strategy,
                    "confidence": total_score,
                    "expected_win_rate": data["win_rate"],
                    "expected_profit": data["avg_profit"],
                    "historical_trades": data["trade_count"],
                    "reasoning": self._generate_strategy_reasoning(strategy, data, market_conditions)
                })

        # 排序并返回Top-K
        scored_strategies.sort(key=lambda x: x["confidence"], reverse=True)
        return scored_strategies[:top_k]

    def _generate_strategy_reasoning(
        self,
        strategy: str,
        data: Dict,
        market_conditions: Dict
    ) -> str:
        """生成策略推荐理由"""
        reasons = []

        # 基于历史表现
        if data["win_rate"] >= 0.7:
            reasons.append(f"在相似市场条件下{strategy}历史胜率{data['win_rate']:.1%}")
        elif data["win_rate"] >= 0.5:
            reasons.append(f"在相似市场条件下{strategy}表现稳定")
        else:
            reasons.append(f"{strategy}在当前市场条件下需谨慎")

        # 基于市场条件
        volatility = market_conditions.get("volatility", 0)
        if volatility > 3.0:
            reasons.append("当前高波动环境，建议降低仓位")
        elif volatility < 1.0:
            reasons.append("当前低波动环境，套利机会可能减少")

        trend = market_conditions.get("trend", "stable")
        if trend == "rising":
            reasons.append("上升趋势，适合趋势跟随策略")
        elif trend == "falling":
            reasons.append("下降趋势，注意止损")

        liquidity = market_conditions.get("liquidity", "normal")
        if liquidity == "low":
            reasons.append("流动性不足，避免大额交易")

        return "; ".join(reasons)

    def _analyze_market_conditions(self, conditions: Dict) -> Dict:
        """分析市场条件"""
        volatility = conditions.get("volatility", 0)

        # 波动率等级
        if volatility > 3.0:
            volatility_level = "高"
        elif volatility > 1.5:
            volatility_level = "中"
        else:
            volatility_level = "低"

        # 趋势强度
        trend = conditions.get("trend", "stable")
        spread = conditions.get("spread", 0)
        if spread > 0.5:
            trend_strength = "强"
        elif spread > 0.2:
            trend_strength = "中"
        else:
            trend_strength = "弱"

        # 流动性状态
        liquidity = conditions.get("liquidity", "normal")

        return {
            "volatility_level": volatility_level,
            "trend_strength": trend_strength,
            "liquidity_status": liquidity
        }

    # ---------------------- 风险评估 ----------------------

    def assess_opportunity_risk(
        self,
        opportunity: Dict[str, Any],
        strategy: str,
        current_market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估交易机会风险

        Args:
            opportunity: 交易机会
            {
                "symbol": str,
                "expected_profit": float,
                "profit_rate": float,
                "max_position_size": float,
                "volatility": float
            }
            strategy: 策略名称
            current_market_conditions: 当前市场条件

        Returns:
            风险评估结果
            {
                "risk_level": str,  # low, medium, high, critical
                "risk_score": float,  # 0-100
                "risk_factors": List[Dict],
                "recommendations": List[str],
                "historical_similar_risks": List[Dict]
            }
        """
        risk_factors = []
        risk_score = 0

        # 1. 波动率风险
        volatility = opportunity.get("volatility", current_market_conditions.get("volatility", 0))
        if volatility > 4.0:
            risk_factors.append({
                "factor": "极端波动",
                "severity": "high",
                "description": f"波动率{volatility:.2f}%超过安全阈值",
                "score": 30
            })
            risk_score += 30
        elif volatility > 2.5:
            risk_factors.append({
                "factor": "高波动",
                "severity": "medium",
                "description": f"波动率{volatility:.2f}%较高",
                "score": 15
            })
            risk_score += 15

        # 2. 利润率风险
        profit_rate = opportunity.get("profit_rate", 0)
        if profit_rate < 0.2:
            risk_factors.append({
                "factor": "低利润率",
                "severity": "low",
                "description": f"利润率{profit_rate:.2f}%较低",
                "score": 5
            })
            risk_score += 5

        # 3. 市场流动性风险
        liquidity = current_market_conditions.get("liquidity", "normal")
        if liquidity == "low":
            risk_factors.append({
                "factor": "流动性不足",
                "severity": "high",
                "description": "市场流动性低，可能出现滑点",
                "score": 25
            })
            risk_score += 25
        elif liquidity == "normal":
            risk_factors.append({
                "factor": "流动性正常",
                "severity": "low",
                "description": "流动性良好",
                "score": 0
            })

        # 4. 策略历史风险
        strategy_risks = self.auto_accumulator.query_risk_events(event_type=strategy, top_k=10)
        if strategy_risks:
            high_severity_count = sum(1 for r in strategy_risks
                                    if r.get("metadata", {}).get("severity") in ["high", "critical"])
            if high_severity_count >= 3:
                risk_factors.append({
                    "factor": "策略历史风险",
                    "severity": "medium",
                    "description": f"{strategy}近期出现{high_severity_count}次高风险事件",
                    "score": 20
                })
                risk_score += 20

        # 风险等级
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 风险缓解建议
        recommendations = self._generate_risk_recommendations(risk_factors, risk_level)

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "historical_similar_risks": strategy_risks[:5],
            "assessed_at": datetime.now().isoformat()
        }

    def _generate_risk_recommendations(
        self,
        risk_factors: List[Dict],
        risk_level: str
    ) -> List[str]:
        """生成风险缓解建议"""
        recommendations = []

        for factor in risk_factors:
            factor_name = factor["factor"]

            if "波动" in factor_name:
                if factor["severity"] == "high":
                    recommendations.append("建议降低仓位至50%以下")
                else:
                    recommendations.append("建议降低仓位至70%以下")

            if "流动性" in factor_name:
                recommendations.append("设置更严格的止损点")
                recommendations.append("避免大额单笔交易")

            if "低利润率" in factor_name:
                recommendations.append("权衡风险收益比，谨慎交易")

            if "历史风险" in factor_name:
                recommendations.append("密切关注策略运行状态")
                recommendations.append("准备暂停策略的应急方案")

        # 基于风险等级的通用建议
        if risk_level == "critical":
            recommendations.insert(0, "强烈建议放弃此次交易机会")
        elif risk_level == "high":
            recommendations.insert(0, "建议大幅降低仓位并设置严格止损")
        elif risk_level == "medium":
            recommendations.insert(0, "建议降低仓位并关注市场变化")

        return list(set(recommendations))  # 去重

    # ---------------------- 参数优化建议 ----------------------

    def suggest_optimization(
        self,
        strategy: str,
        current_parameters: Dict[str, Any],
        current_performance: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """建议参数优化

        Args:
            strategy: 策略名称
            current_parameters: 当前参数
            current_performance: 当前表现
            market_conditions: 市场条件

        Returns:
            优化建议
            {
                "parameter_suggestions": List[Dict],
                "expected_improvement": Dict,
                "rationale": str
            }
        """
        suggestions = []

        # 查询历史表现
        historical_performance = self.auto_accumulator.query_strategy_performance(
            strategy=strategy,
            top_k=20
        )

        # 分析最佳参数
        best_parameters = self._analyze_best_parameters(historical_performance, market_conditions)

        # 生成参数建议
        for param_name, current_value in current_parameters.items():
            if param_name in best_parameters:
                best_value = best_parameters[param_name]
                improvement_potential = self._calculate_improvement_potential(
                    current_value,
                    best_value,
                    current_performance,
                    historical_performance
                )

                if improvement_potential > 0.1:  # 超过10%的改进潜力
                    suggestions.append({
                        "parameter": param_name,
                        "current_value": current_value,
                        "suggested_value": best_value,
                        "change_type": self._get_change_type(current_value, best_value),
                        "improvement_potential": improvement_potential,
                        "confidence": self._calculate_suggestion_confidence(historical_performance)
                    })

        return {
            "parameter_suggestions": suggestions,
            "expected_improvement": self._estimate_expected_improvement(suggestions),
            "rationale": self._generate_optimization_rationale(suggestions, historical_performance),
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_best_parameters(
        self,
        historical_performance: List[Dict],
        market_conditions: Dict
    ) -> Dict[str, Any]:
        """分析历史最佳参数"""
        # 简化实现：使用胜率最高的参数
        # 实际应该使用更复杂的统计分析
        best_params = {}

        win_rates = []
        for perf in historical_performance:
            metadata = perf.get("metadata", {})
            metrics = metadata.get("metrics", {})
            parameters = metadata.get("parameters", {})

            win_rate = metrics.get("win_rate", 0)
            if win_rate > 0:
                win_rates.append((parameters, win_rate))

        if win_rates:
            # 选择胜率最高的参数集
            best_params = max(win_rates, key=lambda x: x[1])[0]

        return best_params

    def _calculate_improvement_potential(
        self,
        current: Any,
        suggested: Any,
        current_perf: Dict,
        historical_perf: List[Dict]
    ) -> float:
        """计算改进潜力"""
        # 简化实现：基于历史数据估算
        # 实际应该使用更复杂的机器学习模型

        if isinstance(current, (int, float)) and isinstance(suggested, (int, float)):
            current_win_rate = current_perf.get("win_rate", 0)

            # 查找使用建议参数的历史表现
            similar_cases = [
                p for p in historical_perf
                if p.get("metadata", {}).get("parameters", {}).values()
                and suggested in p.get("metadata", {}).get("parameters", {}).values()
            ]

            if similar_cases:
                avg_win_rate_with_suggested = sum(
                    p.get("metadata", {}).get("metrics", {}).get("win_rate", 0)
                    for p in similar_cases
                ) / len(similar_cases)

                improvement = avg_win_rate_with_suggested - current_win_rate
                return max(0, improvement)

        return 0.0

    def _get_change_type(self, current: Any, suggested: Any) -> str:
        """获取参数变更类型"""
        if isinstance(current, (int, float)) and isinstance(suggested, (int, float)):
            if suggested > current:
                return "increase"
            elif suggested < current:
                return "decrease"
            else:
                return "no_change"
        return "modify"

    def _calculate_suggestion_confidence(self, historical_performance: List[Dict]) -> float:
        """计算建议置信度"""
        # 基于数据量
        data_points = len(historical_performance)

        if data_points < 5:
            return 0.3
        elif data_points < 10:
            return 0.5
        elif data_points < 20:
            return 0.7
        else:
            return 0.9

    def _estimate_expected_improvement(self, suggestions: List[Dict]) -> Dict[str, Any]:
        """估算预期改进"""
        if not suggestions:
            return {}

        avg_improvement = sum(s["improvement_potential"] for s in suggestions) / len(suggestions)

        return {
            "win_rate_improvement": avg_improvement,
            "profit_improvement": avg_improvement * 0.8,  # 保守估计
            "confidence": max(s["confidence"] for s in suggestions)
        }

    def _generate_optimization_rationale(
        self,
        suggestions: List[Dict],
        historical_perf: List[Dict]
    ) -> str:
        """生成优化建议理由"""
        if not suggestions:
            return "当前参数配置合理，无需调整"

        reasons = []

        # 数据量说明
        data_count = len(historical_perf)
        if data_count >= 20:
            reasons.append(f"基于{data_count}条历史数据分析")
        elif data_count >= 10:
            reasons.append(f"基于{data_count}条历史数据，建议谨慎参考")
        else:
            reasons.append(f"数据量有限（{data_count}条），建议持续观察")

        # 改进潜力说明
        improvements = [s["improvement_potential"] for s in suggestions]
        avg_improvement = sum(improvements) / len(improvements)

        if avg_improvement > 0.3:
            reasons.append(f"预期可提升胜率{avg_improvement:.1%}以上")
        elif avg_improvement > 0.1:
            reasons.append(f"预期可提升胜率{avg_improvement:.1%}")
        else:
            reasons.append("预期改进幅度较小")

        return "; ".join(reasons)

    # ---------------------- 异常检测 ----------------------

    def detect_anomalies(
        self,
        current_market_data: Dict[str, Any],
        historical_window: int = 100
    ) -> Dict[str, Any]:
        """检测市场异常

        Args:
            current_market_data: 当前市场数据
            {
                "price": float,
                "volume": float,
                "volatility": float,
                "spread": float
            }
            historical_window: 历史数据窗口大小

        Returns:
            异常检测结果
            {
                "anomalies": List[Dict],
                "anomaly_score": float,  # 0-100
                "market_status": str,  # normal, warning, critical
                "recommendations": List[str]
            }
        """
        anomalies = []
        anomaly_score = 0

        # 1. 价格异常检测
        price = current_market_data.get("price", 0)
        if price > 0:
            # 使用Memo0查询历史价格范围
            historical_prices = self._query_historical_prices(historical_window)

            if historical_prices:
                price_mean = sum(historical_prices) / len(historical_prices)
                price_std = (sum((p - price_mean) ** 2 for p in historical_prices) / len(historical_prices)) ** 0.5

                # 3σ原则检测异常
                z_score = (price - price_mean) / price_std if price_std > 0 else 0

                if abs(z_score) > 3:
                    anomalies.append({
                        "type": "price_anomaly",
                        "severity": "critical",
                        "description": f"价格偏离均值{abs(z_score):.1f}σ",
                        "z_score": z_score,
                        "score": 40
                    })
                    anomaly_score += 40
                elif abs(z_score) > 2:
                    anomalies.append({
                        "type": "price_anomaly",
                        "severity": "high",
                        "description": f"价格偏离均值{abs(z_score):.1f}σ",
                        "z_score": z_score,
                        "score": 25
                    })
                    anomaly_score += 25

        # 2. 成交量异常
        volume = current_market_data.get("volume", 0)
        if volume > 0:
            historical_volumes = self._query_historical_volumes(historical_window)

            if historical_volumes:
                volume_mean = sum(historical_volumes) / len(historical_volumes)
                volume_ratio = volume / volume_mean

                if volume_ratio > 5.0:
                    anomalies.append({
                        "type": "volume_anomaly",
                        "severity": "high",
                        "description": f"成交量是平均的{volume_ratio:.1f}倍",
                        "ratio": volume_ratio,
                        "score": 30
                    })
                    anomaly_score += 30
                elif volume_ratio < 0.1:
                    anomalies.append({
                        "type": "volume_anomaly",
                        "severity": "medium",
                        "description": f"成交量异常低（平均的{volume_ratio:.1%}）",
                        "ratio": volume_ratio,
                        "score": 20
                    })
                    anomaly_score += 20

        # 3. 波动率异常
        volatility = current_market_data.get("volatility", 0)
        if volatility > 5.0:
            anomalies.append({
                "type": "volatility_anomaly",
                "severity": "critical",
                "description": f"极端波动率{volatility:.2f}%",
                "value": volatility,
                "score": 35
            })
            anomaly_score += 35
        elif volatility > 3.5:
            anomalies.append({
                "type": "volatility_anomaly",
                "severity": "high",
                "description": f"高波动率{volatility:.2f}%",
                "value": volatility,
                "score": 20
            })
            anomaly_score += 20

        # 4. 价差异常
        spread = current_market_data.get("spread", 0)
        if spread > 1.0:
            anomalies.append({
                "type": "spread_anomaly",
                "severity": "high",
                "description": f"价差过大{spread:.2f}%",
                "value": spread,
                "score": 25
            })
            anomaly_score += 25

        # 市场状态
        if anomaly_score >= 70:
            market_status = "critical"
        elif anomaly_score >= 40:
            market_status = "warning"
        else:
            market_status = "normal"

        # 异常应对建议
        recommendations = self._generate_anomaly_recommendations(anomalies, market_status)

        return {
            "anomalies": anomalies,
            "anomaly_score": anomaly_score,
            "market_status": market_status,
            "recommendations": recommendations,
            "detected_at": datetime.now().isoformat()
        }

    def _query_historical_prices(self, window: int) -> List[float]:
        """查询历史价格"""
        # 简化实现：从知识库查询
        # 实际应该从数据库查询历史数据
        try:
            results = self.storage.search_knowledge(
                query="价格历史记录",
                category="market_data",
                top_k=window
            )

            prices = []
            for r in results:
                metadata = r.get("metadata", {})
                if "price" in metadata:
                    prices.append(metadata["price"])

            return prices[-window:] if len(prices) > window else prices
        except:
            return []

    def _query_historical_volumes(self, window: int) -> List[float]:
        """查询历史成交量"""
        # 简化实现
        try:
            results = self.storage.search_knowledge(
                query="成交量历史记录",
                category="market_data",
                top_k=window
            )

            volumes = []
            for r in results:
                metadata = r.get("metadata", {})
                if "volume" in metadata:
                    volumes.append(metadata["volume"])

            return volumes[-window:] if len(volumes) > window else volumes
        except:
            return []

    def _generate_anomaly_recommendations(
        self,
        anomalies: List[Dict],
        market_status: str
    ) -> List[str]:
        """生成异常应对建议"""
        recommendations = []

        for anomaly in anomalies:
            anomaly_type = anomaly["type"]

            if "price_anomaly" in anomaly_type:
                recommendations.append("价格异常，暂停新开仓")
                recommendations.append("密切关注价格走势，准备平仓")

            if "volume_anomaly" in anomaly_type:
                if anomaly["ratio"] > 5.0:
                    recommendations.append("成交量激增，可能有大户操作")
                    recommendations.append("降低仓位，防范流动性风险")

            if "volatility_anomaly" in anomaly_type:
                recommendations.append("波动率过高，收紧止损")
                recommendations.append("考虑使用更保守的策略参数")

            if "spread_anomaly" in anomaly_type:
                recommendations.append("价差过大，套利机会增加但风险也增加")

        # 基于市场状态的通用建议
        if market_status == "critical":
            recommendations.insert(0, "市场异常严重，建议暂停所有交易")
        elif market_status == "warning":
            recommendations.insert(0, "市场异常，建议降低仓位并谨慎操作")

        return list(set(recommendations))


# ---------------------- 便捷函数 ----------------------

_decision_engine: Optional[IntelligentDecisionEngine] = None


def get_decision_engine() -> Optional[IntelligentDecisionEngine]:
    """获取智能决策引擎实例（全局单例）

    Returns:
        IntelligentDecisionEngine 实例，如果未初始化则返回 None
    """
    return _decision_engine


def initialize_decision_engine(storage, auto_accumulator) -> IntelligentDecisionEngine:
    """初始化智能决策引擎（V5.3线程安全版）

    Args:
        storage: 统一存储实例
        auto_accumulator: 自动知识积累器实例

    Returns:
        IntelligentDecisionEngine 实例
    """
    global _decision_engine

    # 双重检查锁定模式（线程安全）
    if _decision_engine is None:
        with _decision_engine_lock:
            # 再次检查，防止其他线程已经初始化
            if _decision_engine is None:
                _decision_engine = IntelligentDecisionEngine(storage, auto_accumulator)
                logger.debug("智能决策引擎初始化完成（线程安全）")

    return _decision_engine
