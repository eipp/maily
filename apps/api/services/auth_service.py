from typing import Optional
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging

from api.models.user import User

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# JWT configuration
SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    """Service for authentication and authorization."""

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email
            password: User's password

        Returns:
            User object if authentication is successful, None otherwise
        """
        try:
            # In a real implementation, this would fetch the user from a database
            # and verify the password hash

            # For now, we'll return a mock user for demonstration
            if email == "user@example.com" and password == "password":
                return User(
                    id="user_1",
                    email=email,
                    name="Test User",
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )

            return None
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """
        Get the current user from the JWT token.

        Args:
            token: JWT token

        Returns:
            User object

        Raises:
            HTTPException: If the token is invalid or the user is not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode the JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")

            if user_id is None:
                raise credentials_exception

            # In a real implementation, this would fetch the user from a database
            # For now, we'll return a mock user for demonstration
            return User(
                id=user_id,
                email="user@example.com",
                name="Test User",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        except jwt.PyJWTError:
            raise credentials_exception

# Create a function that will be used as a dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from the JWT token.

    Args:
        token: JWT token

    Returns:
        User object
    """
    auth_service = AuthService()
    return await auth_service.get_current_user(token)

# Singleton instance
auth_service = AuthService()
