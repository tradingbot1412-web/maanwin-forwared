import os
import asyncio
from aiohttp import web
from telethon import TelegramClient, events

# Credentials
API_ID = 36378979
API_HASH = 'c74ff922f82543daf2e14e7468b2a9b0'
BOT_TOKEN = '8961588391:AAHDllCXuFPj0UsgitPcvxrsDwZtMRQYMtg'

# Chat IDs extracted from your raw data
SOURCE_CHAT = -1002369799233  # KING ARMY
DEST_CHAT = -1002199309542    # MAANWIN (TAMIL)

client = TelegramClient('bot_session', API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def forwarder(event):
    try:
        await client.send_message(DEST_CHAT, event.message)
        print("Message forwarded successfully!")
    except Exception as e:
        print(f"Failed to forward message: {e}")

async def health_check(request):
    return web.Response(text="Forwarder is actively running 24/7!")

async def main():
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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
