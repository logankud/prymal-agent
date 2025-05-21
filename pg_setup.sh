#!/bin/bash
set -e

# Load environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Required ENV vars
DB_NAME="agent_memory"
DB_HOST="${PGHOST}"        
DB_PORT="${PGPORT}"
AGENT_USER="agent_user"
AGENT_PW="${AGENT_USER_PW}"               

if [ -z "$AGENT_PW" ] || [ -z "$DB_USER" ]; then
  echo "❌ Error: Missing required environment variables: AGENT_USER_PW or DB_USER"
  exit 1
fi

echo "⚙️ Connecting to Neon Postgres and setting up agent permissions..."

psql "sslmode=require host=$DB_HOST port=$DB_PORT user=$DB_USER dbname=$DB_NAME" <<EOF

-- 1. Create agent_user
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${AGENT_USER}') THEN
    CREATE ROLE ${AGENT_USER} LOGIN PASSWORD '${AGENT_PW}';
  END IF;
END
\$\$;

-- 2. Set up schema and permissions
CREATE SCHEMA IF NOT EXISTS agent_memory AUTHORIZATION ${AGENT_USER};

GRANT USAGE ON SCHEMA agent_memory TO ${AGENT_USER};
GRANT CREATE, TEMP ON DATABASE ${DB_NAME} TO ${AGENT_USER};
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA agent_memory TO ${AGENT_USER};

ALTER DEFAULT PRIVILEGES IN SCHEMA agent_memory
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${AGENT_USER};

EOF

echo "✅ Done: Agent role and schema set up in Neon DB."
