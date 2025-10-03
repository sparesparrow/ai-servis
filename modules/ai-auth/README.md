# AI Authentication & Authorization Module

This module provides comprehensive authentication and authorization services for the AI-SERVIS system using JWT tokens, API keys, and role-based access control (RBAC).

## Features

### 🔐 Authentication
- **JWT-based Authentication**: Secure token-based authentication with access and refresh tokens
- **API Key Authentication**: Long-lived API keys for service-to-service communication
- **Session Management**: Active session tracking and management
- **Password Security**: Bcrypt password hashing with salt

### 👥 User Management
- **User Registration**: Create new user accounts with validation
- **User Profiles**: Manage user information and preferences
- **Account Status**: Enable/disable user accounts
- **User Listing**: Paginated user management

### 🛡️ Authorization
- **Role-Based Access Control (RBAC)**: Five predefined roles with different permission levels
- **Permission System**: Granular permissions for different system operations
- **Token Verification**: Real-time token validation and permission checking
- **API Key Permissions**: Scoped permissions for API keys

### 🔑 API Key Management
- **Key Generation**: Secure API key generation with prefixes
- **Key Lifecycle**: Create, list, revoke API keys
- **Expiration Support**: Optional expiration dates for API keys
- **Usage Tracking**: Track API key usage and last access

## User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | Full system access | All permissions |
| **Manager** | Management access | User management, service management, monitoring |
| **Technician** | Technical access | Service management, API access |
| **Viewer** | Read-only access | Service viewing, basic API access |
| **Guest** | Limited access | Basic API read access |

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `POST /auth/verify` - Verify token

### User Management
- `POST /users` - Create user
- `GET /users/{id}` - Get user
- `PUT /users/{id}` - Update user
- `GET /users` - List users

### API Key Management
- `POST /api-keys` - Create API key
- `GET /api-keys` - List API keys
- `DELETE /api-keys/{id}` - Revoke API key
- `POST /api-keys/verify` - Verify API key

### Session Management
- `GET /sessions` - List active sessions
- `DELETE /sessions/{token}` - Invalidate session

## Configuration

### Environment Variables
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
DATABASE_URL=sqlite:///./ai_auth.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/ai_auth

# Security
BCRYPT_ROUNDS=12
```

### Database Setup
The module automatically creates the required database tables on startup. For production, use PostgreSQL:

```bash
# Install PostgreSQL dependencies
pip install psycopg2-binary

# Set database URL
export DATABASE_URL="postgresql://user:password@localhost/ai_auth"
```

## Usage Examples

### Creating a User
```python
from ai_auth import AuthMCPServer

auth_server = AuthMCPServer()

# Create admin user
result = await auth_server.handle_create_user(
    username="admin",
    email="admin@example.com",
    password="secure_password",
    full_name="System Administrator",
    role="admin"
)
```

### User Login
```python
# Login user
result = await auth_server.handle_login(
    username="admin",
    password="secure_password"
)

access_token = result["access_token"]
refresh_token = result["refresh_token"]
```

### Token Verification
```python
# Verify token
result = await auth_server.handle_verify_token(access_token)

if result["valid"]:
    user_info = result["payload"]
    print(f"User: {user_info['username']}")
    print(f"Role: {user_info['role']}")
```

### Permission Checking
```python
# Check permission
result = await auth_server.handle_check_permission(
    token=access_token,
    permission="user:create"
)

if result["has_permission"]:
    print("User can create other users")
```

### API Key Management
```python
# Create API key
result = await auth_server.handle_create_api_key(
    user_id=1,
    key_name="Service Integration",
    permissions=["service:read", "service:write"],
    expires_in_days=365
)

api_key = result["api_key_data"]["api_key"]
```

## Security Features

### Token Security
- **JWT Tokens**: Industry-standard JWT with HMAC-SHA256
- **Token Expiration**: Configurable expiration times
- **Refresh Tokens**: Secure token refresh mechanism
- **Token Invalidation**: Immediate session termination

### Password Security
- **Bcrypt Hashing**: Strong password hashing with salt
- **Configurable Rounds**: Adjustable bcrypt rounds for security
- **Password Validation**: Minimum length and complexity requirements

### API Key Security
- **Secure Generation**: Cryptographically secure random keys
- **Hashed Storage**: API keys hashed in database
- **Prefix Identification**: First 8 characters for identification
- **Usage Tracking**: Monitor API key usage

### Session Security
- **Session Tracking**: Monitor active sessions
- **IP Tracking**: Record IP addresses for sessions
- **User Agent Tracking**: Track client information
- **Automatic Cleanup**: Remove expired sessions

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    preferences JSON
);
```

### Sessions Table
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    permissions JSON,
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Testing

Run the authentication tests:

```bash
cd modules/ai-auth
python -m pytest tests/
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Production Considerations
1. **Use PostgreSQL** for production database
2. **Set strong JWT secret** with sufficient entropy
3. **Enable HTTPS** for all authentication endpoints
4. **Configure proper CORS** settings
5. **Set up monitoring** for authentication events
6. **Regular security audits** of user accounts and permissions

## Integration

This module integrates with:
- **Service Discovery**: Register auth service with service discovery
- **Core Orchestrator**: Provide authentication for orchestrator operations
- **API Gateway**: Secure all API endpoints
- **Monitoring**: Track authentication metrics and events

## License

This module is part of the AI-SERVIS project and follows the same licensing terms.
