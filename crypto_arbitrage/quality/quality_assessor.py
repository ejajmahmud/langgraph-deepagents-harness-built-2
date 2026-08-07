"""质量评估和时效性管理 V15.9 Phase 3

评估知识质量和时效性,确保知识库的高质量。

核心功能：
1. 质量评估 - 评估知识的准确性、完整性、一致性
2. 时效性管理 - 管理知识的时效性和更新频率
3. 质量评分 - 综合评分算法
4. 质量报告 - 生成质量报告
5. 质量优化 - 提供质量优化建议

性能目标：
- 质量评估准确率 > 90%
- 评估速度 > 100条/秒
- 时效性预测准确率 > 85%
- 质量提升效果 > 20%

创建时间：2026-05-01 05:22
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import statistics
import time
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """质量维度"""
    ACCURACY = "accuracy"  # 准确性
    COMPLETENESS = "completeness"  # 完整性
    CONSISTENCY = "consistency"  # 一致性
    TIMELINESS = "timeliness"  # 时效性
    RELEVANCE = "relevance"  # 相关性
    CONFIDENCE = "confidence"  # 置信度


class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = "excellent"  # 优秀 (>= 90)
    GOOD = "good"  # 良好 (75 - 89)
    FAIR = "fair"  # 一般 (60 - 74)
    POOR = "poor"  # 较差 (< 60)


@dataclass
class QualityScore:
    """质量分数"""
    overall_score: float  # 总体分数 (0 - 100)
    dimension_scores: Dict[QualityDimension, float]  # 各维度分数
    quality_level: QualityLevel  # 质量等级
    assessed_at: float  # 评估时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_score": self.overall_score,
            "dimension_scores": {
                dim.value: score
                for dim, score in self.dimension_scores.items()
            },
            "quality_level": self.quality_level.value,
            "assessed_at": self.assessed_at
        }

    def get_quality_level(self) -> QualityLevel:
        """获取质量等级"""
        if self.overall_score >= 90:
            return QualityLevel.EXCELLENT
        elif self.overall_score >= 75:
            return QualityLevel.GOOD
        elif self.overall_score >= 60:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR


@dataclass
class QualityMetrics:
    """质量指标"""
    total_assessed: int = 0
    excellent_count: int = 0
    good_count: int = 0
    fair_count: int = 0
    poor_count: int = 0
    avg_overall_score: float = 0.0
    avg_timeliness_score: float = 0.0
    avg_accuracy_score: float = 0.0

    def get_quality_distribution(self) -> Dict[str, float]:
        """获取质量分布

        Returns:
            质量分布字典
        """
        if self.total_assessed == 0:
            return {}

        return {
            "excellent": self.excellent_count / self.total_assessed,
            "good": self.good_count / self.total_assessed,
            "fair": self.fair_count / self.total_assessed,
            "poor": self.poor_count / self.total_assessed
        }


class TimelinessPredictor:
    """时效性预测器

    预测知识的时效性。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化时效性预测器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 时效性历史
        self.timeliness_history: List[Dict[str, Any]] = []

        # 半衰期（知识过期的平均时间）
        self.half_life_hours = self.config.get("half_life_hours", 24)  # 默认24小时

    def predict_timeliness(self, knowledge: Dict[str, Any]) -> float:
        """预测知识的时效性

        Args:
            knowledge: 知识数据

        Returns:
            时效性分数 (0 - 100)
        """
        knowledge_type = knowledge.get("knowledge_type", "")
        created_at = knowledge.get("created_at", time.time())

        # 计算知识年龄
        age_hours = (time.time() - created_at) / 3600

        # 根据知识类型调整半衰期
        type_half_life = self._get_type_half_life(knowledge_type)

        # 计算时效性分数
        if age_hours >= type_half_life:
            timeliness_score = max(0, 100 * (0.5 ** (age_hours / type_half_life)))
        else:
            timeliness_score = 100 - (age_hours / type_half_life) * 50

        # 记录历史
        self.timeliness_history.append({
            "knowledge_type": knowledge_type,
            "age_hours": age_hours,
            "predicted_score": timeliness_score
        })

        # 保持最近1000条记录
        if len(self.timeliness_history) > 1000:
            self.timeliness_history.pop(0)

        return timeliness_score

    def _get_type_half_life(self, knowledge_type: str) -> float:
        """获取知识类型的半衰期

        Args:
            knowledge_type: 知识类型

        Returns:
            半衰期（小时）
        """
        # 不同类型的知识有不同的时效性
        half_lives = {
            "market_pattern": 12,  # 市场模式：12小时
            "price_relation": 24,  # 价格关系：24小时
            "volatility_pattern": 6,  # 波动率模式：6小时
            "correlation": 48,  # 相关性：48小时
            "arbitrage_opportunity": 1,  # 套利机会：1小时
            "risk_signal": 4,  # 风险信号：4小时
            "trend_analysis": 24  # 趋势分析：24小时
        }

        return half_lives.get(knowledge_type, self.half_life_hours)


