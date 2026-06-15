"""JWT authentication and password hashing utilities.

Uses python-jose for JWT creation/validation and SHA-256
with salt for password hashing (bcrypt not used due to
compatibility issues with Windows Python builds).
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# --- Configuration ---
SECRET_KEY = "super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a random salt.

    Format returned: ``salt:hexdigest``

    Args:
        password: Plain-text password.

    Returns:
        Salted password hash string.
    """
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a salted hash.

    Args:
        plain_password: Password to check.
        hashed_password: Previously generated hash (salt:hexdigest).

    Returns:
        True if the password matches, False otherwise.
    """
    salt, expected = hashed_password.split(":", 1)
    h = hashlib.sha256(f"{salt}:{plain_password}".encode()).hexdigest()
    return h == expected


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Claims to encode (must include 'sub' for username).
        expires_delta: Token lifetime (defaults to ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string.

    Returns:
        Decoded payload dict.

    Raises:
        HTTPException 401: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    """FastAPI dependency that extracts and validates the current user.

    Expects a Bearer token in the Authorization header.

    Args:
        credentials: Extracted Bearer credentials.

    Returns:
        Username string from the token's 'sub' claim.
    """
    payload = decode_token(credentials.credentials)
    username: str = payload.get("sub", "")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no contiene usuario",
        )
    return username
