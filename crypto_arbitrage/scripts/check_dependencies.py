"""检查系统依赖状态 - V3.6"""
import sys

def check_dependencies():
    """检查所有依赖包的安装状态"""
    packages = [
        'deepagents',
        'langchain',
        'mem0',  # Fixed: mem0ai is installed as mem0
        'ccxt',
        'pandas',
        'numpy',
        'langchain_anthropic',
        'langchain_google_genai',
        'torch',
        'sklearn',
        'talib',
        'pandas_ta',
        'sqlalchemy',
        'redis',
        'fastapi',
        'uvicorn',
        'pydantic',
        'websockets',
        'pytest',
        'pytest_asyncio'
    ]

    print("=" * 60)
    print("Dependency Status Check")
    print("=" * 60)

    installed = []
    missing = []

    for package in packages:
        try:
            __import__(package)
            print(f"[OK] {package}: Installed")
            installed.append(package)
        except ImportError:
            print(f"[X] {package}: Missing")
            missing.append(package)

    print("=" * 60)
    print(f"Total: {len(installed)} installed, {len(missing)} missing")
    print("=" * 60)

    if missing:
        print("\nMissing packages:")
        for pkg in missing:
            print(f"  - {pkg}")

    return missing

if __name__ == "__main__":
    missing_packages = check_dependencies()
    sys.exit(0 if not missing_packages else 1)