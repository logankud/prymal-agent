import os
import json 
import yaml
from smolagents import CodeAgent, ToolCallingAgent, OpenAIServerModel, InferenceClientModel
from tools.shopify_mcp import search_shopify_docs, introspect_shopify_schema
from tools import run_shopify_query
from utils import build_prompt_with_memory, analysis_validation
from models.huggingface import HFTextGenModel
from memory_utils import store_message, get_recent_history
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from llm.huggingface_model import HFModel

register()
SmolagentsInstrumentor().instrument()

# Set your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")



# ----------------------------------------
# Initialize Agents
# ----------------------------------------


# Custom class for self-validating agents
class SelfValidatingCodeAgent(CodeAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.final_answer_checks = [analysis_validation(self.model)]


# Analyst Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/analyst_system_prompt.txt", "r") as f:
    ANALYST_SYSTEM_PROMPT = f.read()

# Set model (use HF if testing)
MODEL = OpenAIServerModel(model_id="gpt-4.1-mini",
                          api_key=os.environ["OPENAI_API_KEY"])


# Instantiate agent
analyst_agent = SelfValidatingCodeAgent(name='Analyst',
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
                  ],
                   # step_callbacks=[trigger_manager_review],
                   provide_run_summary=True  # provide summary of work done
                 )

# Manager Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/manager_system_prompt.txt", "r") as f:
    MANAGER_SYSTEM_PROMPT = f.read()

# Set model 
# -------

MODEL = OpenAIServerModel(model_id="gpt-4.1-mini",    # OpenAI model
                          api_key=os.environ["OPENAI_API_KEY"])

# MODEL = HFModel(model_id="deepseek-ai/DeepSeek-R1-0528")    # HuggingFace model

# MODEL = InferenceClientModel(
#     model_id="deepseek-ai/DeepSeek-R1-0528",
#     # provider="together",  
#     token=os.environ["HUGGING_FACE_TOKEN"]  
# )


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
                  managed_agents=[analyst_agent],
                  # final_answer_checks=True  # validates final answers from managed agents
                         )

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
