from pathlib import Path

import asyncpg


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def init(self, sql_init_path: str) -> None:
        self.pool = await asyncpg.create_pool(dsn=self.database_url)
        script = Path(sql_init_path).read_text(encoding="utf-8")
        async with self.pool.acquire() as conn:
            await conn.execute(script)

    def _require_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database is not initialized")
        return self.pool

    async def execute(self, query: str, params: tuple = ()) -> None:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            await conn.execute(query, *params)

    async def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            return dict(row) if row else None

    async def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def insert_and_get_id(self, query: str, params: tuple = ()) -> int:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            if not row:
                raise RuntimeError("Insert query did not return an id")
            return int(row[0])

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
