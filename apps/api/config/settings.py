"""
Settings module (Forwarding to standardized config)

This module imports and re-exports the settings from the standardized location.
This is only for backward compatibility - new code should import directly from
config/app/api/settings.py.
"""

import sys
import os
import warnings

# Show deprecation warning
warnings.warn(
    "Importing from apps/api/config/settings.py is deprecated. "
    "Please import directly from config/app/api/settings.py instead.",
    DeprecationWarning, stacklevel=2
)

# Add parent directory to path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Import settings from standardized location
from config.app.api.settings import settings, Settings, load_blockchain_abis

# Re-export for backward compatibility
__all__ = ["settings", "Settings", "load_blockchain_abis"]