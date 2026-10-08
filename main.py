import os
import asyncio
import re
from aiohttp import web
from telethon import TelegramClient, events
from telethon.extensions import html  # <-- This is the magic tool for Premium Emojis

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
            # Get raw text and formatting entities (this contains the premium emojis)
            raw_text = event.message.message or ""
            entities = event.message.entities
            
            # Convert the message to HTML to preserve Bold, Italics, and Premium Emojis
            html_text = html.unparse(raw_text, entities)
            
            # Remove inline hyperlink tags (e.g., if words are hyperlinked)
            clean_html = re.sub(r'<a[^>]*>.*?</a>', '', html_text, flags=re.IGNORECASE)
            
            # Safely remove URLs without accidentally deleting surrounding HTML tags [^\s<]+
            clean_html = re.sub(r'https?://[^\s<]+', '', clean_html, flags=re.IGNORECASE)
            clean_html = re.sub(r'www\.[^\s<]+', '', clean_html, flags=re.IGNORECASE)
            clean_html = re.sub(r't\.me/[^\s<]+', '', clean_html, flags=re.IGNORECASE)
            clean_html = re.sub(r'telegram\.me/[^\s<]+', '', clean_html, flags=re.IGNORECASE)
            clean_html = re.sub(r'@[a-zA-Z0-9_]+', '', clean_html)
            
            # Clean up extra blank lines
            clean_html = re.sub(r'\n\s*\n', '\n\n', clean_html).strip()
            
            # Ensure we only forward real files, NOT Web Page Previews
            actual_media = event.message.media
            if hasattr(actual_media, 'webpage'):
                actual_media = None
                
            # Safety check
            if not clean_html and not actual_media:
                print("Message was only a link. Skipped.")
                return

            # Send the cleaned HTML message (Telegram turns the HTML back into premium emojis)
            await client.send_message(
                DEST_CHAT, 
                message=clean_html, 
                file=actual_media,
                parse_mode='html',  # <-- This tells Telegram to render the emojis
                link_preview=False
            )
            print("Message copied successfully with Premium Emojis preserved!")
            
        except Exception as e:
            print(f"Failed to copy message: {e}")

    # Start the Telegram bot
    await client.start(bot_token=BOT_TOKEN)
    print("Bot logged in and listening for messages...")

    # Start the web server
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server is live on port {port}")

    # Keep running
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
