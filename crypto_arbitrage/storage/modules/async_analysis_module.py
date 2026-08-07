"""异步分析模块 V5.9 - AsyncAnalysisModule

V5.9新增的第6个核心模块，专注异步LLM分析功能。
基于V5.8模块化架构标准，内聚性目标0.48+。

核心功能：
1. 异步LLM分析管理 - 集成AsyncLLMAnalyzer
2. 批量并发分析 - 智能并发控制
3. 智能缓存优化 - 分析结果缓存
4. 性能统计监控 - 详细的性能指标
5. 超时和错误处理 - 健壮的错误处理

模块职责：专注异步分析相关的所有功能
内聚性设计：所有方法都围绕异步分析这一核心职责
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    """分析状态"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


@dataclass
class AnalysisResult:
    """分析结果"""
    symbol: str
    status: AnalysisStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: float = field(default_factory=time.time)
    cache_hit: bool = False


@dataclass
class BatchAnalysisResult:
    """批量分析结果"""
    total_symbols: int
    successful: int
    failed: int
    timeout: int
    cache_hits: int
    total_duration: float
    results: Dict[str, AnalysisResult] = field(default_factory=dict)


class AsyncAnalysisModule:
    """异步分析模块 V5.9

    专注异步LLM分析的所有功能，包括单个分析、批量分析、
    缓存管理、性能统计等。高内聚性设计，所有方法都围绕
    异步分析这一核心职责。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化异步分析模块

        Args:
            config: 配置字典，包含:
                - max_workers: 最大并发工作线程数
                - cache_ttl: 缓存TTL（秒）
                - timeout: 单次分析超时时间（秒）
                - enable_batch_analysis: 是否启用批量分析
                - max_concurrent_batch: 批量分析最大并发数
                - enable_smart_cache: 是否启用智能缓存
                - cache_warmup_symbols: 缓存预热符号列表
        """
        self.config = config

        # 异步分析器配置
        self.max_workers = config.get('max_workers', 3)
        self.cache_ttl = config.get('cache_ttl', 300)
        self.timeout = config.get('timeout', 120)

        # 批量分析配置
        self.enable_batch_analysis = config.get('enable_batch_analysis', True)
        self.max_concurrent_batch = config.get('max_concurrent_batch', 5)

        # 智能缓存配置
        self.enable_smart_cache = config.get('enable_smart_cache', True)
        self.cache_warmup_symbols = config.get('cache_warmup_symbols', [])

        # 延迟导入AsyncLLMAnalyzer（避免初始化阻塞）
        self._async_analyzer = None
        self._analyzer_lock = asyncio.Lock()

        # 分析缓存（模块级别缓存，与AsyncLLMAnalyzer的缓存互补）
        self._module_cache: Dict[str, tuple] = {}  # key: (timestamp, result)
        self._cache_lock = asyncio.Lock()

        # 性能统计
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "timeout_analyses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_duration": 0.0,
            "avg_duration": 0.0,
            "batch_analyses": 0,
            "concurrent_analyses": 0
        }

        # 实时分析状态
        self._active_analyses: Dict[str, AnalysisStatus] = {}
        self._analysis_history: List[AnalysisResult] = []
        self._max_history = 100

        logger.info(
            f"[OK] 异步分析模块V5.9初始化成功: "
            f"max_workers={self.max_workers}, "
            f"cache_ttl={self.cache_ttl}s, "
            f"timeout={self.timeout}s"
        )

    # ==================== 核心分析方法 ====================

    async def analyze_symbol_async(
        self,
        symbol: str,
        date: Optional[str] = None,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> AnalysisResult:
        """异步分析单个交易对

        Args:
            symbol: 交易对符号（如BTC/USDT）
            date: 分析日期（默认今天）
            use_cache: 是否使用缓存
            force_refresh: 强制刷新缓存

        Returns:
            AnalysisResult对象
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cache_key = f"{symbol}_{date}"
        start_time = time.time()

        # 更新统计
        self.stats["total_analyses"] += 1

        # 检查模块缓存
        if use_cache and not force_refresh:
            cached_result = await self._get_from_module_cache(cache_key)
            if cached_result is not None:
                self.stats["cache_hits"] += 1
                duration = time.time() - start_time
                self._update_duration_stats(duration)

                logger.debug(f"模块缓存命中: {symbol}")
                return AnalysisResult(
                    symbol=symbol,
                    status=AnalysisStatus.COMPLETED,
                    result=cached_result,
                    duration=duration,
                    cache_hit=True
                )

        self.stats["cache_misses"] += 1

        # 标记分析状态
        self._active_analyses[cache_key] = AnalysisStatus.RUNNING
        self.stats["concurrent_analyses"] = max(
            self.stats["concurrent_analyses"],
            len(self._active_analyses)
        )

        try:
            # 获取异步分析器
            analyzer = await self._get_async_analyzer()

            # 执行异步分析
            result = await analyzer.analyze_async(symbol, date, use_cache=not force_refresh)

            # 等待结果
            analysis_result = await result

            # 检查分析结果
            if analysis_result.get("success", False):
                self.stats["successful_analyses"] += 1
                status = AnalysisStatus.COMPLETED

                # 缓存结果
                if use_cache:
                    await self._add_to_module_cache(cache_key, analysis_result)

            elif analysis_result.get("error") == "Timeout":
                self.stats["timeout_analyses"] += 1
                status = AnalysisStatus.TIMEOUT
            else:
                self.stats["failed_analyses"] += 1
                status = AnalysisStatus.FAILED

            duration = time.time() - start_time
            self._update_duration_stats(duration)

            # 创建结果对象
            result_obj = AnalysisResult(
                symbol=symbol,
                status=status,
                result=analysis_result if status == AnalysisStatus.COMPLETED else None,
                error=analysis_result.get("error"),
                duration=duration,
                cache_hit=False
            )

            # 添加到历史记录
            await self._add_to_history(result_obj)

            logger.info(
                f"异步分析完成: {symbol}, "
                f"状态={status.value}, "
                f"耗时={duration:.2f}s, "
                f"信号={analysis_result.get('signal', 'N/A')}"
            )

            return result_obj

        except Exception as e:
            self.stats["failed_analyses"] += 1
            duration = time.time() - start_time

            logger.error(f"异步分析失败: {symbol}, 错误: {e}")

            return AnalysisResult(
                symbol=symbol,
                status=AnalysisStatus.FAILED,
                error=str(e),
                duration=duration,
                cache_hit=False
            )

        finally:
            # 清除活跃状态
            if cache_key in self._active_analyses:
                del self._active_analyses[cache_key]

    async def analyze_batch_async(
        self,
        symbols: List[str],
        date: Optional[str] = None,
        max_concurrent: Optional[int] = None,
        use_cache: bool = True
    ) -> BatchAnalysisResult:
        """批量异步分析多个交易对

        Args:
            symbols: 交易对符号列表
            date: 分析日期（默认今天）
            max_concurrent: 最大并发数（默认使用配置值）
            use_cache: 是否使用缓存

        Returns:
            BatchAnalysisResult对象
        """
        if not self.enable_batch_analysis:
            logger.warning("批量分析未启用，将逐个分析")
            return await self._analyze_batch_sequential(symbols, date, use_cache)

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if max_concurrent is None:
            max_concurrent = self.max_concurrent_batch

        start_time = time.time()
        self.stats["batch_analyses"] += 1

        logger.info(f"开始批量分析: {len(symbols)}个交易对, 最大并发={max_concurrent}")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _analyze_with_limit(symbol: str) -> tuple:
            async with semaphore:
                result = await self.analyze_symbol_async(symbol, date, use_cache)
                return symbol, result

        # 创建所有任务
        tasks = [_analyze_with_limit(symbol) for symbol in symbols]

        # 并发执行所有分析
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        results = {}
        successful = 0
        failed = 0
        timeout_count = 0
        cache_hits = 0

        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                logger.error(f"批量分析异常: {task_result}")
                failed += 1
            else:
                symbol, result = task_result
                results[symbol] = result

                if result.status == AnalysisStatus.COMPLETED:
                    successful += 1
                elif result.status == AnalysisStatus.FAILED:
                    failed += 1
                elif result.status == AnalysisStatus.TIMEOUT:
                    timeout_count += 1

                if result.cache_hit:
                    cache_hits += 1

        total_duration = time.time() - start_time

        batch_result = BatchAnalysisResult(
            total_symbols=len(symbols),
            successful=successful,
            failed=failed,
            timeout=timeout_count,
            cache_hits=cache_hits,
            total_duration=total_duration,
            results=results
        )

        logger.info(
            f"批量分析完成: {successful}/{len(symbols)}成功, "
            f"失败={failed}, 超时={timeout_count}, "
            f"缓存命中={cache_hits}, "
            f"总耗时={total_duration:.2f}s"
        )

        return batch_result

    async def analyze_market_conditions_async(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """异步分析市场条件

        Args:
            symbols: 要分析的交易对列表（默认使用缓存预热列表）

        Returns:
            市场条件分析结果
        """
        if symbols is None:
            symbols = self.cache_warmup_symbols

        if not symbols:
            logger.warning("没有指定交易对，使用默认列表")
            symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]

        logger.info(f"开始分析市场条件: {len(symbols)}个交易对")

        # 批量分析
        batch_result = await self.analyze_batch_async(symbols)

        # 汇总市场条件
        market_conditions = {
            "analysis_time": datetime.now().isoformat(),
            "total_symbols": len(symbols),
            "successful_analyses": batch_result.successful,
            "failed_analyses": batch_result.failed,
            "market_sentiment": self._calculate_market_sentiment(batch_result.results),
            "opportunities": self._identify_opportunities(batch_result.results),
            "risk_level": self._assess_market_risk(batch_result.results),
            "analysis_details": {
                symbol: {
                    "signal": result.result.get("signal") if result.result else None,
                    "score": result.result.get("score") if result.result else None,
                    "confidence": result.result.get("confidence") if result.result else None,
                    "status": result.status.value
                }
                for symbol, result in batch_result.results.items()
            }
        }

        logger.info(
            f"市场条件分析完成: "
            f"情绪={market_conditions['market_sentiment']}, "
            f"风险等级={market_conditions['risk_level']}, "
            f"机会数={len(market_conditions['opportunities'])}"
        )

        return market_conditions

    async def analyze_arbitrage_opportunity_async(
        self,
        opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """异步分析套利机会

        Args:
            opportunity: 套利机会字典

        Returns:
            套利机会分析结果
        """
        symbol = opportunity.get("symbol", "UNKNOWN")
        strategy = opportunity.get("strategy", "UNKNOWN")

        logger.info(f"开始分析套利机会: {symbol} ({strategy})")

        start_time = time.time()

        try:
            # 分析相关交易对
            symbols_to_analyze = self._extract_symbols_from_opportunity(opportunity)
            batch_result = await self.analyze_batch_async(symbols_to_analyze)

            # 评估套利机会
            opportunity_analysis = {
                "opportunity_id": opportunity.get("id", "unknown"),
                "symbol": symbol,
                "strategy": strategy,
                "analysis_time": datetime.now().isoformat(),
                "market_analysis": {
                    "sentiment": self._calculate_market_sentiment(batch_result.results),
                    "risk_level": self._assess_market_risk(batch_result.results)
                },
                "feasibility": self._assess_feasibility(opportunity, batch_result.results),
                "recommendation": self._generate_recommendation(opportunity, batch_result.results),
                "confidence": self._calculate_confidence(opportunity, batch_result.results),
                "analysis_duration": time.time() - start_time,
                "supporting_data": {
                    symbol: {
                        "signal": result.result.get("signal") if result.result else None,
                        "score": result.result.get("score") if result.result else None
                    }
                    for symbol, result in batch_result.results.items()
                }
            }

            logger.info(
                f"套利机会分析完成: {symbol}, "
                f"可行性={opportunity_analysis['feasibility']}, "
                f"建议={opportunity_analysis['recommendation']}, "
                f"置信度={opportunity_analysis['confidence']:.2f}"
            )

            return opportunity_analysis

        except Exception as e:
            logger.error(f"套利机会分析失败: {e}")
            return {
                "opportunity_id": opportunity.get("id", "unknown"),
                "error": str(e),
                "analysis_failed": True
            }

    # ==================== 缓存管理 ====================

    async def _get_from_module_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从模块缓存获取结果

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果或None
        """
        async with self._cache_lock:
            if cache_key in self._module_cache:
                timestamp, result = self._module_cache[cache_key]

                # 检查TTL
                if time.time() - timestamp < self.cache_ttl:
                    return result
                else:
                    # 缓存过期，删除
                    del self._module_cache[cache_key]

        return None

    async def _add_to_module_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """添加结果到模块缓存

        Args:
            cache_key: 缓存键
            result: 结果字典
        """
        async with self._cache_lock:
            self._module_cache[cache_key] = (time.time(), result)

            # 限制缓存大小
            if len(self._module_cache) > 50:
                await self._evict_oldest_cache()

    async def _evict_oldest_cache(self) -> None:
        """清除最旧的缓存项"""
        async with self._cache_lock:
            if not self._module_cache:
                return

            # 按时间戳排序，删除最旧的20%
            sorted_items = sorted(
                self._module_cache.items(),
                key=lambda x: x[1][0]
            )
            num_to_evict = max(1, len(sorted_items) // 5)

            for cache_key, _ in sorted_items[:num_to_evict]:
                del self._module_cache[cache_key]

            logger.debug(f"清除{num_to_evict}个最旧缓存项")

    async def warmup_cache(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """缓存预热

        Args:
            symbols: 要预热的交易对列表

        Returns:
            预热结果
        """
        if symbols is None:
            symbols = self.cache_warmup_symbols

        if not symbols:
            logger.warning("没有指定预热符号")
            return {"status": "skipped", "reason": "no_symbols"}

        logger.info(f"开始缓存预热: {len(symbols)}个交易对")

        start_time = time.time()

        try:
            # 批量分析（使用缓存）
            batch_result = await self.analyze_batch_async(symbols, use_cache=True)

            warmup_result = {
                "status": "completed",
                "total_symbols": len(symbols),
                "successful": batch_result.successful,
                "cache_hits": batch_result.cache_hits,
                "duration": time.time() - start_time,
                "cache_hit_rate": batch_result.cache_hits / len(symbols) if symbols else 0
            }

            logger.info(
                f"缓存预热完成: {warmup_result['cache_hit_rate']:.1%}命中率, "
                f"耗时={warmup_result['duration']:.2f}s"
            )

            return warmup_result

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
            return {"status": "failed", "error": str(e)}

    async def clear_cache(self) -> None:
        """清空模块缓存"""
        async with self._cache_lock:
            self._module_cache.clear()

        logger.info("模块缓存已清空")

    # ==================== 性能统计 ====================

    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计信息

        Returns:
            统计信息字典
        """
        cache_hit_rate = 0.0
        if self.stats["total_analyses"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_analyses"]

        success_rate = 0.0
        if self.stats["total_analyses"] > 0:
            success_rate = self.stats["successful_analyses"] / self.stats["total_analyses"]

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "success_rate": success_rate,
            "failure_rate": 1.0 - success_rate,
            "module_cache_size": len(self._module_cache),
            "active_analyses": len(self._active_analyses),
            "max_concurrent_analyses": self.stats["concurrent_analyses"],
            "history_size": len(self._analysis_history)
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "timeout_analyses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_duration": 0.0,
            "avg_duration": 0.0,
            "batch_analyses": 0,
            "concurrent_analyses": 0
        }
        logger.info("分析统计已重置")

    def _update_duration_stats(self, duration: float) -> None:
        """更新耗时统计

        Args:
            duration: 耗时（秒）
        """
        self.stats["total_duration"] += duration
        if self.stats["total_analyses"] > 0:
            self.stats["avg_duration"] = (
                self.stats["total_duration"] / self.stats["total_analyses"]
            )

    # ==================== 历史记录管理 ====================

    async def _add_to_history(self, result: AnalysisResult) -> None:
        """添加结果到历史记录

        Args:
            result: 分析结果
        """
        self._analysis_history.append(result)

        # 限制历史记录大小
        if len(self._analysis_history) > self._max_history:
            self._analysis_history.pop(0)

    def get_analysis_history(
        self,
        limit: Optional[int] = None,
        symbol: Optional[str] = None
    ) -> List[AnalysisResult]:
        """获取分析历史记录

        Args:
            limit: 返回记录数量限制
            symbol: 筛选特定交易对

        Returns:
            分析结果列表
        """
        history = self._analysis_history

        # 筛选交易对
        if symbol:
            history = [r for r in history if r.symbol == symbol]

        # 限制数量
        if limit:
            history = history[-limit:]

        return history

    # ==================== 工具方法 ====================

    async def _get_async_analyzer(self):
        """获取异步分析器实例（延迟初始化）

        Returns:
            AsyncLLMAnalyzer实例
        """
        async with self._analyzer_lock:
            if self._async_analyzer is None:
                from llm.async_trading_agents import AsyncLLMAnalyzer
                self._async_analyzer = AsyncLLMAnalyzer(
                    max_workers=self.max_workers,
                    cache_ttl=self.cache_ttl,
                    timeout=self.timeout
                )
                logger.info("AsyncLLMAnalyzer初始化完成")

            return self._async_analyzer

    async def _analyze_batch_sequential(
        self,
        symbols: List[str],
        date: Optional[str],
        use_cache: bool
    ) -> BatchAnalysisResult:
        """顺序批量分析（备用方案）

        Args:
            symbols: 交易对列表
            date: 分析日期
            use_cache: 是否使用缓存

        Returns:
            批量分析结果
        """
        start_time = time.time()
        results = {}
        successful = 0
        failed = 0
        timeout_count = 0
        cache_hits = 0

        for symbol in symbols:
            result = await self.analyze_symbol_async(symbol, date, use_cache)
            results[symbol] = result

            if result.status == AnalysisStatus.COMPLETED:
                successful += 1
            elif result.status == AnalysisStatus.FAILED:
                failed += 1
            elif result.status == AnalysisStatus.TIMEOUT:
                timeout_count += 1

            if result.cache_hit:
                cache_hits += 1

        return BatchAnalysisResult(
            total_symbols=len(symbols),
            successful=successful,
            failed=failed,
            timeout=timeout_count,
            cache_hits=cache_hits,
            total_duration=time.time() - start_time,
            results=results
        )

    def _calculate_market_sentiment(self, results: Dict[str, AnalysisResult]) -> str:
        """计算市场情绪

        Args:
            results: 分析结果字典

        Returns:
            市场情绪 (BULLISH/BEARISH/NEUTRAL)
        """
        if not results:
            return "NEUTRAL"

        buy_signals = 0
        sell_signals = 0
        hold_signals = 0

        for result in results.values():
            if result.result:
                signal = result.result.get("signal", "HOLD")
                if signal == "BUY":
                    buy_signals += 1
                elif signal == "SELL":
                    sell_signals += 1
                else:
                    hold_signals += 1

        total = buy_signals + sell_signals + hold_signals
        if total == 0:
            return "NEUTRAL"

        buy_ratio = buy_signals / total
        sell_ratio = sell_signals / total

        if buy_ratio > 0.6:
            return "BULLISH"
        elif sell_ratio > 0.6:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _assess_market_risk(self, results: Dict[str, AnalysisResult]) -> str:
        """评估市场风险

        Args:
            results: 分析结果字典

        Returns:
            风险等级 (LOW/MEDIUM/HIGH)
        """
        if not results:
            return "MEDIUM"

        failed_count = sum(1 for r in results.values() if r.status != AnalysisStatus.COMPLETED)
        failure_rate = failed_count / len(results) if results else 0

        if failure_rate > 0.3:
            return "HIGH"
        elif failure_rate > 0.1:
            return "MEDIUM"
        else:
            return "LOW"

    def _identify_opportunities(self, results: Dict[str, AnalysisResult]) -> List[Dict[str, Any]]:
        """识别套利机会

        Args:
            results: 分析结果字典

        Returns:
            机会列表
        """
        opportunities = []

        for symbol, result in results.items():
            if result.result and result.status == AnalysisStatus.COMPLETED:
                signal = result.result.get("signal")
                score = result.result.get("score", 50)
                confidence = result.result.get("confidence", 0.0)

                if signal in ["BUY", "SELL"] and confidence > 0.7:
                    opportunities.append({
                        "symbol": symbol,
                        "signal": signal,
                        "score": score,
                        "confidence": confidence
                    })

        # 按置信度排序
        opportunities.sort(key=lambda x: x["confidence"], reverse=True)

        return opportunities

    def _extract_symbols_from_opportunity(self, opportunity: Dict[str, Any]) -> List[str]:
        """从套利机会中提取交易对

        Args:
            opportunity: 套利机会字典

        Returns:
            交易对列表
        """
        symbols = []

        # 主交易对
        if "symbol" in opportunity:
            symbols.append(opportunity["symbol"])

        # 相关交易对
        if "related_symbols" in opportunity:
            symbols.extend(opportunity["related_symbols"])

        # 策略特定交易对
        strategy = opportunity.get("strategy", "")
        if strategy == "triangular":
            # 三角套利需要3个交易对
            symbols.extend(opportunity.get("triangle_symbols", []))
        elif strategy == "statistical":
            # 统计套利需要配对交易对
            symbols.extend(opportunity.get("pair_symbols", []))

        return list(set(symbols))  # 去重

    def _assess_feasibility(
        self,
        opportunity: Dict[str, Any],
        analysis_results: Dict[str, AnalysisResult]
    ) -> str:
        """评估套利可行性

        Args:
            opportunity: 套利机会
            analysis_results: 分析结果

        Returns:
            可行性 (HIGH/MEDIUM/LOW)
        """
        # 检查分析成功率
        success_count = sum(
            1 for r in analysis_results.values()
            if r.status == AnalysisStatus.COMPLETED
        )
        success_rate = success_count / len(analysis_results) if analysis_results else 0

        if success_rate < 0.8:
            return "LOW"

        # 检查市场情绪
        sentiment = self._calculate_market_sentiment(analysis_results)
        if sentiment == "HIGH":
            return "LOW"

        # 检查风险等级
        risk = self._assess_market_risk(analysis_results)
        if risk == "HIGH":
            return "MEDIUM"

        return "HIGH"

    def _generate_recommendation(
        self,
        opportunity: Dict[str, Any],
        analysis_results: Dict[str, AnalysisResult]
    ) -> str:
        """生成建议

        Args:
            opportunity: 套利机会
            analysis_results: 分析结果

        Returns:
            建议 (EXECUTE/MONITOR/SKIP)
        """
        feasibility = self._assess_feasibility(opportunity, analysis_results)

        if feasibility == "HIGH":
            return "EXECUTE"
        elif feasibility == "MEDIUM":
            return "MONITOR"
        else:
            return "SKIP"

    def _calculate_confidence(
        self,
        opportunity: Dict[str, Any],
        analysis_results: Dict[str, AnalysisResult]
    ) -> float:
        """计算置信度

        Args:
            opportunity: 套利机会
            analysis_results: 分析结果

        Returns:
            置信度 (0.0-1.0)
        """
        if not analysis_results:
            return 0.0

        # 基于分析结果计算平均置信度
        confidences = []
        for result in analysis_results.values():
            if result.result:
                conf = result.result.get("confidence", 0.0)
                confidences.append(conf)

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)


def create_async_analysis_module(config: Dict[str, Any]) -> AsyncAnalysisModule:
    """创建异步分析模块实例

    Args:
        config: 配置字典

    Returns:
        AsyncAnalysisModule实例
    """
    return AsyncAnalysisModule(config)
