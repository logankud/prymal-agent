
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


def setup_database() -> None:
    try:
        subprocess.run(["sh", "setup.sh"], check=True)
        print("✅ Database setup completed")
    except subprocess.CalledProcessError as exc:
        print(f"⚠️  Database setup failed: {exc}", file=sys.stderr)

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

    port = int(os.getenv("PORT", 5000))
    print(f"🌐 Starting Flask on :{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
