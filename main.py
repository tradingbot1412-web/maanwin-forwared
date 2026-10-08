import os
import asyncio
import re
import copy
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

def remove_links_and_preserve_emojis(text, entities):
    if not text:
        return text, entities
    
    # Telegram calculates emoji positions in UTF-16 bytes. 
    # We convert the text to UTF-16 so we can perfectly map the premium emojis.
    utf16_bytes = text.encode('utf-16-le')
    code_units = [utf16_bytes[i:i+2] for i in range(0, len(utf16_bytes), 2)]
    
    # Find all URLs and @usernames
    matches = list(re.finditer(r'(https?://[^\s]+|www\.[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+|@[a-zA-Z0-9_]+)', text, flags=re.IGNORECASE))
    
    # Map Python character indices to Telegram's UTF-16 offset system
    char_to_utf16_offset = []
    current_utf16_offset = 0
    for char in text:
        char_to_utf16_offset.append(current_utf16_offset)
        # Premium emojis take up 2 spaces in UTF-16, standard letters take 1
        if ord(char) > 0xFFFF:
            current_utf16_offset += 2
        else:
            current_utf16_offset += 1
    char_to_utf16_offset.append(current_utf16_offset)
    
    # Calculate exact positions to delete
    delete_ranges = []
    for match in matches:
        start_char, end_char = match.span()
        start_u16 = char_to_utf16_offset[start_char]
        end_u16 = char_to_utf16_offset[end_char]
        delete_ranges.append((start_u16, end_u16))
    
    # Sort in reverse to delete from back to front (prevents shifting errors)
    delete_ranges.sort(key=lambda x: x[0], reverse=True)
    
    new_entities = []
    if entities:
        for ent in entities:
            # Drop the actual clickable URL entities so the invisible text isn't clickable
            if type(ent).__name__ in ['MessageEntityUrl', 'MessageEntityTextUrl']:
                continue
            new_entities.append(copy.copy(ent))
    
    # Surgically remove the links and adjust the premium emoji positions
    for start_u16, end_u16 in delete_ranges:
        delete_len = end_u16 - start_u16
        del code_units[start_u16:end_u16]
        
        for ent in new_entities:
            if ent.offset >= end_u16:
                ent.offset -= delete_len
            elif ent.offset + ent.length <= start_u16:
                pass
            else:
                overlap_start = max(ent.offset, start_u16)
                overlap_end = min(ent.offset + ent.length, end_u16)
                overlap_len = overlap_end - overlap_start
                ent.length -= overlap_len
                if ent.offset > start_u16:
                    ent.offset = start_u16
    
    # Reassemble the perfectly preserved text
    new_utf16_bytes = b''.join(code_units)
    new_text = new_utf16_bytes.decode('utf-16-le')
    valid_entities = [e for e in new_entities if getattr(e, 'length', 0) > 0]
    
    return new_text, valid_entities

async def main():
    client = TelegramClient('bot_session', API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=SOURCE_CHAT))
    async def forwarder(event):
        try:
            # Get the exact raw text and raw entity map
            raw_text = event.message.message or ""
            raw_entities = event.message.entities or []
            
            # Process the text to remove links while keeping entity offsets perfectly aligned
            clean_text, clean_entities = remove_links_and_preserve_emojis(raw_text, raw_entities)
            
            # Ensure we only forward real files (Photos/Videos/Docs), NOT Web Page Previews
            actual_media = event.message.media
            if hasattr(actual_media, 'webpage'):
                actual_media = None
                
            # Safety check
            if not clean_text and not actual_media:
                print("Message contained only a link. Skipped.")
                return

            # Send the cleaned message, feeding the exact Premium Emoji data directly back into Telegram
            await client.send_message(
                DEST_CHAT, 
                message=clean_text, 
                formatting_entities=clean_entities,  # <-- This guarantees Premium Emojis work
                file=actual_media,
                link_preview=False
            )
            print("Message copied successfully with direct Premium Emoji preservation!")
            
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
