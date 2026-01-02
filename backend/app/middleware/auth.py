"""HTTP Basic Authentication middleware."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config.settings import settings

security = HTTPBasic()


async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Validate HTTP Basic Auth credentials and return username.

    Compares provided credentials against settings.auth_username and settings.auth_password.
    Returns username if valid, raises 401 if invalid.

    Args:
        credentials: HTTP Basic Auth credentials from request

    Returns:
        Username (user_id) if authentication succeeds

    Raises:
        HTTPException: 401 if credentials are invalid

    Usage:
        @router.get("/api/endpoint")
        async def endpoint(user_id: str = Depends(get_current_user)):
            # user_id is the authenticated username
            pass
    """
    is_valid_username = credentials.username == settings.auth_username
    is_valid_password = credentials.password == settings.auth_password

    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username  # Return username as user_id
