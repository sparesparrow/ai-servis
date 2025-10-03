"""
JWT Authentication Service
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class JWTAuthService:
    """JWT Authentication Service"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise ValueError("Failed to hash password")
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise ValueError("Failed to create access token")
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Refresh token creation error: {e}")
            raise ValueError("Failed to create refresh token")
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type: expected {token_type}, got {payload.get('type')}")
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None:
                logger.warning("Token missing expiration")
                return None
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Token expired")
                return None
            
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def create_token_pair(self, user_id: int, username: str, role: str, permissions: List[str]) -> Dict[str, Any]:
        """Create both access and refresh tokens"""
        token_data = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "permissions": permissions,
            "iat": datetime.utcnow()
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Create new access token from refresh token"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # Create new access token with same data
        token_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions", []),
            "iat": datetime.utcnow()
        }
        
        access_token = self.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }
    
    def extract_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        return {
            "user_id": int(payload.get("sub", 0)),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions", [])
        }
    
    def has_permission(self, token: str, required_permission: str) -> bool:
        """Check if token has required permission"""
        user_info = self.extract_user_info(token)
        if not user_info:
            return False
        
        permissions = user_info.get("permissions", [])
        return required_permission in permissions
    
    def has_role(self, token: str, required_role: str) -> bool:
        """Check if token has required role"""
        user_info = self.extract_user_info(token)
        if not user_info:
            return False
        
        return user_info.get("role") == required_role
    
    def has_any_role(self, token: str, required_roles: List[str]) -> bool:
        """Check if token has any of the required roles"""
        user_info = self.extract_user_info(token)
        if not user_info:
            return False
        
        user_role = user_info.get("role")
        return user_role in required_roles


class APIKeyAuthService:
    """API Key Authentication Service"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
    
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        return f"ai_servis_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        return bcrypt.hash(api_key)
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash"""
        try:
            return bcrypt.verify(api_key, hashed_key)
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return False
    
    def extract_key_prefix(self, api_key: str) -> str:
        """Extract the first 8 characters as key prefix"""
        return api_key[:8]
    
    def create_api_key_token(self, user_id: int, username: str, role: str, permissions: List[str]) -> str:
        """Create a token for API key authentication"""
        token_data = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "permissions": permissions,
            "type": "api_key",
            "iat": datetime.utcnow()
        }
        
        # API key tokens don't expire
        return jwt.encode(token_data, self.secret_key, algorithm=ALGORITHM)
    
    def verify_api_key_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify an API key token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            
            if payload.get("type") != "api_key":
                return None
            
            return payload
        except JWTError as e:
            logger.warning(f"API key token verification error: {e}")
            return None
        except Exception as e:
            logger.error(f"API key token verification error: {e}")
            return None
