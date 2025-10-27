"""Middleware for IP allowlist and logging."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access to allowed IPs only."""
    
    def __init__(self, app, allowed_ips: list[str]):
        super().__init__(app)
        self.allowed_ips = allowed_ips
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        
        # Log all requests
        logger.info(f"Request from {client_ip}: {request.method} {request.url.path}")
        
        # Check if IP is in allowlist (allow all if list is empty)
        if self.allowed_ips and client_ip not in self.allowed_ips:
            logger.warning(f"Access denied for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "error": "Access denied",
                    "error_code": "FORBIDDEN"
                }
            )
        
        response = await call_next(request)
        return response

