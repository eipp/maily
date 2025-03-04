"""
Session Management System for AI Mesh Network

This module provides a session management system with TTL for AI agent networks,
allowing for persistent conversational state and automatic cleanup of expired sessions.
"""

import json
import time
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from ...utils.redis_client import get_redis_client

logger = logging.getLogger("ai_service.implementations.memory.session_management")

# Constants
SESSION_KEY_PREFIX = "ai_mesh:session:"
SESSION_INDEX_PREFIX = "ai_mesh:session_index:"
SESSION_USER_PREFIX = "ai_mesh:session_user:"
SESSION_CLEANUP_INTERVAL = 300  # 5 minutes
DEFAULT_SESSION_TTL = 86400  # 24 hours

class SessionManager:
    """Session management system with TTL for AI agent networks"""
    
    def __init__(self):
        """Initialize the session manager"""
        self.redis = get_redis_client()
        self.active_session_cleanup_tasks = set()
        
        # Start background cleanup task
        asyncio.create_task(self._cleanup_sessions_periodically())
    
    async def create_session(
        self,
        network_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: int = DEFAULT_SESSION_TTL
    ) -> str:
        """
        Create a new session for an AI network
        
        Args:
            network_id: ID of the AI network
            user_id: Optional user ID associated with the session
            metadata: Optional metadata for the session
            ttl: Time-to-live in seconds
            
        Returns:
            Session ID
        """
        try:
            # Generate session ID
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            # Create session object
            current_time = int(time.time())
            expiry_time = current_time + ttl
            
            session = {
                "id": session_id,
                "network_id": network_id,
                "user_id": user_id,
                "created_at": current_time,
                "updated_at": current_time,
                "expires_at": expiry_time,
                "ttl": ttl,
                "metadata": metadata or {},
                "turns": [],
                "state": "active"
            }
            
            # Store session
            session_key = f"{SESSION_KEY_PREFIX}{session_id}"
            await self.redis.set(session_key, json.dumps(session), ex=ttl)
            
            # Add to network index
            network_index_key = f"{SESSION_INDEX_PREFIX}{network_id}"
            await self.redis.lpush(network_index_key, session_id)
            
            # Add to user index if user_id provided
            if user_id:
                user_index_key = f"{SESSION_USER_PREFIX}{user_id}"
                await self.redis.lpush(user_index_key, session_id)
            
            logger.info(f"Created session {session_id} for network {network_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session data dictionary if found, None otherwise
        """
        try:
            # Get session data
            session_key = f"{SESSION_KEY_PREFIX}{session_id}"
            session_data = await self.redis.get(session_key)
            
            if not session_data:
                return None
            
            # Parse session data
            session = json.loads(session_data)
            
            # Check expiration
            current_time = int(time.time())
            if session.get("expires_at", 0) < current_time:
                logger.warning(f"Accessed expired session {session_id}")
                await self.delete_session(session_id)
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any],
        extend_ttl: bool = True
    ) -> bool:
        """
        Update session data
        
        Args:
            session_id: ID of the session
            updates: Dictionary of fields to update
            extend_ttl: Whether to extend the session TTL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current session data
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Update fields
            current_time = int(time.time())
            session.update(updates)
            session["updated_at"] = current_time
            
            # Extend TTL if requested
            ttl = session["ttl"]
            if extend_ttl:
                session["expires_at"] = current_time + ttl
            
            # Store updated session
            session_key = f"{SESSION_KEY_PREFIX}{session_id}"
            await self.redis.set(session_key, json.dumps(session), ex=ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    async def add_session_turn(
        self,
        session_id: str,
        user_input: str,
        system_response: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a conversation turn to a session
        
        Args:
            session_id: ID of the session
            user_input: User input text
            system_response: System response text
            metadata: Optional metadata for the turn
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current session data
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Create turn object
            turn = {
                "timestamp": int(time.time()),
                "user_input": user_input,
                "system_response": system_response,
                "metadata": metadata or {}
            }
            
            # Add turn to session
            session["turns"].append(turn)
            
            # Update session
            return await self.update_session(session_id, {"turns": session["turns"]})
            
        except Exception as e:
            logger.error(f"Failed to add turn to session {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get session to get network_id and user_id
            session_key = f"{SESSION_KEY_PREFIX}{session_id}"
            session_data = await self.redis.get(session_key)
            
            if session_data:
                session = json.loads(session_data)
                network_id = session.get("network_id")
                user_id = session.get("user_id")
                
                # Remove from network index
                if network_id:
                    network_index_key = f"{SESSION_INDEX_PREFIX}{network_id}"
                    await self.redis.lrem(network_index_key, 0, session_id)
                
                # Remove from user index
                if user_id:
                    user_index_key = f"{SESSION_USER_PREFIX}{user_id}"
                    await self.redis.lrem(user_index_key, 0, session_id)
            
            # Delete session data
            await self.redis.delete(session_key)
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def get_user_sessions(
        self, 
        user_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user
        
        Args:
            user_id: ID of the user
            active_only: Only return active sessions
            
        Returns:
            List of session data dictionaries
        """
        try:
            # Get session IDs for user
            user_index_key = f"{SESSION_USER_PREFIX}{user_id}"
            session_ids = await self.redis.lrange(user_index_key, 0, -1)
            
            if not session_ids:
                return []
            
            # Get session data for each ID
            sessions = []
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session and (not active_only or session.get("state") == "active"):
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    async def get_network_sessions(
        self, 
        network_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions for a network
        
        Args:
            network_id: ID of the network
            active_only: Only return active sessions
            
        Returns:
            List of session data dictionaries
        """
        try:
            # Get session IDs for network
            network_index_key = f"{SESSION_INDEX_PREFIX}{network_id}"
            session_ids = await self.redis.lrange(network_index_key, 0, -1)
            
            if not session_ids:
                return []
            
            # Get session data for each ID
            sessions = []
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session and (not active_only or session.get("state") == "active"):
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for network {network_id}: {e}")
            return []
    
    async def get_session_metrics(
        self,
        network_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get session metrics
        
        Args:
            network_id: Optional network ID to limit metrics to
            
        Returns:
            Dictionary with session metrics
        """
        try:
            metrics = {
                "total_sessions": 0,
                "active_sessions": 0,
                "expired_sessions": 0,
                "average_turns_per_session": 0,
                "total_turns": 0
            }
            
            # Get session IDs
            if network_id:
                network_index_key = f"{SESSION_INDEX_PREFIX}{network_id}"
                session_ids = await self.redis.lrange(network_index_key, 0, -1)
            else:
                session_keys = await self.redis.keys(f"{SESSION_KEY_PREFIX}*")
                session_ids = [key.replace(SESSION_KEY_PREFIX, "") for key in session_keys]
            
            if not session_ids:
                return metrics
            
            metrics["total_sessions"] = len(session_ids)
            
            # Analyze each session
            total_turns = 0
            active_sessions = 0
            
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session:
                    # Count active sessions
                    if session.get("state") == "active":
                        active_sessions += 1
                    
                    # Count turns
                    turns = session.get("turns", [])
                    total_turns += len(turns)
            
            metrics["active_sessions"] = active_sessions
            metrics["expired_sessions"] = metrics["total_sessions"] - active_sessions
            metrics["total_turns"] = total_turns
            
            # Calculate average turns per session
            if metrics["total_sessions"] > 0:
                metrics["average_turns_per_session"] = total_turns / metrics["total_sessions"]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get session metrics: {e}")
            return {}
    
    async def _cleanup_sessions_periodically(self):
        """Periodically clean up expired sessions"""
        try:
            while True:
                # Wait for next cleanup interval
                await asyncio.sleep(SESSION_CLEANUP_INTERVAL)
                
                # Get all session keys
                session_keys = await self.redis.keys(f"{SESSION_KEY_PREFIX}*")
                
                if not session_keys:
                    continue
                
                logger.info(f"Checking {len(session_keys)} sessions for expiration")
                
                # Current time
                current_time = int(time.time())
                expired_count = 0
                
                # Check each session
                for session_key in session_keys:
                    try:
                        session_data = await self.redis.get(session_key)
                        if not session_data:
                            continue
                        
                        session = json.loads(session_data)
                        
                        # Check if expired
                        if session.get("expires_at", 0) < current_time:
                            # Delete expired session
                            session_id = session_key.replace(SESSION_KEY_PREFIX, "")
                            await self.delete_session(session_id)
                            expired_count += 1
                    except Exception as inner_e:
                        logger.error(f"Error checking session {session_key}: {inner_e}")
                
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")
                
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in session cleanup task: {e}")
            # Restart the task
            asyncio.create_task(self._cleanup_sessions_periodically())

# Singleton instance
_session_manager_instance = None

def get_session_manager() -> SessionManager:
    """Get the singleton instance of SessionManager"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance