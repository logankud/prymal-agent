from smolagents import tool
import pandas as pd
import os
from tools.memory_setup import get_agent_memory

DATA_PATH = "memories" 

os.makedirs(DATA_PATH, exist_ok=True)


@tool
def load_dataset(name: str) -> pd.DataFrame:
    """
    Load a dataset from disk by name.

    Args:
        name: Identifier used when storing the dataset.

    Returns:
        The dataset as a Pandas DataFrame.
    """    
    memory = get_agent_memory()
    path = memory.recall(f"{name}_path")
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Dataset '{name}' not found in memory.")
    return pd.read_parquet(path)
