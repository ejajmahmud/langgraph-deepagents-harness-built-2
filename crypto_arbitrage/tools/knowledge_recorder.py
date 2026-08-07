"""知识记录器 (KnowledgeRecorder) - V4.0

自动记录系统知识到 Memo0 存储系统。

核心功能：
1. 交易知识记录
2. 风险预测记录
3. 预警历史记录
4. 系统性能记录
5. 策略效果记录
6. 智能知识分类和标签

集成范围：
- 套利引擎
- 风险管理器
- 预测性健康监控器
- 决策系统
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知识类型"""
    TRADE = "trade"  # 交易记录
    RISK_PREDICTION = "risk_prediction"  # 风险预测
    WARNING = "warning"  # 预警记录
    PERFORMANCE = "performance"  # 性能记录
    STRATEGY = "strategy"  # 策略记录
    DECISION = "decision"  # 决策记录
    LEARNING = "learning"  # 学习记录


class KnowledgeCategory(Enum):
    """知识分类"""
    MARKET = "market"  # 市场
    RISK = "risk"  # 风险
    EXECUTION = "execution"  # 执行
    PREDICTION = "prediction"  # 预测
    OPTIMIZATION = "optimization"  # 优化


@dataclass
class KnowledgeRecord:
    """知识记录

    Attributes:
        knowledge_type: 知识类型
        content: 知识内容
        metadata: 元数据
        categories: 分类标签
        confidence: 置信度 (0-1)
        timestamp: 时间戳
        source: 来源
    """
    knowledge_type: KnowledgeType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    categories: List[str] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    source: str = "system"