class QualityAssessor:
    """质量评估器

    评估知识质量。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化质量评估器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 时效性预测器
        self.timeliness_predictor = TimelinessPredictor(config)

        # 质量评估历史
        self.assessment_history: List[QualityScore] = []

        # 质量指标
        self.metrics = QualityMetrics()

        logger.info("质量评估器初始化完成")

    async def assess_quality(self, knowledge: Dict[str, Any]) -> QualityScore:
        """评估知识质量

        Args:
            knowledge: 知识数据

        Returns:
            质量分数
        """
        self.metrics.total_assessed += 1

        # 评估各维度
        dimension_scores = {
            QualityDimension.ACCURACY: self._assess_accuracy(knowledge),
            QualityDimension.COMPLETENESS: self._assess_completeness(knowledge),
            QualityDimension.CONSISTENCY: self._assess_consistency(knowledge),
            QualityDimension.TIMELINESS: self._assess_timeliness(knowledge),
            QualityDimension.RELEVANCE: self._assess_relevance(knowledge),
            QualityDimension.CONFIDENCE: self._assess_confidence(knowledge)
        }

        # 计算总体分数（加权平均）
        weights = {
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.COMPLETENESS: 0.15,
            QualityDimension.CONSISTENCY: 0.20,
            QualityDimension.TIMELINESS: 0.15,
            QualityDimension.RELEVANCE: 0.15,
            QualityDimension.CONFIDENCE: 0.10
        }

        overall_score = sum(
            dimension_scores[dim] * weights[dim]
            for dim in QualityDimension
        )

        # 确定质量等级
        quality_level = QualityScore(overall_score, dimension_scores, QualityLevel.EXCELLENT, time.time()).get_quality_level()

        # 创建质量分数
        quality_score = QualityScore(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            quality_level=quality_level,
            assessed_at=time.time()
        )

        # 记录历史
        self.assessment_history.append(quality_score)

        # 更新指标
        self._update_metrics(quality_score)

        return quality_score

    def _assess_accuracy(self, knowledge: Dict[str, Any]) -> float:
        """评估准确性

        Args:
            knowledge: 知识数据

        Returns:
            准确性分数 (0 - 100)
        """
        # 基于证据数量评估
        evidence = knowledge.get("evidence", [])

        if not evidence:
            return 50.0  # 没有证据，中等分数

        # 证据数量越多，准确性越高
        evidence_score = min(100.0, 50.0 + len(evidence) * 10.0)

        # 基于置信度调整
        confidence = knowledge.get("confidence", 0.5)
        accuracy_score = evidence_score * (0.5 + confidence * 0.5)

        return accuracy_score

    def _assess_completeness(self, knowledge: Dict[str, Any]) -> float:
        """评估完整性

        Args:
            knowledge: 知识数据

        Returns:
            完整性分数 (0 - 100)
        """
        required_fields = ["knowledge_id", "knowledge_type", "content", "confidence"]
        present_fields = sum(1 for field in required_fields if field in knowledge)

        # 计算完整性比例
        completeness_ratio = present_fields / len(required_fields)

        # 基础分数
        completeness_score = completeness_ratio * 80.0

        # 检查可选字段
        optional_fields = ["evidence", "metadata", "created_at", "updated_at"]
        optional_present = sum(1 for field in optional_fields if field in knowledge)

        # 可选字段加分
        completeness_score += min(20.0, optional_present * 5.0)

        return completeness_score

    def _assess_consistency(self, knowledge: Dict[str, Any]) -> float:
        """评估一致性

        Args:
            knowledge: 知识数据

        Returns:
            一致性分数 (0 - 100)
        """
        # 基于知识类型的一致性
        knowledge_type = knowledge.get("knowledge_type", "")
        content = knowledge.get("content", "")

        # 检查内容是否与类型匹配
        type_keywords = {
            "market_pattern": ["趋势", "模式", "上涨", "下降", "横盘"],
            "price_relation": ["关系", "高于", "低于", "偏离", "平均"],
            "volatility_pattern": ["波动率", "波动", "低", "中", "高"],
            "correlation": ["相关", "相关系数", "正相关", "负相关"],
            "arbitrage_opportunity": ["套利", "机会", "价差", "利润"],
            "risk_signal": ["风险", "警告", "危险", "信号"],
            "trend_analysis": ["趋势", "分析", "预测", "预期"]
        }

        keywords = type_keywords.get(knowledge_type, [])

        if not keywords:
            return 70.0  # 未知类型，中等分数

        # 检查内容是否包含关键词
        keyword_count = sum(1 for keyword in keywords if keyword in content)

        consistency_score = 50.0 + min(50.0, keyword_count * 10.0)

        return consistency_score

    def _assess_timeliness(self, knowledge: Dict[str, Any]) -> float:
        """评估时效性

        Args:
            knowledge: 知识数据

        Returns:
            时效性分数 (0 - 100)
        """
        return self.timeliness_predictor.predict_timeliness(knowledge)

    def _assess_relevance(self, knowledge: Dict[str, Any]) -> float:
        """评估相关性

        Args:
            knowledge: 知识数据

        Returns:
            相关性分数 (0 - 100)
        """
        # 基于知识类型和内容的相关性
        knowledge_type = knowledge.get("knowledge_type", "")
        content = knowledge.get("content", "")

        # 高相关性知识类型
        high_relevance_types = [
            "arbitrage_opportunity",
            "risk_signal",
            "market_pattern"
        ]

        if knowledge_type in high_relevance_types:
            relevance_score = 90.0
        else:
            relevance_score = 70.0

        # 内容长度调整（太短可能不相关）
        if len(content) < 10:
            relevance_score -= 20.0

        return max(0.0, relevance_score)

    def _assess_confidence(self, knowledge: Dict[str, Any]) -> float:
        """评估置信度

        Args:
            knowledge: 知识数据

        Returns:
            置信度分数 (0 - 100)
        """
        confidence = knowledge.get("confidence", 0.0)
        return confidence * 100.0

    def _update_metrics(self, quality_score: QualityScore) -> None:
        """更新质量指标

        Args:
            quality_score: 质量分数
        """
        # 更新质量等级计数
        quality_level = quality_score.quality_level

        if quality_level == QualityLevel.EXCELLENT:
            self.metrics.excellent_count += 1
        elif quality_level == QualityLevel.GOOD:
            self.metrics.good_count += 1
        elif quality_level == QualityLevel.FAIR:
            self.metrics.fair_count += 1
        else:
            self.metrics.poor_count += 1

        # 更新平均分数
        total = self.metrics.total_assessed
        self.metrics.avg_overall_score = (
            self.metrics.avg_overall_score * (total - 1) +
            quality_score.overall_score
        ) / total

        self.metrics.avg_timeliness_score = (
            self.metrics.avg_timeliness_score * (total - 1) +
            quality_score.dimension_scores[QualityDimension.TIMELINESS]
        ) / total

        self.metrics.avg_accuracy_score = (
            self.metrics.avg_accuracy_score * (total - 1) +
            quality_score.dimension_scores[QualityDimension.ACCURACY]
        ) / total

    def get_metrics(self) -> QualityMetrics:
        """获取质量指标

        Returns:
            质量指标
        """
        return self.metrics

    def generate_quality_report(self) -> Dict[str, Any]:
        """生成质量报告

        Returns:
            质量报告
        """
        metrics = self.get_metrics()

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_assessed": metrics.total_assessed,
            "quality_distribution": metrics.get_quality_distribution(),
            "average_scores": {
                "overall": metrics.avg_overall_score,
                "timeliness": metrics.avg_timeliness_score,
                "accuracy": metrics.avg_accuracy_score
            },
            "quality_counts": {
                "excellent": metrics.excellent_count,
                "good": metrics.good_count,
                "fair": metrics.fair_count,
                "poor": metrics.poor_count
            },
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成质量优化建议

        Returns:
            建议列表
        """
        recommendations = []
        metrics = self.get_metrics()

        # 基于质量分布生成建议
        distribution = metrics.get_quality_distribution()

        poor_ratio = distribution.get("poor", 0.0)
        fair_ratio = distribution.get("fair", 0.0)

        if poor_ratio > 0.2:
            recommendations.append("较差质量知识比例过高，建议加强知识验证")

        if fair_ratio > 0.4:
            recommendations.append("一般质量知识比例较高，建议提升知识提取质量")

        if metrics.avg_timeliness_score < 60:
            recommendations.append("知识时效性较低，建议增加更新频率")

        if metrics.avg_accuracy_score < 70:
            recommendations.append("知识准确性有待提升，建议增加证据支持")

        if not recommendations:
            recommendations.append("知识质量良好，继续保持")

        return recommendations


