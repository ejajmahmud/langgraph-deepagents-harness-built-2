"""Phase 10 集成测试脚本

测试Phase 10核心功能：生产部署、健康检查。

创建时间：2026-04-19 19:52:00
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deployment.deployment_config import DeploymentConfig
from deployment.health_checker import HealthChecker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase10IntegrationTest:
    """Phase 10集成测试类"""

    def __init__(self):
        self.test_results = {}

    async def test_deployment_config(self):
        """测试部署配置功能"""
        logger.info("=" * 60)
        logger.info("测试1: 部署配置")
        logger.info("=" * 60)

        try:
            # 测试不同环境配置
            logger.info("测试开发环境配置...")
            dev_config = DeploymentConfig(env='development')
            assert dev_config.env == 'development', "开发环境配置错误"
            logger.info(f"✅ 开发环境配置: {dev_config.env}")

            logger.info("测试生产环境配置...")
            prod_config = DeploymentConfig(env='production')
            assert prod_config.env == 'production', "生产环境配置错误"
            logger.info(f"✅ 生产环境配置: {prod_config.env}")

            # 测试配置获取
            logger.info("测试配置获取...")
            storage_config = prod_config.get_storage_config()
            assert 'storage_type' in storage_config, "缺少存储类型配置"
            logger.info(f"✅ 存储配置: {storage_config['storage_type']}")

            database_config = prod_config.get_database_config()
            assert 'type' in database_config, "缺少数据库类型配置"
            logger.info(f"✅ 数据库配置: {database_config['type']}")

            # 测试配置验证
            logger.info("测试配置验证...")
            validation = prod_config.validate_config()
            assert validation['valid'] == True, "配置验证失败"
            logger.info(f"✅ 配置验证通过: {validation['valid']}")

            # 测试配置导出
            logger.info("测试配置导出...")
            config_json = prod_config.export_config(format='json')
            assert 'env' in config_json, "导出配置缺少env字段"
            logger.info(f"✅ 配置导出成功: {len(config_json)} 字符")

            self.test_results['deployment_config'] = 'PASSED'

        except Exception as e:
            logger.error(f"❌ 部署配置测试失败: {e}")
            self.test_results['deployment_config'] = f'FAILED: {str(e)}'

    async def test_health_checker(self):
        """测试健康检查功能"""
        logger.info("=" * 60)
        logger.info("测试2: 健康检查")
        logger.info("=" * 60)

        try:
            # 创建健康检查器
            logger.info("创建健康检查器...")
            checker = HealthChecker()
            assert len(checker.checks) > 0, "健康检查器没有注册检查"
            logger.info(f"✅ 健康检查器创建成功: {len(checker.checks)} 个检查")

            # 测试单个检查
            logger.info("测试单个健康检查...")
            system_check = await checker.check_system()
            assert system_check.status in ['healthy', 'degraded', 'unhealthy'], "健康状态错误"
            logger.info(f"✅ 系统检查: {system_check.status} - {system_check.message}")

            storage_check = await checker.check_storage()
            assert storage_check.status in ['healthy', 'degraded', 'unhealthy'], "存储状态错误"
            logger.info(f"✅ 存储检查: {storage_check.status} - {storage_check.message}")

            database_check = await checker.check_database()
            assert database_check.status in ['healthy', 'degraded', 'unhealthy'], "数据库状态错误"
            logger.info(f"✅ 数据库检查: {database_check.status} - {database_check.message}")

            # 测试综合检查
            logger.info("测试综合健康检查...")
            report = await checker.check_all_services()
            assert 'overall_status' in report, "健康报告缺少总体状态"
            assert 'checks' in report, "健康报告缺少检查详情"
            logger.info(f"✅ 综合检查: {report['overall_status']}")

            # 打印健康报告摘要
            logger.info(f"  总体状态: {report['overall_status']}")
            logger.info(f"  执行时间: {report['total_duration_seconds']:.3f}s")
            logger.info(f"  检查摘要: {report['summary']}")

            # 测试检查历史
            logger.info("测试检查历史...")
            history = checker.get_check_history(limit=10)
            assert len(history) > 0, "健康检查历史为空"
            logger.info(f"✅ 检查历史: {len(history)} 条记录")

            self.test_results['health_checker'] = 'PASSED'

        except Exception as e:
            logger.error(f"❌ 健康检查测试失败: {e}")
            self.test_results['health_checker'] = f'FAILED: {str(e)}'

    def print_summary(self):
        """打印测试摘要"""
        logger.info("=" * 60)
        logger.info("Phase 10 集成测试摘要")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == 'PASSED')
        failed_tests = total_tests - passed_tests

        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests}")
        logger.info(f"失败: {failed_tests}")
        logger.info(f"通过率: {(passed_tests / total_tests * 100) if total_tests > 0 else 0:.1f}%")

        logger.info("\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result == 'PASSED' else f"❌ {result}"
            logger.info(f"  {test_name}: {status}")

        logger.info("=" * 60)

        if failed_tests == 0:
            logger.info("🎉 Phase 10 所有测试通过！")
            return True
        else:
            logger.warning(f"⚠️  Phase 10 有 {failed_tests} 个测试失败")
            return False


async def main():
    """主函数"""
    logger.info("Phase 10 集成测试开始")
    logger.info("=" * 60)

    tester = Phase10IntegrationTest()

    # 运行所有测试
    await tester.test_deployment_config()
    await tester.test_health_checker()

    # 打印摘要
    success = tester.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
