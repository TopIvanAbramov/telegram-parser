"""Telethon client wrapper for parsing Telegram posts."""

import re
import logging
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    FloodWaitError,
    UserIsBlockedError,
    ChannelPrivateError,
    MsgIdInvalidError,
    MessageNotModifiedError,
    UnauthorizedError
)
from telethon import functions, types
from io import BytesIO

logger = logging.getLogger(__name__)


class TelegramParserClient:
    """Singleton client for parsing Telegram posts."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelegramParserClient, cls).__new__(cls)
        return cls._instance
    
    def initialize(self, api_id: str, api_hash: str, session_path: str = "/app/data/telegram_session"):
        """Initialize the Telegram client."""
        if self._client is None:
            self._client = TelegramClient(session_path, api_id, api_hash)
            logger.info("Telegram client initialized")
    
    async def connect(self):
        """Connect to Telegram."""
        if self._client and not self._client.is_connected():
            await self._client.connect()
            logger.info("Connected to Telegram")
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            logger.info("Disconnected from Telegram")
    
    async def get_channel_id_by_username(self, channel_username: str) -> int:
        """Get numeric channel_id from channel username."""
        await self.connect()
        channel = await self._client.get_entity(channel_username)
        return channel.id
    
    async def get_comments_count(self, channel_id: int, message_id: int) -> int:
        """Get total comments count for a message given channel_id and message_id.
        Returns 0 if unavailable or fails."""
        try:
            await self.connect()
            channel = await self._client.get_entity(channel_id)
            result = await self._client(functions.messages.GetRepliesRequest(
                peer=channel,
                msg_id=message_id,
                offset_id=0,
                offset_date=0,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            return result.count if result else 0
        except Exception as e:
            logger.warning(f"Failed to get comments count: {e}")
            return 0
    
    async def get_reposts_count(self, channel_id: int, message_id: int) -> int:
        """Get total reposts count for a message given channel_id and message_id.
        Returns 0 if unavailable or fails."""
        try:
            await self.connect()
            channel = await self._client.get_entity(channel_id)
            result = await self._client(functions.stats.GetMessagePublicForwardsRequest(
                channel=channel,
                msg_id=message_id,
                offset='',
                limit=100
            ))
            return result.count if result else 0
        except Exception as e:
            logger.warning(f"Failed to get reposts count: {e}")
            return 0

    async def get_channel_subscribers_safe(self, channel_id: int) -> int | None:
        """Try to fetch channel subscribers count. Returns None if unavailable."""
        try:
            await self.connect()
            channel = await self._client.get_entity(channel_id)
            # Get full channel info
            full = await self._client(functions.channels.GetFullChannelRequest(channel))
            # participants_count may be under full.full_chat.participants_count
            count = getattr(getattr(full, 'full_chat', None), 'participants_count', None)
            return int(count) if count is not None else None
        except Exception as e:
            logger.warning(f"Failed to get channel subscribers: {e}")
            return None

    async def get_post_photo_bytes(self, channel_id: int, message_id: int) -> bytes | None:
        """Download the best available photo from a post, return bytes or None."""
        try:
            await self.connect()
            messages = await self._client.get_messages(channel_id, ids=[message_id])
            if not messages or messages[0] is None:
                return None
            message = messages[0]
            if not getattr(message, 'photo', None):
                return None
            bio = BytesIO()
            await self._client.download_media(message.photo, file=bio)
            return bio.getvalue()
        except Exception as e:
            logger.warning(f"Failed to download post photo: {e}")
            return None
    
    @staticmethod
    def parse_post_url(url: str) -> tuple[str, int]:
        """
        Parse Telegram post URL to extract channel username and message ID.
        
        Args:
            url: Telegram post URL (e.g., https://t.me/ivan_talknow/99)
        
        Returns:
            Tuple of (channel_username, message_id)
        
        Raises:
            ValueError: If URL format is invalid
        """
        # Match pattern: https://t.me/channelname/123
        pattern = r'https://t\.me/([a-zA-Z0-9_]+)/(\d+)'
        match = re.match(pattern, url)
        
        if not match:
            raise ValueError(f"Invalid Telegram URL format: {url}")
        
        channel = match.group(1)
        message_id = int(match.group(2))
        
        return channel, message_id
    
    async def parse_post(self, url: str) -> dict:
        """
        Parse a Telegram post and extract statistics.
        
        Args:
            url: Telegram post URL
        
        Returns:
            Dictionary with post statistics
        
        Raises:
            Various Telethon exceptions with error codes
        """
        # Parse URL
        try:
            channel, message_id = self.parse_post_url(url)
        except ValueError as e:
            logger.error(f"Invalid URL: {url}")
            raise ValueError(str(e))
        
        # Ensure client is connected
        await self.connect()
        
        try:
            # Get channel_id from username
            channel_id = await self.get_channel_id_by_username(channel)
            
            # Get the message/post using channel_id and message_id
            messages = await self._client.get_messages(channel_id, ids=[message_id])
            
            if not messages or messages[0] is None:
                logger.error(f"Post not found: {url}")
                raise ValueError(f"Post not found: {url}")
            
            message = messages[0]
            
            # Get channel entity for channel info
            channel_entity = await self._client.get_entity(channel_id)
            
            # Extract statistics
            views = message.views or 0
            
            # Get comments count (defaults to 0 if fails)
            comments = await self.get_comments_count(channel_id, message_id)
            
            # Get reposts count (defaults to 0 if fails)
            reposts = await self.get_reposts_count(channel_id, message_id)
            
            # Get channel information
            channel_name = getattr(channel_entity, 'title', None) or getattr(channel_entity, 'first_name', None) or channel
            channel_username = getattr(channel_entity, 'username', None) or channel
            channel_thumbnail = None
            if hasattr(channel_entity, 'photo') and channel_entity.photo:
                # Get photo file location if available
                if hasattr(channel_entity.photo, 'photo_id'):
                    channel_thumbnail = f"https://t.me/i/userpic/320/{channel_username}.jpg"

            # Get channel subscribers if possible
            channel_subscribers = await self.get_channel_subscribers_safe(channel_id)

            # Check if post has photo
            post_photo_available = bool(getattr(message, 'photo', None))
            post_photo_id = None
            if post_photo_available and isinstance(message.photo, types.Photo):
                post_photo_id = str(getattr(message.photo, 'id', ''))
            
            # Prepare result
            result = {
                "success": True,
                "channel": channel_username,
                "channel_id": channel_id,
                "channel_username": channel_username,
                "channel_name": channel_name,
                "channel_thumbnail": channel_thumbnail,
                "channel_subscribers": channel_subscribers,
                "message_id": message_id,
                "views": views,
                "comments": comments,
                "reposts": reposts,
                "message_date": message.date.isoformat() if message.date else None,
                "post_photo_available": post_photo_available,
                "post_photo_id": post_photo_id,
            }
            
            logger.info(f"Successfully parsed post: {channel_username}/{message_id} (channel_id: {channel_id})")
            return result
            
        except MsgIdInvalidError:
            logger.error(f"Invalid message ID for channel {channel}")
            raise ValueError(f"Invalid message ID for channel {channel}")
        except ChannelPrivateError:
            logger.error(f"Channel {channel} is private or inaccessible")
            raise ValueError(f"Channel {channel} is private or inaccessible")
        except UserIsBlockedError:
            logger.error(f"Channel {channel} has blocked this account")
            raise ValueError(f"Channel {channel} has blocked this account")
        except FloodWaitError as e:
            logger.warning(f"Rate limited. Try again in {e.seconds} seconds")
            raise ValueError(f"Rate limited. Try again in {e.seconds} seconds")
        except MessageNotModifiedError:
            logger.error("Message has not been modified")
            raise ValueError("Message has not been modified")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ValueError(f"Failed to parse post: {str(e)}")


# Global instance
telegram_parser = TelegramParserClient()

