
import os
from agents import manager_agent, set_agents_session_id
from memory_utils import store_message, get_recent_history

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")


def chat_loop():
    # Use a console session ID for main.py
    console_session_id = 'console_main'
    set_agents_session_id(console_session_id)
    
    while True:
        user_input = input("\nUSER ▶ ")

        if user_input.lower() in {"exit", "quit"}:
            break

        store_message(session_id=console_session_id, agent_name='user', role='user', message=user_input)

        # Retrieve recent history
        recent_chat_history = get_recent_history(session_id=console_session_id, limit=10)
        recent_chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_chat_history])
        prompt = f"""Recent chat history:\n{recent_chat_text}\n\nUser Input:\n{user_input}\n"""

        print("\n━━━━━━━━━━━━━━━━━━━━━━━ AGENT RUN START ━━━━━━━━━━━━━━━━━━━━━━━")

        # Use .run() to allow step_callbacks to handle logging
        reply = manager_agent.run(prompt)

        print("\n📘 Final Answer:")
        print(reply)

        store_message(session_id=console_session_id, agent_name='Manager', role='agent', message=reply)

        print("\n━━━━━━━━━━━━━━━━━━━━━━━ AGENT RUN END ━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    chat_loop()