class KnowledgeRecorder:
    """知识记录器

    自动记录系统知识到 Memo0 存储系统。
    """

    def __init__(self, mem0_storage=None, config: Optional[Dict[str, Any]] = None):
        """初始化知识记录器

        Args:
            mem0_storage: Memo0 存储实例
            config: 配置字典
        """
        self.mem0 = mem0_storage
        self.config = config or {}

        # 配置参数
        self.auto_record = self.config.get('auto_record', True)
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.batch_size = self.config.get('batch_size', 10)
        self.batch_records: List[KnowledgeRecord] = []

        # 统计数据
        self.total_records = 0
        self.by_type: Dict[KnowledgeType, int] = {}

        logger.info("✅ 知识记录器初始化完成")

    async def record_trade(
        self,
        trade_data: Dict[str, Any]
    ) -> bool:
        """记录交易知识

        Args:
            trade_data: 交易数据字典，包含：
                - symbol: 交易对
                - strategy: 策略名称
                - profit: 利润
                - risk_score: 风险分数
                - execution_time: 执行时间
                - status: 状态
                - error: 错误信息（如果有）

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.TRADE,
                content=f"完成{trade_data['symbol']}交易，策略：{trade_data['strategy']}，利润：{trade_data['profit']:.2f}",
                metadata={
                    "symbol": trade_data["symbol"],
                    "strategy": trade_data["strategy"],
                    "profit": trade_data["profit"],
                    "risk_score": trade_data.get("risk_score", 0),
                    "execution_time": trade_data.get("execution_time", 0),
                    "status": trade_data.get("status", "unknown"),
                    "error": trade_data.get("error"),
                },
                categories=["trade", "strategy", "market"],
                confidence=1.0 if trade_data.get("status") == "completed" else 0.5,
                source="trading_engine"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录交易知识失败: {e}")
            return False

    async def record_risk_prediction(
        self,
        prediction_data: Dict[str, Any]
    ) -> bool:
        """记录风险预测知识

        Args:
            prediction_data: 风险预测数据，包含：
                - risk_level: 风险级别
                - risk_score: 风险分数
                - prediction_confidence: 预测置信度
                - recommendations: 推荐措施
                - metrics: 指标数据

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.RISK_PREDICTION,
                content=f"风险预测：{prediction_data['risk_level']}，分数：{prediction_data['risk_score']:.2f}，置信度：{prediction_data['prediction_confidence']:.2f}",
                metadata={
                    "risk_level": prediction_data["risk_level"],
                    "risk_score": prediction_data["risk_score"],
                    "prediction_confidence": prediction_data["prediction_confidence"],
                    "recommendations": prediction_data.get("recommendations", []),
                    "metrics": prediction_data.get("metrics", {}),
                },
                categories=["risk", "prediction"],
                confidence=prediction_data.get("prediction_confidence", 0.5),
                source="risk_manager"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录风险预测知识失败: {e}")
            return False

    async def record_warning(
        self,
        warning_data: Dict[str, Any]
    ) -> bool:
        """记录预警知识

        Args:
            warning_data: 预警数据，包含：
                - warning_type: 预警类型
                - severity: 严重程度
                - message: 预警消息
                - confidence: 置信度
                - recommended_action: 推荐行动

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.WARNING,
                content=f"预警：{warning_data['warning_type']}，严重程度：{warning_data['severity']}，{warning_data['message']}",
                metadata={
                    "warning_type": warning_data["warning_type"],
                    "severity": warning_data["severity"],
                    "message": warning_data["message"],
                    "recommended_action": warning_data.get("recommended_action"),
                },
                categories=["risk", "warning", "prediction"],
                confidence=warning_data.get("confidence", 0.7),
                source="monitoring_system"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录预警知识失败: {e}")
            return False

    async def record_performance(
        self,
        performance_data: Dict[str, Any]
    ) -> bool:
        """记录系统性能知识

        Args:
            performance_data: 性能数据，包含：
                - health_score: 健康分数
                - metrics: 指标字典
                - trends: 趋势信息
                - anomalies: 异常列表

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.PERFORMANCE,
                content=f"系统性能：健康分数 {performance_data['health_score']:.2f}，异常数量：{len(performance_data.get('anomalies', []))}",
                metadata={
                    "health_score": performance_data["health_score"],
                    "metrics": performance_data.get("metrics", {}),
                    "trends": performance_data.get("trends", []),
                    "anomalies": performance_data.get("anomalies", []),
                },
                categories=["performance", "system", "optimization"],
                confidence=0.9,
                source="health_monitor"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录性能知识失败: {e}")
            return False

    async def record_strategy(
        self,
        strategy_data: Dict[str, Any]
    ) -> bool:
        """记录策略知识

        Args:
            strategy_data: 策略数据，包含：
                - strategy_name: 策略名称
                - performance: 性能指标
                - parameters: 参数配置
                - effectiveness: 有效性评估

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            effectiveness = strategy_data.get("effectiveness", {})
            win_rate = effectiveness.get("win_rate", 0)

            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.STRATEGY,
                content=f"策略 {strategy_data['strategy_name']}：胜率 {win_rate:.2%}，盈亏比 {effectiveness.get('profit_loss_ratio', 0):.2f}",
                metadata={
                    "strategy_name": strategy_data["strategy_name"],
                    "performance": strategy_data.get("performance", {}),
                    "parameters": strategy_data.get("parameters", {}),
                    "effectiveness": effectiveness,
                },
                categories=["strategy", "execution", "optimization"],
                confidence=effectiveness.get("confidence", 0.7),
                source="strategy_manager"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录策略知识失败: {e}")
            return False

    async def record_decision(
        self,
        decision_data: Dict[str, Any]
    ) -> bool:
        """记录决策知识

        Args:
            decision_data: 决策数据，包含：
                - decision_type: 决策类型
                - context: 决策上下文
                - action: 采取的行动
                - outcome: 结果
                - reasoning: 推理过程

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.DECISION,
                content=f"决策：{decision_data['decision_type']}，行动：{decision_data['action']}，结果：{decision_data.get('outcome', 'unknown')}",
                metadata={
                    "decision_type": decision_data["decision_type"],
                    "context": decision_data.get("context", {}),
                    "action": decision_data["action"],
                    "outcome": decision_data.get("outcome"),
                    "reasoning": decision_data.get("reasoning"),
                },
                categories=["decision", "execution", "learning"],
                confidence=decision_data.get("confidence", 0.7),
                source="decision_engine"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录决策知识失败: {e}")
            return False

    async def record_learning(
        self,
        learning_data: Dict[str, Any]
    ) -> bool:
        """记录学习知识

        Args:
            learning_data: 学习数据，包含：
                - insight: 洞察
                - pattern: 模式
                - improvement: 改进建议
                - validation: 验证结果

        Returns:
            是否记录成功
        """
        if not self.auto_record:
            return False

        try:
            # 创建知识记录
            record = KnowledgeRecord(
                knowledge_type=KnowledgeType.LEARNING,
                content=f"学习洞察：{learning_data.get('insight', '')}",
                metadata={
                    "insight": learning_data.get("insight"),
                    "pattern": learning_data.get("pattern"),
                    "improvement": learning_data.get("improvement"),
                    "validation": learning_data.get("validation"),
                },
                categories=["learning", "optimization", "prediction"],
                confidence=learning_data.get("confidence", 0.8),
                source="learning_system"
            )

            return await self._add_record(record)

        except Exception as e:
            logger.error(f"记录学习知识失败: {e}")
            return False

    async def _add_record(self, record: KnowledgeRecord) -> bool:
        """添加知识记录

        Args:
            record: 知识记录

        Returns:
            是否添加成功
        """
        # 检查置信度
        if record.confidence < self.min_confidence:
            logger.debug(f"知识置信度不足，跳过记录: {record.confidence} < {self.min_confidence}")
            return False

        # 添加到批处理队列
        self.batch_records.append(record)

        # 如果达到批处理大小，则执行批量添加
        if len(self.batch_records) >= self.batch_size:
            await self._flush_batch()

        # 更新统计
        self.total_records += 1
        self.by_type[record.knowledge_type] = self.by_type.get(record.knowledge_type, 0) + 1

        return True

    async def _flush_batch(self) -> bool:
        """刷新批处理队列

        Returns:
            是否刷新成功
        """
        if not self.batch_records:
            return True

        try:
            if self.mem0:
                # 批量添加到 Memo0
                for record in self.batch_records:
                    await self._add_to_mem0(record)

                logger.info(f"批量添加 {len(self.batch_records)} 条知识到 Memo0")
            else:
                # 降级：添加到本地存储
                await self._add_to_local_storage(self.batch_records)
                logger.info(f"批量添加 {len(self.batch_records)} 条知识到本地存储")

            # 清空批处理队列
            self.batch_records.clear()
            return True

        except Exception as e:
            logger.error(f"刷新批处理失败: {e}")
            return False

    async def _add_to_mem0(self, record: KnowledgeRecord) -> bool:
        """添加到 Memo0

        Args:
            record: 知识记录

        Returns:
            是否添加成功
        """
        try:
            # 构建知识对象
            knowledge = {
                "content": record.content,
                "metadata": {
                    **record.metadata,
                    "knowledge_type": record.knowledge_type.value,
                    "categories": record.categories,
                    "confidence": record.confidence,
                    "timestamp": record.timestamp,
                    "source": record.source,
                }
            }

            # 添加到 Memo0
            result = await self.mem0.add([knowledge])

            return result is not None

        except Exception as e:
            logger.error(f"添加到 Memo0 失败: {e}")
            return False

    async def _add_to_local_storage(self, records: List[KnowledgeRecord]) -> bool:
        """添加到本地存储（降级模式）

        Args:
            records: 知识记录列表

        Returns:
            是否添加成功
        """
        try:
            import sqlite3
            from pathlib import Path

            # 创建数据库
            db_path = Path.cwd() / "storage" / "knowledge_base.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    categories TEXT,
                    confidence REAL,
                    timestamp REAL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 批量插入
            for record in records:
                cursor.execute("""
                    INSERT INTO knowledge_records (
                        knowledge_type, content, metadata, categories,
                        confidence, timestamp, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.knowledge_type.value,
                    record.content,
                    json.dumps(record.metadata),
                    json.dumps(record.categories),
                    record.confidence,
                    record.timestamp,
                    record.source
                ))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"添加到本地存储失败: {e}")
            return False

    async def flush(self) -> bool:
        """刷新所有待处理的记录

        Returns:
            是否刷新成功
        """
        return await self._flush_batch()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_records": self.total_records,
            "pending_records": len(self.batch_records),
            "by_type": {k.value: v for k, v in self.by_type.items()},
        }


# 全局单例
_knowledge_recorder: Optional[KnowledgeRecorder] = None


def get_knowledge_recorder(mem0_storage=None, config: Optional[Dict[str, Any]] = None) -> KnowledgeRecorder:
    """获取知识记录器实例

    Args:
        mem0_storage: Memo0 存储实例
        config: 配置字典

    Returns:
        KnowledgeRecorder 实例
    """
    global _knowledge_recorder

    if _knowledge_recorder is None:
        _knowledge_recorder = KnowledgeRecorder(mem0_storage, config)

    return _knowledge_recorder
