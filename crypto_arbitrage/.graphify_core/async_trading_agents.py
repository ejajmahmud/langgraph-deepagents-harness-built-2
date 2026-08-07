"""异步LLM分析引擎

V2.7新增：将同步的TradingAgents分析升级为异步实现，
显著提升系统响应速度，避免LLM调用阻塞主流程。

核心特性：
1. 异步LLM分析 - 使用asyncio和线程池
2. 并发控制 - 限制最大并发数
3. 请求队列 - 智能调度LLM请求
4. 超时处理 - 防止长时间阻塞
5. 结果缓存 - 避免重复分析
"""

import asyncio
import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AsyncLLMAnalyzer:
    """异步LLM分析器

    使用线程池和队列实现异步LLM分析，避免阻塞主流程。
    """

    def __init__(
        self,
        max_workers: int = 3,
        cache_ttl: int = 300,
        timeout: int = 120
    ):
        """初始化异步分析器

        Args:
            max_workers: 最大并发工作线程数
            cache_ttl: 缓存TTL（秒）
            timeout: 单次分析超时时间（秒）
        """
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self.timeout = timeout

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 结果缓存
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_lock = threading.Lock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "timeouts": 0,
            "errors": 0
        }

        logger.info(
            f"AsyncLLMAnalyzer initialized: "
            f"max_workers={max_workers}, "
            f"cache_ttl={cache_ttl}s, "
            f"timeout={timeout}s"
        )

    def analyze_async(
        self,
        symbol: str,
        date: str,
        use_cache: bool = True
    ) -> asyncio.Future:
        """异步分析加密货币

        Args:
            symbol: 加密货币代码
            date: 分析日期
            use_cache: 是否使用缓存

        Returns:
            asyncio.Future对象，通过await获取结果
        """
        cache_key = f"{symbol}_{date}"

        # 检查缓存
        if use_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                loop = asyncio.get_event_loop()
                return loop.create_future_from_result(cached_result)

        # 提交异步任务
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.executor,
            self._analyze_sync,
            symbol,
            date,
            use_cache
        )

        return future

    async def analyze_batch_async(
        self,
        symbols: List[str],
        date: str,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        """批量异步分析多个加密货币

        Args:
            symbols: 加密货币代码列表
            date: 分析日期
            max_concurrent: 最大并发数（默认使用max_workers）

        Returns:
            字典，键为symbol，值为分析结果
        """
        if max_concurrent is None:
            max_concurrent = self.max_workers

        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _analyze_with_limit(sym: str) -> tuple:
            async with semaphore:
                result = await self.analyze_async(sym, date)
                return sym, result

        # 创建所有任务
        tasks = [_analyze_with_limit(symbol) for symbol in symbols]

        # 等待所有任务完成
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                logger.error(f"Batch analysis error: {task_result}")
            else:
                symbol, result = task_result
                results[symbol] = result

        return results

    def _analyze_sync(
        self,
        symbol: str,
        date: str,
        use_cache: bool
    ) -> Dict[str, Any]:
        """同步分析（在独立线程中执行）

        Args:
            symbol: 加密货币代码
            date: 分析日期
            use_cache: 是否使用缓存

        Returns:
            分析结果
        """
        cache_key = f"{symbol}_{date}"
        start_time = time.time()

        # 更新统计
        self.stats["total_requests"] += 1

        try:
            # 导入TradingAgents（延迟导入，避免初始化阻塞）
            from llm.trading_agents_wrapper import TradingAgentsWrapper

            # 创建包装器
            wrapper = TradingAgentsWrapper()

            # 检查缓存
            if use_cache:
                cached = self._get_from_cache(cache_key)
                if cached is not None:
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for {symbol}")
                    return cached

            self.stats["cache_misses"] += 1

            # 执行分析（带超时）
            try:
                result = wrapper.analyze_crypto(symbol, date, timeout=self.timeout)

                # 缓存结果
                if use_cache and result.get("success"):
                    self._add_to_cache(cache_key, result)

                duration = time.time() - start_time
                logger.info(
                    f"LLM analysis completed: {symbol}, "
                    f"duration={duration:.2f}s, "
                    f"signal={result.get('signal', 'N/A')}"
                )

                return result

            except TimeoutError:
                self.stats["timeouts"] += 1
                logger.warning(f"LLM analysis timeout for {symbol}")
                return self._create_timeout_result(symbol)

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"LLM analysis failed for {symbol}: {e}")
            return self._create_error_result(symbol, str(e))

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取结果

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果或None
        """
        with self.cache_lock:
            if cache_key in self.cache:
                timestamp, result = self.cache[cache_key]

                # 检查TTL
                if time.time() - timestamp < self.cache_ttl:
                    return result
                else:
                    # 缓存过期，删除
                    del self.cache[cache_key]

        return None

    def _add_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """添加结果到缓存

        Args:
            cache_key: 缓存键
            result: 结果字典
        """
        with self.cache_lock:
            self.cache[cache_key] = (time.time(), result)

        # 限制缓存大小
        if len(self.cache) > 100:
            self._evict_oldest_cache()

    def _evict_oldest_cache(self) -> None:
        """清除最旧的缓存项"""
        with self.cache_lock:
            if not self.cache:
                return

            # 按时间戳排序，删除最旧的20%
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1][0]
            )
            num_to_evict = max(1, len(sorted_items) // 5)

            for cache_key, _ in sorted_items[:num_to_evict]:
                del self.cache[cache_key]

            logger.debug(f"Evicted {num_to_evict} oldest cache entries")

    def _create_timeout_result(self, symbol: str) -> Dict[str, Any]:
        """创建超时结果

        Args:
            symbol: 加密货币代码

        Returns:
            超时结果字典
        """
        return {
            "signal": "HOLD",
            "score": 50,
            "confidence": 0.0,
            "analyst_reports": {},
            "investment_plan": "",
            "trader_plan": "",
            "final_decision": "Analysis timeout",
            "duration_seconds": self.timeout,
            "success": False,
            "error": "Timeout"
        }

    def _create_error_result(self, symbol: str, error_msg: str) -> Dict[str, Any]:
        """创建错误结果

        Args:
            symbol: 加密货币代码
            error_msg: 错误消息

        Returns:
            错误结果字典
        """
        return {
            "signal": "HOLD",
            "score": 50,
            "confidence": 0.0,
            "analyst_reports": {},
            "investment_plan": "",
            "trader_plan": "",
            "final_decision": f"Error: {error_msg}",
            "duration_seconds": 0,
            "success": False,
            "error": error_msg
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        cache_hit_rate = 0.0
        if self.stats["total_requests"] > 0:
            cache_hit_rate = (
                self.stats["cache_hits"] / self.stats["total_requests"]
            )

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache)
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "timeouts": 0,
            "errors": 0
        }
        logger.info("Stats reset")

    def clear_cache(self) -> None:
        """清空缓存"""
        with self.cache_lock:
            self.cache.clear()
        logger.info("Cache cleared")

    def shutdown(self) -> None:
        """关闭分析器，释放资源"""
        self.executor.shutdown(wait=True)
        logger.info("AsyncLLMAnalyzer shutdown")


# ---------------------- 单例管理 ----------------------

_global_analyzer: Optional[AsyncLLMAnalyzer] = None


def get_async_analyzer(
    max_workers: int = 3,
    cache_ttl: int = 300,
    timeout: int = 120
) -> AsyncLLMAnalyzer:
    """获取全局异步分析器实例

    Args:
        max_workers: 最大并发工作线程数
        cache_ttl: 缓存TTL（秒）
        timeout: 单次分析超时时间（秒）

    Returns:
        AsyncLLMAnalyzer实例
    """
    global _global_analyzer

    if _global_analyzer is None:
        _global_analyzer = AsyncLLMAnalyzer(
            max_workers=max_workers,
            cache_ttl=cache_ttl,
            timeout=timeout
        )

    return _global_analyzer


async def analyze_crypto_async(
    symbol: str,
    date: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """异步分析加密货币（便捷函数）

    Args:
        symbol: 加密货币代码
        date: 分析日期（默认今天）
        use_cache: 是否使用缓存

    Returns:
        分析结果
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    analyzer = get_async_analyzer()
    return await analyzer.analyze_async(symbol, date, use_cache)


async def analyze_batch_async(
    symbols: List[str],
    date: Optional[str] = None,
    max_concurrent: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """批量异步分析（便捷函数）

    Args:
        symbols: 加密货币代码列表
        date: 分析日期（默认今天）
        max_concurrent: 最大并发数

    Returns:
        字典，键为symbol，值为分析结果
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    analyzer = get_async_analyzer()
    return await analyzer.analyze_batch_async(symbols, date, max_concurrent)
