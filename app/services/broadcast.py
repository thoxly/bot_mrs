import logging
from typing import Any

from aiogram import Bot
from aiogram.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo

from app.repositories.users_repo import UsersRepository
from app.utils.parsing import format_header

logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, users_repo: UsersRepository) -> None:
        self.users_repo = users_repo

    async def broadcast_text(
        self,
        bot: Bot,
        sender_id: int,
        code: str,
        pseudo: str,
        side: str,
        text: str,
        reply_to_code: str | None = None,
        reply_quote: str | None = None,
    ) -> None:
        header = format_header(code=code, pseudo=pseudo, side=side, reply_to_code=reply_to_code)
        payload = text.strip()

        if reply_to_code:
            quote = (reply_quote or "message").strip()[:200]
            payload = f'Цитата: "{quote}"\n{payload}' if payload else f'Цитата: "{quote}"'

        recipients = await self.users_repo.get_active_user_ids(exclude_telegram_id=sender_id)
        outgoing_text = f"{header}\n{payload}".strip()

        for chat_id in recipients:
            try:
                await bot.send_message(chat_id=chat_id, text=outgoing_text)
            except Exception:
                logger.exception("Failed to deliver text message to %s", chat_id)

    async def broadcast_single_media(
        self,
        bot: Bot,
        sender_chat_id: int,
        sender_id: int,
        source_message_id: int,
        code: str,
        pseudo: str,
        side: str,
        comment: str | None,
        reply_to_code: str | None = None,
        reply_quote: str | None = None,
    ) -> None:
        caption = self._build_caption(
            code=code,
            pseudo=pseudo,
            side=side,
            comment=comment,
            reply_to_code=reply_to_code,
            reply_quote=reply_quote,
        )
        recipients = await self.users_repo.get_active_user_ids(exclude_telegram_id=sender_id)

        for chat_id in recipients:
            try:
                await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=sender_chat_id,
                    message_id=source_message_id,
                    caption=caption,
                )
            except Exception:
                logger.exception("Failed to deliver media message to %s", chat_id)

    async def broadcast_album(
        self,
        bot: Bot,
        sender_id: int,
        code: str,
        pseudo: str,
        side: str,
        album_items: list[dict[str, Any]],
        comment: str | None = None,
        reply_to_code: str | None = None,
        reply_quote: str | None = None,
    ) -> None:
        recipients = await self.users_repo.get_active_user_ids(exclude_telegram_id=sender_id)
        caption = self._build_caption(
            code=code,
            pseudo=pseudo,
            side=side,
            comment=comment,
            reply_to_code=reply_to_code,
            reply_quote=reply_quote,
        )

        media = []
        for index, item in enumerate(album_items):
            item_type = item["type"]
            file_id = item["file_id"]
            item_caption = caption if index == 0 else None
            if item_type == "photo":
                media.append(InputMediaPhoto(media=file_id, caption=item_caption))
            elif item_type == "video":
                media.append(InputMediaVideo(media=file_id, caption=item_caption))
            elif item_type == "document":
                media.append(InputMediaDocument(media=file_id, caption=item_caption))

        if not media:
            return

        for chat_id in recipients:
            try:
                await bot.send_media_group(chat_id=chat_id, media=media)
            except Exception:
                logger.exception("Failed to deliver album to %s", chat_id)

    @staticmethod
    def _build_caption(
        code: str,
        pseudo: str,
        side: str,
        comment: str | None,
        reply_to_code: str | None = None,
        reply_quote: str | None = None,
    ) -> str:
        header = format_header(code=code, pseudo=pseudo, side=side, reply_to_code=reply_to_code)
        clean_comment = (comment or "").strip()

        if reply_to_code:
            quote = (reply_quote or "message").strip()[:200]
            if clean_comment:
                return f'{header}\nЦитата: "{quote}"\n{clean_comment}'
            return f'{header}\nЦитата: "{quote}"'

        if clean_comment:
            return f"{header}\n{clean_comment}"
        return header
