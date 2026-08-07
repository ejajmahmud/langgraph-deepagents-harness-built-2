"""V5.8 模块化架构验证测试

测试目标：
1. 验证5个新模块能够正常初始化
2. 验证外观模式适配器的向后兼容性
3. 验证模块间的基本协作
4. 验证性能统计功能

预期结果：所有测试通过，模块化架构正常工作
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置简单日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_v5_8_architecture():
    """测试V5.8模块化架构"""

    logger.info("=" * 70)
    logger.info("🚀 开始V5.8模块化架构验证测试")
    logger.info("=" * 70)

    test_results = []

    # 测试1: 导入新模块
    logger.info("\n📦 测试1: 导入新模块")
    try:
        from storage.modules import (
            SemanticSearchModule,
            KnowledgeFusionModule,
            PredictiveAnalysisModule,
            KnowledgeManagementModule,
            CacheManagerModule
        )
        from storage.deep_memo0_integration_v5_8 import DeepMemo0IntegrationV58
        logger.info("✅ 所有模块导入成功")
        test_results.append(("模块导入", True))
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        test_results.append(("模块导入", False))
        return test_results

    # 测试2: 初始化外观模式适配器
    logger.info("\n🏗️  测试2: 初始化外观模式适配器")
    try:
        config = {
            'semantic_search': {
                'enable_semantic_search': True,
                'cache_ttl': 300,
                'max_cache_size': 100
            },
            'knowledge_fusion': {
                'enable_knowledge_fusion': True,
                'min_relevance_score': 0.7
            },
            'predictive_analysis': {
                'enable_predictive_analysis': True,
                'min_confidence_threshold': 0.5
            },
            'knowledge_management': {
                'enable_auto_deduplicate': True,
                'deduplicate_threshold': 0.8
            },
            'cache_manager': {
                'enable_cache_management': True,
                'default_ttl': 300,
                'max_cache_size': 1000
            }
        }

        integration = DeepMemo0IntegrationV58(config)
        logger.info("✅ 外观模式适配器初始化成功")
        test_results.append(("适配器初始化", True))
    except Exception as e:
        logger.error(f"❌ 适配器初始化失败: {e}")
        test_results.append(("适配器初始化", False))
        return test_results

    # 测试3: 验证模块实例化
    logger.info("\n🔧 测试3: 验证模块实例化")
    try:
        assert hasattr(integration, 'semantic_search'), "缺少语义搜索模块"
        assert hasattr(integration, 'knowledge_fusion'), "缺少知识融合模块"
        assert hasattr(integration, 'predictive_analysis'), "缺少预测分析模块"
        assert hasattr(integration, 'knowledge_management'), "缺少知识管理模块"
        assert hasattr(integration, 'cache_manager'), "缺少缓存管理模块"

        logger.info("✅ 所有5个模块实例化成功")
        test_results.append(("模块实例化", True))
    except Exception as e:
        logger.error(f"❌ 模块实例化验证失败: {e}")
        test_results.append(("模块实例化", False))

    # 测试4: 验证向后兼容性
    logger.info("\n🔄 测试4: 验证向后兼容性")
    try:
        # 检查原有接口是否存在
        compatible_methods = [
            'semantic_search',
            'knowledge_fusion',
            'predictive_analysis',
            'smart_knowledge_update',
            'clear_cache',
            'get_integration_stats'
        ]

        for method_name in compatible_methods:
            assert hasattr(integration, method_name), f"缺少兼容接口: {method_name}"

        logger.info(f"✅ 所有{len(compatible_methods)}个兼容接口存在")
        test_results.append(("向后兼容性", True))
    except Exception as e:
        logger.error(f"❌ 向后兼容性验证失败: {e}")
        test_results.append(("向后兼容性", False))

    # 测试5: 验证新增接口
    logger.info("\n🆕 测试5: 验证新增接口")
    try:
        new_methods = [
            'get_semantic_search_module',
            'get_knowledge_fusion_module',
            'get_predictive_analysis_module',
            'get_knowledge_management_module',
            'get_cache_manager_module',
            'get_architecture_info',
            'get_optimization_suggestions'
        ]

        for method_name in new_methods:
            assert hasattr(integration, method_name), f"缺少新增接口: {method_name}"

        logger.info(f"✅ 所有{len(new_methods)}个新增接口存在")
        test_results.append(("新增接口", True))
    except Exception as e:
        logger.error(f"❌ 新增接口验证失败: {e}")
        test_results.append(("新增接口", False))

    # 测试6: 验证架构信息
    logger.info("\n📊 测试6: 验证架构信息")
    try:
        arch_info = integration.get_architecture_info()

        assert arch_info['version'] == 'V5.8', "版本号不正确"
        assert arch_info['architecture'] == 'modular', "架构类型不正确"
        assert 'modules' in arch_info, "缺少模块信息"
        assert len(arch_info['modules']) == 5, "模块数量不正确"

        logger.info(f"✅ 架构信息正确: {arch_info['version']} - {arch_info['architecture']}")
        logger.info(f"   模块数量: {len(arch_info['modules'])}")
        logger.info(f"   内聚性提升: {arch_info['improvements']['cohesion_improvement']}")
        test_results.append(("架构信息", True))
    except Exception as e:
        logger.error(f"❌ 架构信息验证失败: {e}")
        test_results.append(("架构信息", False))

    # 测试7: 验证缓存管理
    logger.info("\n💾 测试7: 验证缓存管理")
    try:
        # 测试缓存设置和获取
        cache_manager = integration.cache_manager

        # 注册测试缓存
        cache_manager.register_cache('test_cache', max_size=10, ttl=60)

        # 设置缓存
        cache_manager.set('test_cache', 'key1', 'value1')
        cache_manager.set('test_cache', 'key2', 'value2')

        # 获取缓存
        value1 = cache_manager.get('test_cache', 'key1')
        value2 = cache_manager.get('test_cache', 'key2')

        assert value1 == 'value1', "缓存值1不正确"
        assert value2 == 'value2', "缓存值2不正确"

        # 获取缓存统计
        stats = cache_manager.get_cache_stats('test_cache')
        assert stats['size'] == 2, "缓存大小不正确"

        logger.info("✅ 缓存管理功能正常")
        test_results.append(("缓存管理", True))
    except Exception as e:
        logger.error(f"❌ 缓存管理验证失败: {e}")
        test_results.append(("缓存管理", False))

    # 测试8: 验证性能统计
    logger.info("\n📈 测试8: 验证性能统计")
    try:
        # 获取集成统计
        stats = integration.get_integration_stats()

        assert 'version' in stats, "统计信息缺少版本号"
        assert 'semantic_search' in stats, "统计信息缺少语义搜索统计"
        assert 'knowledge_fusion' in stats, "统计信息缺少知识融合统计"
        assert 'cache_manager' in stats, "统计信息缺少缓存管理统计"

        logger.info("✅ 性能统计功能正常")
        logger.info(f"   版本: {stats['version']}")
        logger.info(f"   缓存命中率: {stats['cache_manager']['hit_rate']:.1%}")
        test_results.append(("性能统计", True))
    except Exception as e:
        logger.error(f"❌ 性能统计验证失败: {e}")
        test_results.append(("性能统计", False))

    # 测试总结
    logger.info("\n" + "=" * 70)
    logger.info("📋 测试结果总结")
    logger.info("=" * 70)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    pass_rate = (passed / total) * 100 if total > 0 else 0

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("=" * 70)
    logger.info(f"总体结果: {passed}/{total} 通过 ({pass_rate:.1f}%)")
    logger.info("=" * 70)

    if pass_rate == 100:
        logger.info("🎉 V5.8模块化架构验证全部通过！")
    else:
        logger.warning(f"⚠️  有 {total - passed} 个测试失败，需要检查")

    return test_results


async def main():
    """主函数"""
    try:
        results = await test_v5_8_architecture()

        # 根据测试结果设置退出码
        passed = sum(1 for _, result in results if result)
        total = len(results)

        if passed == total:
            logger.info("\n✅ V5.8模块化架构准备就绪，可以投入使用！")
            return 0
        else:
            logger.warning(f"\n⚠️  V5.8模块化架构有 {total - passed} 个问题需要解决")
            return 1

    except Exception as e:
        logger.error(f"\n❌ 测试过程发生异常: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
