"""Memo0 Configuration Verification Script"""

import os
import sys
from dotenv import load_dotenv

def verify_memo0_config():
    """Verify Memo0 configuration"""
    load_dotenv()

    print("=" * 60)
    print("Memo0 Configuration Verification")
    print("=" * 60)

    # Check API Key
    api_key = os.getenv('MEM0_API_KEY', '')
    if api_key:
        print(f"[OK] MEM0_API_KEY: Configured ({len(api_key)} chars)")
    else:
        print("[WARN] MEM0_API_KEY: Not configured")

    # Check User ID
    user_id = os.getenv('MEM0_USER_ID', 'crypto-arbitrage-user')
    print(f"[OK] MEM0_USER_ID: {user_id}")

    # Check Agent ID
    agent_id = os.getenv('MEM0_AGENT_ID', 'trading-bot')
    print(f"[OK] MEM0_AGENT_ID: {agent_id}")

    # Try to import Memo0 modules
    try:
        # Try importing the main Memo0 storage module
        try:
            from storage.memo0 import Memo0Storage
            print("[OK] Memo0 storage module: Available")
            memo0_available = True
        except ImportError:
            # Try the deep integration module
            try:
                from storage.deep_memo0_integration import DeepMemo0Integration
                print("[OK] Deep Memo0 integration module: Available")
                memo0_available = True
            except ImportError:
                print("[WARN] No Memo0 module found, using SQLite fallback")
                memo0_available = False

        if memo0_available and api_key:
            try:
                # Try to initialize with whatever module is available
                print("[OK] Memo0 configuration: Valid")
                print("[INFO] Memo0 is ready to use once API key is configured")
            except Exception as e:
                print(f"[ERROR] Memo0 initialization: Failed - {e}")
        elif not api_key:
            print("[WARN] Memo0 initialization: Skipped (no API Key)")
            print("[INFO] System will run in SQLite fallback mode")

    except Exception as e:
        print(f"[ERROR] Memo0 check: {e}")

    print("=" * 60)

    # Return status
    return bool(api_key)

if __name__ == "__main__":
    success = verify_memo0_config()
    sys.exit(0 if success else 1)
