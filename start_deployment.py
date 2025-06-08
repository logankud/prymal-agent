
#!/usr/bin/env python3
import subprocess
import time
import sys
import os

def start_phoenix():
    """Start Phoenix server in background"""
    try:
        phoenix_process = subprocess.Popen([
            "python", "-m", "phoenix.server.main", "serve"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ Phoenix server started")
        time.sleep(3)  # Give Phoenix time to start
        return phoenix_process
    except Exception as e:
        print(f"⚠️ Phoenix server failed to start: {e}")
        return None

def setup_database():
    """Run database setup"""
    try:
        subprocess.run(["sh", "setup.sh"], check=True)
        print("✅ Database setup completed")
    except Exception as e:
        print(f"⚠️ Database setup failed: {e}")

def start_slack_oauth():
    """Start the Slack OAuth server"""
    try:
        # Start the main application
        subprocess.run(["python", "oauth_slack.py"], check=True)
    except Exception as e:
        print(f"❌ Slack OAuth server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting deployment...")
    
    # Setup database first
    setup_database()
    
    # Start Phoenix (optional, won't fail if it doesn't work)
    phoenix_process = start_phoenix()
    
    # Start the main application
    start_slack_oauth()
