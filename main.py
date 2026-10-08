import os
import asyncio
import re
from aiohttp import web
from telethon import TelegramClient, events

# Credentials
API_ID = 36378979
API_HASH = 'c74ff922f82543daf2e14e7468b2a9b0'
BOT_TOKEN = '8961588391:AAHDllCXuFPj0UsgitPcvxrsDwZtMRQYMtg'

# Chat IDs
SOURCE_CHAT = -1002369799233  # KING ARMY
DEST_CHAT = -1002199309542    # MAANWIN (TAMIL)

async def health_check(request):
    return web.Response(text="Forwarder is actively running 24/7!")

async def main():
    client = TelegramClient('bot_session', API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=SOURCE_CHAT))
    async def forwarder(event):
        try:
            # Extract the raw text or media caption
            text = event.message.text or ""
            
            # Aggressive Regex: Targets https://, http://, www., t.me, telegram.me, and @usernames
            clean_text = re.sub(
                r'(https?://\S+|www\.\S+|t\.me\S+|telegram\.me\S+|@[a-zA-Z0-9_]+)', 
                '', 
                text, 
                flags=re.IGNORECASE
            )
            
            # Clean up formatting: Remove large empty gaps left behind by deleted links
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text).strip()
            
            # Safety check: If the message was ONLY a link, skip sending an empty text block
            if not clean_text and not event.message.media:
                print("Message contained only a link. Skipping to prevent empty message errors.")
                return

            # Send the cleaned paragraph as a brand new message (no forward tag)
            await client.send_message(
                DEST_CHAT, 
                message=clean_text, 
                file=event.message.media
            )
            print("Message copied successfully with all links completely erased!")
            
        except Exception as e:
            print(f"Failed to copy message: {e}")

    # Start the Telegram bot
    await client.start(bot_token=BOT_TOKEN)
    print("Bot logged in and listening for messages...")

    # Start the web server for Render / UptimeRobot
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server is live on port {port}")

    # Keep the script running continuously
    await client.run_until_disconnected()

if __name__ == '__main__':
    # Safely start the event loop
    asyncio.run(main())
