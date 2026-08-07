"""Phase 12 基本测试脚本

测试系统集成模块的基本功能。

创建时间：2026-04-19 22:00:00
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_system_coordinator():
    """测试系统协调器"""
    logger.info("\n=== 测试系统协调器 ===")

    try:
        from integration.system_coordinator import SystemCoordinator

        # 创建协调器
        coordinator = SystemCoordinator()

        # 初始化
        logger.info("初始化系统协调器...")
        success = await coordinator.initialize()

        if success:
            logger.info("✅ 系统协调器初始化成功")

            # 获取系统状态
            status = coordinator.get_system_status()
            logger.info(f"系统状态: {status['system_status']}")

            return True
        else:
            logger.error("❌ 系统协调器初始化失败")
            return False

    except Exception as e:
        logger.error(f"❌ 系统协调器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_storage_integrator():
    """测试存储集成器"""
    logger.info("\n=== 测试存储集成器 ===")

    try:
        from integration.storage_integration import StorageIntegrator

        # 创建存储集成器
        integrator = StorageIntegrator()

        # 初始化
        logger.info("初始化存储集成器...")
        success = await integrator.initialize()

        if success:
            logger.info("✅ 存储集成器初始化成功")

            # 测试数据持久化
            logger.info("测试数据持久化...")
            test_metrics = {
                'system': {
                    'cpu_percent': 15.5,
                    'memory_percent': 45.2,
                    'disk_percent': 65.3,
                },
                'trading': {
                    'trades_executed': 10,
                    'total_profit': 0.0125,
                },
            }

            success = await integrator.persist_metrics(test_metrics)
            if success:
                logger.info("✅ 指标持久化成功")
            else:
                logger.error("❌ 指标持久化失败")

            # 获取统计信息
            stats = integrator.get_statistics()
            logger.info(f"存储统计: {stats}")

            # 关闭
            await integrator.close()

            return True
        else:
            logger.error("❌ 存储集成器初始化失败")
            return False

    except Exception as e:
        logger.error(f"❌ 存储集成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_strategy_optimizer():
    """测试策略优化器"""
    logger.info("\n=== 测试策略优化器 ===")

    try:
        from integration.strategy_optimizer import StrategyOptimizer

        # 创建策略优化器
        optimizer = StrategyOptimizer()

        # 初始化
        logger.info("初始化策略优化器...")
        success = await optimizer.initialize()

        if success:
            logger.info("✅ 策略优化器初始化成功")

            # 测试监控反馈处理
            logger.info("测试监控反馈处理...")
            test_metrics = {
                'system': {
                    'cpu_percent': 85.0,
                    'memory_percent': 88.0,
                    'disk_percent': 90.0,
                },
                'trading': {
                    'success_rate': 0.65,
                    'trades_executed': 20,
                    'total_profit': 0.015,
                },
            }

            test_alerts = [
                {
                    'name': 'high_cpu_usage',
                    'severity': 'WARNING',
                    'message': 'CPU使用率过高',
                    'timestamp': '2026-04-19T22:00:00',
                },
            ]

            optimizations = await optimizer.process_monitoring_feedback(
                test_metrics,
                test_alerts
            )

            logger.info(f"✅ 生成 {len(optimizations)} 个优化建议")
            for opt in optimizations[:3]:
                logger.info(f"  - {opt.get('description')} (优先级: {opt.get('priority')})")

            # 获取优化报告
            report = optimizer.get_optimization_report()
            logger.info(f"✅ 优化报告生成成功")

            return True
        else:
            logger.error("❌ 策略优化器初始化失败")
            return False

    except Exception as e:
        logger.error(f"❌ 策略优化器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """测试系统集成"""
    logger.info("\n=== 测试系统集成 ===")

    try:
        from integration.system_coordinator import get_system_coordinator
        from integration.storage_integration import get_storage_integrator
        from integration.strategy_optimizer import get_strategy_optimizer

        # 获取单例
        coordinator = get_system_coordinator()
        integrator = get_storage_integrator()
        optimizer = get_strategy_optimizer()

        # 初始化所有模块
        logger.info("初始化所有模块...")

        init_success = await asyncio.gather(
            coordinator.initialize(),
            integrator.initialize(),
            optimizer.initialize()
        )

        if all(init_success):
            logger.info("✅ 所有模块初始化成功")

            # 获取系统状态
            status = coordinator.get_system_status()
            logger.info(f"✅ 系统状态: {status['system_status']}")

            # 获取存储统计
            storage_stats = integrator.get_statistics()
            logger.info(f"✅ 存储统计: {storage_stats}")

            # 获取优化报告
            opt_report = optimizer.get_optimization_report()
            logger.info(f"✅ 优化报告: {len(opt_report.get('recent_optimizations', []))} 条记录")

            return True
        else:
            logger.error("❌ 模块初始化失败")
            return False

    except Exception as e:
        logger.error(f"❌ 系统集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始 Phase 12 基本测试...")

    # 运行所有测试
    results = []

    # 测试1: 系统协调器
    result1 = await test_system_coordinator()
    results.append(('SystemCoordinator', result1))

    # 测试2: 存储集成器
    result2 = await test_storage_integrator()
    results.append(('StorageIntegrator', result2))

    # 测试3: 策略优化器
    result3 = await test_strategy_optimizer()
    results.append(('StrategyOptimizer', result3))

    # 测试4: 系统集成
    result4 = await test_integration()
    results.append(('Integration', result4))

    # 生成测试报告
    logger.info("\n" + "="*50)
    logger.info("📊 Phase 12 测试报告")
    logger.info("="*50)

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status}: {name}")

    logger.info("="*50)
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过: {passed_tests}")
    logger.info(f"失败: {failed_tests}")
    logger.info(f"通过率: {passed_tests/total_tests*100:.1f}%")
    logger.info("="*50)

    # 返回结果
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
