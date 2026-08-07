#!/usr/bin/env python3
"""
V15.0 系统验证脚本 - 简化版
验证核心组件的初始化和基本功能
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
log_dir = project_root / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'verify_v15_0.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def test_imports():
    """测试模块导入"""
    logger.info("[TEST] 测试模块导入...")

    try:
        from storage.hybrid_memo0_storage import HybridMemo0Storage, create_hybrid_storage
        from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine, initialize_low_risk_arbitrage_engine, get_low_risk_arbitrage_engine
        from storage.knowledge_base import KnowledgeBase, initialize_knowledge_base, get_knowledge_base
        from risk.deep_risk_manager import DeepRiskManager, initialize_deep_risk_manager, get_deep_risk_manager

        logger.info("[SUCCESS] 所有模块导入成功")
        return {
            "status": "success",
            "modules": ["hybrid_memo0_storage", "low_risk_arbitrage_engine", "knowledge_base", "deep_risk_manager"]
        }

    except Exception as e:
        logger.error(f"[FAILED] 模块导入失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def test_storage_initialization():
    """测试存储系统初始化"""
    logger.info("[TEST] 测试存储系统初始化...")

    try:
        import os
        from storage.hybrid_memo0_storage import create_hybrid_storage

        config = {
            'hot_cache_size': 1000,
            'compression': True,
            'local_db_path': 'crypto_arbitrage_data.db',
            'mem0': {
                'api_key': os.getenv('MEM0_API_KEY', ''),
                'user_id': os.getenv('MEM0_USER_ID', 'crypto-arbitrage-v15-user'),
                'agent_id': os.getenv('MEM0_AGENT_ID', 'trading-bot-v15')
            }
        }

        storage = create_hybrid_storage(config)
        logger.info(f"[SUCCESS] 存储系统初始化成功: {type(storage).__name__}")

        return {
            "status": "success",
            "storage_type": type(storage).__name__
        }

    except Exception as e:
        logger.error(f"[FAILED] 存储系统初始化失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def test_knowledge_base_initialization():
    """测试知识库初始化"""
    logger.info("[TEST] 测试知识库初始化...")

    try:
        from storage.knowledge_base import initialize_knowledge_base

        kb = initialize_knowledge_base()
        logger.info(f"[SUCCESS] 知识库初始化成功: {type(kb).__name__}")

        # 检查知识库状态
        stats = kb.get_statistics()
        logger.info(f"[INFO] 知识库统计: {stats}")

        return {
            "status": "success",
            "kb_type": type(kb).__name__,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"[FAILED] 知识库初始化失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def test_risk_manager_initialization():
    """测试风险管理器初始化"""
    logger.info("[TEST] 测试风险管理器初始化...")

    try:
        from risk.deep_risk_manager import initialize_deep_risk_manager, get_deep_risk_manager

        config = {
            'max_loss_per_trade': 500,
            'daily_loss_limit': 1000,
            'max_drawdown': 0.10,
            'max_position_size': 5000,
            'risk_tolerance': 'conservative'
        }

        initialize_deep_risk_manager(config)
        risk_manager = get_deep_risk_manager()

        if risk_manager is None:
            raise Exception("风险管理器初始化后为None")

        logger.info(f"[SUCCESS] 风险管理器初始化成功: {type(risk_manager).__name__}")

        return {
            "status": "success",
            "risk_manager_type": type(risk_manager).__name__
        }

    except Exception as e:
        logger.error(f"[FAILED] 风险管理器初始化失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def test_arbitrage_engine_initialization():
    """测试套利引擎初始化"""
    logger.info("[TEST] 测试套利引擎初始化...")

    try:
        from strategies.low_risk_arbitrage_engine import initialize_low_risk_arbitrage_engine, get_low_risk_arbitrage_engine

        initialize_low_risk_arbitrage_engine()
        engine = get_low_risk_arbitrage_engine()

        if engine is None:
            raise Exception("套利引擎初始化后为None")

        logger.info(f"[SUCCESS] 套利引擎初始化成功: {type(engine).__name__}")

        return {
            "status": "success",
            "engine_type": type(engine).__name__
        }

    except Exception as e:
        logger.error(f"[FAILED] 套利引擎初始化失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def generate_verification_report(results):
    """生成验证报告"""
    report = f"""
