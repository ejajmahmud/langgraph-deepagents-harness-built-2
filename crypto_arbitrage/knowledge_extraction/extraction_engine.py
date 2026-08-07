"""知识提取引擎 V15.9 Phase 3

从市场数据中提取知识,为知识图谱提供数据源。

核心功能：
1. 模式识别 - 识别市场模式和规律
2. 知识提取 - 从数据中提取结构化知识
3. 关系发现 - 发现数据之间的关系
4. 质量评估 - 评估提取知识的质量
5. 去重和合并 - 合并重复知识

性能目标：
- 知识提取准确率 > 90%
- 提取速度 > 100条/秒
- 去重准确率 > 95%
- 知识质量评分 > 85%

创建时间：2026-05-01 05:10
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import statistics
import hashlib
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知识类型"""
    MARKET_PATTERN = "market_pattern"  # 市场模式
    PRICE_RELATION = "price_relation"  # 价格关系
    VOLATILITY_PATTERN = "volatility_pattern"  # 波动率模式
    CORRELATION = "correlation"  # 相关性
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"  # 套利机会
    RISK_SIGNAL = "risk_signal"  # 风险信号
    TREND_ANALYSIS = "trend_analysis"  # 趋势分析


class Confidence(Enum):
    """置信度"""
    HIGH = "high"  # 高置信度 (>0.8)
    MEDIUM = "medium"  # 中置信度 (0.6-0.8)
    LOW = "low"  # 低置信度 (<0.6)


