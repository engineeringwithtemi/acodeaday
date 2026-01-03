"""Supabase JWT token authentication middleware."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate Supabase JWT token and return user information.

    The Supabase client is accessed from app.state (initialized in lifespan).

    Args:
        request: FastAPI request object (provides access to app.state.supabase)
        credentials: Bearer token from Authorization header

    Returns:
        User dict with id, email, etc.

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials
    supabase = request.app.state.supabase

    try:
        response = await supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("auth_validation_failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
