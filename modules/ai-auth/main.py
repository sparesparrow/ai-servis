"""
Authentication & Authorization MCP Server
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from mcp_framework import MCPServer, create_tool
from auth_models import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, TokenResponse,
    RefreshTokenRequest, APIKeyCreate, APIKeyResponse, APIKeyFullResponse,
    SessionInfo, UserPreferences, UserRole, Permission, ROLE_PERMISSIONS
)
from database import DatabaseService
from sqlalchemy import and_
from jwt_auth import JWTAuthService, APIKeyAuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_auth.db")


class AuthMCPServer(MCPServer):
    """Authentication & Authorization MCP Server"""
    
    def __init__(self):
        super().__init__("ai-auth", "1.0.0")
        self.db_service = DatabaseService(DATABASE_URL)
        self.jwt_auth = JWTAuthService()
        self.api_key_auth = APIKeyAuthService()
        self.setup_tools()
        self._initialize_database()
        self._start_cleanup_task()
    
    def _initialize_database(self):
        """Initialize database tables"""
        try:
            self.db_service.create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        async def cleanup():
            while True:
                try:
                    db = self.db_service.get_db_session()
                    self.db_service.cleanup_expired_sessions(db)
                    db.close()
                    await asyncio.sleep(3600)  # Clean up every hour
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                    await asyncio.sleep(3600)
        
        asyncio.create_task(cleanup())
    
    def setup_tools(self):
        """Setup authentication tools"""
        
        # User management tools
        create_user_tool = create_tool(
            name="create_user",
            description="Create a new user account",
            schema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username"},
                    "email": {"type": "string", "description": "Email address"},
                    "password": {"type": "string", "description": "Password"},
                    "full_name": {"type": "string", "description": "Full name"},
                    "role": {"type": "string", "enum": ["admin", "manager", "technician", "viewer", "guest"], "description": "User role"}
                },
                "required": ["username", "email", "password"]
            },
            handler=self.handle_create_user,
        )
        self.add_tool(create_user_tool)
        
        # Authentication tools
        login_tool = create_tool(
            name="login",
            description="Authenticate user and get tokens",
            schema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username"},
                    "password": {"type": "string", "description": "Password"}
                },
                "required": ["username", "password"]
            },
            handler=self.handle_login,
        )
        self.add_tool(login_tool)
        
        refresh_token_tool = create_tool(
            name="refresh_token",
            description="Refresh access token using refresh token",
            schema={
                "type": "object",
                "properties": {
                    "refresh_token": {"type": "string", "description": "Refresh token"}
                },
                "required": ["refresh_token"]
            },
            handler=self.handle_refresh_token,
        )
        self.add_tool(refresh_token_tool)
        
        logout_tool = create_tool(
            name="logout",
            description="Logout user and invalidate session",
            schema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "Access token"}
                },
                "required": ["access_token"]
            },
            handler=self.handle_logout,
        )
        self.add_tool(logout_tool)
        
        # Token verification tools
        verify_token_tool = create_tool(
            name="verify_token",
            description="Verify and decode a JWT token",
            schema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "JWT token to verify"}
                },
                "required": ["token"]
            },
            handler=self.handle_verify_token,
        )
        self.add_tool(verify_token_tool)
        
        check_permission_tool = create_tool(
            name="check_permission",
            description="Check if token has required permission",
            schema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "JWT token"},
                    "permission": {"type": "string", "description": "Required permission"}
                },
                "required": ["token", "permission"]
            },
            handler=self.handle_check_permission,
        )
        self.add_tool(check_permission_tool)
        
        # API key management tools
        create_api_key_tool = create_tool(
            name="create_api_key",
            description="Create a new API key for a user",
            schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID"},
                    "key_name": {"type": "string", "description": "API key name"},
                    "permissions": {"type": "array", "items": {"type": "string"}, "description": "List of permissions"},
                    "expires_in_days": {"type": "integer", "description": "Expiration in days (optional)"}
                },
                "required": ["user_id", "key_name"]
            },
            handler=self.handle_create_api_key,
        )
        self.add_tool(create_api_key_tool)
        
        verify_api_key_tool = create_tool(
            name="verify_api_key",
            description="Verify an API key and get user info",
            schema={
                "type": "object",
                "properties": {
                    "api_key": {"type": "string", "description": "API key to verify"}
                },
                "required": ["api_key"]
            },
            handler=self.handle_verify_api_key,
        )
        self.add_tool(verify_api_key_tool)
        
        list_api_keys_tool = create_tool(
            name="list_api_keys",
            description="List API keys for a user",
            schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID"}
                },
                "required": ["user_id"]
            },
            handler=self.handle_list_api_keys,
        )
        self.add_tool(list_api_keys_tool)
        
        revoke_api_key_tool = create_tool(
            name="revoke_api_key",
            description="Revoke an API key",
            schema={
                "type": "object",
                "properties": {
                    "key_id": {"type": "integer", "description": "API key ID"},
                    "user_id": {"type": "integer", "description": "User ID"}
                },
                "required": ["key_id", "user_id"]
            },
            handler=self.handle_revoke_api_key,
        )
        self.add_tool(revoke_api_key_tool)
        
        # User management tools
        get_user_tool = create_tool(
            name="get_user",
            description="Get user information",
            schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID"}
                },
                "required": ["user_id"]
            },
            handler=self.handle_get_user,
        )
        self.add_tool(get_user_tool)
        
        update_user_tool = create_tool(
            name="update_user",
            description="Update user information",
            schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID"},
                    "full_name": {"type": "string", "description": "Full name"},
                    "role": {"type": "string", "enum": ["admin", "manager", "technician", "viewer", "guest"], "description": "User role"},
                    "is_active": {"type": "boolean", "description": "Active status"},
                    "preferences": {"type": "object", "description": "User preferences"}
                },
                "required": ["user_id"]
            },
            handler=self.handle_update_user,
        )
        self.add_tool(update_user_tool)
        
        list_users_tool = create_tool(
            name="list_users",
            description="List all users with pagination",
            schema={
                "type": "object",
                "properties": {
                    "skip": {"type": "integer", "description": "Number of users to skip", "default": 0},
                    "limit": {"type": "integer", "description": "Maximum number of users to return", "default": 100}
                }
            },
            handler=self.handle_list_users,
        )
        self.add_tool(list_users_tool)
        
        # Session management tools
        list_sessions_tool = create_tool(
            name="list_sessions",
            description="List active sessions for a user",
            schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID"}
                },
                "required": ["user_id"]
            },
            handler=self.handle_list_sessions,
        )
        self.add_tool(list_sessions_tool)
        
        invalidate_session_tool = create_tool(
            name="invalidate_session",
            description="Invalidate a specific session",
            schema={
                "type": "object",
                "properties": {
                    "session_token": {"type": "string", "description": "Session token"}
                },
                "required": ["session_token"]
            },
            handler=self.handle_invalidate_session,
        )
        self.add_tool(invalidate_session_tool)
    
    # Handler methods
    async def handle_create_user(self, username: str, email: str, password: str, full_name: str = None, role: str = "viewer") -> Dict[str, Any]:
        """Handle user creation"""
        try:
            db = self.db_service.get_db_session()
            
            # Check if user already exists
            existing_user = self.db_service.get_user_by_username(db, username)
            if existing_user:
                db.close()
                return {"error": "Username already exists"}
            
            existing_email = self.db_service.get_user_by_email(db, email)
            if existing_email:
                db.close()
                return {"error": "Email already exists"}
            
            # Create user
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role
            }
            
            user = self.db_service.create_user(db, user_data)
            db.close()
            
            if user:
                return {
                    "message": "User created successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "created_at": user.created_at.isoformat()
                    }
                }
            else:
                return {"error": "Failed to create user"}
                
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return {"error": str(e)}
    
    async def handle_login(self, username: str, password: str) -> Dict[str, Any]:
        """Handle user login"""
        try:
            db = self.db_service.get_db_session()
            
            # Authenticate user
            user = self.db_service.authenticate_user(db, username, password)
            if not user:
                db.close()
                return {"error": "Invalid credentials"}
            
            # Create session
            session = self.db_service.create_session(db, user.id)
            db.close()
            
            if session:
                return {
                    "message": "Login successful",
                    "access_token": session.session_token,
                    "refresh_token": session.refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.jwt_auth.access_token_expire_minutes * 60,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role
                    }
                }
            else:
                return {"error": "Failed to create session"}
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"error": str(e)}
    
    async def handle_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Handle token refresh"""
        try:
            db = self.db_service.get_db_session()
            
            new_token = self.db_service.refresh_session(db, refresh_token)
            db.close()
            
            if new_token:
                return {
                    "message": "Token refreshed successfully",
                    **new_token
                }
            else:
                return {"error": "Invalid or expired refresh token"}
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return {"error": str(e)}
    
    async def handle_logout(self, access_token: str) -> Dict[str, Any]:
        """Handle user logout"""
        try:
            db = self.db_service.get_db_session()
            
            success = self.db_service.invalidate_session(db, access_token)
            db.close()
            
            if success:
                return {"message": "Logout successful"}
            else:
                return {"error": "Session not found"}
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return {"error": str(e)}
    
    async def handle_verify_token(self, token: str) -> Dict[str, Any]:
        """Handle token verification"""
        try:
            payload = self.jwt_auth.verify_token(token)
            if payload:
                return {
                    "valid": True,
                    "payload": payload
                }
            else:
                return {"valid": False, "error": "Invalid token"}
                
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return {"valid": False, "error": str(e)}
    
    async def handle_check_permission(self, token: str, permission: str) -> Dict[str, Any]:
        """Handle permission check"""
        try:
            has_permission = self.jwt_auth.has_permission(token, permission)
            user_info = self.jwt_auth.extract_user_info(token) if has_permission else None
            
            return {
                "has_permission": has_permission,
                "user_info": user_info
            }
                
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return {"has_permission": False, "error": str(e)}
    
    async def handle_create_api_key(self, user_id: int, key_name: str, permissions: List[str] = None, expires_in_days: int = None) -> Dict[str, Any]:
        """Handle API key creation"""
        try:
            db = self.db_service.get_db_session()
            
            # Check if user exists
            user = self.db_service.get_user_by_id(db, user_id)
            if not user:
                db.close()
                return {"error": "User not found"}
            
            # Create API key
            api_key_data = self.db_service.create_api_key(db, user_id, key_name, permissions or [], expires_in_days)
            db.close()
            
            if api_key_data:
                return {
                    "message": "API key created successfully",
                    "api_key_data": api_key_data
                }
            else:
                return {"error": "Failed to create API key"}
                
        except Exception as e:
            logger.error(f"API key creation error: {e}")
            return {"error": str(e)}
    
    async def handle_verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Handle API key verification"""
        try:
            db = self.db_service.get_db_session()
            
            user = self.db_service.verify_api_key(db, api_key)
            db.close()
            
            if user:
                permissions = self.db_service.get_user_permissions(user)
                return {
                    "valid": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "permissions": permissions
                    }
                }
            else:
                return {"valid": False, "error": "Invalid API key"}
                
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return {"valid": False, "error": str(e)}
    
    async def handle_list_api_keys(self, user_id: int) -> Dict[str, Any]:
        """Handle API key listing"""
        try:
            db = self.db_service.get_db_session()
            
            api_keys = self.db_service.list_api_keys(db, user_id)
            db.close()
            
            return {
                "api_keys": [
                    {
                        "id": key.id,
                        "key_name": key.key_name,
                        "key_prefix": key.key_prefix,
                        "permissions": key.permissions,
                        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                        "created_at": key.created_at.isoformat(),
                        "last_used": key.last_used.isoformat() if key.last_used else None,
                        "is_active": key.is_active
                    }
                    for key in api_keys
                ]
            }
                
        except Exception as e:
            logger.error(f"API key listing error: {e}")
            return {"error": str(e)}
    
    async def handle_revoke_api_key(self, key_id: int, user_id: int) -> Dict[str, Any]:
        """Handle API key revocation"""
        try:
            db = self.db_service.get_db_session()
            
            success = self.db_service.revoke_api_key(db, key_id, user_id)
            db.close()
            
            if success:
                return {"message": "API key revoked successfully"}
            else:
                return {"error": "API key not found"}
                
        except Exception as e:
            logger.error(f"API key revocation error: {e}")
            return {"error": str(e)}
    
    async def handle_get_user(self, user_id: int) -> Dict[str, Any]:
        """Handle get user"""
        try:
            db = self.db_service.get_db_session()
            
            user = self.db_service.get_user_by_id(db, user_id)
            db.close()
            
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "created_at": user.created_at.isoformat(),
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "preferences": user.preferences
                    }
                }
            else:
                return {"error": "User not found"}
                
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return {"error": str(e)}
    
    async def handle_update_user(self, user_id: int, full_name: str = None, role: str = None, is_active: bool = None, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle user update"""
        try:
            db = self.db_service.get_db_session()
            
            update_data = {}
            if full_name is not None:
                update_data["full_name"] = full_name
            if role is not None:
                update_data["role"] = role
            if is_active is not None:
                update_data["is_active"] = is_active
            if preferences is not None:
                update_data["preferences"] = preferences
            
            user = self.db_service.update_user(db, user_id, update_data)
            db.close()
            
            if user:
                return {
                    "message": "User updated successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "is_active": user.is_active,
                        "preferences": user.preferences
                    }
                }
            else:
                return {"error": "User not found"}
                
        except Exception as e:
            logger.error(f"User update error: {e}")
            return {"error": str(e)}
    
    async def handle_list_users(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Handle list users"""
        try:
            db = self.db_service.get_db_session()
            
            users = self.db_service.list_users(db, skip, limit)
            db.close()
            
            return {
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat(),
                        "last_login": user.last_login.isoformat() if user.last_login else None
                    }
                    for user in users
                ],
                "total": len(users)
            }
                
        except Exception as e:
            logger.error(f"List users error: {e}")
            return {"error": str(e)}
    
    async def handle_list_sessions(self, user_id: int) -> Dict[str, Any]:
        """Handle list sessions"""
        try:
            db = self.db_service.get_db_session()
            
            # Get user sessions
            sessions = db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            ).all()
            db.close()
            
            return {
                "sessions": [
                    {
                        "id": session.id,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "ip_address": session.ip_address,
                        "user_agent": session.user_agent,
                        "expires_at": session.expires_at.isoformat()
                    }
                    for session in sessions
                ]
            }
                
        except Exception as e:
            logger.error(f"List sessions error: {e}")
            return {"error": str(e)}
    
    async def handle_invalidate_session(self, session_token: str) -> Dict[str, Any]:
        """Handle session invalidation"""
        try:
            db = self.db_service.get_db_session()
            
            success = self.db_service.invalidate_session(db, session_token)
            db.close()
            
            if success:
                return {"message": "Session invalidated successfully"}
            else:
                return {"error": "Session not found"}
                
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point for authentication server"""
    logger.info("Starting AI Authentication MCP Server")
    
    # Create authentication server
    auth_server = AuthMCPServer()
    
    # Start server
    await auth_server.start()


if __name__ == "__main__":
    asyncio.run(main())
