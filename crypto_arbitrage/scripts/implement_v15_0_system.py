"""V15.0 系统集成 - 混合存储系统 + 低风险套利引擎完善

主要功能:
1. V15.0 混合存储系统集成
2. 低风险套利引擎与 Memo0 集成
3. 性能优化和测试基准建立
4. 环境变量配置支持
5. 系统健康检查
"""

import asyncio
import json
import logging
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.hybrid_memo0_storage import HybridMemo0Storage, create_hybrid_storage
from strategies.low_risk_arbitrage_engine import LowRiskArbitrageEngine, initialize_low_risk_arbitrage_engine
from storage.knowledge_base import KnowledgeBase, initialize_knowledge_base
from risk.deep_risk_manager import DeepRiskManager, initialize_deep_risk_manager, get_deep_risk_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/v15_0_integration.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class V15SystemIntegrator:
    """V15.0 系统集成器"""

    def __init__(self, config_path: str = "config/config_v15_0.yaml"):
        """初始化系统集成器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.hybrid_storage = None
        self.arbitrage_engine = None
        self.knowledge_base = None
        self.risk_manager = None

        # 加载环境变量
        self._load_environment_variables()

        # 加载配置
        self._load_config()

    def _load_environment_variables(self) -> None:
        """加载环境变量"""
        logger.info("🔑 加载环境变量...")

        # Memo0 API 配置
        self.memo0_api_key = os.getenv('MEM0_API_KEY', '')
        self.memo0_user_id = os.getenv('MEM0_USER_ID', 'crypto-arbitrage-v15-user')
        self.memo0_agent_id = os.getenv('MEM0_AGENT_ID', 'trading-bot-v15')

        # 交易所 API 配置
        self.binance_api_key = os.getenv('BINANCE_API_KEY', '')
        self.binance_secret = os.getenv('BINANCE_SECRET', '')

        logger.info(f"✅ Memo0 API Key: {'已设置' if self.memo0_api_key else '未设置'}")
        logger.info(f"✅ Binance API Key: {'已设置' if self.binance_api_key else '未设置'}")

    def _load_config(self) -> None:
        """加载配置文件"""
        logger.info(f"📋 加载配置文件: {self.config_path}")

        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"❌ 配置文件不存在: {self.config_path}")
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            logger.info(f"✅ 配置文件加载成功")
            logger.info(f"   系统版本: {self.config.get('system', {}).get('version', 'Unknown')}")
            logger.info(f"   运行模式: {self.config.get('system', {}).get('mode', 'Unknown')}")

            # 更新 Memo0 配置（使用环境变量）
            if 'mem0' in self.config:
                self.config['mem0']['api_key'] = self.memo0_api_key or self.config['mem0'].get('api_key', '')
                self.config['mem0']['user_id'] = self.memo0_user_id
                self.config['mem0']['agent_id'] = self.memo0_agent_id

            # 更新交易所配置
            if 'exchanges' in self.config:
                if self.binance_api_key:
                    self.config['exchanges']['binance']['api_key'] = self.binance_api_key
                if self.binance_secret:
                    self.config['exchanges']['binance']['secret'] = self.binance_secret

        except Exception as e:
            logger.error(f"❌ 配置文件加载失败: {e}")
            raise

    def initialize_hybrid_storage(self) -> bool:
        """初始化混合存储系统

        Returns:
            是否成功
        """
        logger.info("🗄️  初始化混合存储系统 V15.0...")

        try:
            hybrid_config = self.config.get('hybrid_storage_v15', {})
            if not hybrid_config.get('enabled', False):
                logger.warning("⚠️  混合存储系统未启用")
                return False

            # 创建混合存储
            self.hybrid_storage = create_hybrid_storage(self.config)

            if not self.hybrid_storage:
                logger.error("❌ 混合存储系统创建失败")
                return False

            # 检查健康状态
            health = self.hybrid_storage.get_health_status()
            logger.info(f"✅ 混合存储系统初始化成功")
            logger.info(f"   云端可用: {health['cloud_available']}")
            logger.info(f"   本地可用: {health['local_available']}")
            logger.info(f"   热缓存大小: {health['hot_cache_size']}")
            logger.info(f"   错误率: {health['error_rate']:.2%}")

            return True

        except Exception as e:
            logger.error(f"❌ 混合存储系统初始化失败: {e}")
            return False

    def initialize_knowledge_base(self) -> bool:
        """初始化知识库

        Returns:
            是否成功
        """
        logger.info("📚 初始化知识库...")

        try:
            storage_config = self.config.get('storage', {})
            db_path = storage_config.get('knowledge_base_db', 'crypto_arbitrage_knowledge.db')

            self.knowledge_base = initialize_knowledge_base(db_path)

            # 获取统计信息
            stats = self.knowledge_base.get_statistics()
            logger.info(f"✅ 知识库初始化成功")
            logger.info(f"   策略数量: {stats['strategies_count']}")
            logger.info(f"   知识条目: {stats['knowledge_entries_count']}")
            logger.info(f"   交易记录: {stats['trades_count']}")

            return True

        except Exception as e:
            logger.error(f"❌ 知识库初始化失败: {e}")
            return False

    def initialize_risk_manager(self) -> bool:
        """初始化风险管理器

        Returns:
            是否成功
        """
        logger.info("⚠️  初始化风险管理器...")

        try:
            risk_config = self.config.get('risk_management', {})

            # 构建风险管理器配置
            config = {
                'max_exposure': risk_config.get('max_total_exposure', 5000),
                'max_drawdown': risk_config.get('max_drawdown', 10.0) / 100.0,  # 转换为小数
                'daily_loss_limit': risk_config.get('max_daily_loss', 500),
                'volatility_threshold': risk_config.get('max_volatility', 5.0),
                'min_liquidity_score': risk_config.get('min_liquidity_ratio', 0.5),
                'alert_callbacks': []  # 可以添加预警回调
            }

            # 初始化风险管理器
            self.risk_manager = initialize_deep_risk_manager(config)

            if self.risk_manager:
                logger.info(f"✅ 风险管理器初始化成功")
                logger.info(f"   最大日损失: ${risk_config.get('max_daily_loss', 500)}")
                logger.info(f"   最大仓位: ${risk_config.get('max_position_size', 1000)}")
                logger.info(f"   最大回撤: {risk_config.get('max_drawdown', 10.0)}%")
                logger.info(f"   最大敞口: ${risk_config.get('max_total_exposure', 5000)}")
                return True
            else:
                logger.warning("⚠️  风险管理器创建失败，将使用默认配置")
                return False

        except Exception as e:
            logger.error(f"❌ 风险管理器初始化失败: {e}")
            return False

    def initialize_arbitrage_engine(self) -> bool:
        """初始化低风险套利引擎

        Returns:
            是否成功
        """
        logger.info("⚡ 初始化低风险套利引擎 V15.0...")

        try:
            engine_config = self.config.get('low_risk_arbitrage_engine_v15', {})
            if not engine_config.get('enabled', False):
                logger.warning("⚠️  低风险套利引擎未启用")
                return False

            # 转换配置格式
            config = {
                'enable_pre_check': engine_config.get('pre_check', {}).get('enabled', True),
                'enable_step_verification': engine_config.get('execution', {}).get('step_verification', True),
                'enable_auto_rollback': engine_config.get('execution', {}).get('auto_rollback', True),
                'max_execution_time': engine_config.get('execution', {}).get('max_execution_time', 30.0),
                'risk_tolerance': 'MEDIUM'  # 默认风险容忍度
            }

            self.arbitrage_engine = initialize_low_risk_arbitrage_engine(
                risk_manager=self.risk_manager,
                config=config
            )

            if not self.arbitrage_engine:
                logger.error("❌ 低风险套利引擎创建失败")
                return False

            # 获取统计信息
            stats = self.arbitrage_engine.get_execution_statistics()
            logger.info(f"✅ 低风险套利引擎初始化成功")
            logger.info(f"   预检机制: {engine_config.get('pre_check', {}).get('enabled', True)}")
            logger.info(f"   自动回滚: {engine_config.get('execution', {}).get('auto_rollback', True)}")
            logger.info(f"   动态止损: {engine_config.get('risk_control', {}).get('dynamic_stop_loss', True)}")
            logger.info(f"   历史执行: {stats['total_executions']}")

            return True

        except Exception as e:
            logger.error(f"❌ 低风险套利引擎初始化失败: {e}")
            return False

    def integrate_systems(self) -> bool:
        """集成所有系统

        Returns:
            是否成功
        """
        logger.info("🔗 开始系统集成...")

        try:
            # 1. 初始化存储层
            if not self.initialize_hybrid_storage():
                logger.error("❌ 存储层初始化失败")
                return False

            # 2. 初始化知识库
            if not self.initialize_knowledge_base():
                logger.error("❌ 知识库初始化失败")
                return False

            # 3. 初始化风险管理器
            if not self.initialize_risk_manager():
                logger.warning("⚠️  风险管理器初始化失败，继续集成")

            # 4. 初始化套利引擎
            if not self.initialize_arbitrage_engine():
                logger.error("❌ 套利引擎初始化失败")
                return False

            logger.info("✅ 系统集成完成")
            return True

        except Exception as e:
            logger.error(f"❌ 系统集成失败: {e}")
            return False

    def run_system_check(self) -> Dict[str, Any]:
        """运行系统检查

        Returns:
            检查结果字典
        """
        logger.info("🔍 运行系统检查...")

        check_results = {
            'timestamp': datetime.now().isoformat(),
            'system_version': self.config.get('system', {}).get('version', 'Unknown'),
            'checks': {}
        }

        # 1. 混合存储检查
        if self.hybrid_storage:
            health = self.hybrid_storage.get_health_status()
            check_results['checks']['hybrid_storage'] = {
                'status': 'healthy' if health['cloud_available'] or health['local_available'] else 'unhealthy',
                'cloud_available': health['cloud_available'],
                'local_available': health['local_available'],
                'cache_hit_rate': health['cache_hit_rate'],
                'error_rate': health['error_rate']
            }
        else:
            check_results['checks']['hybrid_storage'] = {
                'status': 'not_initialized'
            }

        # 2. 知识库检查
        if self.knowledge_base:
            stats = self.knowledge_base.get_statistics()
            check_results['checks']['knowledge_base'] = {
                'status': 'healthy',
                'strategies_count': stats['strategies_count'],
                'knowledge_entries_count': stats['knowledge_entries_count'],
                'trades_count': stats['trades_count'],
                'total_profit': stats['total_profit'],
                'win_rate': stats['win_rate']
            }
        else:
            check_results['checks']['knowledge_base'] = {
                'status': 'not_initialized'
            }

        # 3. 套利引擎检查
        if self.arbitrage_engine:
            stats = self.arbitrage_engine.get_execution_statistics()
            check_results['checks']['arbitrage_engine'] = {
                'status': 'healthy',
                'total_executions': stats['total_executions'],
                'success_rate': stats['success_rate'],
                'rollback_rate': stats['rollback_rate'],
                'average_profit': stats['average_profit']
            }
        else:
            check_results['checks']['arbitrage_engine'] = {
                'status': 'not_initialized'
            }

        # 4. 风险管理器检查
        if self.risk_manager:
            check_results['checks']['risk_manager'] = {
                'status': 'healthy'
            }
        else:
            check_results['checks']['risk_manager'] = {
                'status': 'not_initialized'
            }

        # 总体状态
        all_healthy = all(
            check.get('status') in ['healthy', 'not_initialized']
            for check in check_results['checks'].values()
        )

        check_results['overall_status'] = 'healthy' if all_healthy else 'degraded'

        logger.info(f"✅ 系统检查完成 - 总体状态: {check_results['overall_status']}")

        return check_results

    def generate_integration_report(self) -> str:
        """生成集成报告

        Returns:
            报告内容
        """
        report = f"""
