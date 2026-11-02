from __future__ import annotations

from datetime import datetime
from urllib.parse import urljoin

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from .models import NewsItem


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


async def collect_rss(session: aiohttp.ClientSession, config: dict) -> list[NewsItem]:
    async with session.get(config["url"], allow_redirects=True) as response:
        response.raise_for_status()
        feed = feedparser.parse(await response.read())
    items: list[NewsItem] = []
    for entry in feed.entries[: config.get("limit", 5)]:
        url = entry.get("link", "")
        title = BeautifulSoup(entry.get("title", ""), "html.parser").get_text(" ", strip=True)
        if url and title:
            image = next((item.get("href") for item in entry.get("media_content", []) if item.get("href")), None)
            items.append(NewsItem(config["name"], config["url"], title, url, BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True), image))
    return items


async def collect_web(session: aiohttp.ClientSession, config: dict) -> list[NewsItem]:
    async with session.get(config["url"], allow_redirects=True) as response:
        response.raise_for_status()
        soup = BeautifulSoup(await response.text(), "html.parser")
    items: list[NewsItem] = []
    for node in soup.select(config["item_selector"])[: config.get("limit", 5)]:
        link = node.select_one(config["link_selector"])
        title = node.select_one(config["title_selector"])
        if not link or not title or not link.get("href"):
            continue
        image = node.select_one(config.get("image_selector", "img"))
        description = node.select_one(config.get("description_selector", "p"))
        items.append(NewsItem(
            config["name"], config["url"], _text(title), urljoin(config["url"], link["href"]),
            _text(description), urljoin(config["url"], image["src"]) if image and image.get("src") else None,
        ))
    return items