@dataclass
class ExtractedKnowledge:
    """提取的知识"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    content: str
    confidence: float  # 0.0 - 1.0
    evidence: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def get_confidence_level(self) -> Confidence:
        """获取置信度级别"""
        if self.confidence >= 0.8:
            return Confidence.HIGH
        elif self.confidence >= 0.6:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW


@dataclass
class ExtractionMetrics:
    """提取指标"""
    total_processed: int = 0
    total_extracted: int = 0
    duplicates_removed: int = 0
    avg_confidence: float = 0.0
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0

    def extraction_rate(self) -> float:
        """提取率"""
        if self.total_processed == 0:
            return 0.0
        return self.total_extracted / self.total_processed

    def avg_confidence_score(self) -> float:
        """平均置信度"""
        if self.total_extracted == 0:
            return 0.0
        return self.avg_confidence


class KnowledgeExtractor(ABC):
    """知识提取器接口"""

    @abstractmethod
    async def extract(self, data: Dict[str, Any]) -> List[ExtractedKnowledge]:
        """从数据中提取知识

        Args:
            data: 输入数据

        Returns:
            提取的知识列表
        """
        pass

    @abstractmethod
    def get_extractor_type(self) -> str:
        """获取提取器类型"""
        pass


class PricePatternExtractor(KnowledgeExtractor):
    """价格模式提取器

    从价格数据中提取价格模式和关系。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化价格模式提取器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.pattern_history: Dict[str, List[float]] = {}

    async def extract(self, data: Dict[str, Any]) -> List[ExtractedKnowledge]:
        """提取价格模式

        Args:
            data: 价格数据

        Returns:
            提取的知识列表
        """
        knowledges = []

        try:
            if "price" not in data:
                return knowledges

            price = data["price"]
            symbol = data.get("symbol", "UNKNOWN")

            # 记录价格历史
            if symbol not in self.pattern_history:
                self.pattern_history[symbol] = []
            self.pattern_history[symbol].append(price)

            # 保持最近100个价格点
            if len(self.pattern_history[symbol]) > 100:
                self.pattern_history[symbol].pop(0)

            # 需要至少10个价格点才能识别模式
            if len(self.pattern_history[symbol]) < 10:
                return knowledges

            # 识别价格模式
            pattern = self._identify_price_pattern(self.pattern_history[symbol])

            if pattern:
                knowledge = ExtractedKnowledge(
                    knowledge_id=self._generate_knowledge_id(symbol, "price_pattern"),
                    knowledge_type=KnowledgeType.MARKET_PATTERN,
                    content=f"{symbol} 价格模式: {pattern}",
                    confidence=0.75,
                    evidence=[f"价格序列: {self.pattern_history[symbol][-5:]}"],
                    metadata={
                        "symbol": symbol,
                        "pattern": pattern,
                        "price": price
                    }
                )
                knowledges.append(knowledge)

            # 识别价格关系
            relation = self._identify_price_relation(self.pattern_history[symbol])

            if relation:
                knowledge = ExtractedKnowledge(
                    knowledge_id=self._generate_knowledge_id(symbol, "price_relation"),
                    knowledge_type=KnowledgeType.PRICE_RELATION,
                    content=f"{symbol} 价格关系: {relation}",
                    confidence=0.70,
                    evidence=[f"当前价格: {price}"],
                    metadata={
                        "symbol": symbol,
                        "relation": relation,
                        "price": price
                    }
                )
                knowledges.append(knowledge)

        except Exception as e:
            logger.error(f"价格模式提取失败: {e}")

        return knowledges

    def _identify_price_pattern(self, price_history: List[float]) -> Optional[str]:
        """识别价格模式

        Args:
            price_history: 价格历史

        Returns:
            模式描述
        """
        if len(price_history) < 10:
            return None

        # 计算趋势
        recent_prices = price_history[-10:]
        trend = sum(recent_prices[-5:]) - sum(recent_prices[:5])

        # 识别模式
        if trend > 0:
            if recent_prices[-1] > max(recent_prices[:-1]):
                return "上升趋势，创新高"
            else:
                return "上升趋势，震荡上涨"
        elif trend < 0:
            if recent_prices[-1] < min(recent_prices[:-1]):
                return "下降趋势，创新低"
            else:
                return "下降趋势，震荡下跌"
        else:
            # 检查是否横盘
            std_dev = statistics.stdev(recent_prices)
            mean_price = statistics.mean(recent_prices)

            if std_dev / mean_price < 0.01:  # 波动率小于1%
                return "横盘整理，波动率低"
            else:
                return "震荡整理，波动率中等"

    def _identify_price_relation(self, price_history: List[float]) -> Optional[str]:
        """识别价格关系

        Args:
            price_history: 价格历史

        Returns:
            关系描述
        """
        if len(price_history) < 10:
            return None

        recent_prices = price_history[-10:]
        current_price = recent_prices[-1]
        avg_price = statistics.mean(recent_prices)

        # 计算价格偏离度
        deviation = (current_price - avg_price) / avg_price

        if abs(deviation) < 0.01:
            return "价格接近平均水平"
        elif deviation > 0:
            return f"价格高于平均水平 {deviation*100:.2f}%"
        else:
            return f"价格低于平均水平 {-deviation*100:.2f}%"

    def _generate_knowledge_id(self, symbol: str, knowledge_type: str) -> str:
        """生成知识ID

        Args:
            symbol: 交易对
            knowledge_type: 知识类型

        Returns:
            知识ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_value = hashlib.md5(f"{symbol}_{knowledge_type}_{timestamp}".encode()).hexdigest()[:8]
        return f"{symbol}_{knowledge_type}_{hash_value}"

    def get_extractor_type(self) -> str:
        """获取提取器类型"""
        return "PricePatternExtractor"


class VolatilityExtractor(KnowledgeExtractor):
    """波动率提取器

    从价格数据中提取波动率模式。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化波动率提取器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.price_history: Dict[str, List[float]] = {}

    async def extract(self, data: Dict[str, Any]) -> List[ExtractedKnowledge]:
        """提取波动率模式

        Args:
            data: 价格数据

        Returns:
            提取的知识列表
        """
        knowledges = []

        try:
            if "price" not in data:
                return knowledges

            price = data["price"]
            symbol = data.get("symbol", "UNKNOWN")

            # 记录价格历史
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(price)

            # 保持最近30个价格点
            if len(self.price_history[symbol]) > 30:
                self.price_history[symbol].pop(0)

            # 需要至少10个价格点才能计算波动率
            if len(self.price_history[symbol]) < 10:
                return knowledges

            # 计算波动率
            volatility = self._calculate_volatility(self.price_history[symbol])

            # 识别波动率模式
            volatility_pattern = self._identify_volatility_pattern(volatility, self.price_history[symbol])

            if volatility_pattern:
                knowledge = ExtractedKnowledge(
                    knowledge_id=self._generate_knowledge_id(symbol, "volatility"),
                    knowledge_type=KnowledgeType.VOLATILITY_PATTERN,
                    content=f"{symbol} 波动率模式: {volatility_pattern}",
                    confidence=0.80,
                    evidence=[f"波动率: {volatility:.4f}"],
                    metadata={
                        "symbol": symbol,
                        "volatility": volatility,
                        "pattern": volatility_pattern
                    }
                )
                knowledges.append(knowledge)

        except Exception as e:
            logger.error(f"波动率提取失败: {e}")

        return knowledges

    def _calculate_volatility(self, price_history: List[float]) -> float:
        """计算波动率

        Args:
            price_history: 价格历史

        Returns:
            波动率（标准差）
        """
        returns = []
        for i in range(1, len(price_history)):
            ret = (price_history[i] - price_history[i-1]) / price_history[i-1]
            returns.append(ret)

        if not returns:
            return 0.0

        return statistics.stdev(returns)

    def _identify_volatility_pattern(self, volatility: float, price_history: List[float]) -> Optional[str]:
        """识别波动率模式

        Args:
            volatility: 波动率
            price_history: 价格历史

        Returns:
            波动率模式描述
        """
        # 根据波动率水平分类
        if volatility < 0.01:
            return "低波动率（<1%），适合套利"
        elif volatility < 0.03:
            return "中等波动率（1%-3%），正常市场"
        elif volatility < 0.05:
            return "高波动率（3%-5%），注意风险"
        else:
            return "极高波动率（>5%），高风险"

    def _generate_knowledge_id(self, symbol: str, knowledge_type: str) -> str:
        """生成知识ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_value = hashlib.md5(f"{symbol}_{knowledge_type}_{timestamp}".encode()).hexdigest()[:8]
        return f"{symbol}_{knowledge_type}_{hash_value}"

    def get_extractor_type(self) -> str:
        """获取提取器类型"""
        return "VolatilityExtractor"


class KnowledgeExtractionEngine:
    """知识提取引擎

    管理多个知识提取器，从数据中提取知识。
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化知识提取引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.extractors: List[KnowledgeExtractor] = []

        # 知识缓存（用于去重）
        self.knowledge_cache: Dict[str, ExtractedKnowledge] = {}

        # 性能指标
        self.metrics = ExtractionMetrics()

        # 初始化提取器
        self._initialize_extractors()

        logger.info("知识提取引擎初始化完成")

    def _initialize_extractors(self) -> None:
        """初始化知识提取器"""
        # 添加价格模式提取器
        self.extractors.append(PricePatternExtractor(self.config))

        # 添加波动率提取器
        self.extractors.append(VolatilityExtractor(self.config))

        logger.info(f"初始化 {len(self.extractors)} 个知识提取器")

    async def extract_from_data(self, data: Dict[str, Any]) -> List[ExtractedKnowledge]:
        """从数据中提取知识

        Args:
            data: 输入数据

        Returns:
            提取的知识列表
        """
        self.metrics.total_processed += 1
        all_knowledges = []

        try:
            # 使用所有提取器提取知识
            for extractor in self.extractors:
                knowledges = await extractor.extract(data)
                all_knowledges.extend(knowledges)

            # 去重
            unique_knowledges = self._deduplicate_knowledges(all_knowledges)
            self.metrics.duplicates_removed += len(all_knowledges) - len(unique_knowledges)

            # 评估知识质量
            for knowledge in unique_knowledges:
                confidence_level = knowledge.get_confidence_level()

                if confidence_level == Confidence.HIGH:
                    self.metrics.high_confidence_count += 1
                elif confidence_level == Confidence.MEDIUM:
                    self.metrics.medium_confidence_count += 1
                else:
                    self.metrics.low_confidence_count += 1

            # 更新指标
            self.metrics.total_extracted += len(unique_knowledges)
            if unique_knowledges:
                avg_conf = statistics.mean([k.confidence for k in unique_knowledges])
                self.metrics.avg_confidence = (
                    self.metrics.avg_confidence * (self.metrics.total_extracted - len(unique_knowledges)) +
                    avg_conf * len(unique_knowledges)
                ) / self.metrics.total_extracted

            # 缓存知识
            for knowledge in unique_knowledges:
                self.knowledge_cache[knowledge.knowledge_id] = knowledge

            return unique_knowledges

        except Exception as e:
            logger.error(f"知识提取失败: {e}")
            return []

    def _deduplicate_knowledges(self, knowledges: List[ExtractedKnowledge]) -> List[ExtractedKnowledge]:
        """去重知识

        Args:
            knowledges: 知识列表

        Returns:
            去重后的知识列表
        """
        seen = set()
        unique_knowledges = []

        for knowledge in knowledges:
            # 使用内容哈希去重
            content_hash = hashlib.md5(knowledge.content.encode()).hexdigest()

            if content_hash not in seen:
                seen.add(content_hash)
                unique_knowledges.append(knowledge)

        return unique_knowledges

    def get_metrics(self) -> ExtractionMetrics:
        """获取提取指标

        Returns:
            提取指标
        """
        return self.metrics

    def reset_metrics(self) -> None:
        """重置提取指标"""
        self.metrics = ExtractionMetrics()