# V15.0 系统集成报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 系统配置

- **系统版本**: {self.config.get('system', {}).get('version', 'Unknown')}
- **运行模式**: {self.config.get('system', {}).get('mode', 'Unknown')}
- **模型**: {self.config.get('model', {}).get('model', 'Unknown')}

## 集成组件

### 1. 混合存储系统 V15.0
"""

        if self.hybrid_storage:
            health = self.hybrid_storage.get_health_status()
            report += f"""
- **状态**: ✅ 已初始化
- **云端可用**: {health['cloud_available']}
- **本地可用**: {health['local_available']}
- **热缓存大小**: {health['hot_cache_size']}
- **缓存命中率**: {health['cache_hit_rate']:.2%}
- **错误率**: {health['error_rate']:.2%}
"""
        else:
            report += "- **状态**: ❌ 未初始化\n"

        report += """
### 2. 知识库
"""

        if self.knowledge_base:
            stats = self.knowledge_base.get_statistics()
            report += f"""
- **状态**: ✅ 已初始化
- **策略数量**: {stats['strategies_count']}
- **知识条目**: {stats['knowledge_entries_count']}
- **交易记录**: {stats['trades_count']}
- **总利润**: ${stats['total_profit']:.2f}
- **胜率**: {stats['win_rate']:.2%}
"""
        else:
            report += "- **状态**: ❌ 未初始化\n"

        report += """
