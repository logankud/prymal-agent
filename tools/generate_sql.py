from smolagents import tool
from langchain_openai import ChatOpenAI
from memory_utils import get_dataframe_from_memory

llm = ChatOpenAI(temperature=0, model="gpt-4.1-mini")  # Or use your preferred LLM

@tool
def generate_sql(memory_key: str, table_name: str, user_question: str) -> str:
    """
    Generate a SQL query that answers the user's question using a table in the database.  The table must already exist, if not use the generate_postgres_ddl tool to create it first.  You must insert data from memory into the table first using the insert_df_to_postgres tool.

    Args:
        memory_key (str): Key to retrieve the dataframe from memory to infer schema.
        table_name (str): Name of the table the data is stored in.
        user_question (str): Natural language instruction from the user.

    Returns:
        str: A SQL query string.
    """
    df = get_dataframe_from_memory(memory_key)
    if df is None:
        return "❌ Error: Could not find dataset in memory."

    sample_schema = df.head(3).to_dict(orient="records")

    prompt = f"""
You are an assistant that writes SQL queries for Postgres. The user has stored their data in a table named "{table_name}".

Here are example rows (sampled from memory):
{sample_schema}

The user asked: "{user_question}"

Write the appropriate SQL query that will return a result answering their question.
Only return valid SQL. Do not explain.
    """

    response = llm.invoke(prompt)
    return response.content.strip()
