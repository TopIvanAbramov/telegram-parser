"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel


class PostParseResponse(BaseModel):
    """Response model for parsed Telegram post data."""
    
    success: bool = True
    channel: str
    channel_id: int
    channel_username: str
    channel_name: Optional[str] = None
    channel_thumbnail: Optional[str] = None
    channel_subscribers: Optional[int] = None
    message_id: int
    views: int
    reactions: Dict[str, int] = {}
    total_reactions: int = 0
    comments: int = 0
    reposts: int = 0
    message_date: Optional[str] = None
    has_reactions: bool = False
    post_photo_available: bool = False
    post_photo_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = False
    error: str
    error_code: str

