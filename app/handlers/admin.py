from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.repositories.users_repo import UsersRepository

router = Router()


def _is_admin(message: Message, admin_id: int) -> bool:
    return bool(message.from_user and message.from_user.id == admin_id)


def _parse_target_id(text: str) -> int | None:
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1])


@router.callback_query(F.data.startswith("approve:"))
async def approve_callback(
    callback: CallbackQuery,
    bot: Bot,
    users_repo: UsersRepository,
    settings: Settings,
) -> None:
    if not callback.from_user or callback.from_user.id != settings.admin_id:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    await users_repo.create_pending(target_id)
    await users_repo.set_status(target_id, "setup")

    try:
        await bot.send_message(
            target_id,
            "Доступ одобрен. Для настройки профиля отправьте /start и следуйте инструкциям.",
        )
    except Exception:
        pass
    await callback.message.edit_text(f"Approved: {target_id}")
    await callback.answer("Approved")


@router.callback_query(F.data.startswith("reject:"))
async def reject_callback(
    callback: CallbackQuery,
    bot: Bot,
    users_repo: UsersRepository,
    settings: Settings,
) -> None:
    if not callback.from_user or callback.from_user.id != settings.admin_id:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    await users_repo.create_pending(target_id)
    await users_repo.set_status(target_id, "pending")
    try:
        await bot.send_message(target_id, "Заявка отклонена.")
    except Exception:
        pass
    await callback.message.edit_text(f"Rejected: {target_id}")
    await callback.answer("Rejected")


@router.message(Command("approve"))
async def approve_command(
    message: Message,
    users_repo: UsersRepository,
    settings: Settings,
    bot: Bot,
) -> None:
    if not _is_admin(message, settings.admin_id):
        return

    target_id = _parse_target_id(message.text or "")
    if not target_id:
        await message.answer("Использование: /approve <telegram_id>")
        return

    await users_repo.create_pending(target_id)
    await users_repo.set_status(target_id, "setup")
    await message.answer(f"Пользователь {target_id} переведен в setup.")
    try:
        await bot.send_message(
            target_id,
            "Доступ одобрен. Для настройки профиля отправьте /start и следуйте инструкциям.",
        )
    except Exception:
        pass


@router.message(Command("reject"))
async def reject_command(
    message: Message,
    users_repo: UsersRepository,
    settings: Settings,
    bot: Bot,
) -> None:
    if not _is_admin(message, settings.admin_id):
        return

    target_id = _parse_target_id(message.text or "")
    if not target_id:
        await message.answer("Использование: /reject <telegram_id>")
        return

    await users_repo.create_pending(target_id)
    await users_repo.set_status(target_id, "pending")
    await message.answer(f"Пользователь {target_id} отклонен.")
    try:
        await bot.send_message(target_id, "Заявка отклонена.")
    except Exception:
        pass


@router.message(Command("ban"))
async def ban_command(
    message: Message,
    users_repo: UsersRepository,
    settings: Settings,
    bot: Bot,
) -> None:
    if not _is_admin(message, settings.admin_id):
        return

    target_id = _parse_target_id(message.text or "")
    if not target_id:
        await message.answer("Использование: /ban <telegram_id>")
        return

    await users_repo.create_pending(target_id)
    await users_repo.set_status(target_id, "banned")
    await message.answer(f"Пользователь {target_id} забанен.")
    try:
        await bot.send_message(target_id, "Ваш доступ заблокирован.")
    except Exception:
        pass


@router.message(Command("list"))
async def list_users(
    message: Message,
    users_repo: UsersRepository,
    settings: Settings,
) -> None:
    if not _is_admin(message, settings.admin_id):
        return

    users = await users_repo.list_users()
    if not users:
        await message.answer("Пользователей пока нет.")
        return

    lines = []
    for user in users[:100]:
        lines.append(
            f'{user["telegram_id"]} | {user["status"]} | {user.get("side") or "-"} | {user.get("pseudo") or "-"}'
        )
    await message.answer("\n".join(lines))


