#!/usr/bin/env python3
"""Quick script to install requirements."""

import subprocess
import sys

print("🚀 Installing dependencies...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
    cwd=".",
    capture_output=False
)

if result.returncode == 0:
    print("\n✅ Installation successful!")
    print("\n📝 Now you can run:")
    print("   python code/08_run_all.py --simulations 300")
else:
    print("\n❌ Installation failed!")
    sys.exit(1)
