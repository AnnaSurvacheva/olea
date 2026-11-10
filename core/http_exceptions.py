"""Reusable HTTP exception factories."""

from fastapi import HTTPException, status


def unauthorized_credentials() -> HTTPException:
    """Create a 401 response for missing or invalid authentication."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )