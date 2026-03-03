from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import Settings
from app.handlers.setup import SetupStates
from app.keyboards.admin import approval_keyboard
from app.repositories.users_repo import UsersRepository

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    bot: Bot,
    users_repo: UsersRepository,
    settings: Settings,
    state: FSMContext,
) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    telegram_id = message.from_user.id

    # Администратор не проходит регистрацию и всегда имеет активный доступ
    if telegram_id == settings.admin_id:
        user = await users_repo.get_by_id(telegram_id)
        if not user or user["status"] != "active":
            username = message.from_user.username or "admin"
            pseudo = username[:32]
            await users_repo.create_pending(telegram_id)
            await users_repo.set_profile(telegram_id, pseudo=pseudo, side="admin")

        await message.answer(
            "Вы администратор. Ваш доступ активен. "
            "Используйте админ-команды (/approve, /reject, /ban, /list) или /whoami."
        )
        return

    user = await users_repo.get_by_id(telegram_id)

    if not user:
        await users_repo.create_pending(telegram_id)
        username = f"@{message.from_user.username}" if message.from_user.username else "—"
        await bot.send_message(
            chat_id=settings.admin_id,
            text=(
                "Новый пользователь запросил доступ:\n"
                f"telegram_id: {telegram_id}\n"
                f"username: {username}"
            ),
            reply_markup=approval_keyboard(telegram_id),
        )
        await message.answer("Заявка отправлена администратору. Ожидайте одобрения.")
        return

    status = user["status"]
    if status == "banned":
        return
    if status == "active":
        await message.answer("Вы уже активны. Используйте /whoami или отправьте сообщение.")
        return
    if status == "setup":
        await state.set_state(SetupStates.waiting_pseudo)
        await message.answer(
            "Доступ одобрен. Введите ник (3–32 символа, латиница/цифры/_). "
            "Он будет отображаться в сообщениях."
        )
        return

    await message.answer("Ваш доступ пока не одобрен. Ожидайте решения администратора.")
