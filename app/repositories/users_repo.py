from app.db import Database


class UsersRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_id(self, telegram_id: int) -> dict | None:
        return await self.db.fetchone(
            "SELECT telegram_id, status, pseudo, side, created_at FROM users WHERE telegram_id = $1",
            (telegram_id,),
        )

    async def create_pending(self, telegram_id: int) -> None:
        await self.db.execute(
            "INSERT INTO users (telegram_id, status) VALUES ($1, 'pending') ON CONFLICT (telegram_id) DO NOTHING",
            (telegram_id,),
        )

    async def set_status(self, telegram_id: int, status: str) -> None:
        await self.db.execute(
            "UPDATE users SET status = $1 WHERE telegram_id = $2",
            (status, telegram_id),
        )

    async def set_profile(self, telegram_id: int, pseudo: str, side: str) -> None:
        await self.db.execute(
            "UPDATE users SET pseudo = $1, side = $2, status = 'active' WHERE telegram_id = $3",
            (pseudo, side, telegram_id),
        )
    async def pseudo_exists(self, pseudo: str) -> bool:
        row = await self.db.fetchone(
            "SELECT 1 as exists_flag FROM users WHERE lower(pseudo) = lower($1) LIMIT 1",
            (pseudo,),
        )
        return bool(row)

    async def pseudo_taken_by_other(self, telegram_id: int, pseudo: str) -> bool:
        row = await self.db.fetchone(
            (
                "SELECT 1 as exists_flag FROM users "
                "WHERE lower(pseudo) = lower($1) AND telegram_id != $2 "
                "LIMIT 1"
            ),
            (pseudo, telegram_id),
        )
        return bool(row)

    async def get_active_user_ids(self, exclude_telegram_id: int | None = None) -> list[int]:
        if exclude_telegram_id is None:
            rows = await self.db.fetchall("SELECT telegram_id FROM users WHERE status = 'active'")
        else:
            rows = await self.db.fetchall(
                "SELECT telegram_id FROM users WHERE status = 'active' AND telegram_id != $1",
                (exclude_telegram_id,),
            )
        return [int(row["telegram_id"]) for row in rows]

    async def list_users(self) -> list[dict]:
        return await self.db.fetchall(
            "SELECT telegram_id, status, pseudo, side, created_at FROM users ORDER BY created_at DESC"
        )
