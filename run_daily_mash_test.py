#!/usr/bin/env python3
"""
Simple test runner for the Daily Mash integration
Run this to quickly test the system
"""

import sys
import os

# Ensure we can import from the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    print(">> Starting Daily Mash Integration Test...")
    print("=" * 50)
    
    try:
        from test_integrated_daily_mash import run_complete_test
        run_complete_test()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required files are in the same directory:")
        print("- integrated_daily_mash_system.py")
        print("- local_functions/textGeneration_gemini.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running test: {e}")
        sys.exit(1)