
#!/bin/bash
set -e
echo "🔧 Starting comprehensive deployment setup..."

# 1. PYTHON DEPENDENCIES
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# 2. NPM DEPENDENCIES 
echo "📦 Installing Shopify MCP..."
npm install

# 3. DIRECTORY STRUCTURE
echo "📁 Creating required directories..."
mkdir -p ./slack_installations
mkdir -p ./slack_states
mkdir -p ./memories
chmod 755 ./slack_installations ./slack_states ./memories

# 4. ENVIRONMENT VALIDATION
echo "🔍 Validating environment variables..."
REQUIRED_VARS=(
    "FLASK_SECRET_KEY"
    "SLACK_CLIENT_ID" 
    "SLACK_CLIENT_SECRET"
    "SLACK_SIGNING_SECRET"
    "OPENAI_API_KEY"
    "PGHOST"
    "PGPORT"
    "PGDATABASE"
    "PGUSER"
    "PGPASSWORD"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
done
echo "✅ All required environment variables present"

# 5. DATABASE SETUP WITH COMPREHENSIVE CHECKS
echo "🗄️ Setting up database..."

# Wait for database server
echo "⏳ Waiting for database server..."
for i in {1..15}; do
    if pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" >/dev/null 2>&1; then
        echo "✅ Database server is ready"
        break
    else
        echo "⏳ Database server not ready, attempt $i/15..."
        sleep 2
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Database server failed to become ready"
        exit 1
    fi
done

# Test database connectivity with credentials
echo "🔐 Testing database connectivity..."
if ! psql -U "$PGUSER" -d "$PGDATABASE" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "❌ Cannot connect to database with provided credentials"
    exit 1
fi
echo "✅ Database connectivity verified"

# Create schema with comprehensive setup
echo "📊 Creating database schema..."
for i in {1..5}; do
    if psql -U "$PGUSER" -d "$PGDATABASE" -c "
-- Create conversation history table
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_session_created 
ON conversation_history(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_conversation_agent_role
ON conversation_history(agent_name, role);

-- Verify table exists and is accessible
INSERT INTO conversation_history (session_id, agent_name, role, message) 
VALUES ('setup_test', 'system', 'system', 'Database setup verification') 
ON CONFLICT DO NOTHING;

DELETE FROM conversation_history WHERE session_id = 'setup_test';

SELECT 'Database setup successful' AS status;
"; then
        echo "✅ Database schema created successfully"
        break
    else
        echo "⚠️ Database schema setup attempt $i failed, retrying in 3 seconds..."
        sleep 3
    fi
    if [ $i -eq 5 ]; then
        echo "❌ Database schema setup failed after 5 attempts"
        exit 1
    fi
done

# 6. MCP SERVER VERIFICATION
echo "🛠️ Verifying MCP server..."
if timeout 10 npx @shopify/dev-mcp --version >/dev/null 2>&1; then
    echo "✅ MCP server is functional"
else
    echo "⚠️ MCP server verification failed (non-critical)"
fi

# 7. SHOPIFY API TEST (if possible)
echo "🛍️ Testing Shopify connectivity..."
if [ -n "$SHOPIFY_ACCESS_TOKEN" ] && [ -n "$SHOPIFY_STORE_URL" ]; then
    echo "✅ Shopify credentials present"
else
    echo "⚠️ Shopify credentials not found (may be configured elsewhere)"
fi

# 8. OPENAI API TEST
echo "🤖 Testing OpenAI connectivity..."
if python3 -c "
import openai
import os
try:
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Quick test - don't use credits
    models = client.models.list()
    print('✅ OpenAI API accessible')
except Exception as e:
    print(f'⚠️ OpenAI API test failed: {e}')
    exit(1)
" 2>/dev/null; then
    echo "✅ OpenAI API connectivity verified"
else
    echo "❌ OpenAI API test failed"
    exit 1
fi

# 9. FINAL VERIFICATION
echo "🔍 Final verification..."
python3 -c "
import sys
sys.path.append('.')

try:
    # Test core imports
    from memory_utils import get_db_connection, store_message
    from agent import manager_agent
    from oauth_slack import app
    
    # Test database connection
    conn = get_db_connection()
    conn.close()
    
    print('✅ All core modules importable')
    print('✅ Database connection functional')
    
except Exception as e:
    print(f'❌ Core module test failed: {e}')
    sys.exit(1)
"

echo "🎉 Deployment setup completed successfully!"
echo "🚀 Ready for Flask app startup"
