import json
from typing import Any

from app.db import Database


class MessagesRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_message(
        self,
        from_telegram_id: int,
        pseudo: str,
        side: str,
        msg_type: str,
        text: str | None,
        file_ids: list[dict[str, Any]] | None,
        reply_to_code: str | None,
    ) -> dict:
        message_id = await self.db.insert_and_get_id(
            """
            INSERT INTO messages (code, from_telegram_id, pseudo, side, type, text, file_ids, reply_to_code)
            VALUES ('', $1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            (
                from_telegram_id,
                pseudo,
                side,
                msg_type,
                text,
                json.dumps(file_ids, ensure_ascii=False) if file_ids else None,
                reply_to_code,
            ),
        )
        code = f"M{message_id:04d}"
        await self.db.execute("UPDATE messages SET code = $1 WHERE id = $2", (code, message_id))
        return {
            "id": message_id,
            "code": code,
            "from_telegram_id": from_telegram_id,
            "pseudo": pseudo,
            "side": side,
            "type": msg_type,
            "text": text,
            "file_ids": file_ids,
            "reply_to_code": reply_to_code,
        }

    async def get_by_code(self, code: str) -> dict | None:
        row = await self.db.fetchone(
            "SELECT id, code, from_telegram_id, pseudo, side, type, text, file_ids, reply_to_code, created_at FROM messages WHERE code = $1",
            (code,),
        )
        if not row:
            return None
        row["file_ids"] = json.loads(row["file_ids"]) if row.get("file_ids") else None
        return row
