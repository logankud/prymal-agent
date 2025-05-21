from smolagents import tool
import pandas as pd
import os
from tools.memory_setup import get_agent_memory

DATA_PATH = "memories" 

os.makedirs(DATA_PATH, exist_ok=True)


@tool
def preview_dataset(name: str) -> str:
    """Return a summary of the first few rows + schema of a stored dataset.
    
    Args:
        name: The name of the dataset to preview.
    
    """
    df = load_dataset(name)
    preview = df.head().to_markdown()
    return f"Preview of {name}:\n{preview}"
