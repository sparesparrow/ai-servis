"""
Database service for authentication and authorization
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from auth_models import Base, User, UserSession, APIKey, UserRole, Permission, ROLE_PERMISSIONS
from jwt_auth import JWTAuthService, APIKeyAuthService

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for authentication operations"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.jwt_auth = JWTAuthService()
        self.api_key_auth = APIKeyAuthService()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def get_db_session(self) -> Session:
        """Get database session (non-generator)"""
        return self.SessionLocal()
    
    # User Management
    def create_user(self, db: Session, user_data: Dict[str, Any]) -> Optional[User]:
        """Create a new user"""
        try:
            # Hash password
            hashed_password = self.jwt_auth.get_password_hash(user_data["password"])
            
            # Create user
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                full_name=user_data.get("full_name"),
                role=user_data.get("role", UserRole.VIEWER.value),
                preferences=user_data.get("preferences", {})
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"User created: {user.username}")
            return user
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"User creation failed - integrity error: {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"User creation failed: {e}")
            return None
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def update_user(self, db: Session, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user information"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info(f"User updated: {user.username}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"User update failed: {e}")
            return None
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            db.delete(user)
            db.commit()
            
            logger.info(f"User deleted: {user.username}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"User deletion failed: {e}")
            return False
    
    def list_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        try:
            return db.query(User).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        try:
            user = self.get_user_by_username(db, username)
            if not user:
                return None
            
            if not user.is_active:
                logger.warning(f"Authentication failed - user inactive: {username}")
                return None
            
            if not self.jwt_auth.verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed - invalid password: {username}")
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            logger.info(f"User authenticated: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    # Session Management
    def create_session(self, db: Session, user_id: int, ip_address: str = None, user_agent: str = None) -> Optional[UserSession]:
        """Create a new user session"""
        try:
            # Generate session tokens
            user = self.get_user_by_id(db, user_id)
            if not user:
                return None
            
            permissions = ROLE_PERMISSIONS.get(UserRole(user.role), [])
            token_data = {
                "sub": str(user_id),
                "username": user.username,
                "role": user.role,
                "permissions": [p.value for p in permissions]
            }
            
            token_pair = self.jwt_auth.create_token_pair(
                user_id, user.username, user.role, [p.value for p in permissions]
            )
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(days=self.jwt_auth.refresh_token_expire_days)
            
            # Create session
            session = UserSession(
                user_id=user_id,
                session_token=token_pair["access_token"],
                refresh_token=token_pair["refresh_token"],
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Session created for user: {user.username}")
            return session
            
        except Exception as e:
            db.rollback()
            logger.error(f"Session creation failed: {e}")
            return None
    
    def get_session(self, db: Session, session_token: str) -> Optional[UserSession]:
        """Get session by token"""
        try:
            return db.query(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def refresh_session(self, db: Session, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh a session"""
        try:
            session = db.query(UserSession).filter(
                and_(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not session:
                return None
            
            # Create new access token
            new_token = self.jwt_auth.refresh_access_token(refresh_token)
            if not new_token:
                return None
            
            # Update session
            session.session_token = new_token["access_token"]
            session.last_activity = datetime.utcnow()
            db.commit()
            
            return new_token
            
        except Exception as e:
            db.rollback()
            logger.error(f"Session refresh failed: {e}")
            return None
    
    def invalidate_session(self, db: Session, session_token: str) -> bool:
        """Invalidate a session"""
        try:
            session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
            if not session:
                return False
            
            session.is_active = False
            db.commit()
            
            logger.info(f"Session invalidated: {session_token[:8]}...")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Session invalidation failed: {e}")
            return False
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions"""
        try:
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_sessions)
            for session in expired_sessions:
                db.delete(session)
            
            db.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Session cleanup failed: {e}")
            return 0
    
    # API Key Management
    def create_api_key(self, db: Session, user_id: int, key_name: str, permissions: List[str], expires_in_days: int = None) -> Optional[Dict[str, Any]]:
        """Create a new API key"""
        try:
            # Generate API key
            api_key = self.api_key_auth.generate_api_key()
            key_hash = self.api_key_auth.hash_api_key(api_key)
            key_prefix = self.api_key_auth.extract_key_prefix(api_key)
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create API key record
            api_key_record = APIKey(
                user_id=user_id,
                key_name=key_name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                permissions=permissions,
                expires_at=expires_at
            )
            
            db.add(api_key_record)
            db.commit()
            db.refresh(api_key_record)
            
            logger.info(f"API key created: {key_name}")
            
            return {
                "id": api_key_record.id,
                "key_name": api_key_record.key_name,
                "api_key": api_key,  # Only returned once
                "key_prefix": api_key_record.key_prefix,
                "permissions": api_key_record.permissions,
                "expires_at": api_key_record.expires_at,
                "created_at": api_key_record.created_at
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"API key creation failed: {e}")
            return None
    
    def verify_api_key(self, db: Session, api_key: str) -> Optional[User]:
        """Verify an API key and return the associated user"""
        try:
            key_prefix = self.api_key_auth.extract_key_prefix(api_key)
            
            # Find API key by prefix
            api_key_record = db.query(APIKey).filter(
                and_(
                    APIKey.key_prefix == key_prefix,
                    APIKey.is_active == True,
                    or_(
                        APIKey.expires_at.is_(None),
                        APIKey.expires_at > datetime.utcnow()
                    )
                )
            ).first()
            
            if not api_key_record:
                return None
            
            # Verify the full key
            if not self.api_key_auth.verify_api_key(api_key, api_key_record.key_hash):
                return None
            
            # Update last used
            api_key_record.last_used = datetime.utcnow()
            db.commit()
            
            # Get user
            user = self.get_user_by_id(db, api_key_record.user_id)
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return None
    
    def list_api_keys(self, db: Session, user_id: int) -> List[APIKey]:
        """List API keys for a user"""
        try:
            return db.query(APIKey).filter(APIKey.user_id == user_id).all()
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
    
    def revoke_api_key(self, db: Session, key_id: int, user_id: int) -> bool:
        """Revoke an API key"""
        try:
            api_key = db.query(APIKey).filter(
                and_(APIKey.id == key_id, APIKey.user_id == user_id)
            ).first()
            
            if not api_key:
                return False
            
            api_key.is_active = False
            db.commit()
            
            logger.info(f"API key revoked: {api_key.key_name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"API key revocation failed: {e}")
            return False
    
    def get_user_permissions(self, user: User) -> List[str]:
        """Get user permissions based on role"""
        role_permissions = ROLE_PERMISSIONS.get(UserRole(user.role), [])
        return [p.value for p in role_permissions]
