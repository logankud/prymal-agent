import os
import yaml
from smolagents import CodeAgent, OpenAIServerModel
from tools.shopify_mcp import shopify_tools
from tools import run_shopify_query
from models.huggingface import HFTextGenModel

SYSTEM_PROMPT = (
    """You are Prymal's Shopify AI Copilot who helps make sure Prymal has facutal data for data-driven operations.  You have access to Shopify's MCP server to fetch Shopify Admin data  (ie. Orders, Products, etc.) for factual analysis and interpretation of Shopify data.  You are also able to write code to enhance this interaction.  """
)

# Set your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")


USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"

# Set model (use HF if testing)
model = OpenAIServerModel(model_id="gpt-4.1-mini", 
                          api_key=os.environ["OPENAI_API_KEY"])

def chat_loop():

    # Format tools
    tools = shopify_tools.append('shopify_tools'])

    # Instantiate agent
    agent = CodeAgent(
        model=model,
        description=SYSTEM_PROMPT,
        additional_authorized_imports=["pandas","numpy","datetime","os","sys","json","requests"],
        tools=tools
    )
    
    while True:
        user = input("\nUSER ▶ ")
        if user.lower() in {"exit", "quit"}:
            break
        reply = agent.run(user)
        print("\nCOPILOT ▶", reply)
    
if __name__ == "__main__":
    chat_loop()
