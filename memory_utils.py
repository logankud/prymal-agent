
from tools.memory_setup import get_agent_memory
import pandas as pd
import psycopg2
import os
import json 



def get_db_connection():
    """
  Returns a new psycopg2 connection to the Replit-hosted Postgres database.
  """
    conn = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"),
                            database=os.environ.get("PGDATABASE", "replitdb"),
                            user=os.environ.get("PGUSER", "user"),
                            password=os.environ.get("PGPASSWORD", "password"))
    return conn


def get_dataframe_from_memory(key: str) -> pd.DataFrame:
    memory = get_agent_memory()
    data = memory.recall(key)
    if not data:
        raise ValueError(f"Memory key '{key}' not found.")
    try:
        df = pd.DataFrame(data)
        if df.empty:
            raise ValueError(f"Memory key '{key}' contains an empty dataset.")
        return df
    except Exception as e:
        raise ValueError(f"Failed to convert memory data to DataFrame: {e}")


def store_message(session_id: str, agent_name: str, role: str, message):
    """
    Stores a message in the conversation history table in postgres

    Args:
        session_id (str): The session ID
        agent_name (str): The name of the agent
        role (str): The role of the agent
        message: The message to store (any type, will be converted to string)

    """
    import json
    
    # Convert message to string regardless of input type
    if isinstance(message, dict):
        message_str = json.dumps(message)
    elif isinstance(message, (list, tuple, set)):
        message_str = json.dumps(list(message))
    else:
        message_str = str(message)

    # Connect to the database
    conn = get_db_connection()
    
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversation_history (session_id, agent_name, role, message)
                VALUES (%s, %s, %s, %s)
            """, (session_id, agent_name, role, message_str))

def get_recent_history(session_id: str, limit=20) -> list[dict]:
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT role, message FROM conversation_history
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (session_id, limit))
            return [{"role": r, "content": m} for r, m in reversed(cur.fetchall())]


def store_agent_step(session_id: str, agent_name: str, step_data: dict):
    """Store details of a smolagengts ActionStep in postgres"""
    
    # Connect to the database
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO agent_steps (
                        session_id,
                        agent_name,
                        step_number,
                        input,
                        output,
                        tool_calls,
                        observations,
                        error
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id,
                    agent_name,
                    step_data.get("step_number"),
                    json.dumps(step_data.get("input")),
                    json.dumps(step_data.get("output")),
                    json.dumps(step_data.get("tool_calls")),
                    json.dumps(step_data.get("observations")),
                    json.dumps(step_data.get("error")),
                ))
    finally:
        conn.close()
