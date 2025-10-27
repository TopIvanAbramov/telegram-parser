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
            # Get the message/post
            messages = await self._client.get_messages(channel, ids=[message_id])
            
            if not messages or messages[0] is None:
                logger.error(f"Post not found: {url}")
                raise ValueError(f"Post not found: {url}")
            
            message = messages[0]
            
            # Extract statistics
            views = message.views or 0
            
            # Get reactions
            reactions = {}
            total_reactions = 0
            
            if message.reactions:
                for reaction in message.reactions.results:
                    if hasattr(reaction, 'count') and reaction.count > 0:
                        emoji = str(reaction.reaction) if hasattr(reaction, 'reaction') else 'unknown'
                        reactions[emoji] = reaction.count
                        total_reactions += reaction.count
            
            # Prepare result
            result = {
                "success": True,
                "channel": channel,
                "message_id": message_id,
                "views": views,
                "reactions": reactions,
                "total_reactions": total_reactions,
                "message_date": message.date.isoformat() if message.date else None,
                "has_reactions": len(reactions) > 0
            }
            
            logger.info(f"Successfully parsed post: {channel}/{message_id}")
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

