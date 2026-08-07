"""V3.7 Phase 3 集成测试 - Production Operations

测试生产运维系统的各个组件及其集成。
"""

import asyncio
import os
import pytest
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# 导入运维模块
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ops import (
    SystemHealthMonitor,
    ComponentHealthCheck,
    ResourceHealthCheck,
    HealthStatus,
    create_system_health_monitor
)

from ops.auto_recovery_engine import (
    AutoRecoveryEngine,
    RecoveryActionExecutor,
    RecoveryActionType,
    RecoveryPriority,
    create_auto_recovery_engine
)

from ops.backup_manager import (
    BackupManager,
    BackupType,
    BackupStatus,
    create_backup_manager
)


class MockComponent:
    """模拟组件"""

    def __init__(self, name: str, healthy: bool = True):
        self.name = name
        self.healthy = healthy
        self.start_count = 0
        self.stop_count = 0

    def get_status(self):
        return {
            'healthy': self.healthy,
            'name': self.name
        }

    async def restart(self):
        """模拟重启"""
        self.healthy = True
        self.start_count += 1
        return {'success': True}


class TestSystemHealthMonitor:
    """系统健康监控器测试"""

    @pytest.mark.asyncio
    async def test_health_monitor_initialization(self):
        """测试健康监控器初始化"""
        monitor = create_system_health_monitor({})

        assert monitor is not None
        assert monitor.is_running is False
        assert len(monitor.checks) == 0

    @pytest.mark.asyncio
    async def test_register_component_check(self):
        """测试注册组件检查"""
        monitor = create_system_health_monitor({})
        component = MockComponent("test_component", healthy=True)

        check = ComponentHealthCheck("component_check", component, critical=True)
        monitor.register_check(check)

        assert len(monitor.checks) == 1

    @pytest.mark.asyncio
    async def test_run_health_checks(self):
        """测试运行健康检查"""
        monitor = create_system_health_monitor({})

        # 注册组件检查
        component = MockComponent("test_component", healthy=True)
        monitor.register_check(ComponentHealthCheck("component_check", component))

        # 运行检查
        report = await monitor.run_checks()

        assert report is not None
        assert report.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert len(report.checks) > 0

    @pytest.mark.asyncio
    async def test_health_report_generation(self):
        """测试健康报告生成"""
        monitor = create_system_health_monitor({})

        component = MockComponent("test_component", healthy=True)
        monitor.register_check(ComponentHealthCheck("component_check", component))

        report = await monitor.run_checks()

        assert report.overall_score >= 0
        assert report.overall_score <= 100
        assert isinstance(report.recommendations, list)
        assert isinstance(report.trends, dict)

    @pytest.mark.asyncio
    async def test_unhealthy_component_detection(self):
        """测试不健康组件检测"""
        monitor = create_system_health_monitor({})

        # 创建不健康的组件
        unhealthy_component = MockComponent("unhealthy_component", healthy=False)
        monitor.register_check(ComponentHealthCheck("unhealthy_check", unhealthy_component))

        # 运行检查
        report = await monitor.run_checks()

        # 应该检测到问题
        unhealthy_checks = [c for c in report.checks if c.status != HealthStatus.HEALTHY]
        assert len(unhealthy_checks) > 0


class TestAutoRecoveryEngine:
    """自动恢复引擎测试"""

    @pytest.mark.asyncio
    async def test_recovery_engine_initialization(self):
        """测试恢复引擎初始化"""
        engine = create_auto_recovery_engine({})

        assert engine is not None
        assert engine.is_running is False
        assert len(engine.plan_queue) == 0

    @pytest.mark.asyncio
    async def test_recovery_plan_creation(self):
        """测试恢复计划创建"""
        engine = create_auto_recovery_engine({})

        # 创建恢复计划
        plan = engine.create_recovery_plan(
            issue_description="Test component failure",
            severity=HealthStatus.UNHEALTHY,
            checks=[]
        )

        assert plan is not None
        assert len(plan.actions) > 0
        assert plan.severity == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_action_registration(self):
        """测试组件注册到执行器"""
        executor = RecoveryActionExecutor({})
        component = MockComponent("test_component")

        executor.register_component("test_component", component)

        assert "test_component" in executor.component_registry

    @pytest.mark.asyncio
    async def test_action_execution(self):
        """测试恢复操作执行"""
        executor = RecoveryActionExecutor({})
        component = MockComponent("test_component", healthy=False)

        executor.register_component("test_component", component)

        # 创建并执行操作
        from ops.auto_recovery_engine import RecoveryAction
        action = RecoveryAction(
            action_id="test_restart",
            action_type=RecoveryActionType.RESTART_COMPONENT,
            priority=RecoveryPriority.HIGH,
            target="test_component",
            description="Test restart"
        )

        result = await executor.execute_action(action)

        assert result['success'] is True
        assert component.healthy is True

    @pytest.mark.asyncio
    async def test_recovery_plan_execution(self):
        """测试恢复计划执行"""
        engine = create_auto_recovery_engine({})
        component = MockComponent("test_component", healthy=False)

        # 注册组件
        engine.executor.register_component("test_component", component)

        # 创建计划
        plan = engine.create_recovery_plan(
            issue_description="Test component failure",
            severity=HealthStatus.UNHEALTHY,
            checks=[]
        )

        # 执行计划
        report = await engine.execute_recovery_plan(plan)

        assert report is not None
        assert report.total_actions > 0
        assert report.started_at is not None
        assert report.completed_at is not None


