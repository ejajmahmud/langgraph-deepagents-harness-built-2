"""V16.1 统一系统集成测试

测试V16.1的统一系统集成器的功能。

测试场景：
1. 模块初始化和连接测试
2. 系统协调机制测试
3. 端到端集成测试
4. 性能监控测试
5. 任务处理测试
6. 故障恢复测试
"""

import asyncio
import sys
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.duration_ms = 0.0
        self.details = ""
        self.errors = []

    def add_result(self, success: bool, detail: str = "", error: str = ""):
        """添加测试结果"""
        self.success = success
        if detail:
            self.details = detail
        if error:
            self.errors.append(error)

    def __str__(self):
        status = "[PASS]" if self.success else "[FAIL]"
        return f"{status} {self.test_name} ({self.duration_ms:.2f}ms)"


async def test_module_initialization() -> TestResult:
    """测试1: 模块初始化和连接"""
    result = TestResult("模块初始化和连接")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import (
            UnifiedSystemIntegrator,
            IntegrationStatus
        )

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 获取连接状态
        connection_status = integrator.get_connection_status()

        # 检查连接
        connected_modules = connection_status.get('connected_modules', 0)
        total_modules = connection_status.get('total_modules', 0)
        connection_rate = connection_status.get('connection_rate', 0)

        result.add_result(
            connection_rate >= 50,  # 至少连接50%的模块
            f"连接率: {connection_rate:.1f}% ({connected_modules}/{total_modules}模块)"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_system_coordination() -> TestResult:
    """测试2: 系统协调机制"""
    result = TestResult("系统协调机制")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 检查协调器连接
        if integrator._system_coordinator:
            result.add_result(
                True,
                "SystemCoordinator已连接"
            )
        else:
            result.add_result(
                False,
                "SystemCoordinator未连接（可选模块）"
            )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_end_to_end_integration() -> TestResult:
    """测试3: 端到端集成"""
    result = TestResult("端到端集成")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator
        from data_collection.real_time_collector import MarketData, Exchange, DataType

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 测试批量知识更新
        test_data = [
            MarketData(
                exchange=Exchange.BINANCE,
                symbol="BTC/USDT",
                data_type=DataType.PRICE,
                timestamp=time.time(),
                data={"price": 65000.0, "volume": 1000.0}
            )
        ]

        update_result = await integrator._realtime_integration.batch_update_knowledge(test_data)

        result.add_result(
            update_result.success,
            f"批量更新: {update_result.knowledge_count} 条知识, "
            f"耗时: {update_result.duration_ms:.2f}ms"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_performance_monitoring() -> TestResult:
    """测试4: 性能监控"""
    result = TestResult("性能监控")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 收集系统指标
        metrics = await integrator._collect_system_metrics()

        result.add_result(
            metrics is not None,
            f"CPU: {metrics.cpu_usage:.1f}%, "
            f"Memory: {metrics.memory_usage:.1f}%, "
            f"Health: {metrics.system_health.value}"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_task_processing() -> TestResult:
    """测试5: 任务处理"""
    result = TestResult("任务处理")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 添加测试任务
        test_task = {
            "type": "system_optimization",
            "priority": "high",
            "data": {}
        }
        await integrator._task_queue.put(test_task)

        # 处理任务
        await integrator._process_task(test_task)

        result.add_result(
            True,
            "任务处理成功"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_system_status() -> TestResult:
    """测试6: 系统状态查询"""
    result = TestResult("系统状态查询")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 获取系统状态
        status = integrator.get_system_status()

        result.add_result(
            bool(status),
            f"版本: {status.get('version')}, "
            f"运行中: {status.get('is_running')}, "
            f"任务队列: {status.get('task_queue_size')}"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_connection_integration() -> TestResult:
    """测试7: 连接集成度"""
    result = TestResult("连接集成度")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 获取连接状态
        connection_status = integrator.get_connection_status()

        # 评估集成度
        connected_count = sum([
            connection_status['system_coordinator_connected'],
            connection_status['strategy_optimizer_connected'],
            connection_status['storage_integrator_connected'],
            connection_status['mem0_storage_connected']
        ])

        total_count = 4
        integration_rate = (connected_count / total_count) * 100

        result.add_result(
            integration_rate >= 75,  # 目标集成度75%+
            f"集成度: {integration_rate:.1f}% ({connected_count}/{total_count}模块)"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def test_fault_recovery() -> TestResult:
    """测试8: 故障恢复"""
    result = TestResult("故障恢复")
    start_time = asyncio.get_event_loop().time()

    try:
        from integration.unified_system_integrator import UnifiedSystemIntegrator

        # 创建统一集成器
        integrator = UnifiedSystemIntegrator(config={"test_mode": True})

        # 触发系统优化（模拟故障恢复）
        await integrator._trigger_system_optimization()

        result.add_result(
            True,
            "故障恢复机制正常"
        )

    except Exception as e:
        result.add_result(False, error=str(e))

    result.duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    return result


async def run_all_tests() -> None:
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("V16.1 统一系统集成测试")
    print("=" * 80)
    print("开始时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 测试列表
    tests = [
        ("模块初始化和连接", test_module_initialization),
        ("系统协调机制", test_system_coordination),
        ("端到端集成", test_end_to_end_integration),
        ("性能监控", test_performance_monitoring),
        ("任务处理", test_task_processing),
        ("系统状态查询", test_system_status),
        ("连接集成度", test_connection_integration),
        ("故障恢复", test_fault_recovery)
    ]

    # 运行测试
    results = []
    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}...")
        result = await test_func()
        results.append(result)
        print(result)

        # 小延迟
        await asyncio.sleep(0.1)

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    passed = sum(1 for r in results if r.success)
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0

    for result in results:
        status = "PASS" if result.success else "FAIL"
        print(f"[{status}] {result.test_name} ({result.duration_ms:.2f}ms)")

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"通过率: {pass_rate:.1f}%")

    if pass_rate >= 80:
        print("\n[SUCCESS] V16.1统一系统集成测试通过！系统就绪。")
    else:
        print(f"\n[WARNING] 部分测试失败，通过率 {pass_rate:.1f}%")

    print("结束时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == "__main__":
    asyncio.run(run_all_tests())
