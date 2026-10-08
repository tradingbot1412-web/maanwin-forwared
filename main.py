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
            # Extract the text (or caption if it's a photo/video)
            text = event.message.text or ""
            
            # Check if the text contains any links (http, https, www, or t.me)
            if re.search(r'(https?://|www\.|t\.me/)', text, re.IGNORECASE):
                print("Message contains a link. Skipping.")
                return # Stops the bot from sending this message
            
            # Send as a brand NEW message to remove the "Forwarded from" tag
            await client.send_message(
                DEST_CHAT, 
                message=text, 
                file=event.message.media
            )
            print("Message copied successfully (no forward tag)!")
            
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
