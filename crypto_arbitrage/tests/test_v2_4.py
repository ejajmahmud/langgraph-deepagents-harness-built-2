"""
V2.4 Web UI测试套件 - 测试前端界面和功能
"""

import pytest
import subprocess
import os
from pathlib import Path


class TestV2_4WebUI:
    """V2.4 Web UI测试"""

    def test_frontend_directory_exists(self):
        """测试前端目录存在"""
        frontend_dir = Path("frontend")
        assert frontend_dir.exists(), "前端目录不存在"
        assert frontend_dir.is_dir(), "前端路径不是目录"

    def test_package_json_exists(self):
        """测试package.json存在"""
        package_json = Path("frontend/package.json")
        assert package_json.exists(), "package.json不存在"

        # 验证关键依赖
        import json
        with open(package_json, 'r', encoding='utf-8') as f:
            config = json.load(f)

        assert "react" in config["dependencies"], "缺少react依赖"
        assert "antd" in config["dependencies"], "缺少antd依赖"
        assert "zustand" in config["dependencies"], "缺少zustand依赖"
        assert "vite" in config["devDependencies"], "缺少vite依赖"

    def test_vite_config_exists(self):
        """测试vite.config.ts存在"""
        vite_config = Path("frontend/vite.config.ts")
        assert vite_config.exists(), "vite.config.ts不存在"

        # 验证配置内容
        with open(vite_config, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "proxy" in content, "vite配置缺少proxy"
        assert "alias" in content, "vite配置缺少alias"

    def test_tsconfig_exists(self):
        """测试TypeScript配置存在"""
        tsconfig = Path("frontend/tsconfig.json")
        assert tsconfig.exists(), "tsconfig.json不存在"

        with open(tsconfig, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "strict" in content, "TypeScript配置缺少strict模式"
        assert "paths" in content, "TypeScript配置缺少paths"

    def test_src_directory_structure(self):
        """测试src目录结构"""
        src_dir = Path("frontend/src")

        # 核心目录
        dirs = [
            "components",
            "pages",
            "store",
            "api",
            "types",
            "utils",
        ]

        for dir_name in dirs:
            dir_path = src_dir / dir_name
            assert dir_path.exists(), f"src/{dir_name}目录不存在"
            assert dir_path.is_dir(), f"src/{dir_name}不是目录"

    def test_core_components_exist(self):
        """测试核心组件存在"""
        components = [
            "App.tsx",
            "main.tsx",
            "index.css",
            "components/Layout.tsx",
            "components/ProtectedRoute.tsx",
        ]

        src_dir = Path("frontend/src")

        for component in components:
            component_path = src_dir / component
            assert component_path.exists(), f"组件{component}不存在"

    def test_pages_exist(self):
        """测试页面组件存在"""
        pages = [
            "pages/Dashboard.tsx",
            "pages/RealtimeMarket.tsx",
            "pages/StrategyManagement.tsx",
            "pages/TradeHistory.tsx",
            "pages/RiskManagement.tsx",
            "pages/MonitoringAlerts.tsx",
            "pages/Settings.tsx",
            "pages/Login.tsx",
        ]

        src_dir = Path("frontend/src")

        for page in pages:
            page_path = src_dir / page
            assert page_path.exists(), f"页面{page}不存在"

    def test_store_exists(self):
        """测试Store存在"""
        store_path = Path("frontend/src/store/index.ts")
        assert store_path.exists(), "Store不存在"

        with open(store_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "useAppStore" in content, "Store缺少useAppStore"
        assert "create" in content, "Store缺少zustand create"

    def test_api_exists(self):
        """测试API服务层存在"""
        api_path = Path("frontend/src/api/index.ts")
        assert api_path.exists(), "API服务层不存在"

        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 验证API模块
        api_modules = [
            "authAPI",
            "systemAPI",
            "strategyAPI",
            "tradeAPI",
            "marketAPI",
            "riskAPI",
            "monitoringAPI",
            "backtestAPI",
            "intelligentAPI",
        ]

        for module in api_modules:
            assert module in content, f"API缺少{module}"

    def test_types_exist(self):
        """测试类型定义存在"""
        types_path = Path("frontend/src/types/index.ts")
        assert types_path.exists(), "类型定义不存在"

        with open(types_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 验证核心类型
        types = [
            "SystemStatus",
            "Strategy",
            "Opportunity",
            "Trade",
            "MarketData",
            "RiskConfig",
            "Alert",
            "WSMessage",
        ]

        for type_name in types:
            assert type_name in content, f"类型定义缺少{type_name}"

    def test_websocket_service_exists(self):
        """测试WebSocket服务存在"""
        ws_path = Path("frontend/src/utils/websocket.ts")
        assert ws_path.exists(), "WebSocket服务不存在"

        with open(ws_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "WebSocketService" in content, "WebSocket服务类不存在"
        assert "connect" in content, "WebSocket服务缺少connect方法"
        assert "subscribe" in content, "WebSocket服务缺少subscribe方法"

    def test_version_consistency(self):
        """测试版本号一致性"""
        # 检查config.yaml
        import yaml

        config_path = Path("config/config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert config["system"]["version"] == "2.4", "config.yaml版本号不是2.4"

        # 检查base.py
        base_path = Path("strategies/base.py")
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "V2.4" in content, "base.py版本号不是2.4"

    def test_index_html_exists(self):
        """测试index.html存在"""
        index_html = Path("frontend/index.html")
        assert index_html.exists(), "index.html不存在"

        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "root" in content, "index.html缺少root节点"
        assert "main.tsx" in content, "index.html未引用main.tsx"

    def test_css_files_exist(self):
        """测试CSS文件存在"""
        css_files = [
            "index.css",
            "components/Layout.css",
            "pages/Dashboard.css",
            "pages/RealtimeMarket.css",
            "pages/Login.css",
        ]

        src_dir = Path("frontend/src")

        for css_file in css_files:
            css_path = src_dir / css_file
            assert css_path.exists(), f"CSS文件{css_file}不存在"

    def test_iteration_document_exists(self):
        """测试V2.4迭代文档存在"""
        iteration_doc = Path("PROJECT_ITERATION_V2.4.md")
        assert iteration_doc.exists(), "V2.4迭代文档不存在"

        with open(iteration_doc, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "V2.4" in content, "迭代文档缺少V2.4"
        assert "Web UI" in content, "迭代文档缺少Web UI内容"

    def test_backend_api_websocket_support(self):
        """测试后端API支持WebSocket"""
        api_path = Path("backend/api.py")

        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "WebSocket" in content, "后端API缺少WebSocket支持"
        assert "ConnectionManager" in content, "后端API缺少ConnectionManager"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
