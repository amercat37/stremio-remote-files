from fastapi import APIRouter, Request, Response, status

from core.auth import valid_stream_token

router = APIRouter()


@router.get("/auth")
def auth(request: Request):
    """
    Authorization endpoint used by Caddy forward_auth.

    Returns:
    - 204 No Content if token is valid
    - 401 Unauthorized if token is missing or invalid
    """

    result = valid_stream_token(request)

    if result:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return Response(status_code=status.HTTP_401_UNAUTHORIZED)