# V15.0 系统验证报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 验证概况

- **总测试数**: {len(results)}
- **成功测试数**: {sum(1 for r in results.values() if r.get('status') == 'success')}
- **失败测试数**: {sum(1 for r in results.values() if r.get('status') == 'failed')}
- **成功率**: {sum(1 for r in results.values() if r.get('status') == 'success') / len(results) * 100:.1f}%

## 测试详情

### 1. 模块导入测试
- **状态**: {results.get('imports', {}).get('status', 'UNKNOWN').upper()}
- **导入模块**: {results.get('imports', {}).get('modules', [])}

### 2. 存储系统初始化测试
- **状态**: {results.get('storage', {}).get('status', 'UNKNOWN').upper()}
- **存储类型**: {results.get('storage', {}).get('storage_type', 'N/A')}

### 3. 知识库初始化测试
- **状态**: {results.get('knowledge_base', {}).get('status', 'UNKNOWN').upper()}
- **知识库类型**: {results.get('knowledge_base', {}).get('kb_type', 'N/A')}

### 4. 风险管理器初始化测试
- **状态**: {results.get('risk_manager', {}).get('status', 'UNKNOWN').upper()}
- **风险管理器类型**: {results.get('risk_manager', {}).get('risk_manager_type', 'N/A')}

### 5. 套利引擎初始化测试
- **状态**: {results.get('arbitrage_engine', {}).get('status', 'UNKNOWN').upper()}
- **套利引擎类型**: {results.get('arbitrage_engine', {}).get('engine_type', 'N/A')}

## 结论

V15.0 系统核心组件{'初始化成功' if all(r.get('status') == 'success' for r in results.values()) else '存在问题'}

{'✅ 所有核心组件正常，系统可以进行下一阶段开发' if all(r.get('status') == 'success' for r in results.values()) else '❌ 部分组件需要修复'}

## 下一步

1. 修复失败的组件
2. 实现完整的交易流程测试
3. 性能基准测试
4. 准备V15.1迭代

---

**报告生成**: V15.0 系统验证器
"""

    return report


def main():
    """主函数"""
    print("\n" + "="*60)
    print("[START] V15.0 系统验证开始")
    print("="*60 + "\n")

    results = {}

    # 运行测试
    try:
        # 1. 模块导入测试
        results['imports'] = test_imports()
        print()

        # 2. 存储系统初始化测试
        results['storage'] = test_storage_initialization()
        print()

        # 3. 知识库初始化测试
        results['knowledge_base'] = test_knowledge_base_initialization()
        print()

        # 4. 风险管理器初始化测试
        results['risk_manager'] = test_risk_manager_initialization()
        print()

        # 5. 套利引擎初始化测试
        results['arbitrage_engine'] = test_arbitrage_engine_initialization()
        print()

    except Exception as e:
        logger.error(f"[ERROR] 验证过程中发生错误: {e}")
        print(f"\n[FAILED] 验证失败: {e}\n")
        return

    # 生成验证报告
    report = generate_verification_report(results)

    # 保存报告 - 修复路径问题
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / 'verify_v15_0_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"[REPORT] 验证报告已保存到: {report_path}")

    # 保存验证结果JSON
    results_path = reports_dir / 'verify_v15_0_results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"[RESULTS] 验证结果已保存到: {results_path}")

    print("\n" + "="*60)
    print("[COMPLETE] V15.0 系统验证完成")
    print("="*60 + "\n")

    # 显示摘要
    print(f"总测试数: {len(results)}")
    print(f"成功测试: {sum(1 for r in results.values() if r.get('status') == 'success')}")
    print(f"失败测试: {sum(1 for r in results.values() if r.get('status') == 'failed')}")
    print(f"成功率: {sum(1 for r in results.values() if r.get('status') == 'success') / len(results) * 100:.1f}%")
    print()


if __name__ == "__main__":
    main()
