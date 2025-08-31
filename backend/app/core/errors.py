from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        self.code, self.message, self.status, self.details = code, message, status, details or {}

class ErrorPayload(BaseModel):
    error: str
    code: str
    correlation_id: str | None = None
    details: dict = {}

class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AppError as e:
            cid = request.headers.get("x-correlation-id")
            body = ErrorPayload(error=e.message, code=e.code, correlation_id=cid, details=e.details)
            return JSONResponse(status_code=e.status, content=body.model_dump())
        except Exception:
            cid = request.headers.get("x-correlation-id")
            body = ErrorPayload(error="internal_error", code="INTERNAL_ERROR", correlation_id=cid, details={})
            return JSONResponse(status_code=500, content=body.model_dump())
