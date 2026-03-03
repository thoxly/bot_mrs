from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.repositories.users_repo import UsersRepository

router = Router()


@router.message(Command("whoami"))
async def whoami_handler(message: Message, users_repo: UsersRepository) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    user = await users_repo.get_by_id(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы. Используйте /start")
        return

    await message.answer(
        "\n".join(
            [
                f'telegram_id: {user["telegram_id"]}',
                f'status: {user["status"]}',
                f'pseudo: {user.get("pseudo") or "-"}',
                f'side: {user.get("side") or "-"}',
            ]
        )
    )
