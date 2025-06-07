
import os
import json
from flask import Flask, request, jsonify, redirect, session, url_for
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.oauth import AuthorizeUrlGenerator, RedirectUriPageRenderer
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
from agent import manager_agent
from memory_utils import store_message, get_recent_history

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key-here")

# OAuth configuration
client_id = os.environ.get("SLACK_CLIENT_ID")
client_secret = os.environ.get("SLACK_CLIENT_SECRET")
scopes = ["channels:history", "chat:write", "im:history", "im:write", "mpim:history", "mpim:write"]

# OAuth stores
installation_store = FileInstallationStore(base_dir="./slack_installations")
state_store = FileOAuthStateStore(expiration_seconds=600, base_dir="./slack_states")

# Initialize components
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=client_id,
    scopes=scopes,
    user_scopes=[]
)

signature_verifier = SignatureVerifier(os.environ.get("SLACK_SIGNING_SECRET"))

@app.route("/slack/install", methods=["GET"])
def oauth_start():
    """Start the OAuth flow"""
    state = state_store.issue()
    url = authorize_url_generator.generate(state=state)
    return f'<a href="{url}"><img alt=""Add to Slack"" height="40" width="139" src="https://platform.slack-cdn.com/img/add_to_slack.png" srcset="https://platform.slack-cdn.com/img/add_to_slack.png 1x, https://platform.slack-cdn.com/img/add_to_slack@2x.png 2x" /></a>'

@app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_callback():
    """Handle OAuth callback"""
    # Verify state parameter
    state = request.args.get("state")
    if not state_store.consume(state):
        return "Invalid state parameter", 400
    
    # Exchange code for access token
    code = request.args.get("code")
    if not code:
        return "Authorization code not found", 400
    
    client = WebClient()
    try:
        oauth_response = client.oauth_v2_access(
            client_id=client_id,
            client_secret=client_secret,
            code=code
        )
        
        # Store installation
        installation_store.save(oauth_response)
        
        return "✅ Installation successful! You can now use the bot in your Slack workspace."
        
    except Exception as e:
        return f"OAuth error: {str(e)}", 500

@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events with OAuth"""
    # Verify request signature
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return "Invalid signature", 403
    
    data = request.json
    
    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return data.get("challenge")
    
    # Handle events
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        team_id = data.get("team_id")
        
        # Only respond to messages (not bot messages)
        if event.get("type") == "message" and not event.get("bot_id"):
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text", "")
            
            # Skip if no actual message
            if not text.strip():
                return "", 200
            
            try:
                # Get bot token from installation store
                installation = installation_store.find_installation(
                    enterprise_id=data.get("enterprise_id"),
                    team_id=team_id
                )
                
                if not installation:
                    return "Bot not installed", 404
                
                bot_token = installation.bot_token
                slack_client = WebClient(token=bot_token)
                
                # Process the message with your agent
                session_id = f"slack_{team_id}_{channel}_{user}"
                store_message(session_id=session_id, agent_name='user', role='user', message=text)
                
                # Get recent chat history
                recent_chat_history = get_recent_history(session_id=session_id, limit=10)
                recent_chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_chat_history])
                
                # Build prompt with memory
                prompt = f"""Recent chat history: \n
                            {recent_chat_text} \n\n
                            User Input: \n
                            {text}
                            """
                
                # Get response from agent
                reply = manager_agent.run(prompt)
                
                # Store agent response
                store_message(session_id=session_id, agent_name='Manager', role='agent', message=reply)
                
                # Convert reply to string if needed
                if isinstance(reply, dict):
                    reply_text = json.dumps(reply, indent=2)
                else:
                    reply_text = str(reply)
                
                # Send response back to Slack
                slack_client.chat_postMessage(
                    channel=channel,
                    text=reply_text
                )
                
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                if 'slack_client' in locals():
                    slack_client.chat_postMessage(
                        channel=channel,
                        text=f"Sorry, I encountered an error: {str(e)}"
                    )
    
    return "", 200

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

if __name__ == "__main__":
    # Create directories for OAuth stores
    os.makedirs("./slack_installations", exist_ok=True)
    os.makedirs("./slack_states", exist_ok=True)
    
    app.run(host="0.0.0.0", port=5000, debug=True)
