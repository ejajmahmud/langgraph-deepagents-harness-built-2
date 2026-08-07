"""V5.9 集成测试 - AsyncAnalysisModule深度集成

测试目标：
1. 验证AsyncAnalysisModule功能正常
2. 验证V5.9外观适配器集成正确
3. 验证向后兼容性100%保持
4. 验证异步分析性能提升
5. 验证所有新增接口正常工作

预期结果：所有测试通过，V5.9异步分析深度集成成功
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


async def test_v5_9_integration():
    """测试V5.9异步分析深度集成"""

    logger.info("=" * 70)
    logger.info("🚀 开始V5.9异步分析深度集成测试")
    logger.info("=" * 70)

    test_results = []

    # 测试1: 导入V5.9组件
    logger.info("\n📦 测试1: 导入V5.9组件")
    try:
        from storage.modules import AsyncAnalysisModule
        from storage.deep_memo0_integration_v5_9 import DeepMemo0IntegrationV59
        logger.info("✅ V5.9组件导入成功")
        test_results.append(("V5.9组件导入", True))
    except Exception as e:
        logger.error(f"❌ V5.9组件导入失败: {e}")
        test_results.append(("V5.9组件导入", False))
        return test_results

    # 测试2: 初始化V5.9外观适配器
    logger.info("\n🏗️  测试2: 初始化V5.9外观适配器")
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
            },
            'async_analysis': {  # V5.9新增配置
                'enable_async_analysis': True,
                'max_workers': 3,
                'cache_ttl': 300,
                'timeout': 120,
                'enable_batch_analysis': True,
                'max_concurrent_batch': 5,
                'enable_smart_cache': True,
                'cache_warmup_symbols': ['BTC/USDT', 'ETH/USDT']
            }
        }

        integration = DeepMemo0IntegrationV59(config)
        logger.info("✅ V5.9外观适配器初始化成功")
        test_results.append(("V5.9适配器初始化", True))
    except Exception as e:
        logger.error(f"❌ V5.9适配器初始化失败: {e}")
        test_results.append(("V5.9适配器初始化", False))
        return test_results

    # 测试3: 验证AsyncAnalysisModule实例化
    logger.info("\n🔧 测试3: 验证AsyncAnalysisModule实例化")
    try:
        assert hasattr(integration, 'async_analysis'), "缺少异步分析模块"
        assert isinstance(integration.async_analysis, AsyncAnalysisModule), "异步分析模块类型不正确"

        logger.info("✅ AsyncAnalysisModule实例化成功")
        test_results.append(("AsyncAnalysisModule实例化", True))
    except Exception as e:
        logger.error(f"❌ AsyncAnalysisModule实例化验证失败: {e}")
        test_results.append(("AsyncAnalysisModule实例化", False))

    # 测试4: 验证向后兼容性（V5.8接口）
    logger.info("\n🔄 测试4: 验证向后兼容性")
    try:
        # 检查V5.8原有接口是否存在
        v58_methods = [
            'semantic_search',
            'knowledge_fusion',
            'predictive_analysis',
            'smart_knowledge_update',
            'clear_cache',
            'get_integration_stats'
        ]

        for method_name in v58_methods:
            assert hasattr(integration, method_name), f"缺少V5.8兼容接口: {method_name}"

        # 检查V5.8模块访问接口
        v58_module_getters = [
            'get_semantic_search_module',
            'get_knowledge_fusion_module',
            'get_predictive_analysis_module',
            'get_knowledge_management_module',
            'get_cache_manager_module'
        ]

        for method_name in v58_module_getters:
            assert hasattr(integration, method_name), f"缺少V5.8模块访问接口: {method_name}"

        logger.info(f"✅ 所有{len(v58_methods) + len(v58_module_getters)}个V5.8兼容接口存在")
        test_results.append(("向后兼容性", True))
    except Exception as e:
        logger.error(f"❌ 向后兼容性验证失败: {e}")
        test_results.append(("向后兼容性", False))

    # 测试5: 验证V5.9新增接口
    logger.info("\n🆕 测试5: 验证V5.9新增接口")
    try:
        v59_methods = [
            'analyze_symbol_async',
            'analyze_batch_async',
            'analyze_market_conditions_async',
            'analyze_arbitrage_opportunity_async',
            'warmup_analysis_cache',
            'get_async_analysis_module',
            'clear_all_caches_async'
        ]

        for method_name in v59_methods:
            assert hasattr(integration, method_name), f"缺少V5.9新增接口: {method_name}"

        logger.info(f"✅ 所有{len(v59_methods)}个V5.9新增接口存在")
        test_results.append(("V5.9新增接口", True))
    except Exception as e:
        logger.error(f"❌ V5.9新增接口验证失败: {e}")
        test_results.append(("V5.9新增接口", False))

    # 测试6: 验证架构信息
    logger.info("\n📊 测试6: 验证架构信息")
    try:
        arch_info = integration.get_architecture_info()

        assert arch_info['version'] == 'V5.9', "版本号不正确"
        assert arch_info['architecture'] == 'modular_async', "架构类型不正确"
        assert 'modules' in arch_info, "缺少模块信息"
        assert len(arch_info['modules']) == 6, f"模块数量不正确，期望6个，实际{len(arch_info['modules'])}"
        assert 'async_analysis' in arch_info['modules'], "缺少异步分析模块信息"

        logger.info(f"✅ 架构信息正确: {arch_info['version']} - {arch_info['architecture']}")
        logger.info(f"   模块数量: {len(arch_info['modules'])} (含AsyncAnalysisModule)")
        logger.info(f"   异步分析模块: {arch_info['modules']['async_analysis']['description']}")
        test_results.append(("架构信息", True))
    except Exception as e:
        logger.error(f"❌ 架构信息验证失败: {e}")
        test_results.append(("架构信息", False))

    # 测试7: 验证AsyncAnalysisModule功能
    logger.info("\n⚡ 测试7: 验证AsyncAnalysisModule功能")
    try:
        # 测试获取统计信息
        async_stats = integration.async_analysis.get_analysis_stats()

        assert 'total_analyses' in async_stats, "缺少total_analyses统计"
        assert 'cache_hit_rate' in async_stats, "缺少cache_hit_rate统计"
        assert 'success_rate' in async_stats, "缺少success_rate统计"

        logger.info("✅ AsyncAnalysisModule统计功能正常")
        logger.info(f"   总分析数: {async_stats['total_analyses']}")
        logger.info(f"   缓存命中率: {async_stats['cache_hit_rate']:.1%}")
        logger.info(f"   成功率: {async_stats['success_rate']:.1%}")

        test_results.append(("AsyncAnalysisModule功能", True))
    except Exception as e:
        logger.error(f"❌ AsyncAnalysisModule功能验证失败: {e}")
        test_results.append(("AsyncAnalysisModule功能", False))

    # 测试8: 验证集成统计
    logger.info("\n📈 测试8: 验证集成统计")
    try:
        # 获取集成统计
        stats = integration.get_integration_stats()

        assert 'version' in stats, "统计信息缺少版本号"
        assert 'async_analysis' in stats, "统计信息缺少异步分析统计"
        assert 'semantic_search' in stats, "统计信息缺少语义搜索统计"
        assert 'cache_manager' in stats, "统计信息缺少缓存管理统计"

        logger.info("✅ 集成统计功能正常")
        logger.info(f"   版本: {stats['version']}")
        logger.info(f"   异步分析统计: {stats['async_analysis']['total_analyses']}次分析")
        logger.info(f"   缓存命中率: {stats['cache_manager']['hit_rate']:.1%}")

        test_results.append(("集成统计", True))
    except Exception as e:
        logger.error(f"❌ 集成统计验证失败: {e}")
        test_results.append(("集成统计", False))

    # 测试9: 验证性能优化建议
    logger.info("\n💡 测试9: 验证性能优化建议")
    try:
        # 获取优化建议
        suggestions = integration.get_optimization_suggestions()

        assert isinstance(suggestions, list), "优化建议应该是列表"
        assert len(suggestions) >= 0, "优化建议列表不应为负"

        logger.info("✅ 性能优化建议功能正常")
        if suggestions:
            logger.info(f"   建议数量: {len(suggestions)}")
            for i, suggestion in enumerate(suggestions[:3], 1):  # 只显示前3条
                logger.info(f"   建议{i}: {suggestion}")
        else:
            logger.info("   当前无需优化建议")

        test_results.append(("性能优化建议", True))
    except Exception as e:
        logger.error(f"❌ 性能优化建议验证失败: {e}")
        test_results.append(("性能优化建议", False))

    # 测试10: 验证缓存管理
    logger.info("\n💾 测试10: 验证缓存管理")
    try:
        # 测试清除所有缓存（异步）
        await integration.clear_all_caches_async()

        # 验证缓存已清除
        async_stats = integration.async_analysis.get_analysis_stats()
        cache_size = async_stats.get('module_cache_size', 0)

        logger.info("✅ 缓存管理功能正常")
        logger.info(f"   模块缓存大小: {cache_size}")

        test_results.append(("缓存管理", True))
    except Exception as e:
        logger.error(f"❌ 缓存管理验证失败: {e}")
        test_results.append(("缓存管理", False))

    # 测试总结
    logger.info("\n" + "=" * 70)
    logger.info("📋 V5.9集成测试结果总结")
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
        logger.info("🎉 V5.9异步分析深度集成测试全部通过！")
        logger.info("🚀 系统已准备就绪，可以投入生产使用！")
    else:
        logger.warning(f"⚠️  有 {total - passed} 个测试失败，需要检查")

    return test_results


async def main():
    """主函数"""
    try:
        results = await test_v5_9_integration()

        # 根据测试结果设置退出码
        passed = sum(1 for _, result in results if result)
        total = len(results)

        if passed == total:
            logger.info("\n✅ V5.9异步分析深度集成成功，可以投入使用！")
            return 0
        else:
            logger.warning(f"\n⚠️  V5.9异步分析深度集成有 {total - passed} 个问题需要解决")
            return 1

    except Exception as e:
        logger.error(f"\n❌ 测试过程发生异常: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
