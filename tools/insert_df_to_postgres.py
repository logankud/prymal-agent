from smolagents import tool
import pandas as pd
import psycopg2
import json
import os
from memory_utils import get_dataframe_from_memory, get_db_connection

@tool
def insert_df_to_postgres(memory_key: str, table_name: str) -> str:
    """
    Use this tool to insert rows from a memory-stored dataframe into the given Postgres table. The table must already exist, if not create table first

    Args:
        memory_key (str): The memory key where the dataframe is stored.
        table_name (str): The name of the Postgres table to insert into.

    Returns:
        str: Success or error message.
    """
    try:
        df = get_dataframe_from_memory(memory_key)
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert row by row
        for _, row in df.iterrows():
            serialized_row = row.apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
            columns = ', '.join(serialized_row.index)
            placeholders = ', '.join(['%s'] * len(serialized_row))
            values = tuple(serialized_row.values)

            insert_query = f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING;
            """
            cursor.execute(insert_query, values)

        conn.commit()
        return f"✅ Inserted {len(df)} rows into {table_name}"
    except Exception as e:
        return f"❌ Error inserting data.  Error: {str(e)}.  Check that the table exists and that the schema of the data matches the table being inserted into.  Insert query: {insert_query}.  Example record from the data: {df.head(1).to_dict(orient='records')}"
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
