"""
自动知识积累系统 V2.5

自动将交易决策、市场模式、策略表现等信息记录到Memo0，
实现无需手动干预的持续学习系统。

核心功能：
1. 交易决策自动记录
2. 交易结果自动学习
3. 市场模式自动记忆
4. 策略表现自动跟踪
"""

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 线程安全锁（V5.3添加）
_auto_accumulator_lock = threading.Lock()


class AutoKnowledgeAccumulator:
    """自动知识积累器

    智能记录交易系统的所有关键决策和结果，
    构建持续学习的知识库。
    """

    def __init__(self, storage):
        """初始化自动知识积累器

        Args:
            storage: 统一存储实例（Memo0或SQLite）
        """
        self.storage = storage
        self._enabled = True
        self._batch_queue: List[Dict] = []
        self._batch_size = 10
        self._batch_timeout = 60  # 秒

        logger.info("自动知识积累器初始化成功")

    def enable(self):
        """启用自动知识积累"""
        self._enabled = True
        logger.info("自动知识积累已启用")

    def disable(self):
        """禁用自动知识积累"""
        self._enabled = False
        logger.info("自动知识积累已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled

    # ---------------------- 交易决策记录 ----------------------

    def record_decision(
        self,
        decision_type: str,
        market_conditions: Dict[str, Any],
        strategy: str,
        reasoning: str,
        parameters: Dict[str, Any],
        outcome: Optional[str] = None
    ) -> bool:
        """记录交易决策

        Args:
            decision_type: 决策类型 (trade_execution, trade_rejection, strategy_selection)
            market_conditions: 市场条件
            {
                "volatility": float,
                "trend": str,  # rising, falling, stable
                "liquidity": str,  # high, normal, low
                "funding_rate": float,
                "spread": float
            }
            strategy: 策略名称
            reasoning: 决策理由
            parameters: 决策参数
            outcome: 决策结果 (如果已执行)

        Returns:
            是否记录成功
        """
        if not self._enabled:
            return False

        timestamp = datetime.now().isoformat()

        knowledge = {
            "type": "decision",
            "decision_type": decision_type,
            "timestamp": timestamp,
            "market_conditions": market_conditions,
            "strategy": strategy,
            "reasoning": reasoning,
            "parameters": parameters,
            "outcome": outcome
        }

        # 格式化为可读文本
        content = self._format_decision_knowledge(knowledge)

        success = self.storage.add_knowledge(
            category="decision",
            content=content,
            metadata=knowledge
        )

        if success:
            logger.info(f"决策记录成功: {decision_type} - {strategy}")
        else:
            logger.warning(f"决策记录失败: {decision_type}")

        return success

    def _format_decision_knowledge(self, knowledge: Dict) -> str:
        """格式化决策知识为可读文本"""
        m = knowledge["market_conditions"]
        p = knowledge["parameters"]

        text = f"""
[决策记录] {knowledge['timestamp']}

决策类型: {knowledge['decision_type']}
策略: {knowledge['strategy']}
决策理由: {knowledge['reasoning']}

市场条件:
- 波动率: {m.get('volatility', 'N/A')}
- 趋势: {m.get('trend', 'N/A')}
- 流动性: {m.get('liquidity', 'N/A')}
- 资金费率: {m.get('funding_rate', 'N/A')}
- 价差: {m.get('spread', 'N/A')}

决策参数:
{json.dumps(p, indent=2, ensure_ascii=False)}

结果: {knowledge.get('outcome', '待定')}
""".strip()

        return text

    # ---------------------- 交易结果学习 ----------------------

    def record_trade_result(
        self,
        trade_id: str,
        strategy: str,
        expected_profit: float,
        actual_profit: float,
        execution_time: float,
        error: Optional[str] = None,
        lessons: Optional[str] = None
    ) -> bool:
        """记录交易结果

        Args:
            trade_id: 交易ID
            strategy: 策略名称
            expected_profit: 预期利润
            actual_profit: 实际利润
            execution_time: 执行时间（秒）
            error: 错误信息（如果有）
            lessons: 经验教训（如果有）

        Returns:
            是否记录成功
        """
        if not self._enabled:
            return False

        timestamp = datetime.now().isoformat()
        profit_accuracy = abs(actual_profit / expected_profit) if expected_profit != 0 else 0

        knowledge = {
            "type": "trade_result",
            "trade_id": trade_id,
            "timestamp": timestamp,
            "strategy": strategy,
            "expected_profit": expected_profit,
            "actual_profit": actual_profit,
            "profit_accuracy": profit_accuracy,
            "execution_time": execution_time,
            "success": error is None,
            "error": error,
            "lessons": lessons
        }

        # 格式化为可读文本
        content = self._format_trade_result_knowledge(knowledge)

        success = self.storage.add_knowledge(
            category="trade_result",
            content=content,
            metadata=knowledge
        )

        if success:
            logger.info(f"交易结果记录成功: {trade_id} - {strategy}")
        else:
            logger.warning(f"交易结果记录失败: {trade_id}")

        return success

    def _format_trade_result_knowledge(self, knowledge: Dict) -> str:
        """格式化交易结果知识为可读文本"""
        text = f"""
[交易结果] {knowledge['timestamp']}

交易ID: {knowledge['trade_id']}
策略: {knowledge['strategy']}
结果: {'成功' if knowledge['success'] else '失败'}

收益分析:
- 预期利润: ${knowledge['expected_profit']:.2f}
- 实际利润: ${knowledge['actual_profit']:.2f}
- 准确度: {knowledge['profit_accuracy']:.1%}
- 执行时间: {knowledge['execution_time']:.2f}秒
"""

        if knowledge['error']:
            text += f"\n错误信息: {knowledge['error']}\n"

        if knowledge['lessons']:
            text += f"\n经验教训: {knowledge['lessons']}\n"

        return text.strip()

    # ---------------------- 市场模式记忆 ----------------------

    def record_market_pattern(
        self,
        pattern_type: str,
        conditions: Dict[str, Any],
        successful_strategies: List[str],
        failed_strategies: List[str],
        confidence: float,
        duration: Optional[float] = None
    ) -> bool:
        """记录市场模式

        Args:
            pattern_type: 模式类型 (bullish_trend, bearish_trend, high_volatility, liquidity_crisis)
            conditions: 市场条件详情
            successful_strategies: 成功的策略列表
            failed_strategies: 失败的策略列表
            confidence: 置信度 (0.0-1.0)
            duration: 模式持续时间（小时）

        Returns:
            是否记录成功
        """
        if not self._enabled:
            return False

        timestamp = datetime.now().isoformat()

        knowledge = {
            "type": "market_pattern",
            "pattern_type": pattern_type,
            "timestamp": timestamp,
            "conditions": conditions,
            "successful_strategies": successful_strategies,
            "failed_strategies": failed_strategies,
            "strategy_count": len(successful_strategies) + len(failed_strategies),
            "success_rate": len(successful_strategies) / (len(successful_strategies) + len(failed_strategies)) if len(successful_strategies) + len(failed_strategies) > 0 else 0,
            "confidence": confidence,
            "duration": duration
        }

        # 格式化为可读文本
        content = self._format_market_pattern_knowledge(knowledge)

        success = self.storage.add_knowledge(
            category="market_pattern",
            content=content,
            metadata=knowledge
        )

        if success:
            logger.info(f"市场模式记录成功: {pattern_type}")
        else:
            logger.warning(f"市场模式记录失败: {pattern_type}")

        return success

    def _format_market_pattern_knowledge(self, knowledge: Dict) -> str:
        """格式化市场模式知识为可读文本"""
        s_count = len(knowledge["successful_strategies"])
        f_count = len(knowledge["failed_strategies"])
        total = s_count + f_count

        text = f"""
[市场模式] {knowledge['timestamp']}

模式类型: {knowledge['pattern_type']}
置信度: {knowledge['confidence']:.1%}
持续时间: {knowledge['duration']}小时

市场条件:
{json.dumps(knowledge['conditions'], indent=2, ensure_ascii=False)}

策略表现 ({total}次尝试):
- 成功策略 ({s_count}次):
{chr(10).join(f"  * {s}" for s in knowledge['successful_strategies'])}

- 失败策略 ({f_count}次):
{chr(10).join(f"  * {f}" for f in knowledge['failed_strategies'])}

成功率: {knowledge['success_rate']:.1%}
""".strip()

        return text

    # ---------------------- 策略表现跟踪 ----------------------

    def record_strategy_performance(
        self,
        strategy: str,
        period: str,  # hourly, daily, weekly, monthly
        metrics: Dict[str, Any],
        market_conditions: Dict[str, Any],
        notes: Optional[str] = None
    ) -> bool:
        """记录策略表现

        Args:
            strategy: 策略名称
            period: 统计周期
            metrics: 性能指标
            {
                "total_trades": int,
                "win_rate": float,
                "total_profit": float,
                "avg_profit_per_trade": float,
                "max_drawdown": float,
                "sharpe_ratio": float
            }
            market_conditions: 市场条件
            notes: 备注信息

        Returns:
            是否记录成功
        """
        if not self._enabled:
            return False

        timestamp = datetime.now().isoformat()

        knowledge = {
            "type": "strategy_performance",
            "strategy": strategy,
            "period": period,
            "timestamp": timestamp,
            "metrics": metrics,
            "market_conditions": market_conditions,
            "notes": notes
        }

        # 格式化为可读文本
        content = self._format_strategy_performance_knowledge(knowledge)

        success = self.storage.add_knowledge(
            category="strategy_performance",
            content=content,
            metadata=knowledge
        )

        if success:
            logger.info(f"策略表现记录成功: {strategy} - {period}")
        else:
            logger.warning(f"策略表现记录失败: {strategy} - {period}")

        return success

    def _format_strategy_performance_knowledge(self, knowledge: Dict) -> str:
        """格式化策略表现知识为可读文本"""
        m = knowledge["metrics"]

        text = f"""
[策略表现] {knowledge['timestamp']}

策略: {knowledge['strategy']}
周期: {knowledge['period']}

核心指标:
- 总交易数: {m.get('total_trades', 0)}
- 胜率: {m.get('win_rate', 0):.1%}
- 总利润: ${m.get('total_profit', 0):.2f}
- 平均每笔利润: ${m.get('avg_profit_per_trade', 0):.2f}
- 最大回撤: {m.get('max_drawdown', 0):.2f}%
- 夏普比率: {m.get('sharpe_ratio', 0):.2f}

市场条件:
{json.dumps(knowledge['market_conditions'], indent=2, ensure_ascii=False)}
"""

        if knowledge.get("notes"):
            text += f"\n备注: {knowledge['notes']}\n"

        return text.strip()

    # ---------------------- 风险事件记录 ----------------------

    def record_risk_event(
        self,
        event_type: str,
        severity: str,  # low, medium, high, critical
        conditions: Dict[str, Any],
        affected_strategies: List[str],
        impact: Dict[str, Any],
        mitigation: Optional[str] = None
    ) -> bool:
        """记录风险事件

        Args:
            event_type: 事件类型 (market_crash, liquidity_crisis, rate_limit, large_loss)
            severity: 严重程度
            conditions: 触发条件
            affected_strategies: 受影响的策略列表
            impact: 事件影响
            {
                "loss_amount": float,
                "trades_cancelled": int,
                "duration": float  # 小时
            }
            mitigation: 缓解措施

        Returns:
            是否记录成功
        """
        if not self._enabled:
            return False

        timestamp = datetime.now().isoformat()

        knowledge = {
            "type": "risk_event",
            "event_type": event_type,
            "severity": severity,
            "timestamp": timestamp,
            "conditions": conditions,
            "affected_strategies": affected_strategies,
            "impact": impact,
            "mitigation": mitigation
        }

        # 格式化为可读文本
        content = self._format_risk_event_knowledge(knowledge)

        success = self.storage.add_knowledge(
            category="risk_event",
            content=content,
            metadata=knowledge
        )

        if success:
            logger.info(f"风险事件记录成功: {event_type} - {severity}")
        else:
            logger.warning(f"风险事件记录失败: {event_type}")

        return success

    def _format_risk_event_knowledge(self, knowledge: Dict) -> str:
        """格式化风险事件知识为可读文本"""
        i = knowledge["impact"]

        text = f"""
[风险事件] {knowledge['timestamp']}

事件类型: {knowledge['event_type']}
严重程度: {knowledge['severity'].upper()}

触发条件:
{json.dumps(knowledge['conditions'], indent=2, ensure_ascii=False)}

受影响策略 ({len(knowledge['affected_strategies'])}):
{chr(10).join(f"  * {s}" for s in knowledge['affected_strategies'])}

事件影响:
- 损失金额: ${i.get('loss_amount', 0):.2f}
- 取消交易: {i.get('trades_cancelled', 0)}笔
- 持续时间: {i.get('duration', 0):.2f}小时
"""

        if knowledge.get("mitigation"):
            text += f"\n缓解措施: {knowledge['mitigation']}\n"

        return text.strip()

    # ---------------------- 批量操作 ----------------------

    def batch_record(self, knowledge_list: List[Dict]) -> bool:
        """批量记录知识

        Args:
            knowledge_list: 知识列表，每个知识包含 category, content, metadata

        Returns:
            是否全部成功
        """
        if not self._enabled or not knowledge_list:
            return False

        success_count = 0
        for knowledge in knowledge_list:
            success = self.storage.add_knowledge(
                category=knowledge.get("category"),
                content=knowledge.get("content"),
                metadata=knowledge.get("metadata")
            )
            if success:
                success_count += 1

        logger.info(f"批量记录完成: {success_count}/{len(knowledge_list)} 成功")
        return success_count == len(knowledge_list)

    # ---------------------- 查询接口 ----------------------

    def query_similar_decisions(
        self,
        market_conditions: Dict[str, Any],
        strategy: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """查询相似的历史决策

        Args:
            market_conditions: 当前市场条件
            strategy: 策略名称（可选）
            top_k: 返回数量

        Returns:
            相似决策列表
        """
        query_parts = [
            f"波动率 {market_conditions.get('volatility', 'unknown')}",
            f"趋势 {market_conditions.get('trend', 'unknown')}",
            f"流动性 {market_conditions.get('liquidity', 'unknown')}"
        ]

        if strategy:
            query_parts.append(f"策略 {strategy}")

        query = " ".join(query_parts)

        results = self.storage.search_knowledge(
            query=query,
            category="decision",
            top_k=top_k
        )

        return results

    def query_strategy_performance(
        self,
        strategy: str,
        period: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """查询策略历史表现

        Args:
            strategy: 策略名称
            period: 统计周期（可选）
            top_k: 返回数量

        Returns:
            表现记录列表
        """
        query = f"策略 {strategy} 表现"

        if period:
            query += f" {period}"

        results = self.storage.search_knowledge(
            query=query,
            category="strategy_performance",
            top_k=top_k
        )

        return results

    def query_risk_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """查询历史风险事件

        Args:
            event_type: 事件类型（可选）
            severity: 严重程度（可选）
            top_k: 返回数量

        Returns:
            风险事件列表
        """
        query_parts = ["风险事件"]

        if event_type:
            query_parts.append(event_type)

        if severity:
            query_parts.append(severity)

        query = " ".join(query_parts)

        results = self.storage.search_knowledge(
            query=query,
            category="risk_event",
            top_k=top_k
        )

        return results

    # ---------------------- 统计分析 ----------------------

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息

        Returns:
            统计信息
        """
        all_knowledge = self.storage.get_all_knowledge()

        stats = {
            "total": len(all_knowledge),
            "by_category": {},
            "by_type": {},
            "recent_count": 0
        }

        # 分类统计
        for item in all_knowledge:
            category = item.get("category", "unknown")
            metadata = item.get("metadata", {})

            # 按类别统计
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1

            # 按类型统计
            type_key = metadata.get("type", "unknown")
            if type_key not in stats["by_type"]:
                stats["by_type"][type_key] = 0
            stats["by_type"][type_key] += 1

        # 最近24小时统计
        recent_threshold = datetime.now().timestamp() - 24 * 3600
        for item in all_knowledge:
            timestamp_str = item.get("timestamp") or item.get("metadata", {}).get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if timestamp.timestamp() >= recent_threshold:
                        stats["recent_count"] += 1
                except:
                    pass

        return stats


# ---------------------- 便捷函数 ----------------------

_auto_accumulator: Optional[AutoKnowledgeAccumulator] = None


def get_auto_accumulator() -> Optional[AutoKnowledgeAccumulator]:
    """获取自动知识积累器实例（全局单例）

    Returns:
        AutoKnowledgeAccumulator 实例，如果未初始化则返回 None
    """
    return _auto_accumulator


def initialize_auto_accumulator(storage) -> AutoKnowledgeAccumulator:
    """初始化自动知识积累器（V5.3线程安全版）

    Args:
        storage: 统一存储实例

    Returns:
        AutoKnowledgeAccumulator 实例
    """
    global _auto_accumulator

    # 双重检查锁定模式（线程安全）
    if _auto_accumulator is None:
        with _auto_accumulator_lock:
            # 再次检查，防止其他线程已经初始化
            if _auto_accumulator is None:
                _auto_accumulator = AutoKnowledgeAccumulator(storage)
                logger.debug("自动知识积累器初始化完成（线程安全）")

    return _auto_accumulator
