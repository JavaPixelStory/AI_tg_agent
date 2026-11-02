from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsItem:
    source: str
    source_url: str
    title: str
    url: str
    description: str = ""
    image_url: str | None = None
    image_data: bytes | None = None
    published_at: datetime | None = None

    @property
    def key(self) -> str:
        return f"{self.source}|{self.url}"
