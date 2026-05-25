from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError,
    DecodeError
)
from bson import ObjectId

from server.app.core.config import settings
from server.app.db.core.connection import (
    get_user_sessions_collection,
    get_users_collection,
)
from server.app.users.models import UserOut
from server.app.users.identity import ACTIVE_USER_STATUSES, coerce_user_status, now_utc
from server.app.users.repository import build_user_out_payload, get_active_session

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    users_collection=Depends(get_users_collection),
    sessions_collection=Depends(get_user_sessions_collection),
) -> UserOut:
    """
    Extract and validate the current user from a JWT token.
    Returns a UserOut object if successful.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        session_id: str | None = payload.get("sid")
        token_type: str = payload.get("type")

        if not user_id or not jti or not session_id or token_type != "access":
            raise credentials_exception

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (ExpiredSignatureError, InvalidTokenError, DecodeError): 
        raise credentials_exception

    # Fetch the user from DB
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    if user is None:
        raise credentials_exception
    if coerce_user_status(user) not in ACTIVE_USER_STATUSES:
        raise HTTPException(status_code=403, detail="Account is not active")

    session = await get_active_session(
        sessions_collection,
        session_id=session_id,
        user_id=user_id,
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Session has been revoked")

    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_seen_at": now_utc()}},
    )

    payload = build_user_out_payload(user)
    if isinstance(payload.get("created_at"), datetime):
        payload["created_at"] = payload["created_at"].isoformat()
    return UserOut(**payload)

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    users_collection=Depends(get_users_collection),
    sessions_collection=Depends(get_user_sessions_collection),
) -> UserOut | None:
    """
    Optional version of get_current_user. Returns None when no/invalid token is provided.
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        session_id: str | None = payload.get("sid")
        token_type: str = payload.get("type")

        if not user_id or not jti or not session_id or token_type != "access":
            return None

    except (ExpiredSignatureError, InvalidTokenError, DecodeError):
        return None

    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None

    if user is None:
        return None
    if coerce_user_status(user) not in ACTIVE_USER_STATUSES:
        return None

    session = await get_active_session(
        sessions_collection,
        session_id=session_id,
        user_id=user_id,
    )
    if session is None:
        return None

    payload = build_user_out_payload(user)
    if isinstance(payload.get("created_at"), datetime):
        payload["created_at"] = payload["created_at"].isoformat()

    return UserOut(**payload)


async def get_verified_user(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Ensure the current authenticated user has a verified email."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return current_user
