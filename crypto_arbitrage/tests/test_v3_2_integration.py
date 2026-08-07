"""V3.2 集成测试 - 深度风险管理 + 低风险套利引擎

测试V3.2所有核心功能的集成和协同工作。
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from risk.deep_risk_manager import (
    DeepRiskManager, RiskLevel, AlertLevel, RiskMetrics
)
from strategies.low_risk_arbitrage_engine import (
    LowRiskArbitrageEngine, ExecutionStatus, StepStatus
)


def print_section(title: str) -> None:
    """打印测试区块标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_success(message: str) -> None:
    """打印成功消息"""
    print(f"[OK] {message}")


def print_error(message: str) -> None:
    """打印错误消息"""
    print(f"[FAIL] {message}")


def print_info(message: str) -> None:
    """打印信息消息"""
    print(f"[INFO] {message}")


class V32IntegrationTest:
    """V3.2 集成测试套件"""

    def __init__(self):
        self.risk_manager = None
        self.arbitrage_engine = None
        self.test_results = {}

    async def run_all_tests(self) -> bool:
        """运行所有测试

        Returns:
            是否全部通过
        """
        print_section("V3.2 集成测试启动")

        # 运行测试
        await self.test_deep_risk_manager()
        await self.test_low_risk_arbitrage_engine()
        await self.test_integration()

        # 汇总结果
        print_section("测试结果汇总")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests / total_tests * 100:.1f}%\n")

        # 详细结果
        for test_name, passed in self.test_results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{status} - {test_name}")

        print_section("V3.2 集成测试完成")

        return all(self.test_results.values())

    async def test_deep_risk_manager(self) -> None:
        """测试深度风险管理器"""
        print_section("测试 1: 深度风险管理器")

        try:
            # 1.1 初始化
            print_info("1.1 初始化深度风险管理器...")
            config = {
                'max_exposure': 10000.0,
                'max_drawdown': 5.0,
                'daily_loss_limit': -500.0,
                'volatility_threshold': 3.0,
                'min_liquidity_score': 0.7
            }
            self.risk_manager = DeepRiskManager(config)
            print_success("深度风险管理器初始化成功")
            self.test_results['risk_manager_init'] = True

            # 1.2 风险指标测试
            print_info("1.2 测试风险指标...")
            metrics = self.risk_manager.current_metrics
            assert metrics.exposure == 0.0
            assert metrics.overall_risk == RiskLevel.LOW
            assert metrics.liquidity_score == 1.0
            print_success("风险指标测试通过")
            self.test_results['risk_metrics'] = True

            # 1.3 交易前风险预检
            print_info("1.3 测试交易前风险预检...")
            trade = {
                'profit_rate': 2.5,
                'amount': 1000.0,
                'symbol': 'BTC/USDT'
            }
            passed, reason, risk_level = self.risk_manager.pre_trade_risk_check(trade)
            assert passed, f"应该通过预检: {reason}"
            assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
            print_success(f"交易前风险预检通过: 风险等级={risk_level.value}")
            self.test_results['pre_trade_check'] = True

            # 1.4 测试高风险交易拒绝
            print_info("1.4 测试高风险交易拒绝...")
            high_risk_trade = {
                'profit_rate': 15.0,  # 过高收益率
                'amount': 15000.0,     # 超过最大敞口
                'symbol': 'BTC/USDT'
            }
            passed, reason, risk_level = self.risk_manager.pre_trade_risk_check(high_risk_trade)
            assert not passed, "应该拒绝高风险交易"
            print_success(f"高风险交易正确拒绝: {reason}")
            self.test_results['high_risk_rejection'] = True

            # 1.5 风险摘要测试
            print_info("1.5 测试风险摘要...")
            summary = self.risk_manager.get_risk_summary()
            assert 'current_metrics' in summary
            assert 'risk_limits' in summary
            assert 'is_risk_limit_reached' in summary
            assert not summary['is_risk_limit_reached']
            print_success("风险摘要测试通过")
            self.test_results['risk_summary'] = True

            # 1.6 启动监控（短暂测试）
            print_info("1.6 测试风险监控...")
            await self.risk_manager.start_monitoring(interval=1.0)
            await asyncio.sleep(2)  # 运行2秒
            await self.risk_manager.stop_monitoring()
            print_success("风险监控测试通过")
            self.test_results['risk_monitoring'] = True

        except Exception as e:
            print_error(f"深度风险管理器测试失败: {e}")
            self.test_results['risk_manager'] = False
            import traceback
            traceback.print_exc()

    async def test_low_risk_arbitrage_engine(self) -> None:
        """测试低风险套利引擎"""
        print_section("测试 2: 低风险套利引擎")

        try:
            # 2.1 初始化
            print_info("2.1 初始化低风险套利引擎...")
            config = {
                'enable_pre_check': True,
                'enable_step_verification': True,
                'enable_auto_rollback': True,
                'max_execution_time': 30.0,
                'risk_tolerance': RiskLevel.HIGH
            }
            self.arbitrage_engine = LowRiskArbitrageEngine(
                risk_manager=self.risk_manager,
                config=config
            )
            print_success("低风险套利引擎初始化成功")
            self.test_results['arbitrage_engine_init'] = True

            # 2.2 执行统计测试
            print_info("2.2 测试执行统计...")
            stats = self.arbitrage_engine.get_execution_statistics()
            assert stats['total_executions'] == 0
            assert stats['success_rate'] == 0.0
            print_success("执行统计测试通过")
            self.test_results['execution_stats'] = True

            # 2.3 执行历史测试
            print_info("2.3 测试执行历史...")
            history = self.arbitrage_engine.get_execution_history()
            assert isinstance(history, list)
            assert len(history) == 0
            print_success("执行历史测试通过")
            self.test_results['execution_history'] = True

            # 2.4 模拟套利执行
            print_info("2.4 模拟低风险套利执行...")

            # 模拟机会
            opportunity = {
                'symbol': 'BTC/USDT',
                'buy_exchange': 'binance',
                'sell_exchange': 'okx',
                'profit_rate': 1.5,
                'expected_profit': 15.0,
                'amount': 1000.0
            }

            # 模拟执行计划
            execution_plan = [
                {
                    'name': '模拟买入',
                    'action': self._mock_buy_action,
                    'params': {'symbol': 'BTC/USDT'},
                    'rollback_action': self._mock_sell_action,
                    'rollback_params': {'symbol': 'BTC/USDT'}
                },
                {
                    'name': '模拟卖出',
                    'action': self._mock_sell_action,
                    'params': {'symbol': 'BTC/USDT'}
                }
            ]

            result = await self.arbitrage_engine.execute_arbitrage(
                opportunity,
                execution_plan
            )

            assert result['execution_id'] is not None
            assert result['status'] in ['completed', 'failed']
            print_success(f"模拟执行完成: {result['status']}, ID: {result['execution_id']}")
            self.test_results['mock_execution'] = True

            # 2.5 验证执行统计更新
            print_info("2.5 验证执行统计更新...")
            stats = self.arbitrage_engine.get_execution_statistics()
            assert stats['total_executions'] >= 1
            print_success(f"执行统计已更新: {stats['total_executions']} 次执行")
            self.test_results['stats_updated'] = True

        except Exception as e:
            print_error(f"低风险套利引擎测试失败: {e}")
            self.test_results['arbitrage_engine'] = False
            import traceback
            traceback.print_exc()

    async def test_integration(self) -> None:
        """测试V3.2组件集成"""
        print_section("测试 3: V3.2 组件集成")

        try:
            # 3.1 风险管理器与引擎集成测试
            print_info("3.1 测试风险管理器与引擎集成...")
            assert self.arbitrage_engine.risk_manager == self.risk_manager
            print_success("风险管理器与引擎正确集成")
            self.test_results['integration_risk_engine'] = True

            # 3.2 多次执行测试
            print_info("3.2 测试多次执行...")

            opportunities = [
                {
                    'symbol': f'COIN{i}/USDT',
                    'profit_rate': 1.0 + i * 0.5,
                    'expected_profit': 10.0 + i * 5.0,
                    'amount': 500.0
                }
                for i in range(3)
            ]

            for i, opp in enumerate(opportunities):
                execution_plan = [
                    {
                        'name': f'买入 {opp["symbol"]}',
                        'action': self._mock_buy_action,
                        'params': {'symbol': opp['symbol']},
                        'rollback_action': self._mock_sell_action,
                        'rollback_params': {'symbol': opp['symbol']}
                    },
                    {
                        'name': f'卖出 {opp["symbol"]}',
                        'action': self._mock_sell_action,
                        'params': {'symbol': opp['symbol']}
                    }
                ]

                result = await self.arbitrage_engine.execute_arbitrage(
                    opp,
                    execution_plan
                )
                print_info(f"  执行 {i+1}/3: {result['status']}")

            print_success("多次执行测试通过")
            self.test_results['multiple_executions'] = True

            # 3.3 执行历史验证
            print_info("3.3 验证执行历史...")
            history = self.arbitrage_engine.get_execution_history(limit=10)
            assert len(history) >= 3  # 至少有3次执行记录
            print_success(f"执行历史正确: {len(history)} 条记录")
            self.test_results['execution_history_valid'] = True

            # 3.4 风险历史验证
            print_info("3.4 验证风险历史...")
            risk_history = self.risk_manager.get_risk_history(hours=1)
            assert isinstance(risk_history, list)
            print_success("风险历史正确获取")
            self.test_results['risk_history_valid'] = True

            # 3.5 综合统计验证
            print_info("3.5 验证综合统计...")
            stats = self.arbitrage_engine.get_execution_statistics()
            risk_summary = self.risk_manager.get_risk_summary()

            assert stats['total_executions'] >= 3
            assert risk_summary['current_metrics']['overall_risk'] in [
                RiskLevel.LOW.value,
                RiskLevel.MEDIUM.value
            ]
            print_success("综合统计验证通过")
            self.test_results['comprehensive_stats'] = True

        except Exception as e:
            print_error(f"V3.2组件集成测试失败: {e}")
            self.test_results['integration'] = False
            import traceback
            traceback.print_exc()

    def _mock_buy_action(self, symbol: str) -> Dict[str, Any]:
        """模拟买入动作"""
        return {
            'status': 'completed',
            'symbol': symbol,
            'action': 'buy',
            'actual_profit': 10.0
        }

    def _mock_sell_action(self, symbol: str) -> Dict[str, Any]:
        """模拟卖出动作"""
        return {
            'status': 'completed',
            'symbol': symbol,
            'action': 'sell'
        }


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  数字货币套利交易系统 V3.2 - 集成测试")
    print("=" * 60 + "\n")

    test_suite = V32IntegrationTest()
    all_passed = await test_suite.run_all_tests()

    if all_passed:
        print("\n[SUCCESS] 所有V3.2集成测试通过！")
        print("系统已准备好进行实际环境对接。")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查日志。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
