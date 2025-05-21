from smolagents import tool
import pandas as pd
import os
from tools.memory_setup import get_agent_memory

DATA_PATH = "memories" 


@tool
def list_datasets() -> list:
    """
    List summaries of all datasets stored in memory.

    Returns:
        A list of summary strings.
    """
    memory = get_agent_memory()
    return [
        value for key, value in memory.store.items()
        if key.endswith("_summary")
    ]

