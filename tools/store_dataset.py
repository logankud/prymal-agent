from smolagents import tool
import pandas as pd
import os
from tools.memory_setup import get_agent_memory

DATA_PATH = "memories"  # make sure this folder exists

os.makedirs(DATA_PATH, exist_ok=True)


@tool
def store_dataset(name: str, df: pd.DataFrame) -> str:
    """
    Store a dataset on disk and register its summary and schema in agent memory.

    Args:
        name: The identifier for the dataset (e.g. 'orders_jan_2025')
        df: The Pandas DataFrame to store

    Returns:
        A confirmation string including summary information.
    """
    # Save DataFrame to disk
    file_path = os.path.join(DATA_PATH, f"{name}.parquet")
    df.to_parquet(file_path, index=False)

    # Generate metadata
    schema = df.columns.tolist()
    summary = f"'{name}' has {len(df)} rows and columns: {', '.join(schema)}"

    # Save metadata to AgentMemory
    memory = get_agent_memory()
    memory.remember(f"{name}_path", file_path)
    memory.remember(f"{name}_schema", schema)
    memory.remember(f"{name}_summary", summary)

    return summary
