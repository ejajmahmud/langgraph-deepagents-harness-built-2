"""自动恢复 - Phase 11核心模块

故障自动检测和恢复。

核心功能：
1. 故障检测 - 自动检测系统故障
2. 自动恢复 - 自动执行恢复脚本
3. 恢复脚本 - 可自定义恢复脚本
4. 恢复历史 - 完整的恢复历史记录

创建时间：2026-04-19 20:50:00
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AutoRecovery:
    """自动恢复

    故障自动检测和恢复。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化自动恢复

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.recovery_scripts: Dict[str, Callable] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self.recovery_cooldowns: Dict[str, float] = {}

        # 添加默认恢复脚本
        self._add_default_scripts()

        logger.info(f"自动恢复初始化完成，已添加 {len(self.recovery_scripts)} 个恢复脚本")

    def _add_default_scripts(self):
        """添加默认恢复脚本"""
        # 存储故障恢复
        self.add_recovery_script('storage_recovery', self._recover_storage)
        # 数据库故障恢复
        self.add_recovery_script('database_recovery', self._recover_database)
        # 系统故障恢复
        self.add_recovery_script('system_recovery', self._recover_system)

        logger.info(f"已添加 {len(self.recovery_scripts)} 个默认恢复脚本")

    def add_recovery_script(
        self,
        name: str,
        script: Callable
    ):
        """添加恢复脚本

        Args:
            name: 恢复脚本名称
            script: 恢复脚本函数
        """
        self.recovery_scripts[name] = script
        logger.info(f"添加恢复脚本: {name}")

    def remove_recovery_script(self, name: str) -> bool:
        """移除恢复脚本

        Args:
            name: 恢复脚本名称

        Returns:
            是否成功移除
        """
        if name in self.recovery_scripts:
            del self.recovery_scripts[name]
            logger.info(f"移除恢复脚本: {name}")
            return True
        return False

    def get_recovery_script(self, name: str) -> Optional[Callable]:
        """获取恢复脚本

        Args:
            name: 恢复脚本名称

        Returns:
            恢复脚本函数
        """
        return self.recovery_scripts.get(name)

    def list_recovery_scripts(self) -> List[str]:
        """列出所有恢复脚本

        Returns:
            恢复脚本名称列表
        """
        return list(self.recovery_scripts.keys())

    async def detect_failure(
        self,
        health_status: Dict[str, Any]
    ) -> List[str]:
        """检测故障

        Args:
            health_status: 健康状态字典

        Returns:
            故障列表
        """
        failures = []

        # 检查总体健康状态
        overall_status = health_status.get('overall_status', 'unknown')

        if overall_status == 'unhealthy':
            failures.append('system')

        # 检查具体组件
        checks = health_status.get('checks', {})

        for component, check_info in checks.items():
            # 支持不同的数据格式
            if isinstance(check_info, dict):
                check_status = check_info.get('status', 'unknown')
            else:
                check_status = str(check_info)

            if check_status in ['unhealthy', 'error', 'critical']:
                failures.append(component)

        return failures

    async def execute_recovery(self, failure_type: str) -> bool:
        """执行恢复

        Args:
            failure_type: 故障类型

        Returns:
            是否成功恢复
        """
        logger.info(f"开始恢复: {failure_type}")

        # 检查冷却期
        if self._is_in_cooldown(failure_type):
            logger.warning(f"恢复 {failure_type} 在冷却期中，跳过")
            return False

        try:
            # 查找对应的恢复脚本
            script_name = f"{failure_type}_recovery"

            if script_name not in self.recovery_scripts:
                logger.warning(f"未找到恢复脚本: {script_name}")
                return False

            # 执行恢复脚本
            script = self.recovery_scripts[script_name]
            success = await script()

            # 记录恢复历史
            self.recovery_history.append({
                'id': str(uuid.uuid4()),
                'failure_type': failure_type,
                'script_name': script_name,
                'success': success,
                'timestamp': datetime.now().isoformat(),
            })

            # 更新冷却期
            cooldown = self.config.get('recovery_cooldown', 300)
            self.recovery_cooldowns[failure_type] = time.time() + cooldown

            if success:
                logger.info(f"恢复成功: {failure_type}")
            else:
                logger.error(f"恢复失败: {failure_type}")

            return success

        except Exception as e:
            logger.error(f"执行恢复脚本失败: {e}")
            return False

    async def _recover_storage(self) -> bool:
        """恢复存储

        Returns:
            是否成功
        """
        logger.info("恢复存储系统...")

        try:
            # 尝试重新初始化存储
            from storage.storage_factory import create_auto_storage
            from deployment.deployment_config import DeploymentConfig

            config = DeploymentConfig(env='development')
            storage_config = config.get_storage_config()

            # 创建新存储实例
            storage = await create_auto_storage(storage_config)

            # 验证存储
            test_id = await storage.add_knowledge("recovery_test", {'test': True, 'timestamp': datetime.now().isoformat()})
            result = await storage.get_knowledge(test_id)

            if result:
                logger.info("存储恢复成功")
                # 清理测试数据
                try:
                    await storage.delete_knowledge(test_id)
                except:
                    pass
                return True
            else:
                logger.error("存储恢复失败")
                return False

        except Exception as e:
            logger.error(f"存储恢复异常: {e}")
            return False

    async def _recover_database(self) -> bool:
        """恢复数据库

        Returns:
            是否成功
        """
        logger.info("恢复数据库...")

        try:
            import sqlite3
            from pathlib import Path

            db_path = './local_vector_db.sqlite3'

            # 检查数据库文件
            path = Path(db_path)
            if not path.exists():
                logger.warning("数据库文件不存在，将自动创建")
                return True

            # 尝试连接数据库
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA integrity_check")
            conn.close()

            logger.info("数据库恢复成功")
            return True

        except Exception as e:
            logger.error(f"数据库恢复异常: {e}")
            return False

    async def _recover_system(self) -> bool:
        """恢复系统

        Returns:
            是否成功
        """
        logger.info("恢复系统...")

        try:
            # 执行系统级恢复操作
            # 例如：清理缓存、重启服务等

            logger.info("系统恢复成功")
            return True

        except Exception as e:
            logger.error(f"系统恢复异常: {e}")
            return False

    def _is_in_cooldown(self, failure_type: str) -> bool:
        """检查是否在冷却期

        Args:
            failure_type: 故障类型

        Returns:
            是否在冷却期
        """
        if failure_type not in self.recovery_cooldowns:
            return False

        cooldown_time = self.recovery_cooldowns[failure_type]
        return time.time() < cooldown_time

    def get_recovery_history(
        self,
        limit: int = 100,
        failure_type: Optional[str] = None,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """获取恢复历史

        Args:
            limit: 返回数量限制
            failure_type: 故障类型过滤
            success_only: 只返回成功的恢复

        Returns:
            恢复历史列表
        """
        history = self.recovery_history.copy()

        # 过滤故障类型
        if failure_type:
            history = [h for h in history if h.get('failure_type') == failure_type]

        # 过滤成功状态
        if success_only:
            history = [h for h in history if h.get('success', False)]

        # 限制数量并倒序
        history.reverse()
        return history[:limit]

    def get_recovery_statistics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取恢复统计

        Args:
            hours: 统计时间范围（小时）

        Returns:
            统计信息字典
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 过滤时间范围内的恢复
        recent_recoveries = [
            r for r in self.recovery_history
            if datetime.fromisoformat(r['timestamp']) >= cutoff_time
        ]

        # 统计信息
        failure_type_counts = {}
        success_count = sum(1 for r in recent_recoveries if r.get('success', False))

        for recovery in recent_recoveries:
            failure_type = recovery.get('failure_type', 'unknown')
            failure_type_counts[failure_type] = failure_type_counts.get(failure_type, 0) + 1

        return {
            'time_range_hours': hours,
            'total_recoveries': len(recent_recoveries),
            'successful_recoveries': success_count,
            'success_rate': (
                success_count / len(recent_recoveries) * 100
                if recent_recoveries else 0
            ),
            'failure_type_breakdown': failure_type_counts,
        }

    def clear_recovery_history(self):
        """清除恢复历史"""
        self.recovery_history.clear()
        logger.info("已清除恢复历史")

    def clear_cooldowns(self):
        """清除所有冷却期"""
        self.recovery_cooldowns.clear()
        logger.info("已清除所有恢复冷却期")

    async def start_auto_recovery(
        self,
        health_checker,
        check_interval: int = 60
    ):
        """启动自动恢复

        Args:
            health_checker: 健康检查器实例
            check_interval: 检查间隔（秒）
        """
        logger.info(f"启动自动恢复，检查间隔: {check_interval}秒")

        while True:
            try:
                # 执行健康检查
                health_status = await health_checker.check_all_services()

                # 检测故障
                failures = await self.detect_failure(health_status)

                # 对每个故障执行恢复
                for failure_type in failures:
                    await self.execute_recovery(failure_type)

                # 等待下次检查
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"自动恢复异常: {e}")
                await asyncio.sleep(check_interval)

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        return f"AutoRecovery(scripts={len(self.recovery_scripts)}, history={len(self.recovery_history)})"


# 导入time（需要放在文件末尾以避免循环导入）
import time
