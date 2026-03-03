import re

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.repositories.users_repo import UsersRepository

router = Router()

PSEUDO_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")


class SetupStates(StatesGroup):
    waiting_pseudo = State()
    waiting_side = State()


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
        await message.answer("Псевдоним: 3-32 символа, только латиница, цифры и _. Попробуйте снова.")
        return

    if await users_repo.pseudo_exists(pseudo):
        await message.answer("Этот псевдоним уже занят. Введите другой.")
        return

    await state.update_data(pseudo=pseudo)
    await state.set_state(SetupStates.waiting_side)
    await message.answer("Укажите сторону: client или vendor")


@router.message(StateFilter(SetupStates.waiting_side))
async def setup_side(
    message: Message,
    state: FSMContext,
    users_repo: UsersRepository,
) -> None:
    if message.chat.type != "private" or not message.from_user:
        return

    side = (message.text or "").strip().lower()
    if side not in {"client", "vendor"}:
        await message.answer("Некорректно. Введите: client или vendor")
        return

    data = await state.get_data()
    pseudo = data.get("pseudo")
    if not pseudo:
        await state.set_state(SetupStates.waiting_pseudo)
        await message.answer("Сначала введите псевдоним.")
        return

    await users_repo.set_profile(message.from_user.id, pseudo=pseudo, side=side)
    await state.clear()
    await message.answer("Профиль завершен. Статус: active. Теперь вы получаете сообщения.")
