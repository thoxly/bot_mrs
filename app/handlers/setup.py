import re

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.repositories.users_repo import UsersRepository

router = Router()

PSEUDO_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")


class SetupStates(StatesGroup):
    waiting_pseudo = State()
    waiting_side = State()


@router.message(Command("profile"))
async def change_profile(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepository,
) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    user = await users_repo.get_by_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запросите доступ через /start и дождитесь одобрения.")
        return

    status = user["status"]
    if status == "banned":
        await message.answer("Ваш доступ заблокирован, изменить профиль нельзя.")
        return
    if status in {"pending", "setup"}:
        await message.answer("Сначала завершите текущую регистрацию через /start.")
        return

    await state.set_state(SetupStates.waiting_pseudo)
    await message.answer(
        "Смена профиля. Введите новый ник (3–32 символа, латиница/цифры/_). "
        "Он будет отображаться в сообщениях."
    )


@router.message(StateFilter(SetupStates.waiting_pseudo))
async def setup_pseudo(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepository,
) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    pseudo = (message.text or "").strip()
    if not PSEUDO_RE.match(pseudo):
        await message.answer("Ник: 3–32 символа, только латиница, цифры и _. Попробуйте снова.")
        return

    if await users_repo.pseudo_taken_by_other(message.from_user.id, pseudo):
        await message.answer("Этот ник уже занят. Введите другой.")
        return

    await state.update_data(pseudo=pseudo)
    await state.set_state(SetupStates.waiting_side)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Клиент", callback_data="side:client"),
                InlineKeyboardButton(text="Подрядчик", callback_data="side:vendor"),
            ]
        ]
    )
    await message.answer("Выберите сторону:", reply_markup=keyboard)


@router.message(StateFilter(SetupStates.waiting_side))
async def setup_side(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepository,
) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    side_raw = (message.text or "").strip().lower()
    if side_raw in {"client", "клиент"}:
        side = "client"
    elif side_raw in {"vendor", "подрядчик"}:
        side = "vendor"
    else:
        await message.answer("Некорректно. Нажмите кнопку или введите: клиент или подрядчик")
        return

    data = await state.get_data()
    pseudo = data.get("pseudo")
    if not pseudo:
        await state.set_state(SetupStates.waiting_pseudo)
        await message.answer("Сначала введите ник — он будет отображаться в сообщениях.")
        return

    await users_repo.set_profile(message.from_user.id, pseudo=pseudo, side=side)
    await state.clear()
    await message.answer("Профиль завершен. Статус: active. Теперь вы получаете сообщения.")
    await message.answer(
        "Кратко о работе бота:\n"
        "- Пишите сообщение боту — оно анонимно рассылается активным пользователям другой стороны.\n"
        "- Чтобы ответить, сделайте Reply на сообщение с кодом M....\n"
        "- /whoami — ваш профиль, /profile — сменить ник и сторону."
    )


@router.callback_query(StateFilter(SetupStates.waiting_side), F.data.startswith("side:"))
async def setup_side_callback(
    callback: CallbackQuery,
    state: FSMContext,
    users_repo: UsersRepository,
) -> None:
    if not callback.from_user:
        await callback.answer()
        return

    side_key = callback.data.split(":", maxsplit=1)[1]
    if side_key not in {"client", "vendor"}:
        await callback.answer("Некорректный выбор", show_alert=True)
        return

    data = await state.get_data()
    pseudo = data.get("pseudo")
    if not pseudo:
        await state.set_state(SetupStates.waiting_pseudo)
        await callback.message.answer("Сначала введите ник — он будет отображаться в сообщениях.")
        await callback.answer()
        return

    await users_repo.set_profile(callback.from_user.id, pseudo=pseudo, side=side_key)
    await state.clear()
    await callback.message.answer(
        "Профиль завершен. Статус: active. Теперь вы получаете сообщения."
    )
    await callback.message.answer(
        "Кратко о работе бота:\n"
        "- Пишите сообщение боту — оно анонимно рассылается активным пользователям другой стороны.\n"
        "- Чтобы ответить, сделайте Reply на сообщение с кодом M....\n"
        "- /whoami — ваш профиль, /profile — сменить ник и сторону."
    )
    await callback.answer("Сторона сохранена")
