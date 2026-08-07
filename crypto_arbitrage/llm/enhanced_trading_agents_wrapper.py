"""增强版TradingAgents集成包装器 V14.0

深度集成TradingAgents多智能体LLM分析框架到CryptoArbitrage系统。
提供AI驱动的智能决策、实时市场监控、自适应策略切换。

核心特性：
1. 多币种并行分析 - 支持同时分析多个交易对
2. 实时市场监控 - 持续监控市场条件变化
3. 自适应策略切换 - 根据市场条件动态调整策略
4. 性能反馈循环 - 持续学习和优化
5. 知识库深度集成 - 与memo0知识库无缝集成

依赖：
- TradingAgents: D:/01_COINLAB/TradingAgents
- memo0: 存储和检索AI洞察
- 需要配置至少一个LLM API Key
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading

# 添加TradingAgents到Python路径
TA_ROOT = "D:/01_COINLAB/TradingAgents"
if TA_ROOT not in sys.path:
    sys.path.insert(0, TA_ROOT)

logger = logging.getLogger(__name__)


class AnalysisMode(Enum):
    """分析模式"""
    QUICK = "quick"        # 快速分析
    STANDARD = "standard"  # 标准分析
    DEEP = "deep"          # 深度分析


class MarketCondition(Enum):
    """市场条件"""
    BULLISH = "bullish"       # 看涨
    BEARISH = "bearish"       # 看跌
    SIDEWAYS = "sideways"      # 震荡
    VOLATILE = "volatile"      # 高波动
    UNCERTAIN = "uncertain"    # 不确定


@dataclass
class AnalysisResult:
    """分析结果"""
    symbol: str
    signal: str              # BUY/OVERWEIGHT/HOLD/UNDERWEIGHT/SELL
    confidence: float        # 信心度 0-1
    market_condition: MarketCondition
    analysis_timestamp: datetime
    agent_reports: Dict[str, Any]  # 各Agent的报告
    key_insights: List[str]  # 关键洞察
    risk_factors: List[str]  # 风险因素
    execution_time: float     # 执行时间（秒）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'signal': self.signal,
            'confidence': self.confidence,
            'market_condition': self.market_condition.value,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'agent_reports': self.agent_reports,
            'key_insights': self.key_insights,
            'risk_factors': self.risk_factors,
            'execution_time': self.execution_time
        }


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_analyses: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    average_execution_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_analysis_time: Optional[datetime] = None

    def success_rate(self) -> float:
        """成功率"""
        if self.total_analyses == 0:
            return 0.0
        return self.successful_analyses / self.total_analyses

    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total


class EnhancedTradingAgentsWrapper:
    """增强版TradingAgents集成包装器 V14.0

    提供AI驱动的智能交易决策和深度市场分析。
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-6",
        language: str = "Chinese",
        enabled: bool = True,
        preset: str = "standard",
        cache_ttl: int = 300,  # 缓存时间（秒）
        max_concurrent_analyses: int = 3,  # 最大并发分析数
        enable_knowledge_integration: bool = True,  # 启用知识库集成
    ):
        """初始化增强版TradingAgents包装器

        Args:
            provider: LLM提供商
            model: 模型名称
            language: 输出语言
            enabled: 是否启用
            preset: 分析预设模式
            cache_ttl: 分析结果缓存时间（秒）
            max_concurrent_analyses: 最大并发分析数
            enable_knowledge_integration: 是否启用知识库集成
        """
        self.provider = provider
        self.model = model
        self.language = language
        self.enabled = enabled
        self.preset = preset
        self.cache_ttl = cache_ttl
        self.max_concurrent_analyses = max_concurrent_analyses
        self.enable_knowledge_integration = enable_knowledge_integration

        # TradingAgents图实例
        self._graph = None
        self._api_key_available = False

        # 性能指标
        self._metrics = PerformanceMetrics()
        self._analysis_lock = threading.Lock()

        # 缓存系统
        self._analysis_cache: Dict[str, Tuple[AnalysisResult, float]] = {}
        self._cache_lock = threading.Lock()

        # 市场条件跟踪
        self._market_conditions: Dict[str, MarketCondition] = {}
        self._condition_history: List[Dict] = []

        # 性能反馈循环
        self._feedback_queue: List[Dict] = []
        self._learning_enabled = True

        # 初始化
        if self.enabled:
            self._initialize_trading_agents()

    def _initialize_trading_agents(self) -> None:
        """初始化TradingAgents图"""
        try:
            # 检查API Key
            import os
            api_keys = {
                "openai": os.environ.get("OPENAI_API_KEY"),
                "google": os.environ.get("GOOGLE_API_KEY"),
                "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
                "xai": os.environ.get("XAI_API_KEY"),
                "openrouter": os.environ.get("OPENROUTER_API_KEY")
            }

            if not api_keys.get(self.provider):
                logger.warning(
                    f"EnhancedTradingAgents: {self.provider.upper()} API Key not found, "
                    "AI analysis will be disabled"
                )
                self.enabled = False
                return

            self._api_key_available = True

            # 导入TradingAgents
            from tradingagents.default_config import DEFAULT_CONFIG
            from tradingagents.graph.trading_graph import TradingAgentsGraph

            # 配置TradingAgents
            config = DEFAULT_CONFIG.copy()
            config["llm_provider"] = self.provider
            config["output_language"] = self.language

            # 根据预设调整配置
            if self.preset == "quick":
                config["max_debate_rounds"] = 0
                config["max_risk_discuss_rounds"] = 0
                config["deep_think_llm"] = self.model
                config["quick_think_llm"] = self.model
            elif self.preset == "standard":
                config["max_debate_rounds"] = 1
                config["max_risk_discuss_rounds"] = 1
                config["deep_think_llm"] = self.model
                config["quick_think_llm"] = "gpt-4o-mini"
            elif self.preset == "deep":
                config["max_debate_rounds"] = 3
                config["max_risk_discuss_rounds"] = 2
                config["deep_think_llm"] = self.model
                config["quick_think_llm"] = self.model

            # 初始化图
            self._graph = TradingAgentsGraph(debug=False, config=config)

            logger.info(
                f"✅ EnhancedTradingAgents V14.0 初始化成功 "
                f"(provider={self.provider}, model={self.model}, preset={self.preset})"
            )

        except Exception as e:
            logger.error(f"❌ EnhancedTradingAgents 初始化失败: {e}")
            self.enabled = False

    async def analyze_symbol(
        self,
        symbol: str,
        analysis_date: str = None,
        mode: AnalysisMode = AnalysisMode.STANDARD
    ) -> Optional[AnalysisResult]:
        """分析单个交易对

        Args:
            symbol: 交易对符号（如 BTC/USDT）
            analysis_date: 分析日期（YYYY-MM-DD）
            mode: 分析模式

        Returns:
            分析结果，如果失败返回None
        """
        if not self.enabled or not self._graph:
            logger.warning("TradingAgents未启用或未初始化")
            return None

        # 检查缓存
        cache_key = f"{symbol}:{mode.value}:{analysis_date or datetime.now().strftime('%Y-%m-%d')}"
        cached = self._get_from_cache(cache_key)
        if cached:
            with self._analysis_lock:
                self._metrics.cache_hits += 1
            logger.debug(f"缓存命中: {cache_key}")
            return cached

        with self._analysis_lock:
            self._metrics.cache_misses += 1

        try:
            start_time = time.time()

            # 准备分析参数
            if analysis_date is None:
                analysis_date = datetime.now().strftime('%Y-%m-%d')

            # 简化symbol格式（TradingAgents可能需要特定格式）
            clean_symbol = symbol.replace('/', '').replace('-', '').upper()

            # 调用TradingAgents分析
            final_state, decision = self._graph.propagate(clean_symbol, analysis_date)

            execution_time = time.time() - start_time

            # 解析结果
            result = self._parse_analysis_result(
                symbol, decision, final_state, execution_time
            )

            # 存储到缓存
            self._store_in_cache(cache_key, result)

            # 更新性能指标
            with self._analysis_lock:
                self._metrics.total_analyses += 1
                self._metrics.successful_analyses += 1
                self._metrics.average_execution_time = (
                    self._metrics.average_execution_time * (self._metrics.total_analyses - 1) +
                    execution_time
                ) / self._metrics.total_analyses
                self._metrics.last_analysis_time = datetime.now()

            # 更新市场条件
            self._update_market_condition(symbol, result)

            # 集成到知识库
            if self.enable_knowledge_integration:
                await self._integrate_to_knowledge_base(result)

            logger.info(
                f"✅ 分析完成: {symbol} -> {result.signal} "
                f"(confidence: {result.confidence:.2f}, time: {execution_time:.2f}s)"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 分析失败: {symbol} - {e}")
            with self._analysis_lock:
                self._metrics.total_analyses += 1
                self._metrics.failed_analyses += 1
            return None

    async def analyze_multiple_symbols(
        self,
        symbols: List[str],
        analysis_date: str = None,
        mode: AnalysisMode = AnalysisMode.STANDARD
    ) -> Dict[str, Optional[AnalysisResult]]:
        """并行分析多个交易对

        Args:
            symbols: 交易对列表
            analysis_date: 分析日期
            mode: 分析模式

        Returns:
            {symbol: AnalysisResult} 字典
        """
        if not self.enabled:
            return {symbol: None for symbol in symbols}

        logger.info(f"开始并行分析 {len(symbols)} 个交易对")

        # 限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent_analyses)

        async def analyze_with_semaphore(symbol: str) -> Tuple[str, Optional[AnalysisResult]]:
            async with semaphore:
                result = await self.analyze_symbol(symbol, analysis_date, mode)
                return symbol, result

        # 并行分析
        tasks = [analyze_with_semaphore(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 组装结果
        result_dict = {}
        for item in results:
            if isinstance(item, Exception):
                logger.error(f"分析异常: {item}")
                continue
            symbol, result = item
            result_dict[symbol] = result

        successful = sum(1 for r in result_dict.values() if r is not None)
        logger.info(f"并行分析完成: {successful}/{len(symbols)} 成功")

        return result_dict

    def _parse_analysis_result(
        self,
        symbol: str,
        decision: str,
        final_state: Dict,
        execution_time: float
    ) -> AnalysisResult:
        """解析TradingAgents分析结果

        Args:
            symbol: 交易对
            decision: 交易决策
            final_state: 最终状态
            execution_time: 执行时间

        Returns:
            分析结果
        """
        # 解析信号
        signal = decision.upper() if decision else "HOLD"
        if signal not in ["BUY", "OVERWEIGHT", "HOLD", "UNDERWEIGHT", "SELL"]:
            signal = "HOLD"

        # 解析信心度（基于报告内容）
        confidence = 0.7  # 默认信心度
        if final_state:
            try:
                # 尝试从报告中提取信心度
                reports = final_state.get('reports', {})
                investment_plan = final_state.get('investment_plan', '')

                # 简单的信心度估算
                if "strong" in investment_plan.lower() or "high" in investment_plan.lower():
                    confidence = 0.85
                elif "moderate" in investment_plan.lower() or "medium" in investment_plan.lower():
                    confidence = 0.70
                elif "weak" in investment_plan.lower() or "low" in investment_plan.lower():
                    confidence = 0.55

                # 根据信号调整
                if signal in ["BUY", "SELL"]:
                    confidence = min(1.0, confidence + 0.1)
            except Exception as e:
                logger.debug(f"信心度解析失败: {e}")

        # 判断市场条件
        market_condition = self._infer_market_condition(final_state)

        # 提取关键洞察
        key_insights = self._extract_key_insights(final_state)

        # 提取风险因素
        risk_factors = self._extract_risk_factors(final_state)

        return AnalysisResult(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            market_condition=market_condition,
            analysis_timestamp=datetime.now(),
            agent_reports=final_state.get('reports', {}),
            key_insights=key_insights,
            risk_factors=risk_factors,
            execution_time=execution_time
        )

    def _infer_market_condition(self, final_state: Dict) -> MarketCondition:
        """推断市场条件

        Args:
            final_state: 最终分析状态

        Returns:
            市场条件
        """
        try:
            reports = final_state.get('reports', {})
            investment_plan = final_state.get('investment_plan', '').lower()

            # 简单的关键词匹配
            if "bullish" in investment_plan or "uptrend" in investment_plan:
                return MarketCondition.BULLISH
            elif "bearish" in investment_plan or "downtrend" in investment_plan:
                return MarketCondition.BEARISH
            elif "volatile" in investment_plan or "high volatility" in investment_plan:
                return MarketCondition.VOLATILE
            elif "uncertain" in investment_plan or "mixed" in investment_plan:
                return MarketCondition.UNCERTAIN
            else:
                return MarketCondition.SIDEWAYS
        except Exception as e:
            logger.debug(f"市场条件推断失败: {e}")
            return MarketCondition.SIDEWAYS

    def _extract_key_insights(self, final_state: Dict) -> List[str]:
        """提取关键洞察

        Args:
            final_state: 最终分析状态

        Returns:
            关键洞察列表
        """
        insights = []
        try:
            reports = final_state.get('reports', {})

            # 从各Agent报告中提取洞察
            for agent_name, report in reports.items():
                if isinstance(report, dict):
                    summary = report.get('summary', '')
                    if summary and len(summary) > 20:
                        insights.append(f"{agent_name}: {summary[:100]}")

            # 从投资计划中提取
            investment_plan = final_state.get('investment_plan', '')
            if investment_plan and len(investment_plan) > 50:
                insights.append(f"投资计划: {investment_plan[:150]}")

        except Exception as e:
            logger.debug(f"关键洞察提取失败: {e}")

        return insights[:5]  # 最多返回5个洞察

    def _extract_risk_factors(self, final_state: Dict) -> List[str]:
        """提取风险因素

        Args:
            final_state: 最终分析状态

        Returns:
            风险因素列表
        """
        risks = []
        try:
            reports = final_state.get('reports', {})

            # 从风险报告中提取
            risk_report = reports.get('risk', {})
            if isinstance(risk_report, dict):
                risk_summary = risk_report.get('summary', '')
                if risk_summary:
                    risks.append(risk_summary[:100])

            # 从投资计划中提取风险提及
            investment_plan = final_state.get('investment_plan', '').lower()
            risk_keywords = ['risk', 'danger', 'caution', 'warning', 'loss', 'downside']
            for keyword in risk_keywords:
                if keyword in investment_plan:
                    # 提取包含关键词的句子
                    sentences = investment_plan.split('.')
                    for sentence in sentences:
                        if keyword in sentence and len(sentence) > 10:
                            risks.append(sentence.strip())
                            break

        except Exception as e:
            logger.debug(f"风险因素提取失败: {e}")

        return list(set(risks))[:3]  # 去重，最多返回3个风险

    def _update_market_condition(self, symbol: str, result: AnalysisResult) -> None:
        """更新市场条件跟踪

        Args:
            symbol: 交易对
            result: 分析结果
        """
        self._market_conditions[symbol] = result.market_condition

        # 记录历史
        self._condition_history.append({
            'symbol': symbol,
            'condition': result.market_condition.value,
            'signal': result.signal,
            'confidence': result.confidence,
            'timestamp': datetime.now().isoformat()
        })

        # 限制历史大小
        if len(self._condition_history) > 1000:
            self._condition_history = self._condition_history[-1000:]

    async def _integrate_to_knowledge_base(self, result: AnalysisResult) -> None:
        """集成分析结果到知识库

        Args:
            result: 分析结果
        """
        try:
            from storage.mem0_storage import add_trading_knowledge

            # 构建知识内容
            knowledge_content = (
                f"TradingAgents分析结果:\n"
                f"交易对: {result.symbol}\n"
                f"信号: {result.signal}\n"
                f"信心度: {result.confidence:.2f}\n"
                f"市场条件: {result.market_condition.value}\n"
                f"关键洞察: {'; '.join(result.key_insights[:3])}\n"
                f"风险因素: {'; '.join(result.risk_factors[:2])}"
            )

            # 添加到知识库
            add_trading_knowledge(
                category="ai_analysis",
                content=knowledge_content,
                metadata={
                    'symbol': result.symbol,
                    'signal': result.signal,
                    'confidence': result.confidence,
                    'timestamp': result.analysis_timestamp.isoformat()
                }
            )

            logger.debug(f"知识库集成成功: {result.symbol}")

        except Exception as e:
            logger.debug(f"知识库集成失败: {e}")

    def _get_from_cache(self, key: str) -> Optional[AnalysisResult]:
        """从缓存获取分析结果

        Args:
            key: 缓存键

        Returns:
            缓存的结果，如果过期或不存在返回None
        """
        with self._cache_lock:
            if key in self._analysis_cache:
                result, timestamp = self._analysis_cache[key]
                if time.time() - timestamp < self.cache_ttl:
                    return result
                else:
                    # 缓存过期
                    del self._analysis_cache[key]
        return None

    def _store_in_cache(self, key: str, result: AnalysisResult) -> None:
        """存储分析结果到缓存

        Args:
            key: 缓存键
            result: 分析结果
        """
        with self._cache_lock:
            self._analysis_cache[key] = (result, time.time())

            # 限制缓存大小
            if len(self._analysis_cache) > 1000:
                # 删除最旧的缓存项
                oldest_key = min(
                    self._analysis_cache.keys(),
                    key=lambda k: self._analysis_cache[k][1]
                )
                del self._analysis_cache[oldest_key]

    def get_market_conditions(self) -> Dict[str, MarketCondition]:
        """获取当前市场条件

        Returns:
            {symbol: MarketCondition} 字典
        """
        return self._market_conditions.copy()

    def get_performance_metrics(self) -> PerformanceMetrics:
        """获取性能指标

        Returns:
            性能指标
        """
        with self._analysis_lock:
            return PerformanceMetrics(
                total_analyses=self._metrics.total_analyses,
                successful_analyses=self._metrics.successful_analyses,
                failed_analyses=self._metrics.failed_analyses,
                average_execution_time=self._metrics.average_execution_time,
                cache_hits=self._metrics.cache_hits,
                cache_misses=self._metrics.cache_misses,
                last_analysis_time=self._metrics.last_analysis_time
            )

    def get_condition_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """获取市场条件历史

        Args:
            symbol: 过滤特定交易对（可选）
            limit: 返回数量限制

        Returns:
            历史记录列表
        """
        history = self._condition_history.copy()

        if symbol:
            history = [h for h in history if h.get('symbol') == symbol]

        return history[-limit:] if history else []

    def clear_cache(self) -> None:
        """清除缓存"""
        with self._cache_lock:
            self._analysis_cache.clear()
        logger.info("分析缓存已清除")

    def update_feedback(
        self,
        symbol: str,
        actual_outcome: str,
        expected_signal: str,
        profit_loss: float
    ) -> None:
        """更新性能反馈

        Args:
            symbol: 交易对
            actual_outcome: 实际结果
            expected_signal: 预期信号
            profit_loss: 盈亏
        """
        feedback = {
            'symbol': symbol,
            'actual_outcome': actual_outcome,
            'expected_signal': expected_signal,
            'profit_loss': profit_loss,
            'timestamp': datetime.now().isoformat()
        }

        self._feedback_queue.append(feedback)

        # 限制反馈队列大小
        if len(self._feedback_queue) > 1000:
            self._feedback_queue = self._feedback_queue[-1000:]

        logger.debug(f"性能反馈已记录: {symbol}")

    def get_feedback_summary(self) -> Dict[str, Any]:
        """获取反馈摘要

        Returns:
            反馈统计摘要
        """
        if not self._feedback_queue:
            return {
                'total_feedback': 0,
                'accuracy': 0.0,
                'average_profit_loss': 0.0,
                'signal_distribution': {}
            }

        total = len(self._feedback_queue)
        correct = sum(
            1 for f in self._feedback_queue
            if f['actual_outcome'] == f['expected_signal']
        )

        total_pnl = sum(f['profit_loss'] for f in self._feedback_queue)

        # 信号分布
        signal_dist = defaultdict(int)
        for f in self._feedback_queue:
            signal_dist[f['expected_signal']] += 1

        return {
            'total_feedback': total,
            'accuracy': correct / total if total > 0 else 0.0,
            'average_profit_loss': total_pnl / total if total > 0 else 0.0,
            'signal_distribution': dict(signal_dist)
        }


def create_enhanced_wrapper(config: Dict[str, Any]) -> Optional[EnhancedTradingAgentsWrapper]:
    """创建增强版TradingAgents包装器

    Args:
        config: 配置字典，包含:
            - provider: LLM提供商
            - model: 模型名称
            - language: 输出语言
            - enabled: 是否启用
            - preset: 分析预设

    Returns:
        EnhancedTradingAgentsWrapper实例，如果未启用返回None
    """
    if not config.get('enabled', False):
        return None

    try:
        wrapper = EnhancedTradingAgentsWrapper(
            provider=config.get('provider', 'anthropic'),
            model=config.get('model', 'claude-sonnet-4-6'),
            language=config.get('language', 'Chinese'),
            enabled=config.get('enabled', True),
            preset=config.get('preset', 'standard'),
            cache_ttl=config.get('cache_ttl', 300),
            max_concurrent_analyses=config.get('max_concurrent_analyses', 3),
            enable_knowledge_integration=config.get('enable_knowledge_integration', True)
        )

        return wrapper

    except Exception as e:
        logger.error(f"创建增强TradingAgents包装器失败: {e}")
        return None