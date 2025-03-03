"""
Database Service Module

This module provides database connectivity and operations for the AI Service.
It implements connection pooling, ORM capabilities, and migration support.
"""

import os
import logging
import uuid
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from datetime import datetime

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
from alembic.config import Config
from alembic import command

# Configure logging
logger = logging.getLogger(__name__)

# Get database configuration from environment variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "maily")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "1800"))  # 30 minutes

# Create database URL
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy base
Base = declarative_base()

# Define models
class AISession(Base):
    """AI Session model for storing AI session data"""
    
    __tablename__ = "ai_sessions"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="active")
    metadata = Column(JSON, default=dict)
    
    # Relationships
    messages = relationship("AIMessage", back_populates="session", cascade="all, delete-orphan")
    agents = relationship("AIAgent", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "metadata": self.metadata,
        }


class AIMessage(Base):
    """AI Message model for storing messages in an AI session"""
    
    __tablename__ = "ai_messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("ai_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    session = relationship("AISession", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


class AIAgent(Base):
    """AI Agent model for storing AI agents in the mesh network"""
    
    __tablename__ = "ai_agents"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("ai_sessions.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    session = relationship("AISession", back_populates="agents")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }


class AIInteraction(Base):
    """AI Interaction model for storing interactions between AI agents"""
    
    __tablename__ = "ai_interactions"
    
    id = Column(String(36), primary_key=True)
    source_agent_id = Column(String(36), ForeignKey("ai_agents.id"), nullable=False, index=True)
    target_agent_id = Column(String(36), ForeignKey("ai_agents.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary"""
        return {
            "id": self.id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "type": self.type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


class AIContentSafety(Base):
    """AI Content Safety model for storing content safety checks"""
    
    __tablename__ = "ai_content_safety"
    
    id = Column(String(36), primary_key=True)
    content_id = Column(String(36), nullable=False, index=True)
    content_type = Column(String(50), nullable=False)  # message, interaction, etc.
    check_type = Column(String(50), nullable=False)  # toxicity, hate, etc.
    score = Column(sqlalchemy.Float, nullable=False)
    is_flagged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert content safety check to dictionary"""
        return {
            "id": self.id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "check_type": self.check_type,
            "score": self.score,
            "is_flagged": self.is_flagged,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


# Create engine with connection pooling
engine = create_engine(
    DB_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    echo=False,
)

# Create session factory
SessionFactory = sessionmaker(bind=engine)

# Create scoped session
ScopedSession = scoped_session(SessionFactory)


@contextmanager
def get_db_session():
    """Get a database session from the pool"""
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()


def init_db():
    """Initialize the database"""
    try:
        # Create tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created")
        
        # Run migrations
        run_migrations()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def run_migrations():
    """Run database migrations"""
    try:
        # Get alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error(f"Failed to run migrations: {str(e)}")
        raise


from ai_service.utils.resilience import circuit_breaker, CircuitBreakerOpenError

@circuit_breaker(
    name="database_get_session",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=lambda session_id: {
        "id": session_id,
        "user_id": "unknown",
        "status": "error",
        "messages": [],
        "agents": [],
        "metadata": {"error": "Database service temporarily unavailable"},
        "created_at": None,
        "updated_at": None
    }
)
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an AI session by ID
    
    Args:
        session_id: The session ID
        
    Returns:
        The session as a dictionary, or None if not found
        When the circuit breaker is open, returns a fallback response with error metadata
    """
    try:
        with get_db_session() as session:
            ai_session = session.query(AISession).filter(AISession.id == session_id).first()
            
            if ai_session:
                # Get messages
                messages = session.query(AIMessage).filter(AIMessage.session_id == session_id).all()
                
                # Get agents
                agents = session.query(AIAgent).filter(AIAgent.session_id == session_id).all()
                
                # Create result
                result = ai_session.to_dict()
                result["messages"] = [message.to_dict() for message in messages]
                result["agents"] = [agent.to_dict() for agent in agents]
                
                return result
            
            return None
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise


@circuit_breaker(
    name="database_create_session",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=lambda user_id, metadata=None: {
        "id": f"fallback-{str(uuid.uuid4())}",
        "user_id": user_id,
        "status": "error",
        "metadata": {
            **(metadata or {}),
            "error": "Database service temporarily unavailable",
            "fallback": True
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
)
def create_session(user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a new AI session
    
    Args:
        user_id: The user ID
        metadata: Optional metadata
        
    Returns:
        The created session as a dictionary
        When the circuit breaker is open, returns a fallback response with error metadata
    """
    try:
        import uuid
        
        session_id = str(uuid.uuid4())
        
        with get_db_session() as session:
            ai_session = AISession(
                id=session_id,
                user_id=user_id,
                metadata=metadata or {},
            )
            
            session.add(ai_session)
            session.commit()
            
            return ai_session.to_dict()
    except Exception as e:
        logger.error(f"Failed to create session for user {user_id}: {str(e)}")
        raise


@circuit_breaker(
    name="database_add_message",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=lambda session_id, role, content, metadata=None: {
        "id": f"fallback-{str(uuid.uuid4())}",
        "session_id": session_id,
        "role": role,
        "content": content,
        "metadata": {
            **(metadata or {}),
            "error": "Database service temporarily unavailable",
            "fallback": True
        },
        "created_at": datetime.utcnow().isoformat()
    }
)
def add_message(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add a message to an AI session
    
    Args:
        session_id: The session ID
        role: The message role (user, assistant, system)
        content: The message content
        metadata: Optional metadata
        
    Returns:
        The created message as a dictionary
        When the circuit breaker is open, returns a fallback response with error metadata
    """
    try:
        import uuid
        
        message_id = str(uuid.uuid4())
        
        with get_db_session() as session:
            # Check if session exists
            ai_session = session.query(AISession).filter(AISession.id == session_id).first()
            
            if not ai_session:
                raise ValueError(f"Session {session_id} not found")
            
            # Create message
            message = AIMessage(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata or {},
            )
            
            # Add message to session
            session.add(message)
            
            # Update session
            ai_session.updated_at = datetime.utcnow()
            
            session.commit()
            
            return message.to_dict()
    except Exception as e:
        logger.error(f"Failed to add message to session {session_id}: {str(e)}")
        raise


@circuit_breaker(
    name="database_add_agent",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=lambda session_id, name, agent_type, metadata=None: {
        "id": f"fallback-{str(uuid.uuid4())}",
        "session_id": session_id,
        "name": name,
        "type": agent_type,
        "status": "error",
        "metadata": {
            **(metadata or {}),
            "error": "Database service temporarily unavailable",
            "fallback": True
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
)
def add_agent(session_id: str, name: str, agent_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add an agent to an AI session
    
    Args:
        session_id: The session ID
        name: The agent name
        agent_type: The agent type
        metadata: Optional metadata
        
    Returns:
        The created agent as a dictionary
        When the circuit breaker is open, returns a fallback response with error metadata
    """
    try:
        agent_id = str(uuid.uuid4())
        
        with get_db_session() as session:
            # Check if session exists
            ai_session = session.query(AISession).filter(AISession.id == session_id).first()
            
            if not ai_session:
                raise ValueError(f"Session {session_id} not found")
            
            # Create agent
            agent = AIAgent(
                id=agent_id,
                session_id=session_id,
                name=name,
                type=agent_type,
                metadata=metadata or {},
            )
            
            # Add agent to session
            session.add(agent)
            
            # Update session
            ai_session.updated_at = datetime.utcnow()
            
            session.commit()
            
            return agent.to_dict()
    except Exception as e:
        logger.error(f"Failed to add agent to session {session_id}: {str(e)}")
        raise


def add_interaction(source_agent_id: str, target_agent_id: str, interaction_type: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add an interaction between AI agents
    
    Args:
        source_agent_id: The source agent ID
        target_agent_id: The target agent ID
        interaction_type: The interaction type
        content: Optional interaction content
        metadata: Optional metadata
        
    Returns:
        The created interaction as a dictionary
    """
    try:
        import uuid
        
        interaction_id = str(uuid.uuid4())
        
        with get_db_session() as session:
            # Check if agents exist
            source_agent = session.query(AIAgent).filter(AIAgent.id == source_agent_id).first()
            target_agent = session.query(AIAgent).filter(AIAgent.id == target_agent_id).first()
            
            if not source_agent:
                raise ValueError(f"Source agent {source_agent_id} not found")
            
            if not target_agent:
                raise ValueError(f"Target agent {target_agent_id} not found")
            
            # Create interaction
            interaction = AIInteraction(
                id=interaction_id,
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                type=interaction_type,
                content=content,
                metadata=metadata or {},
            )
            
            # Add interaction
            session.add(interaction)
            
            # Update agents
            source_agent.updated_at = datetime.utcnow()
            target_agent.updated_at = datetime.utcnow()
            
            session.commit()
            
            return interaction.to_dict()
    except Exception as e:
        logger.error(f"Failed to add interaction between agents {source_agent_id} and {target_agent_id}: {str(e)}")
        raise


def add_content_safety_check(content_id: str, content_type: str, check_type: str, score: float, is_flagged: bool, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add a content safety check
    
    Args:
        content_id: The content ID
        content_type: The content type
        check_type: The check type
        score: The safety score
        is_flagged: Whether the content is flagged
        metadata: Optional metadata
        
    Returns:
        The created content safety check as a dictionary
    """
    try:
        import uuid
        
        check_id = str(uuid.uuid4())
        
        with get_db_session() as session:
            # Create content safety check
            check = AIContentSafety(
                id=check_id,
                content_id=content_id,
                content_type=content_type,
                check_type=check_type,
                score=score,
                is_flagged=is_flagged,
                metadata=metadata or {},
            )
            
            # Add check
            session.add(check)
            
            session.commit()
            
            return check.to_dict()
    except Exception as e:
        logger.error(f"Failed to add content safety check for content {content_id}: {str(e)}")
        raise


def get_content_safety_checks(content_id: str, content_type: str) -> List[Dict[str, Any]]:
    """
    Get content safety checks for a content
    
    Args:
        content_id: The content ID
        content_type: The content type
        
    Returns:
        The content safety checks as a list of dictionaries
    """
    try:
        with get_db_session() as session:
            checks = session.query(AIContentSafety).filter(
                AIContentSafety.content_id == content_id,
                AIContentSafety.content_type == content_type,
            ).all()
            
            return [check.to_dict() for check in checks]
    except Exception as e:
        logger.error(f"Failed to get content safety checks for content {content_id}: {str(e)}")
        raise


def get_flagged_content(content_type: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get flagged content
    
    Args:
        content_type: Optional content type filter
        limit: Maximum number of results
        offset: Result offset
        
    Returns:
        The flagged content as a list of dictionaries
    """
    try:
        with get_db_session() as session:
            query = session.query(AIContentSafety).filter(AIContentSafety.is_flagged == True)
            
            if content_type:
                query = query.filter(AIContentSafety.content_type == content_type)
            
            checks = query.order_by(AIContentSafety.created_at.desc()).limit(limit).offset(offset).all()
            
            return [check.to_dict() for check in checks]
    except Exception as e:
        logger.error(f"Failed to get flagged content: {str(e)}")
        raise


def execute_raw_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query
    
    Args:
        query: The SQL query
        params: Optional query parameters
        
    Returns:
        The query results as a list of dictionaries
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            
            # Convert result to list of dictionaries
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
    except Exception as e:
        logger.error(f"Failed to execute query: {str(e)}")
        raise


def close_db_connections():
    """Close all database connections"""
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Failed to close database connections: {str(e)}")
        raise
