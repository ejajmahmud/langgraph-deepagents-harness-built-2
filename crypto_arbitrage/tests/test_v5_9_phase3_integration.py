"""V5.9 Phase 3 集成测试

测试V5.9 Phase 3所有核心模块的集成：
1. SmartCacheOptimizer - 智能缓存优化器
2. ConcurrentController - 并发控制器
3. MemoryOptimizer - 内存优化器
4. RealTimeDashboard - 实时监控Dashboard
5. PerformanceAutoTuner - 性能自动调优系统

测试覆盖：
- 模块初始化
- 核心功能
- 模块间集成
- 性能指标
- 优化效果
"""

import asyncio
import sys
import os
import time
import unittest
from unittest.mock import Mock, patch, AsyncMock

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入测试模块
try:
    from storage.modules.smart_cache_optimizer import (
        SmartCacheOptimizer,
        create_smart_cache_optimizer,
        CacheEvictionPolicy,
        CacheEntry
    )
    from storage.modules.concurrent_controller import (
        ConcurrentController,
        create_concurrent_controller,
        TaskPriority,
        Task,
        ConcurrencyState
    )
    from storage.modules.memory_optimizer import (
        MemoryOptimizer,
        create_memory_optimizer,
        MemoryState,
        ObjectPool
    )
    from monitoring.real_time_dashboard_v5_9 import (
        RealTimeDashboard,
        create_real_time_dashboard,
        HealthStatus,
        AlertLevel,
        Alert
    )
    from monitoring.performance_auto_tuner import (
        PerformanceAutoTuner,
        create_performance_auto_tuner,
        OptimizationAction,
        OptimizationStatus,
        PerformanceGoal
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"Python路径: {sys.path}")
    raise


class TestSmartCacheOptimizer(unittest.TestCase):
    """测试智能缓存优化器"""

    def setUp(self):
        """设置测试环境"""
        self.config = {
            'max_total_size': 100,
            'eviction_policy': 'HYBRID',
            'enable_partitioning': True,
            'default_ttl': 60,
            'max_memory_mb': 50,
            'enable_smart_warmup': True
        }
        self.cache_optimizer = SmartCacheOptimizer(self.config)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.cache_optimizer)
        self.assertEqual(self.cache_optimizer.max_total_size, 100)
        self.assertEqual(self.cache_optimizer.eviction_policy, CacheEvictionPolicy.HYBRID)
        self.assertTrue(self.cache_optimizer.enable_partitioning)

    def test_cache_operations(self):
        """测试缓存操作"""
        async def test_async():
            # 设置缓存
            result = await self.cache_optimizer.set(
                key='test_key',
                value='test_value',
                ttl=60,
                partition='default'
            )
            self.assertTrue(result)

            # 获取缓存
            value = await self.cache_optimizer.get('test_key', 'default')
            self.assertEqual(value, 'test_value')

            # 删除缓存
            result = await self.cache_optimizer.remove('test_key')
            self.assertTrue(result)

            # 验证删除
            value = await self.cache_optimizer.get('test_key', 'default')
            self.assertIsNone(value)

        asyncio.run(test_async())

    def test_cache_eviction(self):
        """测试缓存淘汰"""
        async def test_async():
            # 填充缓存
            for i in range(150):
                await self.cache_optimizer.set(
                    key=f'key_{i}',
                    value=f'value_{i}',
                    ttl=60
                )

            # 验证缓存大小受限制
            cache_info = self.cache_optimizer.get_cache_info()
            self.assertLessEqual(cache_info['total_entries'], 100)

            # 验证有淘汰发生
            metrics = self.cache_optimizer.get_performance_metrics()
            self.assertGreater(metrics.total_evictions, 0)

        asyncio.run(test_async())

    def test_cache_partitions(self):
        """测试缓存分区"""
        async def test_async():
            # 测试不同分区
            await self.cache_optimizer.set('key1', 'value1', partition='high_priority')
            await self.cache_optimizer.set('key2', 'value2', partition='market_data')

            # 验证分区存在
            self.assertIn('high_priority', self.cache_optimizer._partitions)
            self.assertIn('market_data', self.cache_optimizer._partitions)

            # 验证分区统计
            metrics = self.cache_optimizer.get_performance_metrics()
            self.assertIn('high_priority', metrics.partition_metrics)
            self.assertIn('market_data', metrics.partition_metrics)

        asyncio.run(test_async())

    def test_performance_metrics(self):
        """测试性能指标"""
        async def test_async():
            # 执行一些缓存操作
            for i in range(10):
                await self.cache_optimizer.set(f'key_{i}', f'value_{i}', ttl=60)

            for i in range(10):
                await self.cache_optimizer.get(f'key_{i}')

            # 获取性能指标
            metrics = self.cache_optimizer.get_performance_metrics()

            # 验证指标
            self.assertGreater(metrics.total_hits, 0)
            self.assertGreater(metrics.hit_rate, 0)
            self.assertGreater(metrics.total_size, 0)

        asyncio.run(test_async())

    def test_optimization_suggestions(self):
        """测试优化建议"""
        suggestions = self.cache_optimizer.get_optimization_suggestions()
        self.assertIsInstance(suggestions, list)


class TestConcurrentController(unittest.TestCase):
    """测试并发控制器"""

    def setUp(self):
        """设置测试环境"""
        self.config = {
            'min_concurrent': 1,
            'max_concurrent': 5,
            'initial_concurrent': 2,
            'enable_priority_queue': True,
            'enable_dynamic_adjustment': True,
            'cpu_threshold_high': 80.0,
            'memory_threshold_high': 85.0
        }
        self.controller = ConcurrentController(self.config)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.controller)
        self.assertEqual(self.controller.current_concurrent, 2)
        self.assertEqual(self.controller.max_concurrent, 5)
        self.assertTrue(self.controller.enable_priority_queue)

    def test_task_submission(self):
        """测试任务提交"""
        async def test_async():
            await self.controller.start()

            # 创建测试任务
            async def test_task(x):
                await asyncio.sleep(0.1)
                return x * 2

            # 提交任务
            task = await self.controller.submit_task(
                test_task, 5,
                priority=TaskPriority.HIGH
            )

            self.assertIsNotNone(task)
            self.assertEqual(task.priority, TaskPriority.HIGH)

            await self.controller.stop()

        asyncio.run(test_async())

    def test_task_execution(self):
        """测试任务执行"""
        async def test_async():
            await self.controller.start()

            # 创建测试任务
            async def test_task(x):
                await asyncio.sleep(0.1)
                return x * 2

            # 执行任务
            result = await self.controller.execute_task(test_task, 5)
            self.assertEqual(result, 10)

            await self.controller.stop()

        asyncio.run(test_async())

    def test_priority_queue(self):
        """测试优先级队列"""
        async def test_async():
            await self.controller.start()

            # 创建测试任务
            async def test_task(x):
                await asyncio.sleep(0.05)
                return x

            # 提交不同优先级的任务
            await self.controller.submit_task(test_task, 1, priority=TaskPriority.LOW)
            await self.controller.submit_task(test_task, 2, priority=TaskPriority.HIGH)
            await self.controller.submit_task(test_task, 3, priority=TaskPriority.NORMAL)

            # 等待任务完成
            await asyncio.sleep(0.5)

            # 验证任务执行
            metrics = self.controller.get_metrics()
            self.assertEqual(metrics.completed_tasks, 3)

            await self.controller.stop()

        asyncio.run(test_async())

    def test_concurrency_metrics(self):
        """测试并发指标"""
        async def test_async():
            await self.controller.start()

            # 创建测试任务
            async def test_task(x):
                await asyncio.sleep(0.1)
                return x

            # 执行多个任务
            for i in range(5):
                await self.controller.execute_task(test_task, i)

            # 获取指标
            metrics = self.controller.get_metrics()

            # 验证指标
            self.assertEqual(metrics.total_tasks, 5)
            self.assertEqual(metrics.completed_tasks, 5)
            self.assertEqual(metrics.failed_tasks, 0)

            await self.controller.stop()

        asyncio.run(test_async())


