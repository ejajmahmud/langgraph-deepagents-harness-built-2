"""Performance Optimizer V3.6
Advanced system performance optimization with intelligent caching and async processing improvements.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from functools import wraps
from collections import defaultdict, OrderedDict
import hashlib
import json

logger = logging.getLogger(__name__)


class PerformanceOptimizerV36:
    """Performance Optimizer V3.6

    Advanced optimization features:
    - Intelligent multi-level caching system
    - Async operation batching and parallelization
    - Resource-aware execution scheduling
    - Performance monitoring and profiling
    - Automatic bottleneck detection
    - Dynamic optimization strategies
    """

    def __init__(self, config: Dict = None):
        """Initialize Performance Optimizer V3.6

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Multi-level cache system
        self.l1_cache = OrderedDict()  # Memory cache (fastest)
        self.l2_cache = {}  # Process cache (medium)
        self.l3_cache_enabled = self.config.get('enable_l3_cache', False)  # Disk cache (slowest)

        # Cache configuration
        self.l1_max_size = self.config.get('l1_cache_size', 1000)
        self.l1_ttl = self.config.get('l1_ttl_seconds', 60)
        self.l2_ttl = self.config.get('l2_ttl_seconds', 300)

        # Cache statistics
        self.cache_stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'evictions': 0,
            'total_requests': 0
        }

        # Async operation queues
        self.operation_queue = asyncio.Queue()
        self.batch_size = self.config.get('batch_size', 10)
        self.batch_timeout = self.config.get('batch_timeout_seconds', 1.0)

        # Performance monitoring
        self.performance_metrics = defaultdict(list)
        self.bottleneck_threshold = self.config.get('bottleneck_threshold_seconds', 1.0)
        self.detected_bottlenecks = []

        # Resource monitoring
        self.resource_usage = {
            'memory_usage': [],
            'cpu_usage': [],
            'io_operations': []
        }

        # Optimization strategies
        self.optimization_strategies = {
            'caching': self._optimize_caching,
            'batching': self._optimize_batching,
            'parallelization': self._optimize_parallelization,
            'resource_management': self._optimize_resources
        }

        # Background processing
        self._processing = False
        self._processor_task = None

        logger.info("Performance Optimizer V3.6 initialized")

    async def cache_result(
        self,
        cache_key: str,
        result: Any,
        ttl: int = None,
        cache_level: str = 'l1'
    ) -> None:
        """Cache a result with specified TTL

        Args:
            cache_key: Unique identifier for the cached result
            result: Result to cache
            ttl: Time to live in seconds (None for default)
            cache_level: Cache level ('l1', 'l2', 'all')
        """
        try:
            cache_entry = {
                'result': result,
                'timestamp': time.time(),
                'ttl': ttl or self._get_default_ttl(cache_level)
            }

            if cache_level in ('l1', 'all'):
                await self._add_to_l1_cache(cache_key, cache_entry)

            if cache_level in ('l2', 'all'):
                await self._add_to_l2_cache(cache_key, cache_entry)

        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Retrieve cached result if available and valid

        Args:
            cache_key: Unique identifier for the cached result

        Returns:
            Cached result if available and valid, None otherwise
        """
        self.cache_stats['total_requests'] += 1

        # Try L1 cache first
        l1_result = await self._get_from_l1_cache(cache_key)
        if l1_result is not None:
            self.cache_stats['l1_hits'] += 1
            return l1_result

        self.cache_stats['l1_misses'] += 1

        # Try L2 cache
        l2_result = await self._get_from_l2_cache(cache_key)
        if l2_result is not None:
            self.cache_stats['l2_hits'] += 1
            # Promote to L1 cache
            await self._add_to_l1_cache(cache_key, {
                'result': l2_result,
                'timestamp': time.time(),
                'ttl': self.l1_ttl
            })
            return l2_result

        self.cache_stats['l2_misses'] += 1
        return None

    async def _add_to_l1_cache(self, cache_key: str, cache_entry: Dict) -> None:
        """Add entry to L1 cache with eviction policy"""
        # Evict old entries if cache is full
        while len(self.l1_cache) >= self.l1_max_size:
            self.l1_cache.popitem(last=False)
            self.cache_stats['evictions'] += 1

        # Remove expired entries
        self._cleanup_l1_cache()

        # Add new entry
        self.l1_cache[cache_key] = cache_entry

    async def _get_from_l1_cache(self, cache_key: str) -> Optional[Any]:
        """Get entry from L1 cache if valid"""
        if cache_key not in self.l1_cache:
            return None

        cache_entry = self.l1_cache[cache_key]

        # Check if expired
        if time.time() - cache_entry['timestamp'] > cache_entry['ttl']:
            del self.l1_cache[cache_key]
            return None

        # Move to end (most recently used)
        self.l1_cache.move_to_end(cache_key)

        return cache_entry['result']

    def _cleanup_l1_cache(self) -> None:
        """Remove expired entries from L1 cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.l1_cache.items()
            if current_time - entry['timestamp'] > entry['ttl']
        ]

        for key in expired_keys:
            del self.l1_cache[key]
            self.cache_stats['evictions'] += 1

    async def _add_to_l2_cache(self, cache_key: str, cache_entry: Dict) -> None:
        """Add entry to L2 cache"""
        self.l2_cache[cache_key] = cache_entry

    async def _get_from_l2_cache(self, cache_key: str) -> Optional[Any]:
        """Get entry from L2 cache if valid"""
        if cache_key not in self.l2_cache:
            return None

        cache_entry = self.l2_cache[cache_key]

        # Check if expired
        if time.time() - cache_entry['timestamp'] > cache_entry['ttl']:
            del self.l2_cache[cache_key]
            return None

        return cache_entry['result']

    def _get_default_ttl(self, cache_level: str) -> int:
        """Get default TTL for cache level"""
        return {
            'l1': self.l1_ttl,
            'l2': self.l2_ttl
        }.get(cache_level, 60)

    async def execute_with_caching(
        self,
        cache_key: str,
        func: Callable,
        *args,
        ttl: int = None,
        cache_level: str = 'l1',
        **kwargs
    ) -> Any:
        """Execute function with intelligent caching

        Args:
            cache_key: Cache key for the result
            func: Function to execute
            *args: Function arguments
            ttl: Time to live for cache
            cache_level: Cache level to use
            **kwargs: Function keyword arguments

        Returns:
            Function result (cached or fresh)
        """
        # Try to get cached result
        cached_result = await self.get_cached_result(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached_result

        # Execute function and cache result
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time

        # Only cache if execution time is significant
        if execution_time > 0.1:  # 100ms threshold
            await self.cache_result(cache_key, result, ttl, cache_level)
            logger.debug(f"Cached result for key: {cache_key} (executed in {execution_time:.3f}s)")

        return result

    async def batch_execute(
        self,
        operations: List[Tuple[Callable, tuple, dict]],
        max_parallel: int = 5
    ) -> List[Any]:
        """Execute multiple operations in parallel batches

        Args:
            operations: List of (function, args, kwargs) tuples
            max_parallel: Maximum parallel operations

        Returns:
            List of results in same order as operations
        """
        results = []

        # Process in batches
        for i in range(0, len(operations), max_parallel):
            batch = operations[i:i + max_parallel]

            # Execute batch in parallel
            batch_results = await asyncio.gather(
                *[func(*args, **kwargs) for func, args, kwargs in batch],
                return_exceptions=True
            )

            # Handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Operation {i+j} failed: {result}")
                    results.append(None)
                else:
                    results.append(result)

        return results

    async def execute_with_profiling(
        self,
        operation_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with performance profiling

        Args:
            operation_name: Name of the operation for profiling
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Record performance metrics
            self.performance_metrics[operation_name].append(execution_time)

            # Check for bottlenecks
            if execution_time > self.bottleneck_threshold:
                bottleneck = {
                    'operation': operation_name,
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
                self.detected_bottlenecks.append(bottleneck)
                logger.warning(f"Performance bottleneck detected: {operation_name} took {execution_time:.3f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Operation {operation_name} failed after {execution_time:.3f}s: {e}")
            raise

    def cache_decorator(self, ttl: int = None, cache_level: str = 'l1'):
        """Decorator for caching function results

        Args:
            ttl: Time to live in seconds
            cache_level: Cache level to use

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)

                # Execute with caching
                return await self.execute_with_caching(
                    cache_key,
                    func,
                    *args,
                    ttl=ttl,
                    cache_level=cache_level,
                    **kwargs
                )
            return wrapper
        return decorator

    def profile_decorator(self, operation_name: str = None):
        """Decorator for profiling function performance

        Args:
            operation_name: Name for profiling (defaults to function name)

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                op_name = operation_name or func.__name__
                return await self.execute_with_profiling(op_name, func, *args, **kwargs)
            return wrapper
        return decorator

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function arguments"""
        # Create a hash of the function name and arguments
        key_data = {
            'function': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"{func_name}:{key_hash}"

    async def optimize_async_operations(
        self,
        operations: List[Callable],
        resource_constraints: Dict = None
    ) -> List[Any]:
        """Optimize async operations with resource-aware scheduling

        Args:
            operations: List of async operations to execute
            resource_constraints: Resource constraints (memory, cpu, etc.)

        Returns:
            List of results
        """
        if not operations:
            return []

        # Analyze operations for dependencies and resource needs
        operation_info = []
        for i, op in enumerate(operations):
            info = {
                'index': i,
                'operation': op,
                'estimated_resources': self._estimate_resources(op),
                'dependencies': self._find_dependencies(op, operations)
            }
            operation_info.append(info)

        # Schedule operations based on resource availability
        execution_order = self._schedule_operations(operation_info, resource_constraints)

        # Execute operations in optimal order
        results = []
        for op_info in execution_order:
            try:
                result = await op_info['operation']()
                results.append((op_info['index'], result))
            except Exception as e:
                logger.error(f"Operation {op_info['index']} failed: {e}")
                results.append((op_info['index'], None))

        # Sort results by original index
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]

    def _estimate_resources(self, operation: Callable) -> Dict:
        """Estimate resource requirements for operation"""
        # In production, this would analyze the operation more carefully
        return {
            'memory': 'medium',
            'cpu': 'low',
            'io': 'low'
        }

    def _find_dependencies(self, operation: Callable, all_operations: List[Callable]) -> List[int]:
        """Find dependencies between operations"""
        # In production, this would analyze operation dependencies
        return []

    def _schedule_operations(
        self,
        operation_info: List[Dict],
        resource_constraints: Dict
    ) -> List[Dict]:
        """Schedule operations considering resource constraints"""
        # Simple scheduling - execute in order
        return operation_info

    async def _optimize_caching(self) -> Dict:
        """Optimize caching strategy"""
        recommendations = []

        # Analyze cache hit rates
        total_requests = self.cache_stats['total_requests']
        if total_requests > 0:
            l1_hit_rate = self.cache_stats['l1_hits'] / total_requests
            l2_hit_rate = self.cache_stats['l2_hits'] / total_requests

            if l1_hit_rate < 0.5:
                recommendations.append({
                    'type': 'cache_size',
                    'message': 'Consider increasing L1 cache size',
                    'current_hit_rate': l1_hit_rate,
                    'suggested_size': self.l1_max_size * 2
                })

            if l2_hit_rate < 0.3:
                recommendations.append({
                    'type': 'cache_ttl',
                    'message': 'Consider increasing L2 cache TTL',
                    'current_hit_rate': l2_hit_rate,
                    'suggested_ttl': self.l2_ttl * 2
                })

        return {'recommendations': recommendations}

    async def _optimize_batching(self) -> Dict:
        """Optimize batching strategy"""
        return {'recommendations': []}

    async def _optimize_parallelization(self) -> Dict:
        """Optimize parallelization strategy"""
        return {'recommendations': []}

    async def _optimize_resources(self) -> Dict:
        """Optimize resource usage"""
        return {'recommendations': []}

    async def analyze_performance(self) -> Dict:
        """Analyze system performance and provide optimization recommendations

        Returns:
            Performance analysis with recommendations
        """
        analysis = {
            'cache_performance': self._analyze_cache_performance(),
            'operation_performance': self._analyze_operation_performance(),
            'bottlenecks': self._analyze_bottlenecks(),
            'recommendations': []
        }

        # Generate optimization recommendations
        for strategy_name, strategy_func in self.optimization_strategies.items():
            try:
                strategy_result = await strategy_func()
                if strategy_result.get('recommendations'):
                    analysis['recommendations'].extend(strategy_result['recommendations'])
            except Exception as e:
                logger.warning(f"Optimization strategy {strategy_name} failed: {e}")

        return analysis

    def _analyze_cache_performance(self) -> Dict:
        """Analyze cache performance"""
        total_requests = self.cache_stats['total_requests']

        if total_requests == 0:
            return {
                'status': 'no_data',
                'message': 'No cache requests recorded'
            }

        l1_hit_rate = self.cache_stats['l1_hits'] / total_requests
        l2_hit_rate = self.cache_stats['l2_hits'] / total_requests
        overall_hit_rate = l1_hit_rate + l2_hit_rate

        return {
            'status': 'healthy' if overall_hit_rate > 0.7 else 'needs_improvement',
            'overall_hit_rate': overall_hit_rate,
            'l1_hit_rate': l1_hit_rate,
            'l2_hit_rate': l2_hit_rate,
            'evictions': self.cache_stats['evictions'],
            'total_requests': total_requests
        }

    def _analyze_operation_performance(self) -> Dict:
        """Analyze operation performance"""
        performance_summary = {}

        for operation_name, timings in self.performance_metrics.items():
            if not timings:
                continue

            timings_sorted = sorted(timings)
            performance_summary[operation_name] = {
                'count': len(timings),
                'avg_time': sum(timings) / len(timings),
                'min_time': timings_sorted[0],
                'max_time': timings_sorted[-1],
                'median_time': timings_sorted[len(timings) // 2],
                'p95_time': timings_sorted[int(len(timings) * 0.95)] if len(timings) >= 20 else timings_sorted[-1]
            }

        return performance_summary

    def _analyze_bottlenecks(self) -> Dict:
        """Analyze detected bottlenecks"""
        if not self.detected_bottlenecks:
            return {
                'status': 'no_bottlenecks',
                'message': 'No significant bottlenecks detected'
            }

        # Group bottlenecks by operation
        bottleneck_groups = defaultdict(list)
        for bottleneck in self.detected_bottlenecks:
            bottleneck_groups[bottleneck['operation']].append(bottleneck)

        # Analyze each group
        analysis = {}
        for operation, bottlenecks in bottleneck_groups.items():
            execution_times = [b['execution_time'] for b in bottlenecks]
            analysis[operation] = {
                'count': len(bottlenecks),
                'avg_time': sum(execution_times) / len(execution_times),
                'max_time': max(execution_times),
                'latest_occurrence': bottlenecks[-1]['timestamp']
            }

        return {
            'status': 'bottlenecks_detected',
            'count': len(self.detected_bottlenecks),
            'operations': analysis
        }

    def get_cache_statistics(self) -> Dict:
        """Get cache statistics"""
        return {
            'l1_cache': {
                'size': len(self.l1_cache),
                'max_size': self.l1_max_size,
                'hits': self.cache_stats['l1_hits'],
                'misses': self.cache_stats['l1_misses']
            },
            'l2_cache': {
                'size': len(self.l2_cache),
                'hits': self.cache_stats['l2_hits'],
                'misses': self.cache_stats['l2_misses']
            },
            'overall': {
                'total_requests': self.cache_stats['total_requests'],
                'evictions': self.cache_stats['evictions']
            }
        }

    def clear_cache(self, cache_level: str = 'all') -> None:
        """Clear specified cache level

        Args:
            cache_level: Cache level to clear ('l1', 'l2', 'all')
        """
        if cache_level in ('l1', 'all'):
            self.l1_cache.clear()
            logger.info("L1 cache cleared")

        if cache_level in ('l2', 'all'):
            self.l2_cache.clear()
            logger.info("L2 cache cleared")

        if cache_level == 'all':
            self.cache_stats = {
                'l1_hits': 0,
                'l1_misses': 0,
                'l2_hits': 0,
                'l2_misses': 0,
                'evictions': 0,
                'total_requests': 0
            }
            logger.info("Cache statistics reset")

    async def start_background_processing(self) -> None:
        """Start background optimization processing"""
        if not self._processing:
            self._processing = True
            self._processor_task = asyncio.create_task(self._process_operations())
            logger.info("Background processing started")

    async def stop_background_processing(self) -> None:
        """Stop background optimization processing"""
        if self._processing:
            self._processing = False
            if self._processor_task:
                self._processor_task.cancel()
                try:
                    await self._processor_task
                except asyncio.CancelledError:
                    pass
            logger.info("Background processing stopped")

    async def _process_operations(self) -> None:
        """Process queued operations in background"""
        while self._processing:
            try:
                # Wait for operations or timeout
                operation = await asyncio.wait_for(
                    self.operation_queue.get(),
                    timeout=self.batch_timeout
                )

                # Process operation
                # In production, implement actual operation processing
                await asyncio.sleep(0.01)  # Simulate processing

            except asyncio.TimeoutError:
                # Batch timeout reached, process accumulated operations
                continue
            except Exception as e:
                logger.error(f"Error processing operation: {e}")

    def is_processing(self) -> bool:
        """Check if background processing is active"""
        return self._processing