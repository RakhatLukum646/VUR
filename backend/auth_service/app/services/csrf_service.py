import secrets

from fastapi import HTTPException, Request, status

CSRF_COOKIE_NAME = "vur_csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


async def validate_csrf(request: Request) -> None:
    """
    CSRF validation. Requires the X-CSRF-Token custom header to be present.
    When the cookie is also present (desktop browsers), the header must match it.
    When the cookie is absent (mobile browsers blocking third-party cookies),
    the presence of the custom header is sufficient — cross-origin requests
    requiring custom headers are already blocked by CORS preflight.
    """
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing.",
        )

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if cookie_token and not secrets.compare_digest(header_token, cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch.",
        )
