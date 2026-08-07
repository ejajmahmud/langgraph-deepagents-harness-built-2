"""交易协调器集成测试脚本

测试 Phase 13 实盘交易模块的完整集成，包括：
- TradingCoordinator: 交易协调器
- MarketDataManager: 市场数据管理器
- SignalGenerator: 信号生成器
- RiskManagerV2: 风险管理器V2
- ExecutionEngine: 交易执行引擎
- PositionManager: 仓位管理器
- TradeMonitor: 交易监控器

创建时间：2026-04-28
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingCoordinatorTester:
    """交易协调器集成测试类"""

    def __init__(self):
        """初始化测试器"""
        self.trading_coordinator = None
        self.market_data_manager = None
        self.signal_generator = None
        self.risk_manager = None
        self.execution_engine = None
        self.position_manager = None
        self.trade_monitor = None

        # 测试统计
        self.test_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': []
        }

    def print_header(self, title: str) -> None:
        """打印测试标题"""
        print("\n" + "=" * 80)
        print(f"测试: {title}")
        print("=" * 80)

    def print_result(self, test_name: str, success: bool, message: str = "") -> None:
        """打印测试结果"""
        self.test_stats['total_tests'] += 1
        if success:
            self.test_stats['passed_tests'] += 1
            print(f"[PASS] {test_name}")
            if message:
                print(f"      {message}")
        else:
            self.test_stats['failed_tests'] += 1
            print(f"[FAIL] {test_name}")
            if message:
                print(f"      {message}")
            self.test_stats['errors'].append(f"{test_name}: {message}")

    def print_summary(self) -> None:
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("测试摘要")
        print("=" * 80)
        print(f"总测试数: {self.test_stats['total_tests']}")
        print(f"通过测试: {self.test_stats['passed_tests']}")
        print(f"失败测试: {self.test_stats['failed_tests']}")
        print(f"成功率: {self.test_stats['passed_tests'] / self.test_stats['total_tests'] * 100:.1f}%")
        if self.test_stats['errors']:
            print("\n错误详情:")
            for error in self.test_stats['errors']:
                print(f"  - {error}")
        print("=" * 80)

    async def test_module_import(self) -> bool:
        """测试1: 模块导入"""
        self.print_header("1. 模块导入测试")

        try:
            # 导入交易模块
            from trading import (
                get_trading_coordinator,
                get_market_data_manager,
                get_signal_generator,
                get_risk_manager_v2,
                get_execution_engine,
                get_position_manager,
                get_trade_monitor,
            )
            from trading import (
                TradingCoordinator,
                MarketDataManager,
                SignalGenerator,
                RiskManagerV2,
                ExecutionEngine,
                PositionManager,
                TradeMonitor,
                TradeStatus,
                TradeEventType,
            )
            from trading import (
                DataQuality,
                SignalAction,
                SignalQuality,
                RiskLevel,
                RiskAction,
                OrderType,
                OrderSide,
                OrderStatus,
                PositionStatus,
                PositionSide,
                TradeSeverity,
                TradeAnomalyType,
            )

            # 保存引用
            self.trading_coordinator = get_trading_coordinator()
            self.market_data_manager = get_market_data_manager()
            self.signal_generator = get_signal_generator()
            self.risk_manager = get_risk_manager_v2()
            self.execution_engine = get_execution_engine()
            self.position_manager = get_position_manager()
            self.trade_monitor = get_trade_monitor()

            self.print_result("模块导入", True, "所有交易模块导入成功")
            return True

        except Exception as e:
            self.print_result("模块导入", False, f"导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_market_data_manager(self) -> bool:
        """测试2: 市场数据管理器"""
        self.print_header("2. 市场数据管理器测试")

        try:
            # 测试初始化
            init_result = await self.market_data_manager.initialize()
            self.print_result("市场数据管理器初始化", init_result)

            # 测试获取市场数据
            market_data = await self.market_data_manager.get_market_data(
                symbols=['BTCUSDT', 'ETHUSDT']
            )
            self.print_result("获取市场数据", market_data is not None,
                           f"获取到 {len(market_data.get('symbols', {}))} 个交易对的数据" if market_data else "")

            # 测试数据质量评估
            if market_data:
                quality = self.market_data_manager.assess_data_quality(market_data)
                self.print_result("数据质量评估", 'overall' in quality,
                               f"质量等级: {quality.get('overall', 'N/A')}")

            # 测试获取统计信息
            stats = self.market_data_manager.get_statistics()
            self.print_result("获取统计信息", 'total_data_requests' in stats,
                           f"总请求数: {stats.get('total_data_requests', 0)}")

            # 停止数据收集
            stop_result = await self.market_data_manager.stop()
            self.print_result("停止数据收集", stop_result)

            return True

        except Exception as e:
            self.print_result("市场数据管理器测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_signal_generator(self) -> bool:
        """测试3: 信号生成器"""
        self.print_header("3. 信号生成器测试")

        try:
            # 测试初始化
            init_result = await self.signal_generator.initialize()
            self.print_result("信号生成器初始化", init_result)

            # 创建模拟市场数据
            market_data = {
                'timestamp': datetime.now().isoformat(),
                'symbols': {
                    'BTCUSDT': {
                        'price': {
                            'symbol': 'BTCUSDT',
                            'price': 65000.0,
                            'bid': 64990.0,
                            'ask': 65010.0,
                            'change_24h': 2.5,
                            'volume_24h': 5000.0,
                        }
                    },
                    'ETHUSDT': {
                        'price': {
                            'symbol': 'ETHUSDT',
                            'price': 3500.0,
                            'bid': 3499.0,
                            'ask': 3501.0,
                            'change_24h': 1.8,
                            'volume_24h': 10000.0,
                        }
                    }
                }
            }

            # 测试信号生成
            signals = await self.signal_generator.generate_signals(market_data)
            self.print_result("信号生成", signals is not None,
                           f"生成 {len(signals) if signals else 0} 个信号")

            # 测试信号评估
            if signals:
                evaluated = await self.signal_generator.evaluate_signals(signals)
                self.print_result("信号评估", evaluated is not None,
                               f"评估 {len(evaluated)} 个信号")

                # 测试信号过滤
                filtered = self.signal_generator.filter_signals(signals)
                self.print_result("信号过滤", filtered is not None,
                               f"过滤后剩余 {len(filtered)} 个信号")

            # 测试获取统计信息
            stats = self.signal_generator.get_statistics()
            self.print_result("获取统计信息", 'total_signals' in stats,
                           f"总信号数: {stats.get('total_signals', 0)}")

            # 测试获取信号历史
            history = self.signal_generator.get_signal_history(limit=10)
            self.print_result("获取信号历史", isinstance(history, list),
                           f"历史记录数: {len(history)}")

            return True

        except Exception as e:
            self.print_result("信号生成器测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_risk_manager(self) -> bool:
        """测试4: 风险管理器"""
        self.print_header("4. 风险管理器V2测试")

        try:
            # 测试初始化
            init_result = await self.risk_manager.initialize()
            self.print_result("风险管理器初始化", init_result)

            # 创建测试信号
            test_signals = [
                {
                    'action': 'buy',
                    'symbol': 'BTCUSDT',
                    'price': 65000.0,
                    'quantity': 0.1,
                    'confidence': 0.8,
                    'position_size': 6500.0
                }
            ]

            # 测试交易前风险检查
            risk_assessment = await self.risk_manager.check_pre_trade_risk(test_signals)
            self.print_result("交易前风险检查", risk_assessment is not None,
                           f"批准: {risk_assessment.get('approved', False)}, "
                           f"风险等级: {risk_assessment.get('risk_level', 'N/A')}")

            # 测试风险监控
            risk_status = await self.risk_manager.monitor_risk()
            self.print_result("风险监控", 'overall_risk_level' in risk_status,
                           f"整体风险等级: {risk_status.get('overall_risk_level', 'N/A')}")

            # 测试获取风险状态
            status = self.risk_manager.get_risk_status()
            self.print_result("获取风险状态", 'circuit_breaker_active' in status,
                           f"熔断器激活: {status.get('circuit_breaker_active', False)}")

            # 测试生成风险报告
            report = await self.risk_manager.generate_risk_report()
            self.print_result("生成风险报告", 'report_time' in report,
                           f"报告时间: {report.get('report_time', 'N/A')}")

            # 停止风险管理器
            stop_result = await self.risk_manager.stop()
            self.print_result("停止风险管理器", stop_result)

            return True

        except Exception as e:
            self.print_result("风险管理器测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_execution_engine(self) -> bool:
        """测试5: 交易执行引擎"""
        self.print_header("5. 交易执行引擎测试")

        try:
            # 测试初始化
            init_result = await self.execution_engine.initialize()
            self.print_result("交易执行引擎初始化", init_result)

            # 创建测试订单
            test_order = {
                'type': 'market',
                'side': 'buy',
                'symbol': 'BTCUSDT',
                'quantity': 0.001
            }

            # 测试订单执行
            execution_result = await self.execution_engine.execute_order(test_order)
            self.print_result("订单执行", 'success' in execution_result,
                           f"成功: {execution_result.get('success', False)}, "
                           f"状态: {execution_result.get('status', 'N/A')}")

            # 测试获取订单状态
            if 'order_id' in execution_result:
                order_status = self.execution_engine.get_order_status(execution_result['order_id'])
                self.print_result("获取订单状态", order_status is not None)

            # 测试获取执行报告
            report = self.execution_engine.get_execution_report()
            self.print_result("获取执行报告", 'stats' in report,
                           f"总订单数: {report.get('stats', {}).get('total_orders', 0)}")

            # 停止交易执行引擎
            stop_result = await self.execution_engine.stop()
            self.print_result("停止交易执行引擎", stop_result)

            return True

        except Exception as e:
            self.print_result("交易执行引擎测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_position_manager(self) -> bool:
        """测试6: 仓位管理器"""
        self.print_header("6. 仓位管理器测试")

        try:
            # 测试初始化
            init_result = await self.position_manager.initialize()
            self.print_result("仓位管理器初始化", init_result)

            # 创建测试仓位
            test_position = {
                'symbol': 'BTCUSDT',
                'side': 'long',
                'size': 0.1,
                'entry_price': 65000.0,
                'current_price': 65100.0,
                'unrealized_pnl': 10.0,
                'status': 'open'
            }

            # 测试添加仓位
            position_id = await self.position_manager.add_position(test_position)
            self.print_result("添加仓位", position_id is not None,
                           f"仓位ID: {position_id}")

            # 测试获取仓位
            if position_id:
                position = self.position_manager.get_position(position_id)
                self.print_result("获取仓位", position is not None)

            # 测试获取所有仓位
            positions = self.position_manager.get_positions()
            self.print_result("获取所有仓位", isinstance(positions, list),
                           f"仓位数: {len(positions)}")

            # 测试更新仓位
            if position_id:
                update_result = await self.position_manager.update_position(
                    position_id,
                    {'current_price': 65200.0, 'unrealized_pnl': 20.0}
                )
                self.print_result("更新仓位", update_result)

            # 测试关闭仓位
            if position_id:
                close_result = await self.position_manager.close_position(position_id)
                self.print_result("关闭仓位", close_result)

            # 测试获取统计信息
            stats = self.position_manager.get_statistics()
            self.print_result("获取统计信息", 'total_opened' in stats,
                           f"总开仓数: {stats.get('total_opened', 0)}")

            return True

        except Exception as e:
            self.print_result("仓位管理器测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_trade_monitor(self) -> bool:
        """测试7: 交易监控器"""
        self.print_header("7. 交易监控器测试")

        try:
            # 测试初始化
            init_result = await self.trade_monitor.initialize()
            self.print_result("交易监控器初始化", init_result)

            # 创建测试交易
            test_trade = {
                'trade_id': 'TEST_TRADE_001',
                'symbol': 'BTCUSDT',
                'side': 'buy',
                'quantity': 0.1,
                'price': 65000.0,
                'status': 'filled',
                'execution_time': 0.5,
                'profit': 10.0,
                'slippage': 0.1
            }

            # 测试添加交易
            add_result = await self.trade_monitor.add_trade(test_trade)
            self.print_result("添加交易", add_result)

            # 测试获取交易
            trade = self.trade_monitor.get_trade('TEST_TRADE_001')
            self.print_result("获取交易", trade is not None)

            # 测试获取所有交易
            trades = self.trade_monitor.get_trades()
            self.print_result("获取所有交易", isinstance(trades, list),
                           f"交易数: {len(trades)}")

            # 测试性能指标
            metrics = self.trade_monitor.get_performance_metrics()
            self.print_result("获取性能指标", 'total_trades' in metrics,
                           f"总交易数: {metrics.get('total_trades', 0)}")

            # 测试异常检测
            if 'execution_time' in test_trade:
                anomaly = self.trade_monitor.detect_anomaly(test_trade)
                self.print_result("异常检测", anomaly is not None)

            # 测试生成报告
            report = await self.trade_monitor.generate_report()
            self.print_result("生成报告", 'report_time' in report)

            # 停止交易监控器
            stop_result = await self.trade_monitor.stop()
            self.print_result("停止交易监控器", stop_result)

            return True

        except Exception as e:
            self.print_result("交易监控器测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_trading_coordinator(self) -> bool:
        """测试8: 交易协调器"""
        self.print_header("8. 交易协调器测试")

        try:
            # 测试初始化
            init_result = await self.trading_coordinator.initialize()
            self.print_result("交易协调器初始化", init_result)

            # 测试启动
            start_result = await self.trading_coordinator.start()
            self.print_result("启动交易协调器", start_result)

            # 测试获取交易状态
            status = self.trading_coordinator.get_trading_status()
            self.print_result("获取交易状态", status is not None,
                           f"队列大小: {status.get('queue_size', 0)}, "
                           f"执行中: {status.get('executing_trades', 0)}")

            # 测试获取性能指标
            metrics = self.trading_coordinator.get_performance_metrics()
            self.print_result("获取性能指标", metrics is not None,
                           f"成功率: {metrics.get('success_rate', 0):.1%}")

            # 测试事件注册
            event_called = []

            async def test_event_handler(event):
                event_called.append(event['type'])

            self.trading_coordinator.register_event_handler('test_event', test_event_handler)

            # 测试事件发布
            await self.trading_coordinator.publish_trade_event({
                'type': 'test_event',
                'data': {'test': True}
            })
            self.print_result("事件发布和处理", 'test_event' in event_called)

            # 等待一小段时间
            await asyncio.sleep(2)

            # 测试停止
            stop_result = await self.trading_coordinator.stop()
            self.print_result("停止交易协调器", stop_result)

            return True

        except Exception as e:
            self.print_result("交易协调器测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_system_integration(self) -> bool:
        """测试9: 系统集成测试"""
        self.print_header("9. 系统集成测试")

        try:
            # 导入系统协调器
            from integration.system_coordinator import get_system_coordinator

            # 获取系统协调器
            coordinator = get_system_coordinator()

            # 测试初始化
            init_result = await coordinator.initialize()
            self.print_result("系统协调器初始化", init_result)

            # 测试启动
            start_result = await coordinator.start()
            self.print_result("启动系统", start_result)

            # 等待一小段时间让系统运行
            await asyncio.sleep(3)

            # 测试获取系统状态
            system_status = coordinator.get_system_status()
            self.print_result("获取系统状态", system_status is not None,
                           f"系统状态: {system_status.get('system_status', 'N/A')}, "
                           f"模块数: {len(system_status.get('module_status', {}))}")

            # 测试停止
            stop_result = await coordinator.stop()
            self.print_result("停止系统", stop_result)

            return True

        except Exception as e:
            self.print_result("系统集成测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_strategy_integration(self) -> bool:
        """测试10: 策略集成测试"""
        self.print_header("10. 策略集成测试")

        try:
            # 导入策略
            from strategies.cross_exchange import CrossExchangeArbitrageStrategy
            from strategies.triangular_arbitrage import TriangularArbitrageStrategy
            from strategies.funding_rate import FundingRateArbitrageStrategy
            from strategies.basis_trading import BasisTradingStrategy

            # 策略配置
            config = {
                'min_profit_rate': 0.5,
                'max_position_size': 1000.0,
                'symbols': ['BTCUSDT', 'ETHUSDT']
            }

            # 测试跨交易所套利策略
            cross_strategy = CrossExchangeArbitrageStrategy(config)
            cross_strategy.start()
            self.print_result("跨交易所套利策略实例化", cross_strategy.STRATEGY_NAME == "cross_exchange")

            # 测试三角套利策略
            tri_strategy = TriangularArbitrageStrategy(config)
            tri_strategy.start()
            self.print_result("三角套利策略实例化", tri_strategy.STRATEGY_NAME == "triangular")

            # 测试资金费率套利策略
            funding_config = config.copy()
            funding_config['spot_symbols'] = ['BTC/USDT', 'ETH/USDT']
            funding_strategy = FundingRateArbitrageStrategy(funding_config)
            funding_strategy.start()
            self.print_result("资金费率套利策略实例化", funding_strategy.STRATEGY_NAME == "funding_rate")

            # 测试基差套利策略
            basis_config = config.copy()
            basis_config['futures_exchange'] = 'binance'  # 假设配置
            basis_config['preferred_exchange'] = 'binance'
            basis_strategy = BasisTradingStrategy(basis_config)
            basis_strategy.start()
            self.print_result("基差套利策略实例化", basis_strategy.STRATEGY_NAME == "basis_trading")

            # 停止策略
            cross_strategy.stop()
            tri_strategy.stop()
            funding_strategy.stop()
            basis_strategy.stop()

            return True

        except Exception as e:
            self.print_result("策略集成测试", False, f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_all_tests(self) -> None:
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("交易协调器集成测试")
        print("=" * 80)
        print(f"开始时间: {datetime.now().isoformat()}")

        # 运行测试
        await self.test_module_import()
        await self.test_market_data_manager()
        await self.test_signal_generator()
        await self.test_risk_manager()
        await self.test_execution_engine()
        await self.test_position_manager()
        await self.test_trade_monitor()
        await self.test_trading_coordinator()
        await self.test_system_integration()
        await self.test_strategy_integration()

        # 打印摘要
        self.print_summary()

        print(f"\n结束时间: {datetime.now().isoformat()}")
        print("=" * 80)


async def main():
    """主函数"""
    tester = TradingCoordinatorTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
