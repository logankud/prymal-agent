# main.py

import os
import yaml
from smolagents.agents import PromptTemplates
from smolagents import CodeAgent, OpenAIServerModel
from smolagents.agents import ToolCallingAgent
from tools import get_orders, group_by_and_agg_data, describe_model, list_models, store_dataset, list_datasets, load_dataset, describe_tool, generate_postgres_ddl, execute_sql, generate_sql, insert_df_to_postgres
from tools.web_browsing import go_back, close_popups, search_item_ctrl_f
from tools.metrics import unique_count, total_count, sum_field, mean_field, top_values, group_sum, group_mean, group_count, average_order_value, percent_missing
from workflows.analysis_workflow import run_analysis_workflow
from models.huggingface import HFTextGenModel
from tools.memory_setup import ChatHistory, AgentMemory
from utils import build_prompt_with_memory, wipe_short_term_memory_postgres_tables

import helium
from dotenv import load_dotenv
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


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
    managed_agents=[code_agent],
    prompt_templates=prompt_templates
    

)













# Configure Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Initialize the browser
driver = helium.start_chrome(headless=True, options=chrome_options)

# Set up screenshot callback
def save_screenshot(memory_step: ActionStep, agent: CodeAgent) -> None:
    sleep(1.0)  # Let JavaScript animations happen before taking the screenshot
    driver = helium.get_driver()
    current_step = memory_step.step_number
    if driver is not None:
        for previous_memory_step in agent.memory.steps:  # Remove previous screenshots for lean processing
            if isinstance(previous_memory_step, ActionStep) and previous_memory_step.step_number <= current_step - 2:
                previous_memory_step.observations_images = None
        png_bytes = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(png_bytes))
        print(f"Captured a browser screenshot: {image.size} pixels")
        memory_step.observations_images = [image.copy()]  # Create a copy to ensure it persists

    # Update observations with current URL
    url_info = f"Current url: {driver.current_url}"
    memory_step.observations = (
        url_info if memory_step.observations is None else memory_step.observations + "\n" + url_info
    )

web_browser_agent = CodeAgent(
    tools=[web_browsing.go_back, web_browsing.close_popups, web_browsing.search_item_ctrl_f],
    model=model,
    additional_authorized_imports=["helium"],
    step_callbacks=[web_browing.save_screenshot],
    max_steps=20,
    verbosity_level=2,
)

# Import helium for the agent
web_browser_agent.python_executor("from helium import *", web_browser_agent.state)

helium_instructions = """
You can use helium to access websites. Don't bother about the helium driver, it's already managed.
We've already ran "from helium import *"
Then you can go to pages!
Code:
```py
go_to('github.com/trending')
```<end_code>

You can directly click clickable elements by inputting the text that appears on them.
Code:
```py
click("Top products")
```<end_code>

If it's a link:
Code:
```py
click(Link("Top products"))
```<end_code>

If you try to interact with an element and it's not found, you'll get a LookupError.
In general stop your action after each button click to see what happens on your screenshot.
Never try to login in a page.

To scroll up or down, use scroll_down or scroll_up with as an argument the number of pixels to scroll from.
Code:
```py
scroll_down(num_pixels=1200) # This will scroll one viewport down
```<end_code>

When you have pop-ups with a cross icon to close, don't try to click the close icon by finding its element or targeting an 'X' element (this most often fails).
Just use your built-in tool `close_popups` to close them:
Code:
```py
close_popups()
```<end_code>

You can use .exists() to check for the existence of an element. For example:
Code:
```py
if Text('Accept cookies?').exists():
    click('I accept')
```<end_code>
"""

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

        # # wipe short-term memory (Postgres)
        # wipe_short_term_memory_postgres_tables()

        




        
    
        # Run the agent
        # response = shopify_agent.run(prompt)
        response = web_browser_agent.run(prompt + helium_instructions)

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