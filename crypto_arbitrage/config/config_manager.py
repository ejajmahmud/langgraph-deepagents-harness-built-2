"""
配置管理器 V2.5

统一管理系统配置，支持环境变量优先级和配置文件。
优先级：环境变量 > 配置文件 > 默认值

核心功能：
1. 环境变量加载
2. 配置文件解析（YAML）
3. 配置合并和覆盖
4. 运行时配置重载
5. 配置变更通知
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器

    支持多层级配置加载，优先级：环境变量 > 配置文件 > 默认值
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path or self._find_config_path()
        self._config: Dict[str, Any] = {}
        self._env_prefix = "CRYPTO_ARBITRAGE_"

        # 配置变更监听器
        self._change_listeners: List[callable] = []

        logger.info(f"配置管理器初始化，配置路径: {self.config_path}")

    def _find_config_path(self) -> str:
        """查找配置文件路径"""
        # 尝试多个可能的位置
        possible_paths = [
            Path.cwd() / "config" / "config.yaml",
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent / "config" / "config.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        # 返回默认路径
        return str(Path.cwd() / "config" / "config.yaml")

    def load_config(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            配置字典
        """
        # 1. 加载默认配置
        self._config = self._load_defaults()

        # 2. 加载配置文件
        if self.config_path:
            file_config = self._load_from_file()
            if file_config:
                self._config = self._merge_configs(self._config, file_config)
                logger.info(f"从配置文件加载配置: {self.config_path}")

        # 3. 加载环境变量
        env_config = self._load_from_env()
        if env_config:
            self._config = self._merge_configs(self._config, env_config)
            logger.info(f"从环境变量加载{len(env_config)}个配置项")

        # 4. 验证配置
        self._validate_after_load()

        return deepcopy(self._config)

    def reload_config(self) -> Dict[str, Any]:
        """重新加载配置

        Returns:
            新的配置字典
        """
        old_config = deepcopy(self._config)
        new_config = self.load_config()

        # 通知配置变更
        self._notify_change(old_config, new_config)

        return new_config

    def _load_defaults(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "system": {
                "name": "CryptoArbitrage",
                "version": "2.5",
                "mode": "simulation",  # simulation, paper_trading, live_trading
            },
            "model": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-5-20250929",
                "temperature": 0.0,
                "max_tokens": 4096,
            },
            "mem0": {
                "api_key": "",
                "user_id": "crypto-arbitrage-user",
                "agent_id": "trading-bot",
                "rerank": True,
                "keyword_search": False,
            },
            "exchanges": {
                "binance": {
                    "enabled": True,
                    "api_key": "",
                    "secret": "",
                    "testnet": False,
                },
                "okx": {
                    "enabled": True,
                    "api_key": "",
                    "secret": "",
                    "passphrase": "",
                    "testnet": False,
                },
            },
            "risk_management": {
                "max_daily_loss": 500,
                "max_position_size": 1000,
                "max_total_exposure": 5000,
                "max_drawdown": 10.0,
                "min_liquidity_ratio": 0.5,
                "base_stop_loss": 2.0,
                "base_take_profit": 1.0,
                "trailing_stop": 0.5,
                "risk_reward_ratio": 2.0,
            },
            "strategy_manager": {
                "max_total_capital": 10000,
                "max_strategy_allocation": 0.40,
                "min_opportunity_score": 60,
                "signal_aggregation": "weighted",
            },
            "monitoring": {
                "enabled": True,
                "alert_methods": ["console", "memo0", "file"],
                "performance_thresholds": {
                    "scan_timeout": 10,
                    "execution_failure_rate": 0.1,
                    "low_profit_rate": 0.1,
                    "low_win_rate": 50,
                },
                "metrics_interval": 60,
            },
            "runtime": {
                "scan_interval": 30,
                "max_concurrent_trades": 3,
                "trade_timeout": 60,
                "log_level": "INFO",
            },
            "storage": {
                "knowledge_base_db": "crypto_arbitrage_knowledge.db",
                "trade_log_path": "logs/trades.log",
                "performance_log_path": "logs/performance.log",
                "alerts_log_path": "logs/alerts_*.log",
                "auto_save_interval": 300,
            },
        }

    def _load_from_file(self) -> Dict[str, Any]:
        """从配置文件加载"""
        import yaml

        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {self.config_path}")
            return {}

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config:
                logger.info(f"成功加载配置文件: {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        env_config = {}

        # Memo0配置
        if "MEM0_API_KEY" in os.environ:
            env_config["mem0"] = env_config.get("mem0", {})
            env_config["mem0"]["api_key"] = os.environ["MEM0_API_KEY"]

        if "MEM0_USER_ID" in os.environ:
            env_config["mem0"] = env_config.get("mem0", {})
            env_config["mem0"]["user_id"] = os.environ["MEM0_USER_ID"]

        if "MEM0_AGENT_ID" in os.environ:
            env_config["mem0"] = env_config.get("mem0", {})
            env_config["mem0"]["agent_id"] = os.environ["MEM0_AGENT_ID"]

        # 交易所配置
        if "BINANCE_API_KEY" in os.environ:
            env_config["exchanges"] = env_config.get("exchanges", {})
            env_config["exchanges"]["binance"] = env_config["exchanges"].get("binance", {})
            env_config["exchanges"]["binance"]["api_key"] = os.environ["BINANCE_API_KEY"]

        if "BINANCE_SECRET" in os.environ:
            env_config["exchanges"] = env_config.get("exchanges", {})
            env_config["exchanges"]["binance"] = env_config["exchanges"].get("binance", {})
            env_config["exchanges"]["binance"]["secret"] = os.environ["BINANCE_SECRET"]

        if "OKX_API_KEY" in os.environ:
            env_config["exchanges"] = env_config.get("exchanges", {})
            env_config["exchanges"]["okx"] = env_config["exchanges"].get("okx", {})
            env_config["exchanges"]["okx"]["api_key"] = os.environ["OKX_API_KEY"]

        if "OKX_SECRET" in os.environ:
            env_config["exchanges"] = env_config.get("exchanges", {})
            env_config["exchanges"]["okx"] = env_config["exchanges"].get("okx", {})
            env_config["exchanges"]["okx"]["secret"] = os.environ["OKX_SECRET"]

        if "OKX_PASSPHRASE" in os.environ:
            env_config["exchanges"] = env_config.get("exchanges", {})
            env_config["exchanges"]["okx"] = env_config["exchanges"].get("okx", {})
            env_config["exchanges"]["okx"]["passphrase"] = os.environ["OKX_PASSPHRASE"]

        # 系统配置
        if "SYSTEM_MODE" in os.environ:
            env_config["system"] = env_config.get("system", {})
            env_config["system"]["mode"] = os.environ["SYSTEM_MODE"]

        if "LOG_LEVEL" in os.environ:
            env_config["runtime"] = env_config.get("runtime", {})
            env_config["runtime"]["log_level"] = os.environ["LOG_LEVEL"]

        return env_config

    def _merge_configs(self, base: Dict, overlay: Dict) -> Dict:
        """递归合并两个配置字典

        Args:
            base: 基础配置
            overlay: 覆盖配置

        Returns:
            合并后的配置
        """
        result = deepcopy(base)

        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = deepcopy(value)

        return result

    def _validate_after_load(self):
        """加载后验证配置"""
        # 基础验证
        if not self._config:
            raise ValueError("配置为空")

        # 系统模式验证
        valid_modes = ["simulation", "paper_trading", "live_trading"]
        mode = self._config.get("system", {}).get("mode", "simulation")
        if mode not in valid_modes:
            logger.warning(f"无效的系统模式: {mode}，使用默认值: simulation")
            self._config["system"]["mode"] = "simulation"

        # 日志级别验证
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self._config.get("runtime", {}).get("log_level", "INFO")
        if log_level not in valid_log_levels:
            logger.warning(f"无效的日志级别: {log_level}，使用默认值: INFO")
            self._config["runtime"]["log_level"] = "INFO"

        # V5.1 配置验证
        try:
            from .config_validator import validate_config

            logger.info("执行 V5.1 配置验证...")
            result = validate_config(self._config)

            if not result.is_valid:
                logger.error(f"配置验证失败: {len(result.errors)} 个错误")
                for error in result.errors:
                    logger.error(f"  [{error.level.value.upper()}] {error.field}: {error.message}")
                    if error.suggestion:
                        logger.info(f"    建议: {error.suggestion}")

                # 对于严重错误，抛出异常
                critical_errors = [e for e in result.errors if e.level.value == "critical"]
                if critical_errors:
                    raise ValueError(f"配置包含 {len(critical_errors)} 个严重错误，无法启动")

            if result.warnings:
                logger.warning(f"配置验证发现 {len(result.warnings)} 个警告")
                for warning in result.warnings:
                    logger.warning(f"  [{warning.level.value.upper()}] {warning.field}: {warning.message}")
                    if warning.suggestion:
                        logger.info(f"    建议: {warning.suggestion}")

            if result.suggestions:
                logger.info(f"配置优化建议 ({len(result.suggestions)} 条):")
                for suggestion in result.suggestions:
                    logger.info(f"  - {suggestion}")

        except ImportError:
            logger.warning("配置验证器不可用，跳过详细验证")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置键，支持点分隔的嵌套键（如 "mem0.api_key"）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """设置配置项

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
            persist: 是否持久化到配置文件
        """
        keys = key.split(".")
        config = self._config

        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

        # 持久化到文件
        if persist:
            self._persist_to_file()

        logger.debug(f"配置更新: {key} = {value}")

    def _persist_to_file(self) -> None:
        """持久化配置到文件"""
        import yaml

        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"配置已保存到文件: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def add_change_listener(self, listener: callable) -> None:
        """添加配置变更监听器

        Args:
            listener: 监听器函数，签名为 listener(old_config, new_config)
        """
        self._change_listeners.append(listener)
        logger.debug(f"添加配置变更监听器: {listener}")

    def _notify_change(self, old_config: Dict, new_config: Dict) -> None:
        """通知配置变更"""
        for listener in self._change_listeners:
            try:
                listener(old_config, new_config)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败: {e}")

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置

        Returns:
            所有配置的深拷贝
        """
        return deepcopy(self._config)

    def get_system_mode(self) -> str:
        """获取系统模式"""
        return self.get("system.mode", "simulation")

    def is_simulation(self) -> bool:
        """是否为模拟模式"""
        return self.get_system_mode() == "simulation"

    def is_paper_trading(self) -> bool:
        """是否为模拟交易模式"""
        return self.get_system_mode() == "paper_trading"

    def is_live_trading(self) -> bool:
        """是否为实盘交易模式"""
        return self.get_system_mode() == "live_trading"

    def get_mem0_config(self) -> Dict[str, Any]:
        """获取Memo0配置"""
        return self.get("mem0", {})

    def get_exchange_config(self, exchange: str) -> Dict[str, Any]:
        """获取交易所配置

        Args:
            exchange: 交易所名称（binance, okx, huobi）

        Returns:
            交易所配置
        """
        return self.get(f"exchanges.{exchange}", {})

    def get_strategy_config(self, strategy: str) -> Dict[str, Any]:
        """获取策略配置

        Args:
            strategy: 策略名称

        Returns:
            策略配置
        """
        return self.get(f"strategies.{strategy}", {})

    def get_risk_config(self) -> Dict[str, Any]:
        """获取风险管理配置"""
        return self.get("risk_management", {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get("monitoring", {})

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get("storage", {})

    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get("runtime.log_level", "INFO")

    def get_scan_interval(self) -> int:
        """获取扫描间隔（秒）"""
        return self.get("runtime.scan_interval", 30)

    def get_max_concurrent_trades(self) -> int:
        """获取最大并发交易数"""
        return self.get("runtime.max_concurrent_trades", 3)

    def validate_sensitivity(self) -> Dict[str, List[str]]:
        """验证敏感配置

        Returns:
            验证结果 {"warnings": [...], "errors": [...]}
        """
        warnings = []
        errors = []

        # 检查Memo0 API Key
        if not self.get("mem0.api_key"):
            warnings.append("Memo0 API Key未配置，将使用本地SQLite存储")

        # 检查交易所API Keys（实盘模式）
        if self.is_live_trading():
            exchanges = ["binance", "okx"]
            for exchange in exchanges:
                config = self.get_exchange_config(exchange)
                if config.get("enabled") and (not config.get("api_key") or not config.get("secret")):
                    errors.append(f"{exchange} API Key未配置，无法进行实盘交易")

        # 检查资金限制
        max_loss = self.get("risk_management.max_daily_loss", 500)
        if max_loss <= 0:
            errors.append("每日最大损失限制必须大于0")

        max_position = self.get("risk_management.max_position_size", 1000)
        if max_position <= 0:
            errors.append("最大持仓大小必须大于0")

        return {
            "warnings": warnings,
            "errors": errors
        }

    def export_to_env_file(self, output_path: str = ".env") -> None:
        """导出配置到环境变量文件

        Args:
            output_path: 输出文件路径
        """
        lines = ["# CryptoArbitrage 环境变量配置", "# 生成时间: " + datetime.now().isoformat(), ""]

        # Memo0配置
        mem0_config = self.get_mem0_config()
        if mem0_config.get("api_key"):
            lines.append(f"MEM0_API_KEY={mem0_config['api_key']}")
        if mem0_config.get("user_id"):
            lines.append(f"MEM0_USER_ID={mem0_config['user_id']}")
        if mem0_config.get("agent_id"):
            lines.append(f"MEM0_AGENT_ID={mem0_config['agent_id']}")
        lines.append("")

        # 交易所配置
        for exchange in ["binance", "okx"]:
            config = self.get_exchange_config(exchange)
            if config.get("api_key"):
                lines.append(f"{exchange.upper()}_API_KEY={config['api_key']}")
            if config.get("secret"):
                lines.append(f"{exchange.upper()}_SECRET={config['secret']}")
            if exchange == "okx" and config.get("passphrase"):
                lines.append(f"OKX_PASSPHRASE={config['passphrase']}")
        lines.append("")

        # 系统配置
        lines.append(f"SYSTEM_MODE={self.get_system_mode()}")
        lines.append(f"LOG_LEVEL={self.get_log_level()}")

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"环境变量配置已导出到: {output_path}")


# ---------------------- 全局单例 ----------------------

_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例（全局单例）

    Returns:
        ConfigManager 实例
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.load_config()

    return _config_manager


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置（便捷函数）

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    manager = get_config_manager()
    if config_path:
        manager.config_path = config_path
        manager.reload_config()
    return manager.get_all()
