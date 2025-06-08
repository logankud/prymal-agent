#!/usr/bin/env python3
import subprocess
import sys
import os

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

    # Start the main application
    start_slack_oauth()