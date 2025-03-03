"""Patched version of aioredis exceptions for Python 3.13 compatibility"""
import asyncio
import builtins
from aioredis.exceptions import RedisError, ConnectionError, ResponseError

# Fix the duplicate base class issue
class TimeoutError(RedisError):
    """
    Patched TimeoutError that doesn't inherit from both asyncio.TimeoutError and builtins.TimeoutError
    to avoid the duplicate base class error in Python 3.13
    """
    pass

# Export the patched TimeoutError
__all__ = ['TimeoutError']
