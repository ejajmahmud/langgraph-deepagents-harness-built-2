"""V56.1 测试套件 - 交易所扩展与ML增强

测试内容:
1. KuCoin/Gate.io交易所支持
2. ML预测器增强 (EWMA/动量)
3. 统一系统集成

创建时间: 2026-05-08
"""

import asyncio
import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.unified_arbitrage_system_v55 import (
    UnifiedArbitrageSystemV55,
    V55ExecutionMode,
    Exchange,
    ExchangeConfig,
    LiveExchangeConnector,
    BridgeFeeMonitor,
    AdvancedRiskManager,
    initialize_v55_system,
    get_v55_system
)
from strategies.cross_chain_arbitrage import (
    CrossChainArbitrageEngine,
    Blockchain,
    MLPredictor,
    MLPredictionResult,
    initialize_cross_chain_arbitrage_engine,
    initialize_ml_predictor
)


def test_v56_1_exchange_enum():
    """测试V56.1交易所枚举扩展"""
    print("[TEST V56.1.1] 测试交易所枚举...")

    # 检查新增交易所
    assert hasattr(Exchange, 'KUCOIN'), "KuCoin未添加到Exchange枚举"
    assert hasattr(Exchange, 'GATEIO'), "Gate.io未添加到Exchange枚举"

    print("  - KuCoin枚举: OK")
    print("  - Gate.io枚举: OK")

    # 验证枚举值
    assert Exchange.KUCOIN.value == "kucoin"
    assert Exchange.GATEIO.value == "gateio"

    print("[PASS] V56.1.1 交易所枚举测试通过")
    return True


def test_v56_1_exchange_connector():
    """测试V56.1交易所连接器"""
    print("[TEST V56.1.2] 测试交易所连接器...")

    # 配置新交易所
    config = {
        'kucoin': {
            'enabled': True,
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True
        },
        'gateio': {
            'enabled': True,
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True
        }
    }

    connector = LiveExchangeConnector(config)

    # 验证配置已添加
    assert Exchange.KUCOIN in connector.exchange_configs
    assert Exchange.GATEIO in connector.exchange_configs

    print("  - KuCoin配置: OK")
    print("  - Gate.io配置: OK")

    print("[PASS] V56.1.2 交易所连接器测试通过")
    return True


def test_v56_1_ml_enhanced():
    """测试V56.1 ML预测器增强"""
    print("[TEST V56.1.3] 测试ML预测器增强...")

    # 初始化ML预测器
    ml_config = {'model_type': 'simple', 'lookback_periods': 20}
    predictor = MLPredictor(ml_config)

    # 添加测试价格数据
    test_token = "BTC"
    test_chain = Blockchain.ETHEREUM

    # 添加足够数据进行预测
    prices = [50000, 50200, 50100, 50300, 50400, 50500, 50600, 50500, 50700, 50800]
    for price in prices:
        predictor.update_price_history(test_token, test_chain, price)

    # 预测价格
    result = predictor.predict_price(test_token, test_chain)

    # 验证结果
    assert result.prediction > 0, "预测价格应该大于0"
    assert result.confidence > 0, "置信度应该大于0"

    # 验证增强特征
    assert 'ewma' in result.features_used, "应包含EWMA特征"
    assert 'momentum' in result.features_used, "应包含动量特征"

    print(f"  - 预测价格: {result.prediction:.2f}")
    print(f"  - 置信度: {result.confidence:.2f}")
    print(f"  - 特征: {result.features_used}")

    print("[PASS] V56.1.3 ML预测器增强测试通过")
    return True


def test_v56_1_system_integration():
    """测试V56.1系统集成"""
    print("[TEST V56.1.4] 测试系统集成...")

    # 配置系统
    config = {
        'execution_mode': 'fusion',
        'exchange_config': {
            'binance': {'enabled': False},
            'kucoin': {'enabled': True, 'testnet': True},
            'gateio': {'enabled': True, 'testnet': True}
        },
        'risk_config': {
            'max_position_pct': 0.1,
            'max_leverage': 3
        }
    }

    system = initialize_v55_system(config)

    # 验证系统初始化
    assert system is not None, "系统应该初始化成功"

    # 获取统计
    stats = system.get_statistics()

    print(f"  - 执行模式: {stats['execution_mode']}")
    print(f"  - 交易所连接器: {stats['components_initialized']['exchange_connector']}")

    print("[PASS] V56.1.4 系统集成测试通过")
    return True


def test_v56_1_bridge_monitor():
    """测试V56.1跨链桥费率监控"""
    print("[TEST V56.1.5] 测试跨链桥费率监控...")

    monitor = BridgeFeeMonitor()

    # 测试费率获取
    eth = Blockchain.ETHEREUM
    bsc = Blockchain.BNB_CHAIN
    sol = Blockchain.SOLANA

    fee_eth_bsc = monitor.get_bridge_fee(eth, bsc)
    fee_eth_sol = monitor.get_bridge_fee(eth, sol)

    print(f"  - ETH->BSC费率: {fee_eth_bsc:.4f}")
    print(f"  - ETH->SOL费率: {fee_eth_sol:.4f}")

    assert fee_eth_bsc > 0, "跨链桥费率应该大于0"

    print("[PASS] V56.1.5 跨链桥费率监控测试通过")
    return True


def test_v56_1_risk_manager():
    """测试V56.1风险管理器"""
    print("[TEST V56.1.6] 测试风险管理器...")

    risk_config = {
        'max_position_pct': 0.1,
        'max_leverage': 3,
        'max_daily_loss_pct': 0.05,
        'max_risk_score': 0.7,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05
    }

    manager = AdvancedRiskManager(risk_config)

    # 测试头寸计算
    position = manager.calculate_position_size(
        capital=10000,
        risk_pct=0.02,
        entry_price=50000,
        stop_loss=49000
    )

    print(f"  - 计算头寸: {position:.4f}")

    assert position > 0, "头寸应该大于0"

    print("[PASS] V56.1.6 风险管理器测试通过")
    return True


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("V56.1 测试套件 - 交易所扩展与ML增强")
    print("=" * 60)
    print()

    tests = [
        ("交易所枚举扩展", test_v56_1_exchange_enum),
        ("交易所连接器", test_v56_1_exchange_connector),
        ("ML预测器增强", test_v56_1_ml_enhanced),
        ("系统集成", test_v56_1_system_integration),
        ("跨链桥监控", test_v56_1_bridge_monitor),
        ("风险管理器", test_v56_1_risk_manager),
    ]

    passed = 0
    failed = 0

    for name, test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()

            if result:
                passed += 1
        except Exception as e:
            print(f"[FAIL] {name} 测试失败: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 60)

    return passed, failed


if __name__ == "__main__":
    asyncio.run(run_all_tests())