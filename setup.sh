#!/bin/bash
echo "🔧 Starting setup..."

# Check if we're in deployment mode (skip MCP in deployment)
if [ "$REPL_DEPLOYMENT" != "1" ]; then
    echo "📦 Installing Shopify MCP..."
    npm install @shopify/dev-mcp
else
    echo "📦 Skipping MCP installation in deployment mode"
fi

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
        echo "✅ Database setup completed successfully"
        exit 0
    else
        echo "⚠️ Database setup attempt $i failed, retrying in 2 seconds..."
        sleep 2
    fi
done

echo "❌ Database setup failed after 5 attempts"
exit 1