async def main():
    """主函数 - 测试知识提取引擎"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 创建知识提取引擎
    engine = KnowledgeExtractionEngine()

    # 测试数据 - 提供足够的历史数据
    test_data = []

    # 为BTC生成15个数据点
    for i in range(15):
        price = 50000.0 + i * 100  # 上升趋势
        test_data.append({"symbol": "BTC/USDT", "price": price, "timestamp": time.time()})

    # 为ETH生成15个数据点
    for i in range(15):
        price = 3000.0 + (i % 5) * 10  # 震荡
        test_data.append({"symbol": "ETH/USDT", "price": price, "timestamp": time.time()})

    # 提取知识
    print("\n=== 测试知识提取 ===")
    all_knowledges = []

    for data in test_data:
        knowledges = await engine.extract_from_data(data)
        all_knowledges.extend(knowledges)

        for knowledge in knowledges:
            print(f"提取知识: {knowledge.content} (置信度: {knowledge.confidence:.2f})")

    # 显示提取指标
    metrics = engine.get_metrics()
    print(f"\n=== 提取指标 ===")
    print(f"处理数据数: {metrics.total_processed}")
    print(f"提取知识数: {metrics.total_extracted}")
    print(f"去重数量: {metrics.duplicates_removed}")
    print(f"提取率: {metrics.extraction_rate()*100:.2f}%")
    print(f"平均置信度: {metrics.avg_confidence_score()*100:.2f}%")
    print(f"高置信度: {metrics.high_confidence_count}")
    print(f"中置信度: {metrics.medium_confidence_count}")
    print(f"低置信度: {metrics.low_confidence_count}")


# 导入time模块
import time

if __name__ == "__main__":
    asyncio.run(main())
