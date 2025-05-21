from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from typing import Optional

# Import your tools
from tools.get_orders import get_orders
from tools.generate_postgres_ddl import generate_postgres_ddl
from tools.execute_sql import execute_sql
from tools.insert_df_to_postgres import insert_df_to_postgres
from tools.generate_sql import generate_sql
from tools.describe_model import describe_model

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# 1. Define Shared State Format
# -----------------------------
class ShopifyAnalysisState(BaseModel):
    intent: str
    start_date: str
    end_date: str
    memory_key: str = "shopify_order_data"
    table_name: str = "shopify_order_data"
    schema_name: str = "ShopifyOrder"
    schema_description: Optional[str] = None
    sql_query: Optional[str] = None
    result: Optional[str] = None

# -----------------------
# 2. Node Implementations
# -----------------------
def fetch_orders(state: ShopifyAnalysisState) -> ShopifyAnalysisState:
    logger.info("[🟦 fetch_orders]")
    get_orders(start_date=state.start_date, end_date=state.end_date)
    return state

def generate_and_execute_ddl(state: ShopifyAnalysisState) -> ShopifyAnalysisState:
    logger.info("[📄 generate_and_execute_ddl]")
    ddl = generate_postgres_ddl(memory_key=state.memory_key, table_name=state.table_name)
    ddl_cleaned = ddl.strip("```sql").strip("```").strip()
    execute_sql(ddl_cleaned)
    return state

def insert_orders_to_pg(state: ShopifyAnalysisState) -> ShopifyAnalysisState:
    logger.info("[📤 insert_orders_to_pg]")
    insert_df_to_postgres(memory_key=state.memory_key, table_name=state.table_name)
    return state

def describe_schema(state: ShopifyAnalysisState) -> ShopifyAnalysisState:
    logger.info("[🔍 describe_schema]")
    schema = describe_model(state.schema_name)
    return state.copy(update={"schema_description": schema})

def generate_sql_query(state: ShopifyAnalysisState) -> ShopifyAnalysisState:
    logger.info("[🧠 generate_sql_query]")
    query = generate_sql(
        memory_key=state.memory_key,
        table_name=state.table_name,
        user_question=state.intent
    )
    return state.copy(update={"sql_query": query})

def execute_query(state: ShopifyAnalysisState) -> ShopifyAnalysisState:
    logger.info("[🟢 execute_query]")
    result = execute_sql(state.sql_query)
    return state.copy(update={"result": result})

# ------------------
# 3. Build LangGraph
# ------------------
workflow = StateGraph(ShopifyAnalysisState)

workflow.add_node("fetch_orders", RunnableLambda(fetch_orders))
workflow.add_node("generate_and_execute_ddl", RunnableLambda(generate_and_execute_ddl))
workflow.add_node("insert_orders", RunnableLambda(insert_orders_to_pg))
workflow.add_node("describe_schema", RunnableLambda(describe_schema))
workflow.add_node("generate_sql", RunnableLambda(generate_sql_query))
workflow.add_node("execute_sql", RunnableLambda(execute_query))

workflow.set_entry_point("fetch_orders")
workflow.add_edge("fetch_orders", "generate_and_execute_ddl")
workflow.add_edge("generate_and_execute_ddl", "insert_orders")
workflow.add_edge("insert_orders", "describe_schema")
workflow.add_edge("describe_schema", "generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_edge("execute_sql", END)

analysis_workflow  = workflow.compile()
