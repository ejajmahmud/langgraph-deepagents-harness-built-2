"""Phase 11 简化验证脚本

快速验证Phase 11核心模块功能。

创建时间：2026-04-19 21:00:00
"""

import sys
import os
from pathlib import Path

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

import asyncio
import logging

# 配置日志（避免中文乱码）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


async def test_phase11_basic():
    """Phase 11 基础功能测试"""

    logger.info("=" * 70)
    logger.info("Phase 11 基础功能测试开始")
    logger.info("=" * 70)

    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'details': {}
    }

    # 测试1: 模块导入
    logger.info("\n[Test 1/7] Module Import Test")
    results['total'] += 1
    try:
        from monitoring import MetricsCollector, AlertManager, NotificationService
        from automation import AutoScaler, AutoRecovery, BackupManager

        results['details']['import'] = 'PASSED'
        results['passed'] += 1
        logger.info("✅ Module Import: PASSED")
    except Exception as e:
        results['details']['import'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ Module Import: FAILED - {str(e)}")

    # 测试2: 指标收集器
    logger.info("\n[Test 2/7] MetricsCollector Test")
    results['total'] += 1
    try:
        from monitoring import MetricsCollector
        collector = MetricsCollector()

        # 收集系统指标
        system_metrics = await collector.collect_system_metrics()

        # 收集所有指标
        all_metrics = await collector.collect_all_metrics()

        # 获取最新指标
        latest = collector.get_latest_metrics()

        # 获取指标历史
        history = collector.get_metrics_history('system', limit=10)

        results['details']['metrics'] = 'PASSED'
        results['passed'] += 1
        logger.info(f"✅ MetricsCollector: PASSED (metrics: {len(all_metrics)}, history: {len(history)})")
    except Exception as e:
        results['details']['metrics'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ MetricsCollector: FAILED - {str(e)}")

    # 测试3: 告警管理器
    logger.info("\n[Test 3/7] AlertManager Test")
    results['total'] += 1
    try:
        from monitoring import AlertManager
        manager = AlertManager()

        # 测试默认规则
        rules = manager.list_alert_rules()

        # 测试告警评估
        test_metrics = {'cpu_percent': 90, 'memory_percent': 85}
        alerts = await manager.evaluate_alerts(test_metrics)

        # 测试告警历史
        history = manager.get_alert_history(limit=10)

        results['details']['alerts'] = 'PASSED'
        results['passed'] += 1
        logger.info(f"✅ AlertManager: PASSED (rules: {len(rules)}, alerts triggered: {len(alerts)})")
    except Exception as e:
        results['details']['alerts'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ AlertManager: FAILED - {str(e)}")

    # 测试4: 仪表板生成器
    logger.info("\n[Test 4/7] DashboardGenerator Test")
    results['total'] += 1
    try:
        from monitoring import DashboardGenerator
        generator = DashboardGenerator()

        # 生成仪表板数据
        dashboard = generator.generate_dashboard(
            metrics_data={'system': {'cpu_percent': 50}},
            alert_data={'alerts': [], 'severity_breakdown': {}},
            health_data={'overall_status': 'healthy', 'checks': {}}
        )

        # 导出HTML
        html = generator.export_dashboard_html(dashboard)

        results['details']['dashboard'] = 'PASSED'
        results['passed'] += 1
        logger.info(f"✅ DashboardGenerator: PASSED (html length: {len(html)})")
    except Exception as e:
        results['details']['dashboard'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ DashboardGenerator: FAILED - {str(e)}")

    # 测试5: 通知服务
    logger.info("\n[Test 5/7] NotificationService Test")
    results['total'] += 1
    try:
        from monitoring import NotificationService
        service = NotificationService()

        # 测试渠道状态
        channels = service.get_channel_status()

        # 测试发送通知
        notification = {
            'type': 'test',
            'title': 'TEST',
            'severity': 'INFO',
            'message': 'Test notification'
        }
        sent = await service.send_notification(notification)

        results['details']['notification'] = 'PASSED'
        results['passed'] += 1
        logger.info(f"✅ NotificationService: PASSED (channels: {len(channels)}, sent: {sent})")
    except Exception as e:
        results['details']['notification'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ NotificationService: FAILED - {str(e)}")

    # 测试6: 自动扩缩容
    logger.info("\n[Test 6/7] AutoScaler Test")
    results['total'] += 1
    try:
        from automation import AutoScaler
        scaler = AutoScaler()

        # 测试扩缩容策略
        policies = scaler.list_scaling_policies()

        # 测试扩缩容评估
        test_metrics = {'cpu_percent': 90}
        actions = await scaler.evaluate_scaling(test_metrics)

        # 测试扩缩容历史
        history = scaler.get_scaling_history(limit=10)

        results['details']['scaler'] = 'PASSED'
        results['passed'] += 1
        logger.info(f"✅ AutoScaler: PASSED (policies: {len(policies)}, actions: {len(actions)})")
    except Exception as e:
        results['details']['scaler'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ AutoScaler: FAILED - {str(e)}")

    # 测试7: 备份管理器
    logger.info("\n[Test 7/7] BackupManager Test")
    results['total'] += 1
    try:
        from automation import BackupManager
        manager = BackupManager()

        # 测试创建备份
        backup_id = await manager.create_backup(backup_type='full')

        # 测试列出备份
        backups = await manager.list_backups()

        # 测试清理
        cleaned = await manager.cleanup_old_backups(keep_days=0)

        results['details']['backup'] = 'PASSED'
        results['passed'] += 1
        logger.info(f"✅ BackupManager: PASSED (backup_id: {backup_id}, cleaned: {cleaned})")
    except Exception as e:
        results['details']['backup'] = f'FAILED: {str(e)}'
        results['failed'] += 1
        logger.error(f"❌ BackupManager: FAILED - {str(e)}")

    # 生成测试报告
    logger.info("\n" + "=" * 70)
    logger.info("Phase 11 基础功能测试报告")
    logger.info("=" * 70)

    pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0

    logger.info(f"\nTotal Tests: {results['total']}")
    logger.info(f"Passed: {results['passed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Pass Rate: {pass_rate:.1f}%")

    logger.info("\nDetailed Results:")
    for test_name, result in results['details'].items():
        status = "✅ PASSED" if result == "PASSED" else "❌ FAILED"
        logger.info(f"{status}: {test_name}")

    logger.info("=" * 70)

    return results


def main():
    """主函数"""
    try:
        # 运行测试
        results = asyncio.run(test_phase11_basic())

        # 根据测试结果返回退出码
        if results['failed'] == 0:
            print("\n[SUCCESS] All Phase 11 tests passed!")
            return 0
        else:
            print(f"\n[FAILURE] {results['failed']} test(s) failed")
            return 1

    except Exception as e:
        logger.error(f"Test execution exception: {str(e)}")
        print(f"\n[ERROR] Test execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
