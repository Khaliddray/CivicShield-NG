#!/usr/bin/env python3
"""CivicShield NG Unified Test Runner."""

import os
import sys
import unittest
from pathlib import Path

# Ensure workspace and site packages are in sys.path
workspace_dir = Path(__file__).resolve().parent
site_pkgs_1 = Path("/home/l2e_abdyhaya/snap/antigravity-cli/common/local/lib/python3.12/site-packages")
site_pkgs_2 = Path("/snap/antigravity-cli/24/usr/lib/python3/dist-packages")

for p in [str(workspace_dir), str(site_pkgs_1), str(site_pkgs_2)]:
    if p not in sys.path and Path(p).exists():
        sys.path.insert(0, p)

if __name__ == "__main__":
    test_dir = workspace_dir / "backend" / "tests"
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(test_dir),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
