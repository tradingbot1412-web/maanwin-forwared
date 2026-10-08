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
            # If the message has no text, just copy it cleanly
            if not event.message.message:
                await client.send_message(DEST_CHAT, event.message)
                return

            # THE BLANK SPACE TRICK: Replace links with blank spaces of the exact same length.
            # This guarantees the hidden Premium Emoji coordinates never shift or break.
            def replace_with_spaces(match):
                return ' ' * len(match.group(0))

            clean_text = re.sub(
                r'(https?://[^\s]+|www\.[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+|@[a-zA-Z0-9_]+)', 
                replace_with_spaces, 
                event.message.message, 
                flags=re.IGNORECASE
            )
            
            # Apply the blanked-out text directly back to the original message object
            event.message.message = clean_text
            
            # Delete any hidden blue webpage preview cards
            if hasattr(event.message.media, 'webpage'):
                event.message.media = None
                
            # Send the exact structural copy (No forward tags, links erased, emojis untouched)
            await client.send_message(
                DEST_CHAT, 
                event.message, 
                link_preview=False
            )
            print("Message copied successfully with structural emoji preservation!")
            
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

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
