from __future__ import annotations

import asyncio
from contextlib import suppress
from io import BytesIO

from telethon import TelegramClient, events

from .config import Settings
from .models import NewsItem


async def watch_channels(settings: Settings, on_item) -> None:
    """Watch configured public channels through the owner's Telegram account."""
    if not settings.telegram_channels:
        return
    if not (settings.tg_api_id and settings.tg_api_hash and settings.tg_phone):
        raise RuntimeError("Telegram channels need TG_API_ID, TG_API_HASH and TG_PHONE in .env.")

    session_path = settings.db_path.parent / "telegram_user"
    client = TelegramClient(str(session_path), settings.tg_api_id, settings.tg_api_hash)
    await client.start(phone=settings.tg_phone)
    entities = await client.get_entity(settings.telegram_channels)
    by_id = {entity.id: entity for entity in entities}

    @client.on(events.NewMessage(chats=entities))
    async def incoming(event):
        message = event.message
        entity = by_id.get(event.chat_id)
        username = getattr(entity, "username", None)
        link = f"https://t.me/{username}/{message.id}" if username else "https://t.me/"
        text = (message.message or "Медиа-публикация").strip()
        image_data = None
        if message.photo:
            raw = await client.download_media(message, bytes)
            image_data = raw if isinstance(raw, bytes) else None
        await on_item(NewsItem(
            source=getattr(entity, "title", username or "Telegram"), source_url=f"https://t.me/{username}" if username else "https://t.me/",
            title=text.splitlines()[0][:500], description="\n".join(text.splitlines()[1:])[:700], url=link, image_data=image_data,
        ))

    try:
        await client.run_until_disconnected()
    except asyncio.CancelledError:
        raise
    finally:
        with suppress(Exception):
            await client.disconnect()
