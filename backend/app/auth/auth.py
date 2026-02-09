"""
Firebase Authentication utilities for the Douban RAG system.
"""

import os
from typing import Optional
from dataclasses import dataclass
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
_firebase_app = None


def get_firebase_app():
    """Initialize Firebase Admin SDK if not already done."""
    global _firebase_app
    if _firebase_app is None:
        # Check for service account file first
        service_account_path = os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS",
            "firebase-service-account.json"
        )
        
        # Also check in project root (one level up from backend)
        project_root_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "firebase-service-account.json"
        )
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        elif os.path.exists(project_root_path):
            cred = credentials.Certificate(project_root_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            # Use project ID from environment (for environments without service account)
            project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            if project_id:
                options = {"projectId": project_id}
                _firebase_app = firebase_admin.initialize_app(options=options)
            else:
                # Last resort: try default credentials (works on Google Cloud)
                _firebase_app = firebase_admin.initialize_app()
    
    return _firebase_app


# Initialize on module load
get_firebase_app()


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


@dataclass
class User:
    """Authenticated user model."""
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    email_verified: bool = False
    
    @classmethod
    def from_firebase_token(cls, decoded_token: dict) -> "User":
        """Create User from decoded Firebase token."""
        return cls(
            uid=decoded_token["uid"],
            email=decoded_token.get("email"),
            display_name=decoded_token.get("name"),
            email_verified=decoded_token.get("email_verified", False),
        )


# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


def verify_token(token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded token.
    
    Args:
        token: Firebase ID token string
        
    Returns:
        Decoded token dictionary with user info
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise AuthenticationError("Invalid authentication token")
    except auth.ExpiredIdTokenError:
        raise AuthenticationError("Authentication token has expired")
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Use this as a dependency in route handlers:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.uid}
    
    Raises:
        HTTPException: 401 if no token provided or token is invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        decoded_token = verify_token(credentials.credentials)
        return User.from_firebase_token(decoded_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current user.
    Returns None if no token is provided, raises error if token is invalid.
    """
    if credentials is None:
        return None
    
    try:
        decoded_token = verify_token(credentials.credentials)
        return User.from_firebase_token(decoded_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
