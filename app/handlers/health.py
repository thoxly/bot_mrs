from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()


@router.message(Command("health"))
async def health_command(message: Message) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    await message.answer("Бот работает. status: ok")

