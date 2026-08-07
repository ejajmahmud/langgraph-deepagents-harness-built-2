"""批量修复storage模块中的Unicode编码问题

将emoji字符替换为ASCII字符，解决Windows GBK编码问题。

创建时间：2026-05-01 04:25
"""

import os
import re
from pathlib import Path


def fix_emoji_in_file(file_path: Path) -> int:
    """修复单个文件中的emoji字符

    Args:
        file_path: 文件路径

    Returns:
        修复的emoji数量
    """
    if not file_path.exists():
        return 0

    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # emoji替换映射
        emoji_map = {
            '✅': '[OK]',
            '❌': '[FAIL]',
            '⚠️': '[WARNING]',
            '🎯': '[TARGET]',
            '📊': '[STATS]',
            '💡': '[NOTE]',
            '⚡': '[FAST]',
            '🚀': '[LAUNCH]',
            '⭐': '[STAR]',
            '🔥': '[HOT]'
        }

        # 计算修复数量
        original_content = content
        fixes_count = 0

        # 替换所有emoji
        for emoji, replacement in emoji_map.items():
            count = content.count(emoji)
            if count > 0:
                content = content.replace(emoji, replacement)
                fixes_count += count

        # 如果有修改，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] 修复: {file_path} ({fixes_count}处)")

        return fixes_count

    except Exception as e:
        print(f"[FAIL] 错误: {file_path} - {e}")
        return 0


def fix_storage_directory(storage_dir: Path) -> dict:
    """修复storage目录中的所有emoji字符

    Args:
        storage_dir: storage目录路径

    Returns:
        修复统计
    """
    if not storage_dir.exists():
        print(f"目录不存在: {storage_dir}")
        return {"total_files": 0, "total_fixes": 0}

    stats = {
        "total_files": 0,
        "total_fixes": 0,
        "fixed_files": []
    }

    print(f"开始扫描目录: {storage_dir}")
    print("=" * 60)

    # 查找所有Python文件
    for py_file in storage_dir.rglob("*.py"):
        # 跳过__pycache__和备份目录
        if "__pycache__" in str(py_file) or ".backup" in str(py_file):
            continue

        stats["total_files"] += 1
        fixes = fix_emoji_in_file(py_file)

        if fixes > 0:
            stats["total_fixes"] += fixes
            stats["fixed_files"].append({
                "file": str(py_file.relative_to(storage_dir)),
                "fixes": fixes
            })

    return stats


def main():
    """主函数"""
    # 获取storage目录路径
    script_dir = Path(__file__).resolve().parent
    storage_dir = script_dir / "storage"

    # 修复storage目录
    stats = fix_storage_directory(storage_dir)

    # 打印统计结果
    print("\n" + "=" * 60)
    print("修复统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  修复文件数: {len(stats['fixed_files'])}")
    print(f"  总修复数: {stats['total_fixes']}")

    if stats['fixed_files']:
        print("\n修复详情:")
        for file_info in stats['fixed_files']:
            print(f"  - {file_info['file']}: {file_info['fixes']}处")

    print("\n[OK] Unicode编码问题修复完成!")


if __name__ == "__main__":
    main()
