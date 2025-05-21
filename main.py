# main.py

import os
import yaml
from smolagents.agents import PromptTemplates
from smolagents import CodeAgent, OpenAIServerModel
from smolagents.agents import ToolCallingAgent
from tools import get_orders, group_by_and_agg_data, describe_model, list_models, store_dataset, list_datasets, load_dataset, describe_tool, generate_postgres_ddl, execute_sql, generate_sql, insert_df_to_postgres
from tools.metrics import unique_count, total_count, sum_field, mean_field, top_values, group_sum, group_mean, group_count, average_order_value, percent_missing
from workflows.analysis_workflow import run_analysis_workflow
from models.huggingface import HFTextGenModel
from tools.memory_setup import ChatHistory, AgentMemory
from utils import build_prompt_with_memory, wipe_short_term_memory_postgres_tables


# Set your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")


USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"

# Set model (use HF if testing)
model = OpenAIServerModel(model_id="gpt-4.1", 
                          api_key=os.environ["OPENAI_API_KEY"])
# model = HFTextGenModel(model_name="Qwen/Qwen3-0.6B")


# Read in prompt templates yaml
with open("prompts/prompt_template.yaml", "r") as f:
    prompt_templates = PromptTemplates(**yaml.safe_load(f))


# Initialize the agent with the tools
code_agent = CodeAgent(
    tools=[],
    additional_authorized_imports=["pandas","numpy","datetime","os","sys","json"],
    model=model,
    description="Expert developer, who is to be used to write code to analyze data",
    name="code_agent"
)

# Initialize a ToolCallingAgent agent with the tools
shopify_agent = ToolCallingAgent(
    tools=[
        get_orders,
        # store_dataset,
        # list_datasets,
        # load_dataset,
        # describe_tool,
        generate_postgres_ddl,
        generate_sql,
        execute_sql,
        insert_df_to_postgres,
        
        # describe_model,
        # list_models,
        # unique_count, 
        # total_count, 
        # sum_field, 
        # mean_field, 
        # top_values, 
        # group_sum, 
        # group_mean, 
        # group_count, 
        # average_order_value, 
        # percent_missing
        # group_by_and_agg_data

        # run_analysis_workflow
        ],
    model=model,
    description="Shopify data expert, pulls data from shopify for you to analyze.",
    name="shopify_agent", 
    # managed_agents=[code_agent],
    prompt_templates=prompt_templates
    

)



# web_use_agent = ToolCallingAgent(
#     tools=[scraper],
#     model= OpenAIServerModel(model_id="computer_use_preview", 
#       api_key=os.environ["OPENAI_API_KEY"]))


# Example usage
if __name__ == "__main__":
    # user_query = "How do I create a new product using the Shopify API?"
    # doc_snippet = search_shopify_docs(user_query)
    # code = generate_shopify_code(doc_snippet, user_query)
    # print(code)

    while True:

        # Prompt the user for a query
        query = input("Ask the Prymal AI Copilot a question: ")
    
        if query.lower() in ["exit", "quit"]:
            print("Exiting the Prymal AI Copilot.")
            break
    
        # Build context-aware prompt
        prompt = build_prompt_with_memory(query, ChatHistory)
    
        # Run the agent
        response = shopify_agent.run(prompt)

        # wipe short-term memory (Postgres)
        wipe_short_term_memory_postgres_tables()
    
        ChatHistory.save_context({"input": query}, {"output": response})

# # Initialize the CodeAgent with your custom tool
# agent = ToolCallingAgent(
#     tools=[fetch_shopify_orders_tool],
#     model=model
# )

# # Prompt the user for a query
# query = input("Ask the Prymal AI Copilot a question: ")

# # Run the agent
# response = agent.run(query)

# # Output the response
# print("\nResponse:", response)