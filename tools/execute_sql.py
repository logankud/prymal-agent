from smolagents import tool
import psycopg2
import os
from memory_utils import get_db_connection

@tool
def execute_sql(sql: str) -> str:
    """
    Execute a SQL query on the agent's Postgres database.

    Args:
        sql (str): A SQL query to execute (SELECT, CREATE, INSERT, etc.)

    Returns:
        str: Query result or success/error message.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)

        if sql.strip().lower().startswith("select"):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
            return f"✅ Query successful. Result: {result}"

        conn.commit()
        return "✅ SQL executed successfully."

    except Exception as e:
        return f"❌ Error executing SQL: {str(e)}"

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()