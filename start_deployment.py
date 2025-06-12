#!/usr/bin/env python3
"""
Replit entry-point:

1. Runs `setup.sh` to create / migrate the Postgres DB.
2. Starts the Flask app **in-process** so Replit can detect the open port.
"""

import os
import subprocess
import sys

from oauth_slack import app  # import AFTER packages are installed


def wait_for_database(max_attempts=30, delay=2) -> bool:
    """Wait for database to be available before proceeding"""
    import time
    import psycopg2

    print("🔍 Waiting for database to be available...")

    for attempt in range(max_attempts):
        try:
            # Try to connect to the database
            conn = psycopg2.connect(
                host=os.environ.get("PGHOST", "localhost"),
                database=os.environ.get("PGDATABASE", "replitdb"), 
                user=os.environ.get("PGUSER", "user"),
                password=os.environ.get("PGPASSWORD", "password")
            )

            # Test that we can actually query
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

            conn.close()
            print(f"✅ Database available after {attempt + 1} attempts")
            return True

        except Exception as e:
            print(f"⏳ Database not ready (attempt {attempt + 1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)

    print("❌ Database failed to become available")
    return False

def setup_database() -> None:
    # First wait for database to be available
    if not wait_for_database():
        print("⚠️ Proceeding without database verification")
        return

    try:
        subprocess.run(["sh", "setup.sh"], check=True)
        print("✅ Database setup completed")

        # Final verification that our schema is ready
        from memory_utils import get_db_connection
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'conversation_history'
            """)
            if cur.fetchone():
                print("✅ Database schema verified")
            else:
                print("⚠️ conversation_history table not found")
        conn.close()

    except subprocess.CalledProcessError as exc:
        print(f"⚠️  Database setup failed: {exc}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Database verification failed: {e}", file=sys.stderr)

def verify_mcp_installation() -> None:
    """Verify MCP server can be launched in deployment environment"""
    try:
        # Quick test to see if MCP is available
        result = subprocess.run(['npx', '@shopify/dev-mcp', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ MCP server available in deployment")
        else:
            print("⚠️ MCP server may not be fully functional")
    except Exception as e:
        print(f"⚠️ MCP verification failed: {e}")
        # Don't fail deployment for MCP issues


def main() -> None:
    print("🚀 Bootstrapping Prymal Agent Copilot deployment…")
    setup_database()
    verify_mcp_installation()

    # Validate environment before starting Flask
    from oauth_slack import _validate_env
    try:
        _validate_env()
        print("✅ Environment validation passed")
    except SystemExit:
        print("❌ Environment validation failed - continuing anyway for debugging")

    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Starting Flask on :{port}")

    # More robust Flask configuration for deployment
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=False, 
        use_reloader=False, 
        threaded=True,
        processes=1  # Ensure single process
    )


if __name__ == "__main__":
    main()