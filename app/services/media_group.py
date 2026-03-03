import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from aiogram.types import Message

AlbumCallback = Callable[[list[Message]], Awaitable[None]]


class MediaGroupBuffer:
    def __init__(self, wait_seconds: float = 1.5) -> None:
        self.wait_seconds = wait_seconds
        self._messages: dict[tuple[int, str], list[Message]] = defaultdict(list)
        self._tasks: dict[tuple[int, str], asyncio.Task] = {}

    async def add(self, message: Message, callback: AlbumCallback) -> None:
        if not message.media_group_id or not message.from_user:
            return

        key = (message.from_user.id, message.media_group_id)
        self._messages[key].append(message)

        if key in self._tasks:
            return

        async def flush() -> None:
            try:
                await asyncio.sleep(self.wait_seconds)
                items = sorted(self._messages.pop(key, []), key=lambda msg: msg.message_id)
                if items:
                    await callback(items)
            finally:
                self._tasks.pop(key, None)

        self._tasks[key] = asyncio.create_task(flush())
