# News concierge for Telegram

This service collects public news from RSS feeds, selected web pages and public Telegram channels, then sends new items as compact cards to your private Telegram chat:

> image · title · short description · source link

It is deliberately an allow-list system: it reads only sources that you configure. It does not scrape private chats, read incoming private messages, or upload collected content to another service.

## What you need

- Python 3.11+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- For channel monitoring: a Telegram API ID/hash from [my.telegram.org/apps](https://my.telegram.org/apps). Telethon uses your own Telegram account, because ordinary bots cannot subscribe to and read arbitrary channels.

Only monitor sources you may access and where monitoring complies with the source's terms and applicable law.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item sources.example.yaml sources.yaml
```

1. Fill in `BOT_TOKEN` in `.env`.
2. Start a chat with your bot and run `python -m app` once.
3. Send `/whoami` to it; copy the displayed ID into `OWNER_CHAT_ID`.
4. Add RSS/web sources to `sources.yaml` and public channel handles to `TELEGRAM_CHANNELS`.
5. Start it again: `python -m app`.

On the first run with Telegram channels, Telethon asks for the code sent by Telegram (and your two-factor password when enabled). Its local session is stored under `data/` and is excluded from Git.

## Commands

- `/whoami` — show your numeric ID (before owner configuration)
- `/status` — source and delivery status (owner only)
- `/digest` — collect and send available web/RSS items now (owner only)

## Privacy and Git safety

- `.env`, Telegram sessions, database, logs and virtual environments are ignored by Git.
- Do not paste tokens, API hashes, phone numbers or chat IDs into source code, commits or issue trackers.
- Before sharing history, run `git status --ignored` and inspect the staged diff with `git diff --cached`.
- If a bot token leaks, revoke it in @BotFather and issue a new one. If Telegram API credentials leak, revoke/regenerate them in Telegram's developer portal.

## Run continuously

For initial testing, leave the terminal open. For production, run it under a process manager (Windows Task Scheduler, NSSM, Docker, or systemd) with the working directory set to this project directory. Back up `data/news.sqlite3` only if you want to preserve the delivered-item history; it contains URLs and titles.
