
from tools.memory_setup import get_agent_memory
import pandas as pd
import psycopg2
import os


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

