"""
Quick smoke test to verify all new modules can be imported and basic functions work.

Run with: python test_smoke.py
"""

import sys
from pathlib import Path

# Add src to path
SRC_PATH = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_PATH))

def test_feature_imports():
    """Test feature module imports."""
    print("\n[TEST] Testing feature module imports...")

    try:
        from football_bi.features import player
        print("  [OK] player module imported")

        from football_bi.features import advanced
        print("  [OK] advanced module imported")

        # Test basic function
        agg = player.compute_squad_aggregations
        print("  [OK] compute_squad_aggregations function found")

        interaction = advanced.compute_form_interaction
        print("  [OK] compute_form_interaction function found")

        return True
    except Exception as e:
        print(f"  [ERR] Error: {e}")
        return False


def test_preprocessing_imports():
    """Test preprocessing module imports."""
    print("\n[TEST] Testing preprocessing module imports...")

    try:
        from football_bi.preprocessing import leakage_check
        print("  [OK] leakage_check module imported")

        from football_bi.preprocessing import imputation
        print("  [OK] imputation module imported")

        from football_bi.preprocessing import scaling
        print("  [OK] scaling module imported")

        # Test basic classes
        validator = leakage_check.TemporalLeakageValidator
        print("  [OK] TemporalLeakageValidator class found")

        imputer = imputation.HierarchicalImputer
        print("  [OK] HierarchicalImputer class found")

        processor = scaling.ScalingProcessor
        print("  [OK] ScalingProcessor class found")

        return True
    except Exception as e:
        print(f"  [ERR] Error: {e}")
        return False


def test_basic_functions():
    """Test basic function calls."""
    print("\n[TEST] Testing basic function calls...")

    try:
        import pandas as pd
        import numpy as np
        from football_bi.features import player, advanced

        # Test player feature names
        player_names = player.get_player_feature_names()
        print(f"  [OK] Player features: {len(player_names)} features created")

        # Test advanced feature names
        advanced_names = advanced.get_advanced_feature_names()
        print(f"  [OK] Advanced features: {len(advanced_names)} features created")

        # Create dummy data
        df_dummy = pd.DataFrame({
            'home_recent_points_avg_pre': [1.5, 2.0],
            'away_recent_points_avg_pre': [1.0, 2.5],
            'elo_diff': [50, -30],
            'home_rest_days_pre': [3, 5],
            'away_rest_days_pre': [3, 3],
        })

        # Test form interaction
        form_int = advanced.compute_form_interaction(1.5, 1.0)
        print(f"  [OK] Form interaction computed: {form_int:.2f}")

        # Test ELO form
        elo_form = advanced.compute_elo_form_product(50, 1.5)
        print(f"  [OK] ELO form product computed: {elo_form:.2f}")

        # Test rest disparity
        rest_disp = advanced.compute_rest_disparity(3, 3)
        print(f"  [OK] Rest disparity computed: {rest_disp:.2f}")

        # Test leakage validator
        from football_bi.preprocessing import leakage_check
        validator = leakage_check.TemporalLeakageValidator()
        result = validator.check_feature_names(df_dummy)
        print(f"  [OK] Leakage check executed: valid={result['valid']}")

        return True
    except Exception as e:
        print(f"  [ERR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test YAML configuration loading."""
    print("\n[TEST] Testing configuration loading...")

    try:
        import yaml
        from pathlib import Path

        config_path = Path(__file__).parent / "config"

        files = ['features.yaml', 'models.yaml', 'experiment.yaml']
        for fname in files:
            fpath = config_path / fname
            if fpath.exists():
                with open(fpath) as f:
                    data = yaml.safe_load(f)
                print(f"  [OK] {fname} loaded successfully")
            else:
                print(f"  [WARN] {fname} not found (expected in {config_path})")

        return True
    except Exception as e:
        print(f"  [ERR] Error: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("FOOTBALL PREDICTION - SMOKE TEST")
    print("=" * 60)

    results = {
        'Features': test_feature_imports(),
        'Preprocessing': test_preprocessing_imports(),
        'Basic Functions': test_basic_functions(),
        'Configuration': test_config_loading(),
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name}: {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All smoke tests PASSED! Project structure is ready.")
        return 0
    else:
        print(f"\n[WARNING] Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
