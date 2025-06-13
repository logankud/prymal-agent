
import os
import json 
import yaml
from smolagents import CodeAgent, ToolCallingAgent, OpenAIServerModel, InferenceClientModel
from tools.shopify_mcp import search_shopify_docs, introspect_shopify_schema
from tools import run_shopify_query
from utils import build_prompt_with_memory, analyst_validation, manager_validation, intercept_manager_final_answer
from models.huggingface import HFTextGenModel
from memory_utils import store_message, get_recent_history
from llm.huggingface_model import HFModel
from prompts.manager_prompt_template import manager_prompt_template

# Set your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# ----------------------------------------
# Initialize Agents
# ----------------------------------------

# Custom class for self-validating Analyst agents
class AnalystAgent(CodeAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.final_answer_checks = [analyst_validation(self.model)]

# Analyst Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/analyst_system_prompt.txt", "r") as f:
    ANALYST_SYSTEM_PROMPT = f.read()

# Set model (use HF if testing)
MODEL = OpenAIServerModel(model_id="gpt-4.1",
                          api_key=os.environ["OPENAI_API_KEY"])

# Instantiate analyst agent
analyst_agent = AnalystAgent(name='Analyst',
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
                   return_full_result=True,
                   provide_run_summary=True  # provide summary of work done
                 )

# Manager Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/manager_system_prompt.txt", "r") as f:
    MANAGER_SYSTEM_PROMPT = f.read()

# Set model 
# -------

MODEL = OpenAIServerModel(model_id="gpt-4.1",    # OpenAI model
                          api_key=os.environ["OPENAI_API_KEY"])

# MODEL = HFModel(model_id="deepseek-ai/DeepSeek-R1-0528")    # HuggingFace model

# MODEL = InferenceClientModel(
#     model_id="deepseek-ai/DeepSeek-R1-0528",
#     # provider="together",  
#     token=os.environ["HUGGING_FACE_TOKEN"]  
# )

# Custom class for self-validating Manager agents
class ManagerAgent(CodeAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.final_answer_checks = [manager_validation(self.model)]

# Instantiate manager agent
manager_agent = ManagerAgent(name='Manager',
                    model=MODEL,
                  description=MANAGER_SYSTEM_PROMPT,
                  # prompt_templates=manager_prompt_template,
                          
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
                  step_callbacks=[intercept_manager_final_answer]
                          
                  # final_answer_checks=True  # validates final answers from managed agents
                         )
