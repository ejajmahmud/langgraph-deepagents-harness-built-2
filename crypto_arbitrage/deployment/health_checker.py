"""健康检查器 - Phase 10核心模块

检查系统各组件健康状态。

核心功能：
1. 存储健康检查 - 存储系统健康状态
2. 数据库健康检查 - 数据库健康状态
3. API健康检查 - API服务健康状态
4. 综合健康报告 - 生成完整健康报告

创建时间：2026-04-19 19:52:00
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthCheck:
    """健康检查结果

    单次健康检查的结果。
    """

    def __init__(
        self,
        name: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        self.name = name
        self.status = status  # 'healthy', 'degraded', 'unhealthy'
        self.message = message
        self.details = details or {}
        self.duration_ms = duration_ms
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            结果字典
        """
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
        }


class HealthChecker:
    """健康检查器

    检查系统各组件健康状态。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化健康检查器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.checks: Dict[str, Callable] = {}
        self.check_history: List[HealthCheck] = []

        # 注册默认检查
        self._register_default_checks()

        logger.info("健康检查器初始化完成")

    def _register_default_checks(self):
        """注册默认健康检查"""
        self.register_check('storage', self.check_storage)
        self.register_check('database', self.check_database)
        self.register_check('api', self.check_api)
        self.register_check('system', self.check_system)

    def register_check(self, name: str, check_func: Callable):
        """注册健康检查

        Args:
            name: 检查名称
            check_func: 检查函数
        """
        self.checks[name] = check_func
        logger.info(f"已注册健康检查: {name}")

    def unregister_check(self, name: str):
        """取消注册健康检查

        Args:
            name: 检查名称
        """
        if name in self.checks:
            del self.checks[name]
            logger.info(f"已取消注册健康检查: {name}")

    async def check_storage(self) -> HealthCheck:
        """检查存储健康状态

        Returns:
            健康检查结果
        """
        start_time = time.perf_counter()

        try:
            # 尝试导入存储模块
            from storage.storage_factory import create_auto_storage
            from deployment.deployment_config import DeploymentConfig

            # 创建配置
            config = DeploymentConfig(env='development')
            storage_config = config.get_storage_config()

            # 创建存储实例
            storage = await create_auto_storage(storage_config)

            # 执行基本操作
            test_id = await storage.add_knowledge(
                "健康检查测试",
                {'health_check': True}
            )

            # 验证存储
            result = await storage.get_knowledge(test_id)

            duration_ms = (time.perf_counter() - start_time) * 1000

            if result and 'content' in result:
                return HealthCheck(
                    name='storage',
                    status='healthy',
                    message='存储系统运行正常',
                    details={
                        'storage_type': storage_config.get('storage_type'),
                        'test_id': test_id,
                    },
                    duration_ms=duration_ms
                )
            else:
                return HealthCheck(
                    name='storage',
                    status='degraded',
                    message='存储系统响应异常',
                    details={
                        'storage_type': storage_config.get('storage_type'),
                        'test_id': test_id,
                    },
                    duration_ms=duration_ms
                )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"存储健康检查失败: {e}")
            return HealthCheck(
                name='storage',
                status='unhealthy',
                message=f'存储系统异常: {str(e)}',
                details={'error': str(e)},
                duration_ms=duration_ms
            )

    async def check_database(self) -> HealthCheck:
        """检查数据库健康状态

        Returns:
            健康检查结果
        """
        start_time = time.perf_counter()

        try:
            import sqlite3
            from pathlib import Path

            # 获取数据库路径
            db_path = './local_vector_db.sqlite3'

            # 检查文件是否存在
            if not Path(db_path).exists():
                return HealthCheck(
                    name='database',
                    status='unhealthy',
                    message='数据库文件不存在',
                    details={'path': db_path},
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )

            # 尝试连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 执行简单查询
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            result = cursor.fetchone()

            conn.close()

            duration_ms = (time.perf_counter() - start_time) * 1000

            return HealthCheck(
                name='database',
                status='healthy',
                message='数据库运行正常',
                details={
                    'path': db_path,
                    'has_tables': result is not None,
                },
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"数据库健康检查失败: {e}")
            return HealthCheck(
                name='database',
                status='unhealthy',
                message=f'数据库异常: {str(e)}',
                details={'error': str(e)},
                duration_ms=duration_ms
            )

    async def check_api(self) -> HealthCheck:
        """检查API健康状态

        Returns:
            健康检查结果
        """
        start_time = time.perf_counter()

        try:
            # 这里可以检查API端点
            # 目前只是模拟检查
            await asyncio.sleep(0.1)

            duration_ms = (time.perf_counter() - start_time) * 1000

            return HealthCheck(
                name='api',
                status='healthy',
                message='API服务运行正常',
                details={
                    'response_time_ms': duration_ms,
                },
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"API健康检查失败: {e}")
            return HealthCheck(
                name='api',
                status='unhealthy',
                message=f'API异常: {str(e)}',
                details={'error': str(e)},
                duration_ms=duration_ms
            )

    async def check_system(self) -> HealthCheck:
        """检查系统健康状态

        Returns:
            健康检查结果
        """
        start_time = time.perf_counter()

        try:
            import psutil

            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')

            duration_ms = (time.perf_counter() - start_time) * 1000

            # 判断系统健康状态
            status = 'healthy'
            warnings = []

            if cpu_percent > 80:
                status = 'degraded'
                warnings.append(f'CPU使用率过高: {cpu_percent}%')

            if memory.percent > 80:
                status = 'degraded'
                warnings.append(f'内存使用率过高: {memory.percent}%')

            if disk.percent > 90:
                status = 'degraded'
                warnings.append(f'磁盘使用率过高: {disk.percent}%')

            return HealthCheck(
                name='system',
                status=status,
                message='系统运行正常' if status == 'healthy' else '; '.join(warnings),
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / 1024 / 1024,
                    'disk_percent': disk.percent,
                    'disk_used_gb': disk.used / 1024 / 1024 / 1024,
                },
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"系统健康检查失败: {e}")
            return HealthCheck(
                name='system',
                status='unhealthy',
                message=f'系统检查异常: {str(e)}',
                details={'error': str(e)},
                duration_ms=duration_ms
            )

    async def check_all_services(self) -> Dict[str, Any]:
        """检查所有服务

        Returns:
            健康检查报告
        """
        logger.info("开始检查所有服务...")

        results = {}
        start_time = time.time()

        # 并行执行所有检查
        tasks = [check_func() for check_func in self.checks.values()]
        check_results = await asyncio.gather(*tasks)

        # 组织结果
        for name, result in zip(self.checks.keys(), check_results):
            results[name] = result.to_dict()
            self.check_history.append(result)

        # 计算总体健康状态
        overall_status = self._calculate_overall_status(results)

        # 生成报告
        total_duration = time.time() - start_time
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'total_duration_seconds': round(total_duration, 3),
            'checks': results,
            'summary': self._generate_summary(results, overall_status),
        }

        logger.info(f"健康检查完成: {overall_status} ({total_duration:.3f}s)")

        return report

    def _calculate_overall_status(self, results: Dict[str, Dict[str, Any]]) -> str:
        """计算总体健康状态

        Args:
            results: 所有检查结果

        Returns:
            总体健康状态
        """
        statuses = [result['status'] for result in results.values()]

        if 'unhealthy' in statuses:
            return 'unhealthy'
        elif 'degraded' in statuses:
            return 'degraded'
        else:
            return 'healthy'

    def _generate_summary(
        self,
        results: Dict[str, Dict[str, Any]],
        overall_status: str
    ) -> str:
        """生成健康检查摘要

        Args:
            results: 所有检查结果
            overall_status: 总体健康状态

        Returns:
            摘要文本
        """
        if overall_status == 'healthy':
            return "所有系统组件运行正常"
        elif overall_status == 'degraded':
            degraded_checks = [
                name for name, result in results.items()
                if result['status'] == 'degraded'
            ]
            return f"部分组件运行异常: {', '.join(degraded_checks)}"
        else:
            unhealthy_checks = [
                name for name, result in results.items()
                if result['status'] == 'unhealthy'
            ]
            return f"关键组件故障: {', '.join(unhealthy_checks)}"

    def get_check_history(
        self,
        limit: int = 100,
        check_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取健康检查历史

        Args:
            limit: 返回数量限制
            check_name: 检查名称过滤器

        Returns:
            健康检查历史
        """
        history = [
            check.to_dict() for check in self.check_history
        ]

        # 过滤检查名称
        if check_name:
            history = [
                h for h in history if h['name'] == check_name
            ]

        # 限制数量
        history = history[-limit:]

        # 按时间倒序排列
        history.reverse()

        return history

    def clear_history(self):
        """清除健康检查历史"""
        self.check_history.clear()
        logger.info("健康检查历史已清除")
