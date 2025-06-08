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


    def main() -> None:
        print("🚀 Bootstrapping Prymal Agent Copilot deployment…")
        setup_database()

        port = int(os.getenv("PORT", 5000))
        print(f"🌐 Starting Flask on :{port}")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)


    if __name__ == "__main__":
        main()