class TestMemoryOptimizer(unittest.TestCase):
    """测试内存优化器"""

    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enable_object_pool': True,
            'enable_leak_detection': False,  # 禁用以避免tracemalloc问题
            'enable_gc_optimization': True,
            'memory_warning_threshold': 256,
            'memory_critical_threshold': 512
        }
        self.memory_optimizer = MemoryOptimizer(self.config)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.memory_optimizer)
        self.assertTrue(self.memory_optimizer.enable_object_pool)
        self.assertTrue(self.memory_optimizer.enable_gc_optimization)

    def test_object_pool(self):
        """测试对象池"""
        async def test_async():
            # 创建对象池
            def create_dict():
                return {}

            def reset_dict(d):
                d.clear()

            pool = self.memory_optimizer.register_object_pool(
                name='dict_pool',
                object_type=dict,
                factory=create_dict,
                reset_func=reset_dict,
                max_size=10
            )

            self.assertIsNotNone(pool)

            # 获取对象
            obj1 = await pool.acquire()
            obj2 = await pool.acquire()

            self.assertIsNotNone(obj1)
            self.assertIsNotNone(obj2)

            # 释放对象
            await pool.release(obj1)
            await pool.release(obj2)

            # 验证对象池统计
            stats = pool.get_stats()
            self.assertGreater(stats.total_created, 0)

        asyncio.run(test_async())

    def test_gc_optimization(self):
        """测试GC优化"""
        async def test_async():
            # 执行GC优化
            result = await self.memory_optimizer.optimize_gc()

            self.assertEqual(result['status'], 'completed')
            self.assertGreaterEqual(result['collected_objects'], 0)

        asyncio.run(test_async())

    def test_history_compression(self):
        """测试历史记录压缩"""
        async def test_async():
            # 创建测试历史
            history = [
                {'data': f'item_{i}', 'timestamp': time.time() - i * 60}
                for i in range(100)
            ]

            # 压缩历史
            compressed = await self.memory_optimizer.compress_history(
                history,
                keep_last=10
            )

            # 验证压缩效果
            self.assertLess(len(compressed), len(history))

        asyncio.run(test_async())

    def test_memory_metrics(self):
        """测试内存指标"""
        async def test_async():
            await self.memory_optimizer.start()

            # 等待一些监控数据
            await asyncio.sleep(1)

            # 获取指标
            metrics = self.memory_optimizer.get_metrics()

            # 验证指标
            self.assertIsNotNone(metrics)
            self.assertGreaterEqual(metrics.avg_memory_mb, 0)

            await self.memory_optimizer.stop()

        asyncio.run(test_async())


class TestRealTimeDashboard(unittest.TestCase):
    """测试实时监控Dashboard"""

    def setUp(self):
        """设置测试环境"""
        self.config = {
            'update_interval': 1,
            'max_history': 10,
            'enable_alerts': True,
            'alert_thresholds': {
                'cpu_warning': 50.0,
                'cpu_critical': 80.0,
                'memory_warning_mb': 200,
                'memory_critical_mb': 400,
                'cache_hit_rate_warning': 0.7
            }
        }
        self.dashboard = RealTimeDashboard(self.config)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.dashboard)
        self.assertTrue(self.dashboard.enable_alerts)
        self.assertEqual(self.dashboard.update_interval, 1)

    def test_dashboard_commands(self):
        """测试Dashboard命令"""
        async def test_async():
            # 测试help命令
            result = await self.dashboard.execute_command('help')
            self.assertIn('可用命令', result)

            # 测试status命令
            result = await self.dashboard.execute_command('status')
            self.assertIn('系统状态', result)

            # 测试metrics命令
            result = await self.dashboard.execute_command('metrics')
            self.assertIn('性能指标', result)

        asyncio.run(test_async())

    def test_alert_system(self):
        """测试告警系统"""
        # 创建告警
        self.dashboard._create_alert(
            AlertLevel.WARNING,
            "测试告警",
            "TEST"
        )

        # 验证告警创建
        self.assertEqual(len(self.dashboard._alerts), 1)

        # 测试alerts命令
        async def test_async():
            result = await self.dashboard.execute_command('alerts')
            self.assertIn('告警列表', result)

        asyncio.run(test_async())

    def test_dashboard_display(self):
        """测试Dashboard显示"""
        display = self.dashboard.get_dashboard_display()

        # 验证显示内容
        self.assertIn('V5.9 实时监控Dashboard', display)
        self.assertIn('系统状态', display)
        self.assertIn('资源使用', display)


class TestPerformanceAutoTuner(unittest.TestCase):
    """测试性能自动调优系统"""

    def setUp(self):
        """设置测试环境"""
        self.config = {
            'tuning_interval': 30,
            'enable_auto_tuning': False,  # 禁用自动调优以避免后台任务
            'max_concurrent_actions': 2,
            'action_timeout': 30
        }
        self.auto_tuner = PerformanceAutoTuner(self.config)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.auto_tuner)
        self.assertFalse(self.auto_tuner.enable_auto_tuning)
        self.assertEqual(len(self.auto_tuner.performance_goals), 5)

    def test_performance_goals(self):
        """测试性能目标"""
        goals = self.auto_tuner.get_performance_goals()

        # 验证目标存在
        self.assertIn('cache_hit_rate', goals)
        self.assertIn('response_time', goals)
        self.assertIn('concurrent_capability', goals)

        # 验证目标属性
        cache_goal = goals['cache_hit_rate']
        self.assertEqual(cache_goal.target_value, 0.95)
        self.assertEqual(cache_goal.priority, 8)

    def test_optimization_report(self):
        """测试优化报告"""
        report = self.auto_tuner.generate_optimization_report(period_seconds=3600)

        # 验证报告结构
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report.actions_executed, 0)
        self.assertIsInstance(report.goals_achieved, list)
        self.assertIsInstance(report.recommendations, list)

    def test_component_integration(self):
        """测试组件集成"""
        # 设置Mock组件
        mock_cache = Mock()
        mock_controller = Mock()
        mock_memory = Mock()
        mock_dashboard = Mock()

        # 设置组件
        self.auto_tuner.set_cache_optimizer(mock_cache)
        self.auto_tuner.set_concurrent_controller(mock_controller)
        self.auto_tuner.set_memory_optimizer(mock_memory)
        self.auto_tuner.set_dashboard(mock_dashboard)

        # 验证组件设置
        self.assertEqual(self.auto_tuner.cache_optimizer, mock_cache)
        self.assertEqual(self.auto_tuner.concurrent_controller, mock_controller)


