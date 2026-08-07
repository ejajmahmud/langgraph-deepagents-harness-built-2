"""Phase 11 集成测试脚本 - 简化版

验证实时监控与运维自动化模块的功能。

创建时间：2026-04-19 20:58:00
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


async def test_phase11_integration():
    """Phase 11 集成测试主函数"""

    logger.info("=" * 70)
    logger.info("Phase 11 集成测试开始")
    logger.info("=" * 70)

    test_results = {}
    passed = 0
    failed = 0

    # 测试1: 指标收集器
    logger.info("\n【测试 1/8】指标收集器")
    try:
        from monitoring.metrics_collector import MetricsCollector
        collector = MetricsCollector()

        # 测试收集系统指标
        system_metrics = await collector.collect_system_metrics()
        assert system_metrics is not None, "系统指标不应为None"
        assert 'cpu_percent' in system_metrics, "应包含CPU指标"

        # 测试收集所有指标
        all_metrics = await collector.collect_all_metrics()
        assert all_metrics is not None, "所有指标不应为None"

        # 测试获取最新指标
        latest = collector.get_latest_metrics()
        assert latest is not None, "最新指标不应为None"

        test_results['metrics_collector'] = {'status': 'PASSED'}
        passed += 1
        logger.info("✅ 指标收集器测试通过")

    except Exception as e:
        test_results['metrics_collector'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 指标收集器测试失败: {e}")

    # 测试2: 告警管理器
    logger.info("\n【测试 2/8】告警管理器")
    try:
        from monitoring.alert_manager import AlertManager
        manager = AlertManager()

        # 测试默认告警规则
        rules = manager.list_alert_rules()
        assert len(rules) > 0, "应有默认告警规则"

        # 测试评估告警
        test_metrics = {
            'cpu_percent': 90,
            'memory_percent': 85,
            'disk_percent': 95,
        }

        alerts = await manager.evaluate_alerts(test_metrics)
        assert alerts is not None, "告警不应为None"

        # 测试获取告警历史
        history = manager.get_alert_history(limit=10)
        assert history is not None, "告警历史不应为None"

        test_results['alert_manager'] = {'status': 'PASSED'}
        passed += 1
        logger.info(f"✅ 告警管理器测试通过 (触发 {len(alerts)} 个告警)")

    except Exception as e:
        test_results['alert_manager'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 告警管理器测试失败: {e}")

    # 测试3: 仪表板生成器
    logger.info("\n【测试 3/8】仪表板生成器")
    try:
        from monitoring.dashboard_generator import DashboardGenerator
        generator = DashboardGenerator()

        # 测试生成仪表板
        dashboard_data = generator.generate_dashboard(
            metrics_data={
                'system': {
                    'cpu_percent': 50,
                    'memory_percent': 60,
                    'disk_percent': 70,
                }
            },
            alert_data={
                'alerts': [],
                'severity_breakdown': {
                    'INFO': 0,
                    'WARNING': 0,
                }
            },
            health_data={
                'overall_status': 'healthy',
                'checks': {
                    'storage': {'status': 'healthy'},
                    'database': {'status': 'healthy'},
                }
            }
        )

        assert dashboard_data is not None, "仪表板数据不应为None"

        # 测试导出HTML
        html = generator.export_dashboard_html(dashboard_data)
        assert html is not None, "HTML不应为None"
        assert '<html' in html, "应包含HTML标签"

        test_results['dashboard_generator'] = {'status': 'PASSED'}
        passed += 1
        logger.info("✅ 仪表板生成器测试通过")

    except Exception as e:
        test_results['dashboard_generator'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 仪表板生成器测试失败: {e}")

    # 测试4: 通知服务
    logger.info("\n【测试 4/8】通知服务")
    try:
        from monitoring.notification_service import NotificationService
        service = NotificationService()

        # 测试渠道初始化
        channels = service.get_channel_status()
        assert 'console' in channels, "应有控制台渠道"
        assert 'file' in channels, "应有文件渠道"

        # 测试发送通知
        notification = {
            'type': 'test',
            'title': 'TEST',
            'severity': 'INFO',
            'message': '测试通知',
        }

        success = await service.send_notification(notification)

        # 测试获取通知历史
        history = service.get_notification_history(limit=10)
        assert history is not None, "通知历史不应为None"

        test_results['notification_service'] = {'status': 'PASSED'}
        passed += 1
        logger.info(f"✅ 通知服务测试通过")

    except Exception as e:
        test_results['notification_service'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 通知服务测试失败: {e}")

    # 测试5: 自动扩缩容
    logger.info("\n【测试 5/8】自动扩缩容")
    try:
        from automation.auto_scaler import AutoScaler
        scaler = AutoScaler()

        # 测试默认扩缩容策略
        policies = scaler.list_scaling_policies()
        assert len(policies) > 0, "应有默认扩缩容策略"

        # 测试评估扩缩容
        test_metrics = {
            'cpu_percent': 90,
            'memory_percent': 85,
        }

        actions = await scaler.evaluate_scaling(test_metrics)
        assert actions is not None, "扩缩容动作不应为None"

        # 测试获取扩缩容历史
        history = scaler.get_scaling_history(limit=10)
        assert history is not None, "扩缩容历史不应为None"

        test_results['auto_scaler'] = {'status': 'PASSED'}
        passed += 1
        logger.info(f"✅ 自动扩缩容测试通过 (生成 {len(actions)} 个扩缩容动作)")

    except Exception as e:
        test_results['auto_scaler'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 自动扩缩容测试失败: {e}")

    # 测试6: 自动恢复
    logger.info("\n【测试 6/8】自动恢复")
    try:
        from automation.auto_recovery import AutoRecovery
        recovery = AutoRecovery()

        # 测试默认恢复脚本
        scripts = recovery.list_recovery_scripts()
        assert len(scripts) > 0, "应有默认恢复脚本"

        # 测试故障检测
        test_health_status = {
            'overall_status': 'unhealthy',
            'checks': {
                'storage': {'status': 'unhealthy'},
                'database': {'status': 'healthy'},
            }
        }

        failures = await recovery.detect_failure(test_health_status)
        assert 'storage' in failures, "应检测到存储故障"

        # 测试获取恢复历史
        history = recovery.get_recovery_history(limit=10)
        assert history is not None, "恢复历史不应为None"

        test_results['auto_recovery'] = {'status': 'PASSED'}
        passed += 1
        logger.info(f"✅ 自动恢复测试通过 (检测到 {len(failures)} 个故障)")

    except Exception as e:
        test_results['auto_recovery'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 自动恢复测试失败: {e}")

    # 测试7: 备份管理器
    logger.info("\n【测试 7/8】备份管理器")
    try:
        from automation.backup_manager import BackupManager
        manager = BackupManager()

        # 测试创建备份
        backup_id = await manager.create_backup(backup_type='full')
        assert backup_id is not None, "备份ID不应为None"

        # 测试列出备份
        backups = await manager.list_backups()
        assert backups is not None, "备份列表不应为None"

        # 测试获取最新备份
        latest = await manager.get_latest_backup()
        assert latest is not None, "最新备份不应为None"

        # 测试清理旧备份
        cleaned = await manager.cleanup_old_backups(keep_days=0)

        test_results['backup_manager'] = {'status': 'PASSED'}
        passed += 1
        logger.info(f"✅ 备份管理器测试通过 (创建备份: {backup_id}, 清理: {cleaned} 个)")

    except Exception as e:
        test_results['backup_manager'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 备份管理器测试失败: {e}")

    # 测试8: 综合集成
    logger.info("\n【测试 8/8】综合集成")
    try:
        # 测试所有模块一起工作
        from monitoring.metrics_collector import MetricsCollector
        from monitoring.alert_manager import AlertManager
        from monitoring.dashboard_generator import DashboardGenerator

        collector = MetricsCollector()
        manager = AlertManager()
        generator = DashboardGenerator()

        # 收集指标
        all_metrics = await collector.collect_all_metrics()

        # 评估告警
        system_metrics = all_metrics.get('system', {})
        alerts = await manager.evaluate_alerts(system_metrics)

        # 生成仪表板
        dashboard = generator.generate_dashboard(
            metrics_data=all_metrics,
            alert_data={'alerts': alerts, 'severity_breakdown': {}},
            health_data={'overall_status': 'healthy', 'checks': {}}
        )

        assert dashboard is not None, "综合仪表板不应为None"

        test_results['integration'] = {'status': 'PASSED'}
        passed += 1
        logger.info(f"✅ 综合集成测试通过")

    except Exception as e:
        test_results['integration'] = {'status': 'FAILED', 'error': str(e)}
        failed += 1
        logger.error(f"❌ 综合集成测试失败: {e}")

    # 生成测试报告
    logger.info("\n" + "=" * 70)
    logger.info("Phase 11 集成测试报告")
    logger.info("=" * 70)

    total_tests = passed + failed
    pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

    logger.info(f"\n总测试数: {total_tests}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")
    logger.info(f"通过率: {pass_rate:.1f}%")

    logger.info("\n详细结果:")
    for test_name, result in test_results.items():
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        logger.info(f"{status_icon} {test_name}: {result['status']}")

    logger.info("=" * 70)

    # 返回测试结果
    return {
        'total_tests': total_tests,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'results': test_results,
    }


def main():
    """主函数"""
    try:
        # 运行测试
        report = asyncio.run(test_phase11_integration())

        # 根据测试结果返回退出码
        if report['failed'] == 0:
            print("\n🎉 Phase 11 集成测试全部通过！")
            return 0
        else:
            print(f"\n⚠️  {report['failed']} 个测试失败")
            return 1

    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        print(f"\n❌ 测试执行异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
