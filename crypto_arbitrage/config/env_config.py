"""环境配置加载器 V16.9

从环境变量和配置文件加载配置，统一提供给所有模块。

功能：
1. 从 .env 文件加载环境变量
2. 从 config.yaml 加载配置
3. 环境变量优先级高于配置文件
4. 提供exchange_configs字典给ccxt_price_feed

创建时间：2026-05-05
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 当前工作目录
_PROJECT_ROOT = Path(__file__).parent.parent


class EnvConfig:
    """环境配置加载器"""

    def __init__(self, env_file: Optional[str] = None):
        """初始化配置加载器

        Args:
            env_file: .env文件路径，默认同目录下的.env
        """
        self._config: Dict[str, Any] = {}
        self._env_file = env_file or str(_PROJECT_ROOT / ".env")

        # 加载配置
        self._load_env_file()
        self._load_yaml_config()

    def _load_env_file(self) -> None:
        """从.env文件加载环境变量"""
        if not os.path.exists(self._env_file):
            logger.warning(f".env文件不存在: {self._env_file}")
            return

        # 逐行读取
        with open(self._env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # 解析 KEY=VALUE 格式
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if key and value and not value.startswith("YOUR_"):
                        self._config[key] = value

        logger.info(f"已加载 {len(self._config)} 个环境变量")

    def _load_yaml_config(self) -> None:
        """从config.yaml加载配置"""
        import yaml

        yaml_path = _PROJECT_ROOT / "config" / "config.yaml"
        if not yaml_path.exists():
            return

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)

            # 合并到配置（环境变量优先）
            if yaml_config:
                # Exchanges配置
                exchanges = yaml_config.get("exchanges", {})
                for exch_name, exch_config in exchanges.items():
                    enabled = exch_config.get("enabled", False)
                    api_key = exch_config.get("api_key", "")
                    secret = exch_config.get("secret", "")

                    # 环境变量优先
                    env_key = f"{exch_name.upper()}_API_KEY"
                    env_secret = f"{exch_name.upper()}_SECRET"

                    if env_key in self._config:
                        api_key = self._config[env_key]
                    if env_secret in self._config:
                        secret = self._config[env_secret]

                    if api_key and not api_key.startswith("YOUR_"):
                        self._config[f"{exch_name}_api_key"] = api_key
                        self._config[f"{exch_name}_secret"] = secret

                # Memo0配置
                mem0_config = yaml_config.get("mem0", {})
                mem0_api_key = mem0_config.get("api_key", "")
                if "MEM0_API_KEY" in self._config:
                    mem0_api_key = self._config["MEM0_API_KEY"]
                self._config["mem0_api_key"] = mem0_api_key

        except Exception as e:
            logger.warning(f"加载config.yaml失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def get_exchange_config(self, exchange: str) -> Dict[str, str]:
        """获取单个交易所配置

        Args:
            exchange: 交易所名称 (binance/okx/huobi等)

        Returns:
            配置字典 {apiKey, secret}
        """
        api_key = self._config.get(f"{exchange}_api_key", "")
        secret = self._config.get(f"{exchange}_secret", "")

        if not api_key:
            return {}

        return {
            "apiKey": api_key,
            "secret": secret
        }

    def get_exchange_configs(self) -> Dict[str, Dict[str, str]]:
        """获取所有交易所配置

        Returns:
            {exchange: {apiKey, secret}}
        """
        exchanges = ["binance", "okx", "huobi", "bybit", "coinbase"]
        configs = {}

        for exch in exchanges:
            config = self.get_exchange_config(exch)
            if config:
                configs[exch] = config

        return configs

    def get_system_mode(self) -> str:
        """获取系统运行模式

        Returns:
            simulation / paper_trading / live_trading
        """
        return self._config.get("SYSTEM_MODE", "simulation")

    def is_live_trading(self) -> bool:
        """是否实盘交易模式"""
        return self.get_system_mode() == "live_trading"

    def get_ccxt_price_feed_config(self) -> Dict[str, Any]:
        """获取ccxt_price_feed的完整配置

        Returns:
            配置字典
        """
        use_real = self.is_live_trading()

        return {
            "use_real_data": use_real,
            "exchange_configs": self.get_exchange_configs(),
            "cache_ttl_sec": 5.0
        }

    def get_mem0_api_key(self) -> str:
        """获取Memo0 API密钥"""
        return self._config.get("mem0_api_key", "")


# 全局配置实例
_config_instance: Optional[EnvConfig] = None


def get_env_config() -> EnvConfig:
    """获取全局配置实例

    Returns:
        EnvConfig实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvConfig()
    return _config_instance