"""
Authentication and security middleware for the AI Agent API.

This module provides JWT token validation, user context management,
and security utilities for protecting API endpoints.
"""

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import jwt
import logging
from datetime import datetime, timedelta

from app.config import settings
from app.auth.schemas import TokenData, UserResponse
from app.auth.models import User
from app.database.connection import get_database_session

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error with detailed logging."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)
        logger.warning(f"Authentication error: {detail}")


class AuthMiddleware:
    """JWT authentication middleware for validating tokens and extracting user context."""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and extract payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dictionary
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                raise AuthenticationError("Token missing subject")
                
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise AuthenticationError("Token has expired")
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    async def get_current_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_database_session)
    ) -> Optional[UserResponse]:
        """
        Get current authenticated user from JWT token.
        
        Args:
            credentials: HTTP authorization credentials
            db: Database session
            
        Returns:
            User information if authenticated, None if optional auth
            
        Raises:
            AuthenticationError: If token is invalid (when required)
        """
        if not credentials:
            return None
            
        token = credentials.credentials
        payload = self.verify_token(token)
        username = payload.get("sub")
        
        if not username:
            raise AuthenticationError("Invalid token payload")
        
        # For demo purposes, return mock user data
        # In production, query the database for the actual user
        if username == "demo":
            return UserResponse(
                id="demo-user-id",
                email="demo@example.com",
                username="demo",
                is_active=True,
                created_at=datetime.utcnow()
            )
        
        # TODO: Implement actual database user lookup
        # user = await get_user_by_username(db, username)
        # if not user or not user.is_active:
        #     raise AuthenticationError("User not found or inactive")
        
        raise AuthenticationError("User not found")
    
    async def get_current_active_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_database_session)
    ) -> UserResponse:
        """
        Get current authenticated and active user (required auth).
        
        Args:
            credentials: HTTP authorization credentials (required)
            db: Database session
            
        Returns:
            User information
            
        Raises:
            AuthenticationError: If not authenticated or user inactive
        """
        if not credentials:
            raise AuthenticationError(
                "Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        user = await self.get_current_user(credentials, db)
        if not user:
            raise AuthenticationError("Authentication required")
            
        if not user.is_active:
            raise AuthenticationError("Inactive user")
            
        return user
    
    async def get_optional_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_database_session)
    ) -> Optional[UserResponse]:
        """
        Get current user if authenticated, None if not (optional auth).
        
        Args:
            credentials: HTTP authorization credentials (optional)
            db: Database session
            
        Returns:
            User information if authenticated, None otherwise
        """
        try:
            return await self.get_current_user(credentials, db)
        except AuthenticationError:
            return None


# Global auth middleware instance
auth_middleware = AuthMiddleware()

# Dependency functions for easy use in endpoints
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> Optional[UserResponse]:
    """Dependency to get current user (optional authentication)."""
    return await auth_middleware.get_current_user(credentials, db)


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> UserResponse:
    """Dependency to get current active user (required authentication)."""
    return await auth_middleware.get_current_active_user(credentials, db)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> Optional[UserResponse]:
    """Dependency to get current user if authenticated (optional authentication)."""
    return await auth_middleware.get_optional_user(credentials, db)


def create_user_context(user: Optional[UserResponse]) -> Dict[str, Any]:
    """
    Create user context dictionary for use in services.
    
    Args:
        user: User information or None for anonymous
        
    Returns:
        User context dictionary
    """
    if user:
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_authenticated": True,
            "is_active": user.is_active
        }
    else:
        return {
            "user_id": None,
            "username": "anonymous",
            "email": None,
            "is_authenticated": False,
            "is_active": False
        }


class APIKeyValidator:
    """Validator for external API keys with secure handling."""
    
    def __init__(self):
        self.required_keys = {
            "groq": settings.GROQ_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "serp": settings.SERP_API_KEY,
            "brave_search": settings.BRAVE_SEARCH_API_KEY,
            "binance": settings.BINANCE_API_KEY
        }
    
    def validate_api_key(self, service: str) -> bool:
        """
        Validate if API key exists for a service.
        
        Args:
            service: Service name (groq, openai, etc.)
            
        Returns:
            True if API key is available
        """
        key = self.required_keys.get(service)
        return key is not None and len(key.strip()) > 0
    
    def get_available_services(self) -> Dict[str, bool]:
        """
        Get availability status of all external services.
        
        Returns:
            Dictionary mapping service names to availability status
        """
        return {
            service: self.validate_api_key(service)
            for service in self.required_keys.keys()
        }
    
    def mask_api_key(self, api_key: str) -> str:
        """
        Mask API key for logging (show only first and last 4 characters).
        
        Args:
            api_key: Full API key
            
        Returns:
            Masked API key string
        """
        if not api_key or len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"


# Global API key validator instance
api_key_validator = APIKeyValidator()