import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from fastapi import FastAPI
import uvicorn

from app.config import load_settings
from app.db import Database
from app.handlers import admin, chat, setup, start, whoami
from app.logging_conf import setup_logging
from app.repositories.messages_repo import MessagesRepository
from app.repositories.users_repo import UsersRepository
from app.services.broadcast import BroadcastService
from app.services.media_group import MediaGroupBuffer

logger = logging.getLogger(__name__)


def build_health_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


async def run_health_server(port: int) -> None:
    config = uvicorn.Config(
        app=build_health_app(),
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config=config)
    await server.serve()


async def run() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    db = Database(settings.database_url)
    await db.init("sql/init.sql")

    users_repo = UsersRepository(db)
    messages_repo = MessagesRepository(db)
    broadcast_service = BroadcastService(users_repo)
    media_group_buffer = MediaGroupBuffer(wait_seconds=1.5)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp["settings"] = settings
    dp["users_repo"] = users_repo
    dp["messages_repo"] = messages_repo
    dp["broadcast_service"] = broadcast_service
    dp["media_group_buffer"] = media_group_buffer

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(setup.router)
    dp.include_router(whoami.router)
    dp.include_router(chat.router)

    @dp.error()
    async def on_error(event: ErrorEvent) -> bool:
        logger.exception("Unhandled update error: %s", event.exception)
        return True

    logger.info("Bot polling and health server are starting...")
    polling_task = asyncio.create_task(dp.start_polling(bot), name="telegram-polling")
    health_task = asyncio.create_task(run_health_server(settings.port), name="health-server")

    try:
        done, pending = await asyncio.wait(
            {polling_task, health_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
    finally:
        await db.close()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