class TestBackupManager:
    """备份管理器测试"""

    @pytest.mark.asyncio
    async def test_backup_manager_initialization(self):
        """测试备份管理器初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            assert manager is not None
            assert manager.backup_dir == Path(tmpdir)

    @pytest.mark.asyncio
    async def test_create_backup(self):
        """测试创建备份"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test_data.txt"
            test_file.write_text("Test data content")

            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            # 创建备份
            metadata = await manager.create_backup(
                sources=[str(test_file)],
                backup_type=BackupType.FULL,
                description="Test backup"
            )

            assert metadata.status == BackupStatus.COMPLETED
            assert metadata.size_bytes > 0
            assert len(metadata.files) > 0

    @pytest.mark.asyncio
    async def test_backup_compression(self):
        """测试备份压缩"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_data.txt"
            test_file.write_text("Test data content" * 1000)  # 创建较大文件

            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            # 创建压缩备份
            metadata_compressed = await manager.create_backup(
                sources=[str(test_file)],
                backup_type=BackupType.FULL,
                compress=True
            )

            # 创建未压缩备份
            metadata_uncompressed = await manager.create_backup(
                sources=[str(test_file)],
                backup_type=BackupType.FULL,
                compress=False
            )

            # 压缩文件应该更小
            assert metadata_compressed.size_bytes < metadata_uncompressed.size_bytes

    @pytest.mark.asyncio
    async def test_restore_backup(self):
        """测试恢复备份"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "original.txt"
            original_content = "Original content"
            test_file.write_text(original_content)

            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            # 创建备份
            metadata = await manager.create_backup(
                sources=[str(test_file)],
                backup_type=BackupType.FULL
            )

            # 删除原文件
            test_file.unlink()

            # 恢复备份
            result = await manager.restore_backup(metadata.backup_id)

            assert result.success is True
            assert len(result.restored_files) > 0

            # 验证文件已恢复
            restored_file = Path(tmpdir) / "original.txt"
            assert restored_file.exists()
            assert restored_file.read_text() == original_content

    @pytest.mark.asyncio
    async def test_backup_list(self):
        """测试备份列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test")

            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            # 创建多个备份
            await manager.create_backup(sources=[str(test_file)])
            await manager.create_backup(sources=[str(test_file)])

            # 获取备份列表
            backups = manager.get_backup_list()

            assert len(backups) >= 2
            assert all('backup_id' in b for b in backups)

    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self):
        """测试清理旧备份"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test")

            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            # 创建多个备份
            for i in range(5):
                await manager.create_backup(sources=[str(test_file)])

            # 清理旧备份（保留2个）
            deleted_count = await manager.cleanup_old_backups(
                keep_days=0,
                keep_count=2
            )

            assert deleted_count >= 3

            # 验证只剩下2个备份
            backups = manager.get_backup_list()
            assert len(backups) <= 2


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_health_monitor_recovery_integration(self):
        """测试健康监控器和恢复引擎集成"""
        monitor = create_system_health_monitor({})
        engine = create_auto_recovery_engine({})

        # 添加告警回调
        recovery_plans = []

        async def alert_callback(alert):
            # 创建恢复计划
            plan = engine.create_recovery_plan(
                issue_description=alert['recommendations'][0],
                severity=HealthStatus(alert['severity']),
                checks=[]
            )
            recovery_plans.append(plan)

        # 模拟告警
        await alert_callback({
            'type': 'health_alert',
            'severity': 'UNHEALTHY',
            'score': 30.0,
            'timestamp': datetime.now().isoformat(),
            'recommendations': ['Component test_component is unhealthy']
        })

        # 验证恢复计划已创建
        assert len(recovery_plans) == 1
        assert recovery_plans[0].issue_description == 'Component test_component is unhealthy'

    @pytest.mark.asyncio
    async def test_full_backup_and_restore_cycle(self):
        """测试完整的备份和恢复周期"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试数据
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()

            for i in range(3):
                test_file = data_dir / f"file_{i}.txt"
                test_file.write_text(f"Content {i}")

            config = {'backup_dir': tmpdir}
            manager = create_backup_manager(config)

            # 1. 创建备份
            metadata = await manager.create_backup(
                sources=[str(data_dir)],
                backup_type=BackupType.FULL
            )
            assert metadata.status == BackupStatus.COMPLETED

            # 2. 删除原数据
            shutil.rmtree(data_dir)
            assert not data_dir.exists()

            # 3. 恢复备份
            result = await manager.restore_backup(metadata.backup_id)
            assert result.success is True

            # 4. 验证数据已恢复
            assert data_dir.exists()
            for i in range(3):
                test_file = data_dir / f"file_{i}.txt"
                assert test_file.exists()
                assert test_file.read_text() == f"Content {i}"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
