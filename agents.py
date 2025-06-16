import os
import json
import yaml
from smolagents import CodeAgent, ToolCallingAgent, OpenAIServerModel, InferenceClientModel, ActionStep
from tools.shopify_mcp import search_shopify_docs, introspect_shopify_schema
from tools import run_shopify_query
from utils import build_prompt_with_memory, analyst_validation, analyst_callback, intercept_manager_final_answer
from models.huggingface import HFTextGenModel
from memory_utils import store_message, get_recent_history
from llm.huggingface_model import HFModel
from prompts.manager_prompt_template import manager_prompt_template
from memory_utils import store_agent_step
import traceback


# Logging function to use as a step callback
def log_step(step, agent):
    print(f"\n=== Step {step.step_number} ===")

    # Build prompt input from memory
    try:
        prompt_msgs = agent.write_memory_to_messages()
        input_text = "\n".join(
            [f"{m['role']}: {m['content']}" for m in prompt_msgs])
        print("📥 LLM Prompt Messages:")
        for msg in prompt_msgs:
            print(f"  {msg['role']}: {msg['content']}")
    except Exception as e:
        input_text = "[Error capturing input]"
        print("📥 LLM Prompt: [Unavailable]", e)

    # Extract output
    output_text = getattr(step, "action_output", None)
    print("📤 LLM Output:\n", output_text)

    # Tool calls
    tool_calls = getattr(step, "tool_calls", None)
    if tool_calls:
        print("🔨 Tool Calls:", tool_calls)

    # Observations
    observations = getattr(step, "observations", None)
    if observations:
        print("🧾 Observations:", observations)

    # Error handling
    error_text = None
    if getattr(step, "error", None):
        try:
            error_text = str(step.error)
            print("❌ Error:", error_text)
        except Exception:
            error_text = "Unserializable error"
            print("❌ Error: [Unserializable]")

    # Store step in the DB using your existing schema
    try:
        store_agent_step(
            session_id=
            "test",  # Replace this with a dynamic session ID if needed
            agent_name=agent.name,
            step_data={
                "step_number": step.step_number,
                "input_text": input_text,
                "output_text": output_text,
                "tool_calls":
                [str(tc) for tc in tool_calls] if tool_calls else None,
                "observations": observations,
                "error": error_text,
            })
    except Exception as db_err:
        print("❌ Failed to store step in DB:", traceback.format_exc())


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
        # self.final_answer_checks = [analyst_validation(self.model)]


# Analyst Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/analyst_system_prompt.txt", "r") as f:
    ANALYST_SYSTEM_PROMPT = f.read()

# Set model (use HF if testing)
MODEL = OpenAIServerModel(model_id="gpt-4.1",
                          api_key=os.environ["OPENAI_API_KEY"])

# Instantiate analyst agent
analyst_agent = AnalystAgent(
    name='Analyst',
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
    tools=[run_shopify_query, search_shopify_docs, introspect_shopify_schema],
    step_callbacks=[log_step, analyst_callback],
    provide_run_summary=True  # provide summary of work done
)

# Manager Agent
# ----------------------------------------

# Read in system prompt text from prompts/researcher_system_prompt.txt
with open("prompts/manager_system_prompt.txt", "r") as f:
    MANAGER_SYSTEM_PROMPT = f.read()

# Set model
# -------

MODEL = OpenAIServerModel(
    model_id="gpt-4.1",  # OpenAI model
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
manager_agent = ManagerAgent(
    name='Manager',
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
    step_callbacks=[log_step]

    # final_answer_checks=True  # validates final answers from managed agents
)
