"""
Authentication and Authorization Models
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"
    VIEWER = "viewer"
    GUEST = "guest"


class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class User(Base):
    """User model for database"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default=UserRole.VIEWER.value)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    preferences = Column(JSON, default=dict)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class APIKey(Base):
    """API Key model"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First 8 chars for identification
    permissions = Column(JSON, default=list)  # List of permissions
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


# Pydantic models for API
class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    preferences: Dict[str, Any]
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class APIKeyCreate(BaseModel):
    """API key creation model"""
    key_name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response model"""
    id: int
    key_name: str
    key_prefix: str
    permissions: List[str]
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class APIKeyFullResponse(APIKeyResponse):
    """API key response with full key (only shown once)"""
    api_key: str


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: int
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool


class UserPreferences(BaseModel):
    """User preferences model"""
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    notifications: Dict[str, bool] = Field(default_factory=dict)
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict)


class Permission(str, Enum):
    """System permissions"""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Service management
    SERVICE_CREATE = "service:create"
    SERVICE_READ = "service:read"
    SERVICE_UPDATE = "service:update"
    SERVICE_DELETE = "service:delete"
    
    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_MONITOR = "system:monitor"
    
    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.SERVICE_CREATE,
        Permission.SERVICE_READ,
        Permission.SERVICE_UPDATE,
        Permission.SERVICE_DELETE,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_LOGS,
        Permission.SYSTEM_MONITOR,
        Permission.API_READ,
        Permission.API_WRITE,
        Permission.API_ADMIN,
    ],
    UserRole.MANAGER: [
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.SERVICE_CREATE,
        Permission.SERVICE_READ,
        Permission.SERVICE_UPDATE,
        Permission.SYSTEM_MONITOR,
        Permission.API_READ,
        Permission.API_WRITE,
    ],
    UserRole.TECHNICIAN: [
        Permission.SERVICE_READ,
        Permission.SERVICE_UPDATE,
        Permission.API_READ,
        Permission.API_WRITE,
    ],
    UserRole.VIEWER: [
        Permission.SERVICE_READ,
        Permission.API_READ,
    ],
    UserRole.GUEST: [
        Permission.API_READ,
    ],
}
