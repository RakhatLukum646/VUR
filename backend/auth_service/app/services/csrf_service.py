import secrets

from fastapi import HTTPException, Request, status

CSRF_COOKIE_NAME = "vur_csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def validate_csrf(request: Request) -> None:
    """
    Double-submit cookie validation.
    The X-CSRF-Token header value must be present and match the vur_csrf_token cookie.
    Raises HTTP 403 on failure.
    """
    header_token = request.headers.get(CSRF_HEADER_NAME)
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

    if not header_token or not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing.",
        )

    if not secrets.compare_digest(header_token, cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch.",
        )
