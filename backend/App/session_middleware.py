from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

class SessionMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Check for session_id in cookies, but don't create one
        session_id = request.cookies.get("session_id")

        # Proceed with the request
        response = await call_next(request)

        # No need to set the cookie again if it's already in the request
        return response


def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID not found"
        )
    return session_id
