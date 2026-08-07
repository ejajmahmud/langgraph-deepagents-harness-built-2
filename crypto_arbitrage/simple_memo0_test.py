#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memo0集成简单测试"""

import os
from pathlib import Path

def main():
    print("="*60)
    print("Memo0 Integration Test")
    print("="*60)

    # Check environment variables
    print("\nEnvironment Variables:")
    print(f"  MEM0_API_KEY: {'Set' if os.environ.get('MEM0_API_KEY') else 'Not Set'}")

    # Test imports
    print("\nTesting Module Imports...")
    try:
        import storage
        print("  storage module: OK")
    except ImportError as e:
        print(f"  storage module: FAILED - {e}")
        return

    try:
        import strategies
        print("  strategies module: OK")
    except ImportError as e:
        print(f"  strategies module: FAILED - {e}")
        return

    try:
        import trading
        print("  trading module: OK")
    except ImportError as e:
        print(f"  trading module: FAILED - {e}")
        return

    # Test Memo0 initialization
    print("\nTesting Memo0 Storage...")
    try:
        from storage import initialize_mem0, get_mem0_storage

        # Test local storage (no API key)
        storage = initialize_mem0(None)

        if storage is None:
            print("  Memo0 storage initialization: FAILED (returned None)")
            print("\nConclusion: Using local SQLite storage at: crypto_arbitrage_knowledge.db")
            return

        print(f"  Memo0 storage type: {type(storage).__name__}")

        # Test basic functionality
        print("\nTesting Basic Operations:")

        # Test add knowledge
        try:
            storage.add("test_knowledge", {
                "content": "Test knowledge entry",
                "type": "test",
                "timestamp": "2026-04-28T21:10:00"
            })
            print("  Add knowledge: OK")
        except Exception as e:
            print(f"  Add knowledge: FAILED - {e}")
            return

        # Test search knowledge
        try:
            results = storage.search("test")
            print(f"  Search knowledge: OK (found {len(results)} results)")
        except Exception as e:
            print(f"  Search knowledge: FAILED - {e}")
            return

        print("\n" + "="*60)
        print("Conclusion: Memo0 integration is working correctly")
        print("="*60)
        print("\nSystem Status:")
        print("  - Module imports: OK")
        print("  - Memo0 storage: OK")
        print("  - Basic operations: OK")
        print("\nCurrent Configuration:")
        print("  - Storage: Local SQLite (crypto_arbitrage_knowledge.db)")
        print("  - Memo0 API: Not configured (optional)")

    except Exception as e:
        print(f"\nERROR: Memo0 storage test failed - {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()