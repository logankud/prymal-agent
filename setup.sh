#!/bin/bash
echo "🔧 Starting setup..."

# Install MCP for both development and deployment
echo "📦 Installing Shopify MCP..."
npm install


# Database setup with retry logic
echo "🗄️ Setting up database..."

# First wait for database server to be ready
echo "⏳ Waiting for database server..."
for i in {1..10}; do
    if pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" >/dev/null 2>&1; then
        echo "✅ Database server is ready"
        break
    else
        echo "⏳ Database server not ready, attempt $i/10..."
        sleep 3
    fi
done

# Now attempt to create schema
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

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_conversation_session_created 
ON conversation_history(session_id, created_at);

SELECT 'Database setup successful' AS status;
"; then
        echo "✅ Database setup completed successfully"
        exit 0
    else
        echo "⚠️ Database setup attempt $i failed, retrying in 3 seconds..."
        sleep 3
    fi
done

echo "❌ Database setup failed after 5 attempts"
exit 1