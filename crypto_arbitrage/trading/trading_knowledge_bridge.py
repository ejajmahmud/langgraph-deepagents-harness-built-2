"""交易知识双向桥接器 V16.6

连接交易管道与Memo0知识存储，实现双向知识流：
1. 写方向 — 交易结果/风控事件/策略性能 → 知识库
2. 读方向 — 知识库 → 市场上下文/历史模式/策略建议 → 管道决策

核心能力：
1. KnowledgeContextProvider — 从知识库提取市场上下文，辅助交易决策
2. TradingResultRecorder — 结构化记录交易结果到知识库
3. StrategyPerformanceTracker — 策略性能追踪与趋势分析
4. RiskEventLogger — 风控事件日志（熔断/拒绝/减仓）

架构位置:
    ArbitragePipeline V16.6
           ↕ 读写
    TradingKnowledgeBridge V16.6
           ↕ 读写
    Memo0/SQLite Knowledge Storage

创建时间：2026-05-05
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KnowledgeCategory(Enum):
    """知识类别"""
    TRADE_RESULT = "trade_result"
    RISK_EVENT = "risk_event"
    STRATEGY_PERF = "strategy_perf"
    MARKET_CONTEXT = "market_context"
    PIPELINE_STATE = "pipeline_state"
    SIGNAL_FEEDBACK = "signal_feedback"


@dataclass
class MarketContext:
    """市场上下文 — 从知识库提取的决策辅助信息"""
    recent_win_rate: float = 0.0            # 近期胜率
    recent_avg_pnl_pct: float = 0.0         # 近期平均盈亏%
    best_strategy: str = ""                  # 最佳策略
    worst_strategy: str = ""                 # 最差策略
    recent_risk_events: int = 0              # 近期风控事件数
    circuit_breaker_count: int = 0           # 熔断触发次数
    symbol_performance: Dict[str, float] = field(default_factory=dict)  # {symbol: win_rate}
    strategy_performance: Dict[str, float] = field(default_factory=dict)  # {strategy: avg_pnl}
    time_of_day_performance: Dict[str, float] = field(default_factory=dict)  # {hour_range: win_rate}
    last_updated: float = 0.0
    confidence: float = 0.0                  # 上下文置信度（基于数据量）
    learned_position_mult: float = 1.0       # V27.0: 学习到的仓位乘数
    learned_stop_pct: float = 0.02           # V27.0: 学习到的止损百分比


@dataclass
class StrategyInsight:
    """策略洞察"""
    strategy_name: str
    total_trades: int
    win_count: int
    loss_count: int
    win_rate: float
    avg_pnl_pct: float
    best_symbol: str
    worst_symbol: str
    trend: str  # "improving" / "declining" / "stable"
    recommendation: str  # "increase" / "decrease" / "maintain"


class TradingKnowledgeBridge:
    """交易知识双向桥接器 V16.6

    提供交易管道与知识库之间的双向数据流：
    - 管道 → 知识库: 交易结果、风控事件、性能指标
    - 知识库 → 管道: 市场上下文、策略建议、历史模式
    """

    def __init__(self, knowledge_storage=None, config: Optional[Dict[str, Any]] = None):
        """初始化知识桥接器

        Args:
            knowledge_storage: Memo0/Mock知识存储实例
            config: 配置字典
        """
        self._knowledge = knowledge_storage
        self.config = config or {}

        # 缓存
        self._context_cache: Optional[MarketContext] = None
        self._context_cache_ttl = self.config.get("context_cache_ttl_sec", 60.0)
        self._context_cache_time = 0.0

        # 性能追踪缓冲区（批量写入）
        self._perf_buffer: List[Dict[str, Any]] = []
        self._perf_buffer_size = self.config.get("perf_buffer_size", 10)

        # 统计
        self.total_reads = 0
        self.total_writes = 0
        self.total_cache_hits = 0

        logger.info("交易知识桥接器 V16.6 初始化完成")

    def _get_knowledge(self):
        """延迟获取知识存储"""
        if self._knowledge is not None:
            return self._knowledge
        try:
            from storage.mem0_mock_storage import create_mock_mem0_storage
            storage = create_mock_mem0_storage({
                "user_id": "crypto-arbitrage-user",
                "agent_id": "knowledge-bridge-v16-6"
            })
            self._knowledge = storage
            return storage
        except Exception as e:
            logger.error(f"获取知识存储失败: {e}")
            return None

    # ==================== 读方向: 知识库 → 管道 ====================

    def get_market_context(self, force_refresh: bool = False) -> MarketContext:
        """获取市场上下文（从知识库提取决策辅助信息）

        分析知识库中的历史数据，生成市场上下文供管道决策参考。

        Args:
            force_refresh: 是否强制刷新（忽略缓存）

        Returns:
            市场上下文
        """
        # 缓存检查
        now = time.time()
        if (not force_refresh and
                self._context_cache is not None and
                now - self._context_cache_time < self._context_cache_ttl):
            self.total_cache_hits += 1
            return self._context_cache

        knowledge = self._get_knowledge()
        if knowledge is None:
            return MarketContext()

        self.total_reads += 1

        try:
            # 1. 搜索近期交易结果
            trade_results = knowledge.search_knowledge(
                query="trade_result",
                category=KnowledgeCategory.TRADE_RESULT.value,
                top_k=50
            )

            # 2. 搜索近期风控事件
            risk_events = knowledge.search_knowledge(
                query="risk_event",
                category=KnowledgeCategory.RISK_EVENT.value,
                top_k=20
            )

            # 3. 搜索策略性能
            strategy_perfs = knowledge.search_knowledge(
                query="strategy_perf",
                category=KnowledgeCategory.STRATEGY_PERF.value,
                top_k=30
            )

            context = self._analyze_context(trade_results, risk_events, strategy_perfs)
            context.last_updated = now

            # 更新缓存
            self._context_cache = context
            self._context_cache_time = now

            return context

        except Exception as e:
            logger.error(f"获取市场上下文失败: {e}")
            return MarketContext()

    def get_strategy_insight(self, strategy_name: str) -> Optional[StrategyInsight]:
        """获取策略洞察

        Args:
            strategy_name: 策略名称

        Returns:
            策略洞察，数据不足时返回None
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return None

        self.total_reads += 1

        try:
            results = knowledge.search_knowledge(
                query=f"strategy_perf {strategy_name}",
                category=KnowledgeCategory.STRATEGY_PERF.value,
                top_k=20
            )

            if len(results) < 3:
                return None

            # 解析策略性能数据
            trades = []
            for r in results:
                content = r.get("content", "")
                # 尝试解析嵌入的JSON元数据
                pnl_str = self._extract_metric(content, "pnl=")
                symbol = self._extract_metric(content, "symbol=")
                if pnl_str:
                    try:
                        pnl = float(pnl_str)
                        trades.append({"pnl": pnl, "symbol": symbol or "unknown"})
                    except ValueError:
                        pass

            if not trades:
                return None

            total = len(trades)
            wins = sum(1 for t in trades if t["pnl"] > 0)
            losses = total - wins
            win_rate = wins / total if total > 0 else 0.0
            avg_pnl = sum(t["pnl"] for t in trades) / total

            # 按币种统计
            symbol_pnl = defaultdict(list)
            for t in trades:
                symbol_pnl[t["symbol"]].append(t["pnl"])

            best_symbol = max(
                symbol_pnl.items(),
                key=lambda x: sum(x[1]) / len(x[1])
            )[0] if symbol_pnl else ""

            worst_symbol = min(
                symbol_pnl.items(),
                key=lambda x: sum(x[1]) / len(x[1])
            )[0] if symbol_pnl else ""

            # 趋势判断（前半vs后半）
            mid = total // 2
            if mid > 0:
                first_half_avg = sum(t["pnl"] for t in trades[:mid]) / mid
                second_half_avg = sum(t["pnl"] for t in trades[mid:]) / (total - mid)
                if second_half_avg > first_half_avg * 1.1:
                    trend = "improving"
                elif second_half_avg < first_half_avg * 0.9:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            # 推荐动作
            if win_rate > 0.6 and trend == "improving":
                recommendation = "increase"
            elif win_rate < 0.4 or trend == "declining":
                recommendation = "decrease"
            else:
                recommendation = "maintain"

            return StrategyInsight(
                strategy_name=strategy_name,
                total_trades=total,
                win_count=wins,
                loss_count=losses,
                win_rate=win_rate,
                avg_pnl_pct=avg_pnl,
                best_symbol=best_symbol,
                worst_symbol=worst_symbol,
                trend=trend,
                recommendation=recommendation
            )

        except Exception as e:
            logger.error(f"获取策略洞察失败: {e}")
            return None

    def get_symbol_history(self, symbol: str) -> Dict[str, Any]:
        """获取币种历史交易数据

        Args:
            symbol: 交易对

        Returns:
            历史数据摘要
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return {}

        self.total_reads += 1

        try:
            results = knowledge.search_knowledge(
                query=symbol,
                category=KnowledgeCategory.TRADE_RESULT.value,
                top_k=30
            )

            if not results:
                return {"symbol": symbol, "trades_found": 0}

            trades = []
            for r in results:
                content = r.get("content", "")
                pnl_str = self._extract_metric(content, "pnl=")
                strategy = self._extract_metric(content, "strategy=")
                outcome = self._extract_metric(content, "outcome=")
                if pnl_str:
                    try:
                        trades.append({
                            "pnl": float(pnl_str),
                            "strategy": strategy,
                            "outcome": outcome
                        })
                    except ValueError:
                        pass

            if not trades:
                return {"symbol": symbol, "trades_found": len(results), "parsed": 0}

            total = len(trades)
            wins = sum(1 for t in trades if t["pnl"] > 0)
            total_pnl = sum(t["pnl"] for t in trades)

            # 按策略分组
            by_strategy = defaultdict(list)
            for t in trades:
                if t["strategy"]:
                    by_strategy[t["strategy"]].append(t["pnl"])

            return {
                "symbol": symbol,
                "trades_found": total,
                "win_rate": wins / total if total > 0 else 0.0,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / total,
                "best_strategy": max(
                    by_strategy.items(),
                    key=lambda x: sum(x[1])
                )[0] if by_strategy else "",
            }

        except Exception as e:
            logger.error(f"获取币种历史失败: {e}")
            return {}

    # ==================== 写方向: 管道 → 知识库 ====================

    def record_trade_result(
        self,
        strategy: str,
        symbol: str,
        exchange: str,
        pnl_pct: float,
        pnl_usd: float,
        outcome: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """记录交易结果到知识库

        Args:
            strategy: 策略名称
            symbol: 交易对
            exchange: 交易所
            pnl_pct: 盈亏百分比
            pnl_usd: 盈亏金额
            outcome: 结果 (profitable/loss/breakeven)
            details: 额外详情

        Returns:
            是否成功
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return False

        content = (
            f"{strategy} {symbol} @ {exchange} | "
            f"pnl={pnl_pct:.4f}% | pnl_usd={pnl_usd:.2f} | "
            f"outcome={outcome}"
        )

        metadata = {
            "strategy": strategy,
            "symbol": symbol,
            "exchange": exchange,
            "pnl_pct": pnl_pct,
            "pnl_usd": pnl_usd,
            "outcome": outcome,
            "timestamp": time.time(),
        }
        if details:
            metadata.update(details)

        try:
            # 使用add_knowledge（带类别）或add_memory
            if hasattr(knowledge, 'add_knowledge'):
                result = knowledge.add_knowledge(
                    category=KnowledgeCategory.TRADE_RESULT.value,
                    content=content,
                    metadata=metadata
                )
            else:
                full = f"[{KnowledgeCategory.TRADE_RESULT.value}] {content}"
                result = knowledge.add_memory(full)

            self.total_writes += 1

            # 添加到性能缓冲区
            self._perf_buffer.append(metadata)
            if len(self._perf_buffer) >= self._perf_buffer_size:
                self._flush_perf_buffer()

            return bool(result)

        except Exception as e:
            logger.error(f"记录交易结果失败: {e}")
            return False

    def record_risk_event(
        self,
        event_type: str,
        severity: str,
        strategy: str,
        symbol: str,
        reason: str,
        action_taken: str = ""
    ) -> bool:
        """记录风控事件到知识库

        Args:
            event_type: 事件类型 (circuit_break/reject/reduce_size)
            severity: 严重程度 (critical/high/medium/low)
            strategy: 策略名称
            symbol: 交易对
            reason: 触发原因
            action_taken: 采取的动作

        Returns:
            是否成功
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return False

        content = (
            f"{event_type} | severity={severity} | "
            f"strategy={strategy} | symbol={symbol} | "
            f"reason={reason} | action={action_taken}"
        )

        metadata = {
            "event_type": event_type,
            "severity": severity,
            "strategy": strategy,
            "symbol": symbol,
            "reason": reason,
            "action_taken": action_taken,
            "timestamp": time.time(),
        }

        try:
            if hasattr(knowledge, 'add_knowledge'):
                result = knowledge.add_knowledge(
                    category=KnowledgeCategory.RISK_EVENT.value,
                    content=content,
                    metadata=metadata
                )
            else:
                full = f"[{KnowledgeCategory.RISK_EVENT.value}] {content}"
                result = knowledge.add_memory(full)

            self.total_writes += 1
            # 风控事件立即刷新上下文缓存
            self._context_cache = None

            return bool(result)

        except Exception as e:
            logger.error(f"记录风控事件失败: {e}")
            return False

    def record_strategy_performance(
        self,
        strategy: str,
        total_trades: int,
        win_rate: float,
        avg_pnl_pct: float,
        best_symbol: str = "",
        period: str = "daily"
    ) -> bool:
        """记录策略性能到知识库

        Args:
            strategy: 策略名称
            total_trades: 总交易数
            win_rate: 胜率
            avg_pnl_pct: 平均盈亏%
            best_symbol: 最佳币种
            period: 统计周期

        Returns:
            是否成功
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return False

        content = (
            f"strategy={strategy} | trades={total_trades} | "
            f"win_rate={win_rate:.2%} | avg_pnl={avg_pnl_pct:.4f}% | "
            f"best_symbol={best_symbol} | period={period}"
        )

        metadata = {
            "strategy": strategy,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_pnl_pct": avg_pnl_pct,
            "best_symbol": best_symbol,
            "period": period,
            "timestamp": time.time(),
        }

        try:
            if hasattr(knowledge, 'add_knowledge'):
                result = knowledge.add_knowledge(
                    category=KnowledgeCategory.STRATEGY_PERF.value,
                    content=content,
                    metadata=metadata
                )
            else:
                full = f"[{KnowledgeCategory.STRATEGY_PERF.value}] {content}"
                result = knowledge.add_memory(full)

            self.total_writes += 1
            return bool(result)

        except Exception as e:
            logger.error(f"记录策略性能失败: {e}")
            return False

    def record_signal_feedback(
        self,
        signal_id: str,
        signal_type: str,
        symbol: str,
        accepted: bool,
        rejection_reason: str = "",
        pnl_if_accepted: float = 0.0
    ) -> bool:
        """记录信号反馈（用于信号过滤器学习）

        Args:
            signal_id: 信号ID
            signal_type: 信号类型
            symbol: 交易对
            accepted: 是否被接受
            rejection_reason: 拒绝原因
            pnl_if_accepted: 如果接受后的盈亏

        Returns:
            是否成功
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return False

        content = (
            f"signal={signal_id} | type={signal_type} | symbol={symbol} | "
            f"accepted={accepted} | reason={rejection_reason} | "
            f"pnl={pnl_if_accepted:.4f}%"
        )

        metadata = {
            "signal_id": signal_id,
            "signal_type": signal_type,
            "symbol": symbol,
            "accepted": accepted,
            "rejection_reason": rejection_reason,
            "pnl_if_accepted": pnl_if_accepted,
            "timestamp": time.time(),
        }

        try:
            if hasattr(knowledge, 'add_knowledge'):
                result = knowledge.add_knowledge(
                    category=KnowledgeCategory.SIGNAL_FEEDBACK.value,
                    content=content,
                    metadata=metadata
                )
            else:
                full = f"[{KnowledgeCategory.SIGNAL_FEEDBACK.value}] {content}"
                result = knowledge.add_memory(full)

            self.total_writes += 1
            return bool(result)

        except Exception as e:
            logger.error(f"记录信号反馈失败: {e}")
            return False

    # ==================== 管道状态持久化 ====================

    def save_pipeline_state(self, state: Dict[str, Any]) -> bool:
        """保存管道状态到知识库

        Args:
            state: 管道状态字典

        Returns:
            是否成功
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return False

        content = json.dumps(state, ensure_ascii=False, default=str)
        metadata = {
            "version": "V16.6",
            "timestamp": time.time(),
            "type": "pipeline_state"
        }

        try:
            if hasattr(knowledge, 'add_knowledge'):
                result = knowledge.add_knowledge(
                    category=KnowledgeCategory.PIPELINE_STATE.value,
                    content=content,
                    metadata=metadata
                )
            else:
                full = f"[{KnowledgeCategory.PIPELINE_STATE.value}] {content}"
                result = knowledge.add_memory(full)

            self.total_writes += 1
            return bool(result)

        except Exception as e:
            logger.error(f"保存管道状态失败: {e}")
            return False

    def load_latest_pipeline_state(self) -> Optional[Dict[str, Any]]:
        """加载最新的管道状态

        Returns:
            管道状态字典，无数据时返回None
        """
        knowledge = self._get_knowledge()
        if knowledge is None:
            return None

        self.total_reads += 1

        try:
            results = knowledge.search_knowledge(
                query="pipeline_state",
                category=KnowledgeCategory.PIPELINE_STATE.value,
                top_k=1
            )

            if not results:
                return None

            content = results[0].get("content", "")
            if content.startswith("{"):
                return json.loads(content)
            # 移除类别前缀
            if content.startswith("["):
                bracket_end = content.find("]")
                if bracket_end > 0:
                    content = content[bracket_end + 1:].strip()
                return json.loads(content) if content.startswith("{") else None

            return None

        except Exception as e:
            logger.error(f"加载管道状态失败: {e}")
            return None

    # ==================== 分析方法 ====================

    def _analyze_context(
        self,
        trade_results: List[Dict],
        risk_events: List[Dict],
        strategy_perfs: List[Dict]
    ) -> MarketContext:
        """分析市场上下文

        Args:
            trade_results: 交易结果列表
            risk_events: 风控事件列表
            strategy_perfs: 策略性能列表

        Returns:
            市场上下文
        """
        context = MarketContext()

        # 解析交易结果
        trades = self._parse_results(trade_results)
        if trades:
            total = len(trades)
            wins = sum(1 for t in trades if t["pnl"] > 0)
            context.recent_win_rate = wins / total if total > 0 else 0.0
            context.recent_avg_pnl_pct = sum(t["pnl"] for t in trades) / total

            # 按策略分组
            by_strategy = defaultdict(list)
            by_symbol = defaultdict(list)
            for t in trades:
                if t.get("strategy"):
                    by_strategy[t["strategy"]].append(t["pnl"])
                if t.get("symbol"):
                    by_symbol[t["symbol"]].append(t["pnl"])

            # 最佳/最差策略
            if by_strategy:
                avg_by_strategy = {
                    k: sum(v) / len(v) for k, v in by_strategy.items()
                }
                context.best_strategy = max(
                    avg_by_strategy, key=avg_by_strategy.get
                )
                context.worst_strategy = min(
                    avg_by_strategy, key=avg_by_strategy.get
                )
                context.strategy_performance = avg_by_strategy

            # 币种表现
            if by_symbol:
                win_by_symbol = {}
                for sym, pnls in by_symbol.items():
                    sym_wins = sum(1 for p in pnls if p > 0)
                    win_by_symbol[sym] = sym_wins / len(pnls) if pnls else 0
                context.symbol_performance = win_by_symbol

            # 数据置信度
            context.confidence = min(1.0, total / 30.0)

        # 解析风控事件
        context.recent_risk_events = len(risk_events)
        context.circuit_breaker_count = sum(
            1 for r in risk_events
            if "circuit_break" in r.get("content", "").lower()
        )

        # 时段性能（简化：按4小时段统计）
        hour_ranges = {
            "00-04": 0.0, "04-08": 0.0,
            "08-12": 0.0, "12-16": 0.0,
            "16-20": 0.0, "20-24": 0.0,
        }

        # 从结果中提取时间信息并统计时段表现
        for t in trades:
            timestamp = t.get("timestamp", 0)
            if timestamp > 0:
                hour = (datetime.fromtimestamp(timestamp).hour // 4) * 4
                hour_key = f"{hour:02d}-{hour+4:02d}"
                if hour_key in hour_ranges:
                    # 只记录有交易结果的时段
                    pnl = t.get("pnl", 0)
                    if pnl > 0:
                        hour_ranges[hour_key] = hour_ranges.get(hour_key, 0) + 1

        # 计算每个时段的胜率
        hour_trade_counts = {k: 0.1 for k in hour_ranges}
        for t in trades:
            timestamp = t.get("timestamp", 0)
            if timestamp > 0:
                hour = (datetime.fromtimestamp(timestamp).hour // 4) * 4
                hour_key = f"{hour:02d}-{hour+4:02d}"
                hour_trade_counts[hour_key] = hour_trade_counts.get(hour_key, 0) + 1

        # 归一化胜率
        if trades:
            context.time_of_day_performance = {
                k: v / hour_trade_counts[k] if hour_trade_counts[k] > 0 else 0
                for k, v in hour_ranges.items()
            }

        # V27.0: 学习最优参数
        if context.recent_win_rate >= 0.6:
            context.learned_position_mult = 1.15
            context.learned_stop_pct = 0.015
        elif context.recent_win_rate >= 0.4:
            context.learned_position_mult = 1.0
            context.learned_stop_pct = 0.02
        else:
            context.learned_position_mult = 0.8
            context.learned_stop_pct = 0.025

        return context

    def _parse_results(self, results: List[Dict]) -> List[Dict]:
        """解析知识搜索结果为结构化交易数据

        Args:
            results: 知识搜索结果

        Returns:
            解析后的交易数据列表
        """
        trades = []
        for r in results:
            content = r.get("content", "")
            if not content:
                continue

            pnl_str = self._extract_metric(content, "pnl=")
            if not pnl_str:
                continue

            try:
                pnl = float(pnl_str.replace("%", ""))
            except ValueError:
                continue

            trade = {
                "pnl": pnl,
                "strategy": self._extract_metric(content, "strategy="),
                "symbol": self._extract_metric(content, "symbol="),
                "exchange": self._extract_metric(content, "exchange="),
                "outcome": self._extract_metric(content, "outcome="),
            }
            trades.append(trade)

        return trades

    @staticmethod
    def _extract_metric(content: str, prefix: str) -> str:
        """从内容中提取指标值

        Args:
            content: 内容字符串
            prefix: 指标前缀 (如 "pnl=")

        Returns:
            提取到的值，未找到返回空字符串
        """
        start = content.find(prefix)
        if start < 0:
            return ""

        start += len(prefix)
        # 找到结束位置（空格、|、]或行尾）
        end = len(content)
        for delim in [" ", "|", "]"]:
            pos = content.find(delim, start)
            if pos > start and pos < end:
                end = pos

        return content[start:end].strip()

    def _flush_perf_buffer(self) -> None:
        """刷新性能缓冲区到知识库"""
        if not self._perf_buffer:
            return

        knowledge = self._get_knowledge()
        if knowledge is None:
            return

        try:
            # 按策略聚合
            by_strategy = defaultdict(list)
            for perf in self._perf_buffer:
                strategy = perf.get("strategy", "unknown")
                by_strategy[strategy].append(perf)

            for strategy, perfs in by_strategy.items():
                total = len(perfs)
                wins = sum(1 for p in perfs if p.get("pnl_usd", 0) > 0)
                avg_pnl = sum(p.get("pnl_pct", 0) for p in perfs) / total

                self.record_strategy_performance(
                    strategy=strategy,
                    total_trades=total,
                    win_rate=wins / total if total > 0 else 0.0,
                    avg_pnl_pct=avg_pnl,
                    period="buffer_flush"
                )

            self._perf_buffer.clear()
            logger.debug("性能缓冲区已刷新")

        except Exception as e:
            logger.error(f"刷新性能缓冲区失败: {e}")

    def get_bridge_statistics(self) -> Dict[str, Any]:
        """获取桥接器统计信息

        Returns:
            统计字典
        """
        return {
            "version": "V16.6",
            "total_reads": self.total_reads,
            "total_writes": self.total_writes,
            "total_cache_hits": self.total_cache_hits,
            "perf_buffer_size": len(self._perf_buffer),
            "context_cached": self._context_cache is not None,
            "context_age_sec": (
                time.time() - self._context_cache_time
                if self._context_cache_time > 0 else 0
            ),
        }


# 全局实例
_trading_knowledge_bridge: Optional[TradingKnowledgeBridge] = None


def get_trading_knowledge_bridge(
    knowledge_storage=None,
    config: Optional[Dict[str, Any]] = None
) -> TradingKnowledgeBridge:
    """获取全局交易知识桥接器实例

    Args:
        knowledge_storage: 知识存储实例
        config: 配置字典

    Returns:
        交易知识桥接器实例
    """
    global _trading_knowledge_bridge
    if _trading_knowledge_bridge is None:
        _trading_knowledge_bridge = TradingKnowledgeBridge(
            knowledge_storage, config
        )
    return _trading_knowledge_bridge
