"""
JWT helper functions for authentication
"""
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    import secrets

import os
from datetime import datetime, timedelta, timezone

# Secret key for JWT signing (use environment variable in production)
# Lazy initialization to avoid issues during build
_SECRET_KEY = None

def _get_secret_key():
    """Get JWT secret key, initializing if necessary"""
    global _SECRET_KEY
    if _SECRET_KEY is None:
        _SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    return _SECRET_KEY

def generate_token(user_email='admin'):
    """Generate JWT token for authenticated user"""
    if not JWT_AVAILABLE:
        # Fallback if PyJWT is not available
        return secrets.token_hex(32)
    
    try:
        payload = {
            'email': user_email,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),  # Token expires in 24 hours
            'iat': datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, _get_secret_key(), algorithm='HS256')
        # PyJWT 2.x returns string, but check if it's bytes
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    except Exception as e:
        # Fallback on error
        import secrets
        return secrets.token_hex(32)

def verify_token(token):
    """Verify JWT token and return payload if valid"""
    if not JWT_AVAILABLE:
        return None
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
    except Exception:
        return None  # Any other error

