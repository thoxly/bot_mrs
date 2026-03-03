import re

from aiogram.types import Message

CODE_RE = re.compile(r"\b(M\d{4,})\b")


def extract_message_code(text: str | None) -> str | None:
    if not text:
        return None
    match = CODE_RE.search(text)
    return match.group(1) if match else None


def extract_reply_code(message: Message) -> str | None:
    if not message.reply_to_message:
        return None
    source = message.reply_to_message.text or message.reply_to_message.caption
    return extract_message_code(source)


def build_quote_from_replied_message(message: Message) -> str:
    if not message.reply_to_message:
        return ""
    replied = message.reply_to_message

    payload = (replied.text or replied.caption or "").strip()
    if payload:
        lines = payload.splitlines()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else payload
        if body:
            return body[:200]

    if replied.media_group_id:
        return "album"
    if replied.photo:
        return "photo"
    if replied.video:
        return "video"
    if replied.document:
        return "document"
    return "message"


def format_header(code: str, pseudo: str, side: str, reply_to_code: str | None = None) -> str:
    side_tag = side.upper()
    if reply_to_code:
        return f"{code} ↪ {reply_to_code} | [{side_tag}] {pseudo}"
    return f"{code} | [{side_tag}] {pseudo}"
