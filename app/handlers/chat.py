from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.repositories.messages_repo import MessagesRepository
from app.repositories.users_repo import UsersRepository
from app.services.broadcast import BroadcastService
from app.services.media_group import MediaGroupBuffer
from app.utils.parsing import build_quote_from_replied_message, extract_reply_code

router = Router()


def _extract_media_meta(message: Message) -> tuple[str, str] | None:
    if message.photo:
        return "photo", message.photo[-1].file_id
    if message.video:
        return "video", message.video.file_id
    if message.document:
        return "document", message.document.file_id
    return None


async def _process_album(
    items: list[Message],
    bot: Bot,
    users_repo: UsersRepository,
    messages_repo: MessagesRepository,
    broadcast_service: BroadcastService,
) -> None:
    first = items[0]
    if not first.from_user:
        return

    user = await users_repo.get_by_id(first.from_user.id)
    if not user or user["status"] != "active":
        return

    pseudo = user["pseudo"]
    side = user["side"]
    if not pseudo or not side:
        return

    album_payload: list[dict[str, Any]] = []
    for item in items:
        meta = _extract_media_meta(item)
        if not meta:
            continue
        item_type, file_id = meta
        album_payload.append({"type": item_type, "file_id": file_id})

    if not album_payload:
        return

    comment = (first.caption or "").strip() or None
    reply_to_code = extract_reply_code(first)
    reply_quote = build_quote_from_replied_message(first) if reply_to_code else None

    stored = await messages_repo.create_message(
        from_telegram_id=first.from_user.id,
        pseudo=pseudo,
        side=side,
        msg_type="album",
        text=comment,
        file_ids=album_payload,
        reply_to_code=reply_to_code,
    )

    await broadcast_service.broadcast_album(
        bot=bot,
        sender_id=first.from_user.id,
        code=stored["code"],
        pseudo=pseudo,
        side=side,
        album_items=album_payload,
        comment=comment,
        reply_to_code=reply_to_code,
        reply_quote=reply_quote,
    )


@router.message(
    StateFilter(None),
    F.chat.type == "private",
    F.content_type.in_({"text", "photo", "video", "document"}),
)
async def chat_message_handler(
    message: Message,
    bot: Bot,
    users_repo: UsersRepository,
    messages_repo: MessagesRepository,
    broadcast_service: BroadcastService,
    media_group_buffer: MediaGroupBuffer,
) -> None:
    if not message.from_user:
        return

    user = await users_repo.get_by_id(message.from_user.id)
    if not user:
        await message.answer("Сначала отправьте /start")
        return

    status = user["status"]
    if status == "banned":
        return
    if status == "setup":
        await message.answer("Завершите настройку профиля: отправьте /start и следуйте инструкциям.")
        return
    if status != "active":
        await message.answer("Ваш доступ пока не одобрен.")
        return

    pseudo = user.get("pseudo")
    side = user.get("side")
    if not pseudo or not side:
        await message.answer("Профиль неполный. Обратитесь к администратору.")
        return

    if message.text and message.text.startswith("/"):
        return

    if message.media_group_id:
        await media_group_buffer.add(
            message,
            lambda items: _process_album(
                items=items,
                bot=bot,
                users_repo=users_repo,
                messages_repo=messages_repo,
                broadcast_service=broadcast_service,
            ),
        )
        return

    reply_to_code = extract_reply_code(message)
    reply_quote = build_quote_from_replied_message(message) if reply_to_code else None

    if message.text:
        text = message.text.strip()
        if not text:
            return
        stored = await messages_repo.create_message(
            from_telegram_id=message.from_user.id,
            pseudo=pseudo,
            side=side,
            msg_type="text",
            text=text,
            file_ids=None,
            reply_to_code=reply_to_code,
        )
        await broadcast_service.broadcast_text(
            bot=bot,
            sender_id=message.from_user.id,
            code=stored["code"],
            pseudo=pseudo,
            side=side,
            text=text,
            reply_to_code=reply_to_code,
            reply_quote=reply_quote,
        )
        return

    media_meta = _extract_media_meta(message)
    if not media_meta:
        return
    media_type, file_id = media_meta
    comment = (message.caption or "").strip() or None

    stored = await messages_repo.create_message(
        from_telegram_id=message.from_user.id,
        pseudo=pseudo,
        side=side,
        msg_type=media_type,
        text=comment,
        file_ids=[{"type": media_type, "file_id": file_id}],
        reply_to_code=reply_to_code,
    )
    await broadcast_service.broadcast_single_media(
        bot=bot,
        sender_chat_id=message.chat.id,
        sender_id=message.from_user.id,
        source_message_id=message.message_id,
        code=stored["code"],
        pseudo=pseudo,
        side=side,
        comment=comment,
        reply_to_code=reply_to_code,
        reply_quote=reply_quote,
    )
