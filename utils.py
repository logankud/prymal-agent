from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from datetime import datetime
import psycopg2
from memory_utils import get_db_connection
from smolagents import ActionStep
from memory_utils import store_message



def trigger_manager_review(step):
    if step.get("is_final_response"):
        step["review_prompt"] = (
            "Please review the Analyst's answer:\n\n"
            f"{step['content']}\n\n"
            "Checklist:\n"
            "- Was the analysis thorough?\n"
            "- Was proper pagination used?\n"
            "- Were assumptions clearly stated?\n"
            "- Any errors or missing considerations?"
        )
    return step

def analysis_validation(model):
    def validate_final_answer(answer: str, memory) -> bool:
        prompt = (
            f"The agent has produced the following answer:\n\n{answer}\n\n"
            "Please review this answer for the following criteria:\n"
            "- Was the analysis thorough?\n"
            "- Was proper pagination used?\n"
            "- Were assumptions clearly stated?\n"
            "- Any errors or missing considerations?\n\n"
            "List your reasoning. At the end, reply with **PASS** or **FAIL**."
        )
        messages = [{"role": "user", "content": prompt}]
        response = model(messages)
        feedback = response.content.strip()

        print("Checklist feedback:", feedback)
        if "FAIL" in feedback:
            raise Exception(feedback)
        return True

    return validate_final_answer
        



def detect_final_response(step: ActionStep, agent):
    """
    Intercepts the step execution of the Analyst managed agent and waits for input before continuing
    Only triggers when final_answer tool is actually being called.
    
    Args:
        step (ActionStep): The step to intercept (huggingface smolagents ActionStep type)
        agent (CodeAgent): The agent executing the step
    """
    
    # Only check if the current step contains an actual final_answer tool call
    if hasattr(step, 'tool_calls') and step.tool_calls:
        for tool_call in step.tool_calls:
            if hasattr(tool_call, 'function') and tool_call.function.name == 'final_answer':
                # Get user input for human-in-the-loop feedback
                user_feedback = input("INTERJECTION: Analyst has provided a final_answer. Please provide feedback: ")
                
                # Store the user feedback in memory thread
                store_message(session_id='test', agent_name='user', role='user', message=user_feedback)
                
                # You can add additional logic here to pause or modify the agent's behavior
                break
        
# def wipe_short_term_memory_postgres_tables():
#     """
#     Drops all Postgres tables in the 'public' schema

#     Args:
#         table_prefix: Prefix to match against table names. Defaults to 'shopify_orders_'.
#     """
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Fetch table names with the prefix
#         cursor.execute(f"""
#             SELECT tablename FROM pg_tables 
#             WHERE schemaname = 'public';
#         """)
#         tables = cursor.fetchall()

#         for (table_name,) in tables:
#             cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
#             print(f"🗑️ Dropped {table_name}")

#         conn.commit()
#     except Exception as e:
#         print(f"❌ Error wiping tables: {e}")
#     finally:
#         if 'cursor' in locals(): cursor.close()
#         if 'conn' in locals(): conn.close()


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


