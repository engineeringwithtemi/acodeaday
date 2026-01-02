"""Supabase JWT token authentication middleware."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from supabase import Client, create_client

from app.config.settings import settings

# HTTP Bearer token security scheme
security = HTTPBearer()

# Initialize Supabase client (for auth validation)
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate Supabase JWT token and return user information.

    How it works:
    1. Frontend authenticates with Supabase Auth (email/password, OAuth, etc.)
    2. Supabase returns a JWT token
    3. Frontend includes token in Authorization header: "Bearer <token>"
    4. This function validates the token using Supabase client
    5. Returns user info (user_id, email, etc.) if valid

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        User dict with id, email, etc.

    Raises:
        HTTPException: 401 if token is invalid or expired

    Usage:
        @router.get("/api/endpoint")
        async def endpoint(user: dict = Depends(get_current_user)):
            user_id = user["id"]
            user_email = user["email"]
    """
    token = credentials.credentials

    try:
        # Validate token using Supabase
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return user information
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
