"""Phase 11 集成测试脚本

验证实时监控与运维自动化模块的功能。

创建时间：2026-04-19 20:55:00
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from monitoring.metrics_collector import MetricsCollector
from monitoring.alert_manager import AlertManager
from monitoring.dashboard_generator import DashboardGenerator
from monitoring.notification_service import NotificationService
from automation.auto_scaler import AutoScaler
from automation.auto_recovery import AutoRecovery
from automation.backup_manager import BackupManager

logger = logging.getLogger(__name__)


class Phase11IntegrationTest:
    """Phase 11 集成测试

    验证实时监控与运维自动化模块。
    """

    def __init__(self):
        """初始化测试"""
        self.test_results = {}
        self.passed = 0
        self.failed = 0

        logger.info("Phase 11 集成测试初始化完成")

    def run_test(self, test_name: str, test_func):
        """运行单个测试

        Args:
            test_name: 测试名称
            test_func: 测试函数
        """
        logger.info(f"运行测试: {test_name}")

        try:
            result = test_func()
            self.test_results[test_name] = {
                'status': 'PASSED',
                'result': result,
            }
            self.passed += 1
            logger.info(f"✅ {test_name}: PASSED")

        except Exception as e:
            self.test_results[test_name] = {
                'status': 'FAILED',
                'error': str(e),
            }
            self.failed += 1
            logger.error(f"❌ {test_name}: FAILED - {str(e)}")

    def test_metrics_collector(self):
        """测试指标收集器"""
        collector = MetricsCollector()

        # 测试收集系统指标
        system_metrics = asyncio.run(collector.collect_system_metrics())

        assert system_metrics is not None, "系统指标不应为None"
        assert 'cpu_percent' in system_metrics, "应包含CPU指标"
        assert 'memory_percent' in system_metrics, "应包含内存指标"

        # 测试收集所有指标
        all_metrics = asyncio.run(collector.collect_all_metrics())

        assert all_metrics is not None, "所有指标不应为None"
        assert 'system' in all_metrics, "应包含系统指标"
        assert 'timestamp' in all_metrics, "应包含时间戳"

        # 测试获取最新指标
        latest = collector.get_latest_metrics()

        assert latest is not None, "最新指标不应为None"

        # 测试指标历史
        collector.get_metrics_history('system', limit=10)

        return {
            'system_metrics': system_metrics,
            'all_metrics': all_metrics,
            'latest': latest,
        }

    def test_alert_manager(self):
        """测试告警管理器"""
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

        alerts = asyncio.run(manager.evaluate_alerts(test_metrics))

        assert alerts is not None, "告警不应为None"

        # 测试获取告警历史
        history = manager.get_alert_history(limit=10)

        assert history is not None, "告警历史不应为None"

        # 测试告警统计
        stats = manager.get_alert_statistics(hours=24)

        assert stats is not None, "告警统计不应为None"

        return {
            'default_rules': len(rules),
            'triggered_alerts': len(alerts),
            'history_count': len(history),
        }

    def test_dashboard_generator(self):
        """测试仪表板生成器"""
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
        assert 'timestamp' in dashboard_data, "应包含时间戳"
        assert 'widgets' in dashboard_data, "应包含组件"

        # 测试导出HTML
        html = generator.export_dashboard_html(dashboard_data)

        assert html is not None, "HTML不应为None"
        assert '<html' in html, "应包含HTML标签"

        return {
            'dashboard_generated': True,
            'html_exported': True,
        }

    def test_notification_service(self):
        """测试通知服务"""
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

        success = asyncio.run(service.send_notification(notification))

        # 测试获取通知历史
        history = service.get_notification_history(limit=10)

        assert history is not None, "通知历史不应为None"

        # 测试通知统计
        stats = service.get_notification_statistics(hours=24)

        assert stats is not None, "通知统计不应为None"

        return {
            'channels_initialized': len(channels),
            'notification_sent': success,
            'history_count': len(history),
        }

    def test_auto_scaler(self):
        """测试自动扩缩容"""
        scaler = AutoScaler()

        # 测试默认扩缩容策略
        policies = scaler.list_scaling_policies()

        assert len(policies) > 0, "应有默认扩缩容策略"

        # 测试评估扩缩容
        test_metrics = {
            'cpu_percent': 90,
            'memory_percent': 85,
        }

        actions = asyncio.run(scaler.evaluate_scaling(test_metrics))

        assert actions is not None, "扩缩容动作不应为None"

        # 测试获取扩缩容历史
        history = scaler.get_scaling_history(limit=10)

        assert history is not None, "扩缩容历史不应为None"

        # 测试扩缩容统计
        stats = scaler.get_scaling_statistics(hours=24)

        assert stats is not None, "扩缩容统计不应为None"

        return {
            'default_policies': len(policies),
            'scaling_actions': len(actions),
            'history_count': len(history),
        }

    def test_auto_recovery(self):
        """测试自动恢复"""
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

        failures = asyncio.run(recovery.detect_failure(test_health_status))

        assert 'storage' in failures, "应检测到存储故障"

        # 测试获取恢复历史
        history = recovery.get_recovery_history(limit=10)

        assert history is not None, "恢复历史不应为None"

        # 测试恢复统计
        stats = recovery.get_recovery_statistics(hours=24)

        assert stats is not None, "恢复统计不应为None"

        return {
            'default_scripts': len(scripts),
            'detected_failures': len(failures),
            'history_count': len(history),
        }

    def test_backup_manager(self):
        """测试备份管理器"""
        manager = BackupManager()

        # 测试创建备份
        backup_id = asyncio.run(manager.create_backup(backup_type='full'))

        assert backup_id is not None, "备份ID不应为None"

        # 测试列出备份
        backups = asyncio.run(manager.list_backups())

        assert backups is not None, "备份列表不应为None"

        # 测试获取最新备份
        latest = asyncio.run(manager.get_latest_backup())

        assert latest is not None, "最新备份不应为None"

        # 测试备份统计
        stats = asyncio.run(manager.get_backup_statistics(days=30))

        assert stats is not None, "备份统计不应为None"

        # 测试清理旧备份
        cleaned = asyncio.run(manager.cleanup_old_backups(keep_days=0))

        return {
            'backup_created': True,
            'backup_id': backup_id,
            'backups_listed': len(backups),
            'cleaned_count': cleaned,
        }

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("Phase 11 集成测试开始")
        logger.info("=" * 60)

        # 运行各项测试
        self.run_test("指标收集器", self.test_metrics_collector)
        self.run_test("告警管理器", self.test_alert_manager)
        self.run_test("仪表板生成器", self.test_dashboard_generator)
        self.run_test("通知服务", self.test_notification_service)
        self.run_test("自动扩缩容", self.test_auto_scaler)
        self.run_test("自动恢复", self.test_auto_recovery)
        self.run_test("备份管理器", self.test_backup_manager)

        # 生成测试报告
        self.generate_report()

        return self.test_results

    def generate_report(self):
        """生成测试报告"""
        logger.info("=" * 60)
        logger.info("Phase 11 集成测试报告")
        logger.info("=" * 60)

        # 测试摘要
        total_tests = self.passed + self.failed
        pass_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"\n总测试数: {total_tests}")
        logger.info(f"通过: {self.passed}")
        logger.info(f"失败: {self.failed}")
        logger.info(f"通过率: {pass_rate:.1f}%")

        # 详细结果
        logger.info("\n详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            logger.info(f"{status_icon} {test_name}: {result['status']}")

        logger.info("=" * 60)

        # 返回测试结果
        return {
            'total_tests': total_tests,
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': pass_rate,
            'results': self.test_results,
        }


def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建并运行测试
    test = Phase11IntegrationTest()
    report = test.run_all_tests()

    # 根据测试结果返回退出码
    if report['failed'] == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {report['failed']} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
