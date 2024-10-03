import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import Depends, Request, HTTPException, status

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        
        if not session_id:
            session_id = str(uuid.uuid4())

        response = await call_next(request)

        if "session_id" not in request.cookies:
            response.set_cookie(
            key="session_id", 
            value=session_id, 
            httponly=True, 
            samesite="Lax",
            secure=False,
)
        return response
    

def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID not found"
        )
    return session_id