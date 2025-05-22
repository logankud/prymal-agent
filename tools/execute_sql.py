from smolagents import tool
import psycopg2
import os
from memory_utils import get_db_connection
from tools.memory_setup import get_agent_memory

@tool
def execute_sql(sql: str) -> str:
    """
    Execute a SQL query on the agent's Postgres database.
    For SELECT, EXPLAIN, WITH, or RETURNING queries, results are stored in memory as 'latest_sql_result'.

    Args:
        sql (str): A SQL query to execute.

    Returns:
        str: Success message or error.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)

        lower_sql = sql.strip().lower()
        should_store_result = (
            lower_sql.startswith("select") or
            lower_sql.startswith("with") or
            lower_sql.startswith("explain") or
            " returning " in lower_sql
        )

        if should_store_result:
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]

            memory = get_agent_memory()
            memory.remember(key="latest_sql_result", value=result)

            return f"✅ Query successful. {len(result)} rows stored in memory as 'latest_sql_result'."

        conn.commit()
        return "✅ SQL executed successfully."

    except Exception as e:
        return f"❌ Error executing SQL: {str(e)}"

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
