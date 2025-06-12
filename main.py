import os
import json 
import yaml
from smolagents import CodeAgent, ToolCallingAgent, OpenAIServerModel, InferenceClientModel
from tools.shopify_mcp import search_shopify_docs, introspect_shopify_schema
from tools import run_shopify_query
from utils import build_prompt_with_memory, analyst_validation, manager_validation
from models.huggingface import HFTextGenModel
from memory_utils import store_message, get_recent_history
from llm.huggingface_model import HFModel
from prompts.manager_prompt_template import manager_prompt_template
from agents import manager_agent, analyst_agent

# Set your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")


def chat_loop():
    while True:
        user_input = input("\nUSER ▶ ")

        store_message(session_id='test', agent_name='user', role='user', message=user_input)
        if user_input.lower() in {"exit", "quit"}:
            break

        # build prompt with memory
        recent_chat_history = get_recent_history(session_id='test', limit=10)
        # Construct the prompt
        recent_chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_chat_history])
        prompt = f"""Recent chat history: \n
                    {recent_chat_text} \n\n
                    User Input: \n
                    {user_input}
                    """

        # reply = run_agent_with_user_interjection(manager_agent, user_input)    
        reply = manager_agent.run(prompt)
        store_message(session_id='test', agent_name='Manager', role='agent', message=reply)

        print("\nCOPILOT ▶", reply)

        # get full steps completed by manager_agent
        mem = manager_agent.memory.get_full_steps()

if __name__ == "__main__":
    chat_loop()