async def main():
    """主函数 - 测试质量评估器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建质量评估器
    assessor = QualityAssessor()

    # 测试知识
    test_knowledges = [
        {
            "knowledge_id": "test_001",
            "knowledge_type": "market_pattern",
            "content": "BTC/USDT 上升趋势，创新高",
            "confidence": 0.85,
            "evidence": ["价格连续上涨", "突破前高"],
            "created_at": time.time() - 3600  # 1小时前
        },
        {
            "knowledge_id": "test_002",
            "knowledge_type": "volatility_pattern",
            "content": "ETH/USDT 低波动率（<1%），适合套利",
            "confidence": 0.78,
            "evidence": ["波动率计算结果"],
            "created_at": time.time() - 7200  # 2小时前
        },
        {
            "knowledge_id": "test_003",
            "knowledge_type": "arbitrage_opportunity",
            "content": "Binance 和 Okex 之间存在套利机会",
            "confidence": 0.72,
            "evidence": ["价差分析"],
            "created_at": time.time() - 300  # 5分钟前
        }
    ]

    # 评估质量
    print("\n=== 评估知识质量 ===")
    quality_scores = []

    for knowledge in test_knowledges:
        quality_score = await assessor.assess_quality(knowledge)
        quality_scores.append(quality_score)

        print(f"\n知识: {knowledge['content'][:40]}...")
        print(f"总体分数: {quality_score.overall_score:.2f}")
        print(f"质量等级: {quality_score.quality_level.value}")
        print(f"各维度分数:")
        for dim, score in quality_score.dimension_scores.items():
            print(f"  {dim.value}: {score:.2f}")

    # 显示质量指标
    metrics = assessor.get_metrics()
    print(f"\n=== 质量指标 ===")
    print(f"总评估数: {metrics.total_assessed}")
    print(f"优秀: {metrics.excellent_count}")
    print(f"良好: {metrics.good_count}")
    print(f"一般: {metrics.fair_count}")
    print(f"较差: {metrics.poor_count}")
    print(f"平均总体分数: {metrics.avg_overall_score:.2f}")
    print(f"平均时效性分数: {metrics.avg_timeliness_score:.2f}")
    print(f"平均准确性分数: {metrics.avg_accuracy_score:.2f}")

    # 显示质量报告
    report = assessor.generate_quality_report()
    print(f"\n=== 质量报告 ===")
    print(f"质量分布: {report['quality_distribution']}")
    print(f"\n优化建议:")
    for i, recommendation in enumerate(report['recommendations'], 1):
        print(f"{i}. {recommendation}")


if __name__ == "__main__":
    asyncio.run(main())
