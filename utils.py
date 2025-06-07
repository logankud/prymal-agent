from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from datetime import datetime
import psycopg2
from memory_utils import get_db_connection
from smolagents import ActionStep
from memory_utils import store_message



def analysis_validation(model):
    def validate_final_answer(answer: str, memory) -> bool:
        prompt = (
            f"The agent has produced the following answer:\n\n{answer}\n\n"
            "Please review this answer for the following criteria:\n"
            "- Did the analysis generate an answer or was an answer made up (or hardcoded) in order to explain how to acheive the answer?\n"
            "- Was the analysis thorough?\n"
            "- Was proper pagination used?\n"
            "- Was the full dataset necessary for this analysis obtained and used?\n"
            "- Were assumptions clearly stated?\n"
            "- Any errors or missing considerations?\n\n"
            "List your reasoning. If no answer was provided, or the criteria is not met, this is a failure.  At the end, reply with **PASS** or **FAIL**."
        )
        messages = [{"role": "user", "content": prompt}]
        response = model(messages)
        feedback = response.content.strip()

        print("Checklist feedback:", feedback)
        if "FAIL" in feedback:
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


