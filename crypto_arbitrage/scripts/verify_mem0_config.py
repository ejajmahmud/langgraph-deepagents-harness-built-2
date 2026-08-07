"""Memo0 配置验证和测试脚本

V3.9 迭代 - 验证 Memo0 配置并测试连接

功能：
1. 验证配置文件格式
2. 检查 API Key 有效性
3. 测试 Memo0 连接
4. 测试基本功能（添加/搜索记忆）
5. 生成配置报告

使用方式:
    python scripts/verify_mem0_config.py [--config CONFIG_PATH]
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.mem0_storage import load_mem0_config, initialize_mem0, is_mem0_available

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    """打印标题"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_success(message: str) -> None:
    """打印成功消息"""
    print(f"[PASS] {message}")


def print_error(message: str) -> None:
    """打印错误消息"""
    print(f"[FAIL] {message}")


def print_info(message: str) -> None:
    """打印信息消息"""
    print(f"[INFO] {message}")


def print_warning(message: str) -> None:
    """打印警告消息"""
    print(f"[WARN] {message}")


class Memo0ConfigValidator:
    """Memo0 配置验证器"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化验证器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.issues: list = []
        self.warnings: list = []

    def validate(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        print_header("Memo0 配置验证")

        # 1. 加载配置
        if not self._load_config():
            return False

        # 2. 验证必需字段
        if not self._validate_required_fields():
            return False

        # 3. 验证可选字段
        self._validate_optional_fields()

        # 4. 验证高级配置
        self._validate_advanced_config()

        # 5. 生成报告
        self._generate_report()

        return len(self.issues) == 0

    def _load_config(self) -> bool:
        """加载配置文件"""
        print_info("正在加载配置文件...")

        # 尝试从多个路径加载
        config_paths = []

        if self.config_path:
            config_paths.append(Path(self.config_path))

        # 添加默认路径
        config_paths.extend([
            Path.cwd() / "config" / "mem0.json",
            Path.cwd() / "config" / "mem0_config.yaml",
            Path.cwd() / "config" / "mem0_config.yml",
        ])

        for config_path in config_paths:
            if config_path.exists():
                try:
                    if config_path.suffix in ['.yaml', '.yml']:
                        import yaml
                        with open(config_path, 'r', encoding='utf-8') as f:
                            self.config = yaml.safe_load(f) or {}
                    else:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            self.config = json.load(f)

                    print_success(f"配置文件加载成功: {config_path}")
                    self.config_path = str(config_path)
                    return True
                except Exception as e:
                    self.issues.append(f"配置文件解析失败 ({config_path}): {e}")
                    continue

        self.issues.append("未找到配置文件。请创建 config/mem0.json 或 config/mem0_config.yaml")
        return False

    def _validate_required_fields(self) -> bool:
        """验证必需字段"""
        print_info("验证必需字段...")

        # 检查 API Key
        api_key = self.config.get('api_key') or self.config.get('memo0', {}).get('api_key')
        if not api_key:
            self.issues.append("缺少必需字段: api_key")
            print_error("API Key 未配置")
            return False

        if api_key in ['your-mem0-api-key-here', 'your-api-key', '', ' ']:
            self.issues.append("API Key 使用了占位符，请填入真实的 API Key")
            print_error("API Key 为占位符，请配置真实值")
            return False

        print_success("API Key 已配置")
        return True

    def _validate_optional_fields(self) -> None:
        """验证可选字段"""
        print_info("验证可选字段...")

        # user_id
        user_id = self.config.get('user_id') or self.config.get('memo0', {}).get('user_id')
        if user_id:
            print_success(f"user_id: {user_id}")
        else:
            self.warnings.append("user_id 未配置，将使用默认值")
            print_warning("user_id 未配置，将使用默认值")

        # agent_id
        agent_id = self.config.get('agent_id') or self.config.get('memo0', {}).get('agent_id')
        if agent_id:
            print_success(f"agent_id: {agent_id}")
        else:
            self.warnings.append("agent_id 未配置，将使用默认值")
            print_warning("agent_id 未配置，将使用默认值")

    def _validate_advanced_config(self) -> None:
        """验证高级配置"""
        print_info("验证高级配置...")

        advanced = self.config.get('advanced', {})

        # 熔断器配置
        circuit_breaker = advanced.get('circuit_breaker', {})
        if circuit_breaker:
            threshold = circuit_breaker.get('threshold')
            if threshold and threshold < 1:
                self.warnings.append(f"熔断器阈值过小: {threshold}，建议设置为 3-10")

            cooldown = circuit_breaker.get('cooldown_seconds')
            if cooldown and cooldown < 30:
                self.warnings.append(f"熔断器冷却时间过短: {cooldown}秒，建议设置为 60-300秒")

        # 缓存配置
        cache = advanced.get('cache', {})
        if cache:
            ttl = cache.get('ttl')
            if ttl and ttl < 60:
                self.warnings.append(f"缓存 TTL 过短: {ttl}秒，可能影响性能")

    def _generate_report(self) -> None:
        """生成验证报告"""
        print_header("配置验证报告")

        print(f"配置文件: {self.config_path}")
        print(f"问题数量: {len(self.issues)}")
        print(f"警告数量: {len(self.warnings)}")

        if self.issues:
            print("\n问题列表:")
            for i, issue in enumerate(self.issues, 1):
                print_error(f"{i}. {issue}")

        if self.warnings:
            print("\n警告列表:")
            for i, warning in enumerate(self.warnings, 1):
                print_warning(f"{i}. {warning}")

        if not self.issues and not self.warnings:
            print_success("配置完全正确，无问题或警告")


class Memo0ConnectionTester:
    """Memo0 连接测试器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化测试器

        Args:
            config: 配置字典
        """
        self.config = config
        self.mem0_client = None

    def test(self) -> bool:
        """测试连接和功能

        Returns:
            bool: 测试是否通过
        """
        print_header("Memo0 连接和功能测试")

        # 1. 初始化 Memo0
        if not self._initialize():
            return False

        # 2. 测试连接
        if not self._test_connection():
            return False

        # 3. 测试添加记忆
        test_memory_id = self._test_add_memory()
        if not test_memory_id:
            return False

        # 4. 测试搜索记忆
        if not self._test_search_memory():
            return False

        # 5. 测试删除记忆
        if not self._test_delete_memory(test_memory_id):
            return False

        print_success("所有测试通过！")
        return True

    def _initialize(self) -> bool:
        """初始化 Memo0"""
        print_info("初始化 Memo0 客户端...")

        try:
            self.mem0_client = initialize_mem0(self.config)
            if self.mem0_client is None:
                print_error("Memo0 客户端初始化失败")
                return False

            print_success("Memo0 客户端初始化成功")
            return True
        except Exception as e:
            print_error(f"初始化失败: {e}")
            return False

    def _test_connection(self) -> bool:
        """测试连接"""
        print_info("测试连接...")

        try:
            # 尝试获取一些记忆来测试连接
            memories = self.mem0_client.search(query="test", limit=1)
            print_success("连接测试成功")
            return True
        except Exception as e:
            print_error(f"连接测试失败: {e}")
            return False

    def _test_add_memory(self) -> Optional[str]:
        """测试添加记忆

        Returns:
            Optional[str]: 记忆 ID，如果失败则返回 None
        """
        print_info("测试添加记忆...")

        try:
            test_content = f"Memo0 配置验证测试记忆 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            result = self.mem0_client.add(
                content=test_content,
                metadata={"test": True, "timestamp": time.time()}
            )

            if result:
                print_success(f"记忆添加成功: {result}")
                return result
            else:
                print_error("记忆添加失败: 返回值为空")
                return None
        except Exception as e:
            print_error(f"记忆添加失败: {e}")
            return None

    def _test_search_memory(self) -> bool:
        """测试搜索记忆"""
        print_info("测试搜索记忆...")

        try:
            # 搜索刚刚添加的测试记忆
            results = self.mem0_client.search(
                query="Memo0 配置验证",
                limit=5
            )

            if results:
                print_success(f"搜索成功，找到 {len(results)} 条记忆")
                for i, memory in enumerate(results[:3], 1):
                    print(f"  {i}. {memory.get('memory', '')[:80]}...")
                return True
            else:
                print_warning("搜索成功，但未找到记忆")
                return True  # 不是错误，可能刚添加的记忆还未索引
        except Exception as e:
            print_error(f"搜索失败: {e}")
            return False

    def _test_delete_memory(self, memory_id: str) -> bool:
        """测试删除记忆"""
        print_info("测试删除记忆...")

        try:
            self.mem0_client.delete(memory_id)
            print_success("记忆删除成功")
            return True
        except Exception as e:
            print_error(f"记忆删除失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Memo0 配置验证和测试工具")
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    parser.add_argument(
        '--skip-test',
        action='store_true',
        help='跳过连接测试'
    )

    args = parser.parse_args()

    print_header("Memo0 配置验证和测试工具")
    print_info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 验证配置
    validator = Memo0ConfigValidator(args.config)
    if not validator.validate():
        print_header("验证失败")
        print_error("配置验证失败，请修复问题后重试")
        sys.exit(1)

    # 2. 测试连接（如果未跳过）
    if not args.skip_test:
        tester = Memo0ConnectionTester(validator.config)
        if not tester.test():
            print_header("测试失败")
            print_error("连接测试失败，请检查 API Key 和网络连接")
            sys.exit(1)

    # 3. 生成最终报告
    print_header("验证和测试完成")
    print_success("Memo0 配置正确且连接正常")
    print_info(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 4. 保存配置信息
    output_file = Path.cwd() / "config" / "mem0_verification_report.json"
    report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "config_path": validator.config_path,
        "validation_passed": len(validator.issues) == 0,
        "issues": validator.issues,
        "warnings": validator.warnings,
        "connection_tested": not args.skip_test,
        "connection_passed": not args.skip_test  # 如果执行了测试，假设成功
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print_success(f"验证报告已保存: {output_file}")
    except Exception as e:
        print_warning(f"保存验证报告失败: {e}")

    print("\n下一步:")
    print("1. 如果有警告，建议根据警告信息优化配置")
    print("2. 启动系统: python main.py")
    print("3. 查看日志确认 Memo0 正常工作")

    sys.exit(0)


if __name__ == "__main__":
    main()