### 3. 低风险套利引擎
"""

        if self.arbitrage_engine:
            stats = self.arbitrage_engine.get_execution_statistics()
            report += f"""
- **状态**: ✅ 已初始化
- **历史执行**: {stats['total_executions']}
- **成功率**: {stats['success_rate']:.2%}
- **回滚率**: {stats['rollback_rate']:.2%}
- **平均利润**: ${stats['average_profit']:.2f}
"""
        else:
            report += "- **状态**: ❌ 未初始化\n"

        report += """
### 4. 风险管理器
"""

        if self.risk_manager:
            report += "- **状态**: ✅ 已初始化\n"
        else:
            report += "- **状态**: ❌ 未初始化\n"

        report += f"""
## 系统检查结果

运行 `python scripts/implement_v15_0_system.py check` 查看详细检查结果。

## 下一步

1. 配置 Memo0 API Key（在 `.env` 文件中设置 `MEM0_API_KEY`）
2. 运行测试套件验证系统功能
3. 启动仿真模式进行测试
4. 逐步过渡到模拟交易

---

**报告生成**: V15.0 系统集成器
"""

        return report

    def shutdown(self) -> None:
        """关闭系统"""
        logger.info("🛑 正在关闭系统...")

        # 关闭混合存储
        if self.hybrid_storage:
            self.hybrid_storage.shutdown()

        logger.info("✅ 系统已关闭")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='V15.0 系统集成工具')
    parser.add_argument('command', nargs='?', default='integrate',
                       choices=['integrate', 'check', 'report'],
                       help='命令: integrate(集成), check(检查), report(报告)')
    parser.add_argument('--config', default='config/config_v15_0.yaml',
                       help='配置文件路径')

    args = parser.parse_args()

    # 创建集成器
    integrator = V15SystemIntegrator(args.config)

    try:
        if args.command == 'integrate':
            # 集成系统
            success = integrator.integrate_systems()
            if success:
                # 运行系统检查
                check_results = integrator.run_system_check()

                # 保存检查结果
                output_file = 'reports/v15_0_system_check.json'
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(check_results, f, indent=2, ensure_ascii=False)

                logger.info(f"✅ 系统检查结果已保存到: {output_file}")

                # 生成集成报告
                report = integrator.generate_integration_report()
                report_file = 'reports/v15_0_integration_report.md'
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)

                logger.info(f"✅ 集成报告已保存到: {report_file}")

        elif args.command == 'check':
            # 运行系统检查
            check_results = integrator.run_system_check()

            # 打印检查结果
            print(json.dumps(check_results, indent=2, ensure_ascii=False))

        elif args.command == 'report':
            # 生成报告
            report = integrator.generate_integration_report()
            print(report)

    finally:
        # 关闭系统
        integrator.shutdown()


if __name__ == '__main__':
    main()