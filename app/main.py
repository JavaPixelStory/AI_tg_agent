from __future__ import annotations

import asyncio
import html
import logging
from pathlib import Path

import aiohttp
import yaml
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import BufferedInputFile

from .collectors import collect_rss, collect_web
from .config import Settings
from .models import NewsItem
from .store import Store
from .telegram_source import watch_channels

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def load_sources(path: Path) -> dict:
    if not path.exists():
        return {"rss": [], "web": []}
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {"rss": [], "web": []}


def caption(item: NewsItem) -> str:
    # Подпись к фото ограничена 1024 символами Telegram; оставляем место для разметки и ссылки.
    body = html.escape(item.description[:250])
    return f"<b>{html.escape(item.title[:500])}</b>\n\n{body}\n\n<a href=\"{html.escape(item.url, quote=True)}\">Источник: {html.escape(item.source)}</a>"


class NewsService:
    def __init__(self, settings: Settings, bot: Bot) -> None:
        self.settings, self.bot, self.store = settings, bot, Store(settings.db_path)

    async def deliver(self, item: NewsItem) -> bool:
        if not self.settings.owner_chat_id or self.store.is_delivered(item.key):
            return False
        try:
            if item.image_data:
                await self.bot.send_photo(self.settings.owner_chat_id, BufferedInputFile(item.image_data, "news.jpg"), caption=caption(item), parse_mode="HTML")
            elif item.image_url:
                await self.bot.send_photo(self.settings.owner_chat_id, item.image_url, caption=caption(item), parse_mode="HTML")
            else:
                await self.bot.send_message(self.settings.owner_chat_id, caption(item), parse_mode="HTML", disable_web_page_preview=False)
            self.store.mark_delivered(item.key)
            return True
        except Exception:
            log.exception("Не удалось доставить материал из источника %s", item.source)
            return False

    async def collect_web_once(self) -> int:
        sources = load_sources(self.settings.sources_path)
        timeout = aiohttp.ClientTimeout(total=20)
        headers = {"User-Agent": "PersonalNewsConcierge/1.0 (+private use)"}
        sent = 0
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for config in sources.get("rss", []):
                try:
                    for item in await collect_rss(session, config):
                        if sent < self.settings.max_items_per_cycle and await self.deliver(item): sent += 1
                except Exception: log.exception("Не удалось собрать RSS: %s", config.get("name"))
            for config in sources.get("web", []):
                try:
                    for item in await collect_web(session, config):
                        if sent < self.settings.max_items_per_cycle and await self.deliver(item): sent += 1
                except Exception: log.exception("Не удалось собрать материалы сайта: %s", config.get("name"))
        return sent

    async def poll_web(self) -> None:
        while True:
            await self.collect_web_once()
            await asyncio.sleep(self.settings.poll_interval_minutes * 60)


async def run() -> None:
    settings = Settings.load()
    bot, dp = Bot(settings.bot_token), Dispatcher()
    service = NewsService(settings, bot)

    @dp.message(Command("whoami"))
    async def whoami(message: Message) -> None:
        await message.answer(f"Ваш Telegram ID: <code>{message.chat.id}</code>", parse_mode="HTML")

    @dp.message(Command("status"))
    async def status(message: Message) -> None:
        if message.chat.id != settings.owner_chat_id: return
        src = load_sources(settings.sources_path)
        await message.answer(f"RSS: {len(src.get('rss', []))}; сайты: {len(src.get('web', []))}; Telegram-каналы: {len(settings.telegram_channels)}")

    @dp.message(Command("digest"))
    async def digest(message: Message) -> None:
        if message.chat.id != settings.owner_chat_id: return
        sent = await service.collect_web_once()
        await message.answer(f"Готово. Отправлено: {sent}.")

    if not settings.owner_chat_id:
        log.warning("Не задан OWNER_CHAT_ID. Выполните /whoami, укажите ID в .env и перезапустите сервис.")
    asyncio.create_task(service.poll_web())
    if settings.telegram_channels:
        asyncio.create_task(watch_channels(settings, service.deliver))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
