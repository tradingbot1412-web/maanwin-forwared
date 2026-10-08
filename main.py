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
            # Use raw_text to strip away any hidden formatting
            text = event.raw_text or ""
            
            # Extremely aggressive link and tag removal
            clean_text = re.sub(r'https?://\S+', '', text, flags=re.IGNORECASE)
            clean_text = re.sub(r'www\.\S+', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r't\.me/\S+', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'@[a-zA-Z0-9_]+', '', clean_text)
            
            # Clean up extra blank lines left by deleted links
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text).strip()
            
            # Ensure we only forward real files (Photos/Videos/Docs), NOT Web Page Previews
            actual_media = event.message.media
            if hasattr(actual_media, 'webpage'):
                actual_media = None
                
            # Safety check: Prevent the bot from sending a completely blank message
            if not clean_text and not actual_media:
                print("Message contained only a link. Skipped.")
                return

            # Send the cleaned message with link previews strictly forced OFF
            await client.send_message(
                DEST_CHAT, 
                message=clean_text, 
                file=actual_media,
                link_preview=False
            )
            print("Message copied successfully with zero links or previews!")
            
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
