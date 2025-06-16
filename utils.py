from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from datetime import datetime
import psycopg2
from memory_utils import get_db_connection
from smolagents import ActionStep, MultiStepAgent
from memory_utils import store_message
import json

def intercept_manager_final_answer(memory_step, agent=None):
    """Intercept the final answer from the agent and extract the concise version key"""

    print("MEMORY STEP: ", memory_step)
    print("AGENT: ", agent)
    
    # When the agent emits a final answer
    if memory_step.action_output is not None and hasattr(agent, "name") and agent.name == "Manager":
        # action_output could be a dict or string
        output = memory_step.action_output
        
        # Try to parse if it's a string
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError:
                print("Warning: Final output not in JSON format")
                return

        if isinstance(output, dict):
            concise = output.get("1. Task outcome (short version)")
            if concise:
                print("Extracted concise answer:", concise)
                memory_step.action_output = concise


def analyst_callback(step: ActionStep, agent: MultiStepAgent):
    """
    Catch the Manger agent's final answer and validate it with the Agent's LLM model for completness
    """

    # Only act on the final answer step
    if not getattr(step, "is_final_answer", False):
        return

    final_answer = step.action_output

    # Collect full trace of agent's steps
    all_steps = agent.memory.get_full_steps()
    trace_str = "\n".join(
        f"Step {s['step_number']}:\n"
        f"Thoughts: {s.get('thoughts', '')}\n"
        f"Code:\n{s.get('code', '')}\n"
        f"Observations: {s.get('observations', '')}\n"
        for s in all_steps
    )

    # Validation prompt
    prompt = f"""
The agent has produced the following final answer:

```
{final_answer}
```

Here is the full trace of steps taken by the agent:

```
{trace_str}
```

You are a critical reviewer responsible for validating the trustworthiness of an Analyst Agent’s final answer.

Please answer the following checklist strictly. Use ✅ Yes / ❌ No / 🤔 Unclear for each, and include a short justification.

1. Does the final answer include executable Python code used to perform the analysis or extract the data?
2. If API calls were required, does the code include pagination logic (e.g., loops, cursors, or query limits)?
3. Does the answer mention what data source(s) were used and how they were accessed?
4. Does the answer indicate that the result was computed or derived — rather than guessed or assumed?
5. If data was unavailable or insufficient, does the answer clearly state this and explain why?
6. Are caveats or assumptions listed, especially when working with incomplete or uncertain data?
7. Is the "short version" answer consistent with the detailed explanation?
8. Overall, would a domain expert trust this answer based on the reasoning and evidence provided?

List your reasoning. If the answer is insufficient or untrustworthy, reply with **FAIL**. Otherwise, reply with **PASS**.
"""

    response = agent.model([{"role": "user", "content": prompt}])
    verdict = response.content.strip()

    if "**FAIL**" in verdict or "FAIL" in verdict:
        raise Exception(f"Validation failed:\n{verdict}")

    print("Validation passed.")
    return True


   

