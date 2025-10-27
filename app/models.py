"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel


class PostParseResponse(BaseModel):
    """Response model for parsed Telegram post data."""
    
    success: bool = True
    channel: str
    message_id: int
    views: int
    reactions: Dict[str, int] = {}
    total_reactions: int = 0
    message_date: Optional[str] = None
    has_reactions: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = False
    error: str
    error_code: str

