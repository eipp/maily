"""
Patch for aioredis TimeoutError in Python 3.13+

This module patches the aioredis.exceptions module to fix the duplicate base class TimeoutError issue
in Python 3.13+. Import this module before importing aioredis or any module that imports aioredis.
"""

import sys
import importlib.abc
import importlib.util
import types
from pathlib import Path

class AioredisMetaPathFinder(importlib.abc.MetaPathFinder):
    """
    A meta path finder that intercepts imports of aioredis.exceptions
    and patches the TimeoutError class to avoid the duplicate base class issue.
    """
    
    def find_spec(self, fullname, path, target=None):
        # Only intercept aioredis.exceptions
        if fullname != 'aioredis.exceptions':
            return None
        
        # Find the original spec
        for finder in sys.meta_path:
            if finder is self:
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                # Create a custom loader that will patch the module
                spec.loader = AioredisExceptionsLoader(spec.loader)
                return spec
        
        return None

class AioredisExceptionsLoader(importlib.abc.Loader):
    """
    A custom loader that patches the aioredis.exceptions module
    to fix the TimeoutError class.
    """
    
    def __init__(self, original_loader):
        self.original_loader = original_loader
    
    def create_module(self, spec):
        # Let the original loader create the module
        return self.original_loader.create_module(spec)
    
    def exec_module(self, module):
        # Execute the original module
        self.original_loader.exec_module(module)
        
        # Patch the TimeoutError class
        if hasattr(module, 'TimeoutError'):
            # In Python 3.13+, asyncio.TimeoutError is the same as builtins.TimeoutError
            # So we need to create a new class that only inherits from RedisError
            original_timeout_error = module.TimeoutError
            
            # Create a new TimeoutError class that only inherits from RedisError
            class PatchedTimeoutError(module.RedisError):
                pass
            
            # Copy attributes from the original TimeoutError
            for attr_name in dir(original_timeout_error):
                if not attr_name.startswith('__'):
                    attr = getattr(original_timeout_error, attr_name)
                    setattr(PatchedTimeoutError, attr_name, attr)
            
            # Replace the original TimeoutError with our patched version
            module.TimeoutError = PatchedTimeoutError

# Install the meta path finder
sys.meta_path.insert(0, AioredisMetaPathFinder())

print("Aioredis TimeoutError patch installed")
