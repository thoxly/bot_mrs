CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    status VARCHAR(32) NOT NULL,
    pseudo TEXT UNIQUE,
    side VARCHAR(32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    from_telegram_id BIGINT NOT NULL,
    pseudo TEXT NOT NULL,
    side TEXT NOT NULL,
    type TEXT NOT NULL,
    text TEXT,
    file_ids TEXT,
    reply_to_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_messages_code ON messages(code);
