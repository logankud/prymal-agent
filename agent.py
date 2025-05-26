import os
import json 
import yaml
from smolagents import CodeAgent, ToolCallingAgent, OpenAIServerModel
from tools.shopify_mcp import search_shopify_docs, introspect_shopify_schema
from tools import run_shopify_query
from tools.memory_setup import ChatHistory
from utils import build_prompt_with_memory
from models.huggingface import HFTextGenModel
from memory_utils import store_message

# Set your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")



# ----------------------------------------
# Initialize Agents
# ----------------------------------------


# Analyst Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/analyst_system_prompt.txt", "r") as f:
    ANALYST_SYSTEM_PROMPT = f.read()
    print(ANALYST_SYSTEM_PROMPT)

# Set model (use HF if testing)
MODEL = OpenAIServerModel(model_id="gpt-4.1-nano",
                          api_key=os.environ["OPENAI_API_KEY"])

# Instantiate agent
analyst_agent = ToolCallingAgent(name='Analyst',
                    model=MODEL,
                  description=ANALYST_SYSTEM_PROMPT,
                  # additional_authorized_imports=[
                  #     "pandas", 
                  #     "numpy", 
                  #     "datetime",
                  #     "os", 
                  #     "sys", 
                  #     "json"
                  # ],
                  tools=[
                      run_shopify_query,
                      search_shopify_docs, 
                    introspect_shopify_schema                
                  ])

# Manager Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/manager_system_prompt.txt", "r") as f:
    MANAGER_SYSTEM_PROMPT = f.read()
    print(MANAGER_SYSTEM_PROMPT)

# Set model (use HF if testing)
MODEL = OpenAIServerModel(model_id="gpt-4.1-nano",
                          api_key=os.environ["OPENAI_API_KEY"])

# Instantiate agent
manager_agent = CodeAgent(name='Manager',
                    model=MODEL,
                  description=MANAGER_SYSTEM_PROMPT,
                  # additional_authorized_imports=[
                  #     "pandas", 
                  #     "numpy", 
                  #     "datetime",
                  #     "os", 
                  #     "sys", 
                  #     "json"
                  # ],
                  tools=[],
                managed_agents=[analyst_agent]
                         )

def chat_loop():

    

    while True:
    
        user_input = input("\nUSER ▶ ")
        if user_input.lower() in {"exit", "quit"}:
            break
    
        # reply = run_agent_with_user_interjection(manager_agent, user_input)    
        reply = manager_agent.run(user_input)
    
        print("\nCOPILOT ▶", reply)
    
        # store agent memory steps locally for inspection:
        mem = manager_agent.memory.get_full_steps()
    
        print(f'mem: {mem}')
    
    

if __name__ == "__main__":
    chat_loop()