class TestV59Phase3Integration(unittest.TestCase):
    """测试V5.9 Phase 3完整集成"""

    def test_module_integration(self):
        """测试模块集成"""
        # 创建所有模块
        cache_config = {
            'max_total_size': 100,
            'eviction_policy': 'HYBRID',
            'enable_partitioning': True
        }
        cache_optimizer = SmartCacheOptimizer(cache_config)

        controller_config = {
            'min_concurrent': 1,
            'max_concurrent': 5,
            'initial_concurrent': 2
        }
        concurrent_controller = ConcurrentController(controller_config)

        memory_config = {
            'enable_object_pool': True,
            'enable_leak_detection': False,
            'enable_gc_optimization': True
        }
        memory_optimizer = MemoryOptimizer(memory_config)

        dashboard_config = {
            'update_interval': 1,
            'enable_alerts': True
        }
        dashboard = RealTimeDashboard(dashboard_config)

        tuner_config = {
            'tuning_interval': 30,
            'enable_auto_tuning': False
        }
        auto_tuner = PerformanceAutoTuner(tuner_config)

        # 设置集成
        dashboard.set_cache_optimizer(cache_optimizer)
        dashboard.set_concurrent_controller(concurrent_controller)
        dashboard.set_memory_optimizer(memory_optimizer)

        auto_tuner.set_cache_optimizer(cache_optimizer)
        auto_tuner.set_concurrent_controller(concurrent_controller)
        auto_tuner.set_memory_optimizer(memory_optimizer)
        auto_tuner.set_dashboard(dashboard)

        # 验证集成
        self.assertEqual(dashboard.cache_optimizer, cache_optimizer)
        self.assertEqual(auto_tuner.dashboard, dashboard)

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        async def test_async():
            # 创建模块
            cache_optimizer = SmartCacheOptimizer({
                'max_total_size': 100,
                'eviction_policy': 'HYBRID'
            })

            dashboard = RealTimeDashboard({
                'update_interval': 1,
                'enable_alerts': False
            })

            # 设置集成
            dashboard.set_cache_optimizer(cache_optimizer)

            # 启动Dashboard
            await dashboard.start()

            # 执行缓存操作
            await cache_optimizer.set('test_key', 'test_value', ttl=60)
            value = await cache_optimizer.get('test_key')
            self.assertEqual(value, 'test_value')

            # 等待监控
            await asyncio.sleep(2)

            # 获取Dashboard显示
            display = dashboard.get_dashboard_display()
            self.assertIn('V5.9 实时监控Dashboard', display)

            # 停止Dashboard
            await dashboard.stop()

        asyncio.run(test_async())

    def test_performance_validation(self):
        """测试性能验证"""
        async def test_async():
            # 创建缓存优化器
            cache_optimizer = SmartCacheOptimizer({
                'max_total_size': 200,
                'eviction_policy': 'HYBRID',
                'enable_partitioning': True,
                'enable_smart_warmup': True
            })

            # 执行大量缓存操作
            start_time = time.time()

            for i in range(1000):
                await cache_optimizer.set(f'key_{i}', f'value_{i}', ttl=60)

            set_time = time.time() - start_time

            # 执行获取操作
            start_time = time.time()

            for i in range(1000):
                await cache_optimizer.get(f'key_{i}')

            get_time = time.time() - start_time

            # 验证性能
            cache_info = cache_optimizer.get_cache_info()
            metrics = cache_optimizer.get_performance_metrics()

            # 性能断言
            self.assertLess(set_time, 10.0, "设置操作应该快速")
            self.assertLess(get_time, 5.0, "获取操作应该快速")
            self.assertGreater(metrics.hit_rate, 0.8, "缓存命中率应该高")

        asyncio.run(test_async())


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSmartCacheOptimizer))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConcurrentController))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMemoryOptimizer))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRealTimeDashboard))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPerformanceAutoTuner))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestV59Phase3Integration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出结果
    print(f"\n{'='*60}")
    print(f"V5.9 Phase 3 集成测试结果")
    print(f"{'='*60}")
    print(f"测试总数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"通过率: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print(f"{'='*60}")

    return result


if __name__ == '__main__':
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