def analyst_validation(model):
    def validate_final_answer(answer: str, memory) -> bool:
        """Validate that the analysis done by the ANalyst agent was legitimate and trustworthy."""

        # Serialize memory steps
        steps = memory.get_full_steps()
        codes = [step.get("code") for step in steps if step.get("code")]
        code_str = "\n\n".join(codes)


        prompt = (
            f"""You are a critical reviewer responsible for validating the trustworthiness of an Analyst Agent’s final answer & approach to obtaining that answer.\n
            
            The agent has produced the following answer:\n\n{answer}\n\n
            Here is all the code it executed:\n{code_str}\n
                
    
    Below is a JSON-formatted response from the Analyst Agent. You must answer the following questions *based solely on the content of the answer*. Be strict — if the answer does not provide clear evidence for something, mark it as a failure.\n\n
    
    For each question below, respond with:\n
    - ✅ Yes \n
    - ❌ No \n
    - 🤔 Unclear \n
    
    Then include a short justification per question. \n\n
    
    
    Questions: \n
    1. Does the final answer include executable Python code used to perform the analysis or extract the data? \n
    2. If API calls were required, does the code include pagination logic (e.g., loops, cursors, or query limits)? \n
    3. Does the answer mention what data source(s) were used and how they were accessed? \n
    4. Does the answer indicate that the result was computed or derived — rather than guessed or assumed? \n
    5. If data was unavailable or insufficient, does the answer clearly state this and explain why? \n
    6. Are caveats or assumptions listed, especially when working with incomplete or uncertain data? \n
    7. Is the "short version" answer consistent with the detailed explanation? \n
    8. Overall, would a domain expert trust this answer based on the reasoning and evidence provided? \n\n
    
    ---
            List your reasoning. If no answer was provided, or the criteria is not met, this is a failure.  At the end, reply with **PASS** or **FAIL**."""
        )
        messages = [{"role": "user", "content": prompt}]
        response = model(messages)
        feedback = response.content.strip()

        print("Checklist feedback:", feedback)
        if "**FAIL**" in feedback:
            raise Exception(feedback)
        return True

    return validate_final_answer
        

def get_role(msg):
    if isinstance(msg, HumanMessage):
        return "User"
    elif isinstance(msg, AIMessage):
        return "Assistant"
    else:
        return "System"


def build_prompt_with_memory(user_input: str,
                             memory: ConversationBufferMemory) -> str:
    history = memory.load_memory_variables({})["chat_history"]
    if isinstance(history, list):
        # If return_messages=True, convert messages to string
        history_text = "\n".join(
            [f"{get_role(msg)}: {msg.content}" for msg in history])
    else:
        history_text = history
    return f"{history_text}\n\nUser: {user_input}"


def format_shopify_order(raw_order: dict) -> dict:
    """Flattens nested Shopify GraphQL order format to match the Pydantic schema with snake_case keys."""

    formatted_order = {
        "id": raw_order["id"],
        "name": raw_order["name"],
        "created_at_ts": raw_order["createdAt"],
        "updated_at_ts": raw_order["updatedAt"],
        "created_at_date": str(
            datetime.fromisoformat(raw_order["createdAt"].replace("Z", "+00:00")).date()
        ),
        "updated_at_date": str(
            datetime.fromisoformat(raw_order["updatedAt"].replace("Z", "+00:00")).date()
        ),
        "email": raw_order.get("email"),
        "customer_email": raw_order.get("customer", {}).get("email"),
        "original_total": float(
            raw_order.get("originalTotalPriceSet", {})
            .get("shopMoney", {})
            .get("amount", 0)
        ),
        "current_total": float(
            raw_order.get("currentTotalPriceSet", {})
            .get("shopMoney", {})
            .get("amount", 0)
        ),
        "line_items": [
            {
                "name": li["node"]["name"],
                "quantity": li["node"]["quantity"],
                "sku": li["node"].get("sku"),
                "amount": float(li["node"]["originalTotalSet"]["shopMoney"]["amount"]),
            }
            for li in raw_order.get("lineItems", {}).get("edges", [])
        ],
    }

    return formatted_order

def describe_model(class_name: str):
    """
    Describe the schema of a Pydantic model class by name, which represents the schema of a dataset stored in memory.

    Args:
        class_name (str): The class name of the Pydantic model

    Returns:
        dict: Field names, types, and descriptions
    """
    try:
        model_class = getattr(models, class_name)
        if not issubclass(model_class, BaseModel):
            return {"error": f"{class_name} is not a Pydantic model."}
    except AttributeError:
        return {"error": f"No model found with name '{class_name}'."}

    description = {}
    for name, field in model_class.model_fields.items():  
        description[name] = {
            "type": str(field.annotation),
            "description": field.description or "N/A"
        }

    return {
        "model": class_name,
        "fields": description
    }


