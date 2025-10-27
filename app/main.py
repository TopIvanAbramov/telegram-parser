"""FastAPI application for Telegram parser."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.telegram_client import telegram_parser
from app.models import PostParseResponse, ErrorResponse
from app.middleware import IPAllowlistMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup/shutdown)."""
    # Startup
    logger.info("Starting Telegram Parser API...")
    
    # Initialize Telegram client
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        logger.error("TELEGRAM_API_ID or TELEGRAM_API_HASH not set!")
        raise ValueError("Telegram API credentials not configured")
    
    telegram_parser.initialize(api_id, api_hash)
    await telegram_parser.connect()
    
    logger.info("Telegram Parser API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Telegram Parser API...")
    await telegram_parser.disconnect()
    logger.info("Telegram Parser API shut down")


# Create FastAPI app
app = FastAPI(
    title="Telegram Parser API",
    description="Parse Telegram channel posts to extract views and reactions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add IP allowlist middleware
allowed_ips = os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else []
if allowed_ips:
    logger.info(f"IP allowlist enabled: {allowed_ips}")
    app.add_middleware(IPAllowlistMiddleware, allowed_ips=allowed_ips)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "telegram-parser"}


@app.get("/parse/telegram/single")
async def parse_telegram_post(url: str = Query(..., description="Telegram post URL")):
    """
    Parse a Telegram channel post and return statistics.
    
    Args:
        url: Telegram post URL (e.g., https://t.me/ivan_talknow/99)
    
    Returns:
        PostParseResponse: Post statistics including views and reactions
    
    Raises:
        HTTPException: If parsing fails or URL is invalid
    """
    try:
        # Parse the post
        result = await telegram_parser.parse_post(url)
        
        # Return successful response
        return PostParseResponse(**result)
    
    except ValueError as e:
        # Determine error code based on error message
        error_message = str(e)
        
        if "Invalid Telegram URL format" in error_message:
            error_code = "INVALID_URL"
        elif "not found" in error_message.lower() or "Invalid message ID" in error_message:
            error_code = "POST_NOT_FOUND"
        elif "private" in error_message.lower() or "inaccessible" in error_message.lower():
            error_code = "CHANNEL_PRIVATE"
        elif "Rate limited" in error_message or "rate" in error_message.lower():
            error_code = "TELEGRAM_RATE_LIMIT"
        elif "blocked" in error_message.lower():
            error_code = "CHANNEL_BLOCKED"
        else:
            error_code = "INTERNAL_ERROR"
        
        # Return error response
        error_response = ErrorResponse(
            success=False,
            error=error_message,
            error_code=error_code
        )
        
        # Map error codes to HTTP status codes
        status_code_map = {
            "INVALID_URL": status.HTTP_400_BAD_REQUEST,
            "POST_NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "CHANNEL_PRIVATE": status.HTTP_403_FORBIDDEN,
            "TELEGRAM_RATE_LIMIT": status.HTTP_429_TOO_MANY_REQUESTS,
            "CHANNEL_BLOCKED": status.HTTP_403_FORBIDDEN,
            "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        status_code = status_code_map.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        raise HTTPException(status_code=status_code, detail=error_response.dict())
    
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        
        error_response = ErrorResponse(
            success=False,
            error="An unexpected error occurred",
            error_code="INTERNAL_ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )

