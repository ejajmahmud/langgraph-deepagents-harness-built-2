"""Phase 11 直接测试脚本

直接测试各模块的功能，避免导入问题。

创建时间：2026-04-19 21:05:00
"""

import sys
import os
import asyncio
from pathlib import Path

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


async def test_metrics_collector():
    """测试指标收集器"""
    logger.info("[Test] MetricsCollector")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "metrics_collector",
            str(project_root / "monitoring" / "metrics_collector.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        collector = module.MetricsCollector()
        system_metrics = await collector.collect_system_metrics()

        logger.info(f"System metrics collected: {list(system_metrics.keys())}")
        return True, "MetricsCollector test PASSED"

    except Exception as e:
        logger.error(f"MetricsCollector test FAILED: {str(e)}")
        return False, f"MetricsCollector test FAILED: {str(e)}"


async def test_alert_manager():
    """测试告警管理器"""
    logger.info("[Test] AlertManager")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "alert_manager",
            str(project_root / "monitoring" / "alert_manager.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        manager = module.AlertManager()
        rules = manager.list_alert_rules()

        test_metrics = {'cpu_percent': 90, 'memory_percent': 85}
        alerts = await manager.evaluate_alerts(test_metrics)

        logger.info(f"Alert rules: {len(rules)}, Alerts triggered: {len(alerts)}")
        return True, "AlertManager test PASSED"

    except Exception as e:
        logger.error(f"AlertManager test FAILED: {str(e)}")
        return False, f"AlertManager test FAILED: {str(e)}"


async def test_dashboard_generator():
    """测试仪表板生成器"""
    logger.info("[Test] DashboardGenerator")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "dashboard_generator",
            str(project_root / "monitoring" / "dashboard_generator.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        generator = module.DashboardGenerator()

        dashboard_data = generator.generate_dashboard(
            metrics_data={'system': {'cpu_percent': 50}},
            alert_data={'alerts': [], 'severity_breakdown': {}},
            health_data={'overall_status': 'healthy', 'checks': {}}
        )

        html = generator.export_dashboard_html(dashboard_data)

        logger.info(f"Dashboard generated: {len(html)} chars")
        return True, "DashboardGenerator test PASSED"

    except Exception as e:
        logger.error(f"DashboardGenerator test FAILED: {str(e)}")
        return False, f"DashboardGenerator test FAILED: {str(e)}"


async def test_notification_service():
    """测试通知服务"""
    logger.info("[Test] NotificationService")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "notification_service",
            str(project_root / "monitoring" / "notification_service.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        service = module.NotificationService()
        channels = service.get_channel_status()

        notification = {
            'type': 'test',
            'title': 'TEST',
            'severity': 'INFO',
            'message': 'Test notification',
        }

        sent = await service.send_notification(notification)

        logger.info(f"Notification service: {len(channels)} channels, sent: {sent}")
        return True, "NotificationService test PASSED"

    except Exception as e:
        logger.error(f"NotificationService test FAILED: {str(e)}")
        return False, f"NotificationService test FAILED: {str(e)}"


async def test_auto_scaler():
    """测试自动扩缩容"""
    logger.info("[Test] AutoScaler")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "auto_scaler",
            str(project_root / "automation" / "auto_scaler.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        scaler = module.AutoScaler()
        policies = scaler.list_scaling_policies()

        test_metrics = {'cpu_percent': 90}
        actions = await scaler.evaluate_scaling(test_metrics)

        logger.info(f"AutoScaler: {len(policies)} policies, {len(actions)} actions")
        return True, "AutoScaler test PASSED"

    except Exception as e:
        logger.error(f"AutoScaler test FAILED: {str(e)}")
        return False, f"AutoScaler test FAILED: {str(e)}"


async def test_auto_recovery():
    """测试自动恢复"""
    logger.info("[Test] AutoRecovery")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "auto_recovery",
            str(project_root / "automation" / "auto_recovery.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        recovery = module.AutoRecovery()
        scripts = recovery.list_recovery_scripts()

        test_health_status = {
            'overall_status': 'unhealthy',
            'checks': {
                'storage': {'status': 'unhealthy'},
                'database': {'status': 'healthy'},
            }
        }

        failures = await recovery.detect_failure(test_health_status)

        logger.info(f"AutoRecovery: {len(scripts)} scripts, {len(failures)} failures detected")
        return True, "AutoRecovery test PASSED"

    except Exception as e:
        logger.error(f"AutoRecovery test FAILED: {str(e)}")
        return False, f"AutoRecovery test FAILED: {str(e)}"


async def test_backup_manager():
    """测试备份管理器"""
    logger.info("[Test] BackupManager")
    try:
        # 直接导入模块
        import importlib
        spec = importlib.util.spec_from_file_location(
            "backup_manager",
            str(project_root / "automation" / "backup_manager.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建实例并测试
        manager = module.BackupManager()

        # 创建备份
        backup_id = await manager.create_backup(backup_type='full')
        backups = await manager.list_backups()

        # 清理测试备份
        cleaned = await manager.cleanup_old_backups(keep_days=0)

        logger.info(f"BackupManager: backup created {backup_id}, {len(backups)} backups, {cleaned} cleaned")
        return True, "BackupManager test PASSED"

    except Exception as e:
        logger.error(f"BackupManager test FAILED: {str(e)}")
        return False, f"BackupManager test FAILED: {str(e)}"


async def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 70)
    logger.info("Phase 11 Direct Module Tests")
    logger.info("=" * 70)

    results = {}
    passed = 0
    failed = 0

    # 运行各项测试
    tests = [
        ("MetricsCollector", test_metrics_collector),
        ("AlertManager", test_alert_manager),
        ("DashboardGenerator", test_dashboard_generator),
        ("NotificationService", test_notification_service),
        ("AutoScaler", test_auto_scaler),
        ("AutoRecovery", test_auto_recovery),
        ("BackupManager", test_backup_manager),
    ]

    for test_name, test_func in tests:
        try:
            success, message = await test_func()
            results[test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'message': message
            }

            if success:
                passed += 1
            else:
                failed += 1

        except Exception as e:
            results[test_name] = {
                'status': 'FAILED',
                'message': f"Exception: {str(e)}"
            }
            failed += 1

    # 生成测试报告
    logger.info("\n" + "=" * 70)
    logger.info("Phase 11 Test Report")
    logger.info("=" * 70)

    total_tests = passed + failed
    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    logger.info(f"\nTotal Tests: {total_tests}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Pass Rate: {pass_rate:.1f}%")

    logger.info("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result['status'] == 'PASSED' else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
        logger.info(f"  {result['message']}")

    logger.info("=" * 70)

    return {
        'total_tests': total_tests,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'results': results,
    }


def main():
    """主函数"""
    try:
        # 运行测试
        report = asyncio.run(run_all_tests())

        # 根据测试结果返回退出码
        if report['failed'] == 0:
            print("\n[SUCCESS] All Phase 11 tests passed!")
            return 0
        else:
            print(f"\n[FAILURE] {report['failed']} test(s) failed")
            return 1

    except Exception as e:
        logger.error(f"Test execution exception: {str(e)}")
        print(f"\n[ERROR] Test execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
