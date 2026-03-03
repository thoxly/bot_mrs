from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    admin_id: int
    database_url: str
    port: int
    log_level: str
    webhook_base_url: str


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_raw = os.getenv("ADMIN_ID", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    port_raw = os.getenv("PORT", "10000").strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/")

    if not bot_token:
        raise ValueError("BOT_TOKEN is required in .env")
    if not admin_id_raw or not admin_id_raw.isdigit():
        raise ValueError("ADMIN_ID must be a numeric Telegram ID in .env")
    if not database_url:
        raise ValueError("DATABASE_URL is required in .env")
    if not port_raw.isdigit():
        raise ValueError("PORT must be a numeric value in .env")
    if not webhook_base_url:
        raise ValueError("WEBHOOK_BASE_URL is required in .env")

    return Settings(
        bot_token=bot_token,
        admin_id=int(admin_id_raw),
        database_url=database_url,
        port=int(port_raw),
        log_level=log_level,
        webhook_base_url=webhook_base_url,
    )
