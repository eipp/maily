#!/usr/bin/env python
"""
Test runner script that applies patches before running tests

This script imports necessary patches before running pytest,
ensuring compatibility with Python 3.13+.
"""

import sys
import os
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the aioredis patch before anything else
from ai_service.patches.patch_aioredis import *

# Run pytest with the provided arguments
if __name__ == "__main__":
    import pytest
    
    # Default to running the AI mesh network tests if no arguments are provided
    if len(sys.argv) == 1:
        test_path = "tests/test_ai_mesh_network.py"
        args = ["-v", test_path]
    else:
        args = sys.argv[1:]
    
    # Run pytest with the provided arguments
    sys.exit(pytest.main(args))
