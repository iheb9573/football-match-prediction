#!/usr/bin/env python3
"""
Football Match Prediction - Setup & Pipeline Runner
Handles dependencies installation and pipeline execution
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, verbose=False):
    """Execute a command and return success status."""
    print(f"\n📌 {description}...")
    print(f"   Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    try:
        result = subprocess.run(cmd, cwd=".", capture_output=not verbose)
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True
        else:
            print(f"   ❌ Failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    """Main setup and execution script."""
    
    print("\n" + "="*70)
    print("🚀 FOOTBALL MATCH PREDICTION - AUTOMATIC SETUP")
    print("="*70)
    
    # Check virtual environment
    venv_python = Path(".venv/Scripts/python.exe")
    if not venv_python.exists():
        print("\n❌ Virtual environment not found!")
        print(f"   Expected path: {venv_python.absolute()}")
        print("\n   Please create it:")
        print("   python -m venv .venv")
        return False
    
    print(f"\n✅ Virtual environment found: {venv_python.absolute()}")
    
    # Step 1: Install dependencies
    print("\n" + "-"*70)
    print("STEP 1: Installing Dependencies")
    print("-"*70)
    
    if not run_command(
        [str(venv_python), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        "Installing packages from requirements.txt"
    ):
        print("\n❌ Failed to install dependencies")
        print("   Try manually:")
        print("   .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        return False
    
    # Verify key packages
    print("\n📋 Verifying key packages...")
    packages_to_check = ["pandas", "scikit-learn", "fastapi", "numpy"]
    for package in packages_to_check:
        result = subprocess.run(
            [str(venv_python), "-c", f"import {package}; print(f'{package}: OK')"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
        else:
            print(f"   ⚠️  {package}: Not found")
    
    # Step 2: Run pipeline
    print("\n" + "-"*70)
    print("STEP 2: Running Complete Pipeline")
    print("-"*70)
    print("\n📊 This may take 10-30 minutes depending on your system...")
    
    if not run_command(
        [str(venv_python), "code/08_run_all.py", "--simulations", "300"],
        "Executing pipeline with 300 simulations",
        verbose=True
    ):
        print("\n❌ Pipeline execution failed")
        return False
    
    # Success
    print("\n" + "="*70)
    print("✅ SETUP COMPLETE - PIPELINE EXECUTED SUCCESSFULLY")
    print("="*70)
    
    print("\n📊 Results Location:")
    print("   • Data: data/processed/football_bi/")
    print("   • Reports: reports/football_bi/")
    print("   • Models: models/football_bi/")
    
    print("\n📈 Key Output Files:")
    print("   • reports/football_bi/model_metrics.csv - MODEL ACCURACY")
    print("   • reports/football_bi/test_predictions.csv - PREDICTIONS")
    print("   • reports/football_bi/figures/*.png - VISUALIZATIONS")
    
    print("\n🖥️  To view dashboard:")
    print("   .venv\\Scripts\\python.exe code/09_run_api.py")
    print("   Then open: http://127.0.0.1:8000")
    
    print("\n" + "="*70)
    print("For more details, see: QUICK_START.md, TROUBLESHOOTING.md")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
