import os
import sys
import json
from flask import Flask, request, jsonify

from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from agent import manager_agent
from memory_utils import store_message, get_recent_history

# ──────────────────────────────────────────────────────────────────────────────
# Flask app & basic config
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")  # dev fallback

# Slack OAuth config
client_id: str | None = os.getenv("SLACK_CLIENT_ID")
client_secret: str | None = os.getenv("SLACK_CLIENT_SECRET")
scopes = [
    "channels:history",
    "chat:write",
    "im:history",
    "im:write",
    "mpim:history",
    "mpim:write",
]

# Local, file-based stores (swap for DB-backed stores in prod)
installation_store = FileInstallationStore(base_dir="./slack_installations")
state_store = FileOAuthStateStore(expiration_seconds=600, base_dir="./slack_states")

authorize_url_generator = AuthorizeUrlGenerator(
    client_id=client_id,
    scopes=scopes,
    user_scopes=[],
)

signature_verifier = SignatureVerifier(os.getenv("SLACK_SIGNING_SECRET", ""))

# ──────────────────────────────────────────────────────────────────────────────
# Utility routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return "Prymal Agent Copilot is alive! 🎉", 200


@app.route("/health")
def health():
    return "OK", 200


# ──────────────────────────────────────────────────────────────────────────────
# OAuth flow
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/slack/install")
def oauth_start():
    state = state_store.issue()
    url = authorize_url_generator.generate(state=state)
    return (
        f'<a href="{url}"><img alt="Add to Slack" height="40" width="139" '
        f'src="https://platform.slack-edge.com/img/add_to_slack.png" '
        f'srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, '
        f'https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>'
    )


@app.route("/slack/oauth_redirect")
def oauth_callback():
    state = request.args.get("state")
    if not state or not state_store.consume(state):
        return "Invalid state parameter", 400

    code = request.args.get("code")
    if not code:
        return "Authorization code not found", 400

    client = WebClient()
    try:
        oauth_response = client.oauth_v2_access(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
        )
        installation_store.save(oauth_response)
        return "✅ Installation successful — you can now use the bot!"
    except Exception as exc:
        return f"OAuth failed: {exc}", 500


# ──────────────────────────────────────────────────────────────────────────────
# Slack events (messages, slash commands, …)
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/slack/events", methods=["POST"])
def slack_events():
    payload = request.get_json(force=True, silent=True) or {}

    # URL-verification challenge
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})

    # Signature check
    if not signature_verifier.is_valid_request(
        body=request.get_data(),
        timestamp=request.headers.get("X-Slack-Request-Timestamp"),
        signature=request.headers.get("X-Slack-Signature"),
    ):
        return "Invalid signature", 403

    event = payload.get("event", {})
    if event.get("type") == "message" and not event.get("bot_id"):
        team_id = payload.get("team_id")
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")

        installation = installation_store.find_installation(
            enterprise_id=payload.get("enterprise_id"), team_id=team_id
        )
        if not installation:
            return "Bot not installed", 404

        slack_client = WebClient(token=installation.bot_token)

        # Memory — store user msg
        session_id = f"slack_{team_id}_{channel}_{user}"
        store_message(session_id, agent_name="user", role="user", message=text)

        # Build prompt with recent history
        recent = get_recent_history(session_id, limit=10)
        history_txt = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
        prompt = (
            "Recent chat history:\n"
            f"{history_txt}\n\n"
            "User input:\n"
            f"{text}"
        )

        # Run agent & reply
        reply = manager_agent.run(prompt)
        slack_client.chat_postMessage(channel=channel, text=reply)
        store_message(session_id, agent_name="assistant", role="assistant", message=reply)

    return "", 200


# ──────────────────────────────────────────────────────────────────────────────
# Boot
# ──────────────────────────────────────────────────────────────────────────────
def _validate_env() -> None:
    required = [
        "FLASK_SECRET_KEY",
        "SLACK_CLIENT_ID",
        "SLACK_CLIENT_SECRET",
        "SLACK_SIGNING_SECRET",
    ]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _validate_env()

    # Ensure file-based stores have somewhere to write
    os.makedirs("./slack_installations", exist_ok=True)
    os.makedirs("./slack_states", exist_ok=True)

    port = int(os.getenv("PORT", 5000))
    print("🚀  Starting Flask on port", port)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
