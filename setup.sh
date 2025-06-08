#!/bin/bash
echo "🔧 Starting setup..."

# Install MCP package
echo "📦 Installing Shopify MCP..."
npm install @shopify/dev-mcp

# Database setup with retry logic
echo "🗄️ Setting up database..."
for i in {1..5}; do
    if psql -U "$PGUSER" -d "$PGDATABASE" -c "
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
SELECT 'Database setup successful' AS status;
"; then
        echo "✅ Database setup completed"
        break
    else
        echo "⚠️ Database setup attempt $i failed, retrying..."
        sleep 2
    fi
done

echo "🔧 Setup complete"