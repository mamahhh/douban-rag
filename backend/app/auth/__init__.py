"""
Authentication module for Firebase-based auth.
"""

from .auth import (
    verify_token,
    get_current_user,
    User,
    AuthenticationError,
)

__all__ = [
    "verify_token",
    "get_current_user", 
    "User",
    "AuthenticationError",
]
