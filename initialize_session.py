#!/usr/bin/env python3
"""
Initialize Telegram session by authenticating once.
This creates a session file that can be used by the API service.
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


async def initialize_session():
    """Initialize Telegram session."""
    
    # Get credentials from environment or input
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    if not api_id:
        api_id = input("Enter your Telegram API ID: ")
    
    if not api_hash:
        api_hash = input("Enter your Telegram API Hash: ")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Initialize client
    client = TelegramClient('data/telegram_session', api_id, api_hash)
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("\n=== Authorization Required ===")
            phone = input('Enter your phone number (with country code, e.g., +1234567890): ')
            await client.send_code_request(phone)
            
            code = input('Enter the verification code: ')
            
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input('Enter your 2FA password: ')
                await client.sign_in(password=password)
        
        print("\n✓ Session initialized successfully!")
        print("✓ Session file saved to: data/telegram_session.session")
        print("\nThis file will be used by the API service. Keep it secure!")
        
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(initialize_session())

