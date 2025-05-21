from smolagents import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from memory_utils import get_dataframe_from_memory, get_db_connection

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

@tool
def generate_postgres_ddl(memory_key: str, table_name: str = "temp_table") -> str:
    """
    Use this tool to enerate a Postgres-compatible DDL statement to create a table based on data stored in agent memory.  This DDL statement will need to be executed to create the table in the database.

    Args:
        memory_key: The key in agent memory where the DataFrame is stored.
        table_name: Desired name for the generated Postgres table.

    Returns:
        A string containing the CREATE TABLE statement.
    """
    df = get_dataframe_from_memory(memory_key)
    schema_sample = df.head(5).to_dict(orient="records")

    prompt = PromptTemplate.from_template(
        "Given this JSON sample data:\n\n{sample}\n\nGenerate a Postgres DDL statement to create a table named {table_name} (if it doesn't already exist).  Return only the DDL statement, nothing else.  Make sure the column names match the JSON keys exactly. Only output the raw SQL, no other text."
    )
    chain = prompt | llm | StrOutputParser()
    ddl = chain.invoke({"sample": schema_sample, "table_name": table_name})

    # try:
    #     conn = get_db_connection()
    #     cursor = conn.cursor()
    #     cursor.execute(ddl)
    #     conn.commit()
    #     return f"Created table {table_name} successfully.  Schema: {ddl}"
    # except Exception as e:
    #     return f"❌ Error running DDL statement.  Error: {e}.  DDL: {ddl}"
    # finally:
    #     if 'cursor' in locals(): cursor.close()
    #     if 'conn' in locals(): conn.close()

    return f"DDL statement to execute: {ddl}"

