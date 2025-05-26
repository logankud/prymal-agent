npm install @shopify/dev-mcp


# Run SQL DDL to create tables if not exists
psql -U $PGUSER -d $PGDATABASE -c "
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,            -- e.g., Slack user ID or channel ID
    agent_name TEXT NOT NULL,            -- manager, developer, researcher, etc.
    role TEXT NOT NULL,                  -- 'user' | 'assistant' | 'system'
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"