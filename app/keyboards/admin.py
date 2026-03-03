from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def approval_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Approve", callback_data=f"approve:{telegram_id}"),
                InlineKeyboardButton(text="Reject", callback_data=f"reject:{telegram_id}"),
            ]
        ]
    )
