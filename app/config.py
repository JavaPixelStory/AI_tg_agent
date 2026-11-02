from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def _csv(name: str) -> list[str]:
    return [value.strip().lstrip("@") for value in os.getenv(name, "").split(",") if value.strip()]


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_chat_id: int | None
    tg_api_id: int | None
    tg_api_hash: str | None
    tg_phone: str | None
    telegram_channels: list[str]
    poll_interval_minutes: int
    max_items_per_cycle: int
    db_path: Path
    sources_path: Path

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv(ROOT / ".env")
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or token == "replace_me":
            raise RuntimeError("Укажите BOT_TOKEN в .env (сначала скопируйте .env.example).")
        owner = os.getenv("OWNER_CHAT_ID", "").strip()
        api_id = os.getenv("TG_API_ID", "").strip()
        return cls(
            bot_token=token,
            owner_chat_id=int(owner) if owner else None,
            tg_api_id=int(api_id) if api_id else None,
            tg_api_hash=os.getenv("TG_API_HASH", "").strip() or None,
            tg_phone=os.getenv("TG_PHONE", "").strip() or None,
            telegram_channels=_csv("TELEGRAM_CHANNELS"),
            poll_interval_minutes=max(1, int(os.getenv("POLL_INTERVAL_MINUTES", "10"))),
            max_items_per_cycle=max(1, int(os.getenv("MAX_ITEMS_PER_CYCLE", "10"))),
            db_path=ROOT / "data" / "news.sqlite3",
            sources_path=ROOT / "sources.yaml",
        )
