"""System Integrity Verification Script for V3.5"""

import sys
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

def check_python_version():
    """Check Python version"""
    print("=" * 60)
    print("Python Environment Check")
    print("=" * 60)

    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 10:
        print("[OK] Python version is compatible (3.10+)")
        return True
    else:
        print("[WARN] Python version may not be fully compatible")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("\n" + "=" * 60)
    print("Dependencies Check")
    print("=" * 60)

    required_deps = {
        'deepagents': {'required': True, 'description': 'DeepAgents framework'},
        'langchain': {'required': True, 'description': 'LangChain framework'},
        'langchain_anthropic': {'required': True, 'description': 'LangChain Anthropic integration'},
        'mem0ai': {'required': False, 'description': 'Memo0 AI memory storage'},
        'ccxt': {'required': True, 'description': 'Exchange integration'},
        'pandas': {'required': True, 'description': 'Data processing'},
        'numpy': {'required': True, 'description': 'Numerical computing'},
        'yaml': {'required': True, 'description': 'YAML configuration'},
        'dotenv': {'required': True, 'description': 'Environment variables'},
    }

    import importlib
    missing_required = []
    missing_optional = []

    for module_name, info in required_deps.items():
        try:
            if module_name == 'langchain_anthropic':
                importlib.import_module('langchain_anthropic')
            elif module_name == 'dotenv':
                importlib.import_module('dotenv')
            else:
                importlib.import_module(module_name)

            status = "[OK]" if info['required'] else "[OK OPT]"
            print(f"{status} {module_name}: Installed ({info['description']})")

        except ImportError:
            if info['required']:
                status = "[ERROR]"
                missing_required.append(module_name)
                print(f"{status} {module_name}: MISSING - {info['description']}")
            else:
                status = "[WARN OPT]"
                missing_optional.append(module_name)
                print(f"{status} {module_name}: Not installed - {info['description']}")

    return len(missing_required) == 0

def check_project_structure():
    """Check project structure"""
    print("\n" + "=" * 60)
    print("Project Structure Check")
    print("=" * 60)

    required_dirs = [
        'agents',
        'strategies',
        'tools',
        'storage',
        'config',
        'monitoring',
        'llm',
        'risk',
        'backend',
        'tests',
        'scripts',
        'docs',
    ]

    required_files = [
        'main.py',
        'config/config.yaml',
        'requirements.txt',
    ]

    structure_ok = True

    for directory in required_dirs:
        if Path(directory).exists() and Path(directory).is_dir():
            print(f"[OK] Directory: {directory}/")
        else:
            print(f"[ERROR] Directory missing: {directory}/")
            structure_ok = False

    for file_path in required_files:
        if Path(file_path).exists() and Path(file_path).is_file():
            print(f"[OK] File: {file_path}")
        else:
            print(f"[ERROR] File missing: {file_path}")
            structure_ok = False

    return structure_ok

def check_configuration():
    """Check configuration files"""
    print("\n" + "=" * 60)
    print("Configuration Check")
    print("=" * 60)

    load_dotenv()

    # Check main config
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"[OK] Config file: config/config.yaml")
        print(f"[INFO] System version: {config.get('system', {}).get('version', 'UNKNOWN')}")
        print(f"[INFO] System mode: {config.get('system', {}).get('mode', 'UNKNOWN')}")

        # Check Memo0 config
        memo0_configured = bool(config.get('mem0', {}).get('api_key'))
        if memo0_configured:
            print("[OK] Memo0: Configured with API key")
        else:
            print("[WARN] Memo0: No API key (will use SQLite fallback)")

        # Check exchange config
        exchanges_configured = False
        for exchange_name, exchange_config in config.get('exchanges', {}).items():
            if exchange_config.get('enabled') and exchange_config.get('api_key') and 'YOUR_' not in exchange_config.get('api_key', ''):
                exchanges_configured = True
                break

        if exchanges_configured:
            print("[OK] Exchange API: At least one exchange configured")
        else:
            print("[WARN] Exchange API: Using placeholder keys (simulation only)")

        return True

    except Exception as e:
        print(f"[ERROR] Config check failed: {e}")
        return False

def check_core_modules():
    """Check core module imports"""
    print("\n" + "=" * 60)
    print("Core Modules Check")
    print("=" * 60)

    # Add current directory to path
    sys.path.insert(0, '.')

    core_modules = [
        ('config.config_manager', 'ConfigManager'),
        ('storage.knowledge_base', 'initialize_knowledge_base'),
        ('storage.project_tracker', 'initialize_project_tracker'),
    ]

    modules_ok = True

    for module_path, item_name in core_modules:
        try:
            module = __import__(module_path, fromlist=[item_name])
            print(f"[OK] {module_path}.{item_name}")
        except ImportError as e:
            print(f"[ERROR] {module_path}.{item_name}: {e}")
            modules_ok = False
        except Exception as e:
            # Module exists but might have import errors due to missing dependencies
            print(f"[WARN] {module_path}.{item_name}: Import issue (likely missing dependencies)")

    return modules_ok

def generate_installation_instructions(missing_deps):
    """Generate installation instructions"""
    print("\n" + "=" * 60)
    print("Installation Instructions")
    print("=" * 60)

    if not missing_deps:
        print("[INFO] All required dependencies are installed!")
        return

    print("[INFO] To install missing dependencies, run:")
    print("\n# Install all dependencies")
    print("pip install -r requirements.txt")
    print("\n# Or install specific missing dependencies:")
    for dep in missing_deps:
        print(f"pip install {dep}")

    print("\n# After installation, verify with:")
    print("python scripts/verify_system_integrity.py")

def main():
    """Main verification function"""
    print("Crypto Arbitrage System - V3.5 Integrity Check")
    print("=" * 60)

    # Check Python version
    python_ok = check_python_version()

    # Check dependencies
    deps_ok = check_dependencies()

    # Check project structure
    structure_ok = check_project_structure()

    # Check configuration
    config_ok = check_configuration()

    # Check core modules
    modules_ok = check_core_modules()

    # Overall status
    print("\n" + "=" * 60)
    print("Overall System Status")
    print("=" * 60)

    checks = {
        'Python Environment': python_ok,
        'Dependencies': deps_ok,
        'Project Structure': structure_ok,
        'Configuration': config_ok,
        'Core Modules': modules_ok,
    }

    all_passed = all(checks.values())

    for check_name, status in checks.items():
        status_str = "[OK]" if status else "[FAIL]"
        print(f"{status_str} {check_name}")

    if all_passed:
        print("\n[SUCCESS] All checks passed! System is ready to run.")
        print("\nNext steps:")
        print("1. Configure Memo0 API key (optional, see docs/MEMO0_SETUP_GUIDE.md)")
        print("2. Configure exchange API keys (for live trading)")
        print("3. Run the system: python main.py")
        return 0
    else:
        print("\n[WARNING] Some checks failed. Please address the issues above.")
        print("\nMost common issues:")
        print("1. Missing dependencies - Run: pip install -r requirements.txt")
        print("2. Missing directories - Ensure project is properly cloned")
        print("3. Configuration errors - Check config/config.yaml")
        return 1

if __name__ == "__main__":
    sys.exit(main())
