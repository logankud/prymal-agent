# tools/group_by_and_agg_data.py

from typing import List, Dict, Union, Optional
from smolagents import tool
from collections import defaultdict
import statistics
from tools.memory_setup import get_agent_memory 

@tool
def group_by_and_agg_data(
    dataset_name: str,
    group_by: str,
    agg_field: str,
    agg_fn: str = "count"
) -> Dict[str, Union[int, float, str]]:
    """
    Group and aggregate a dataset stored in memory by a field.  Use this only if the answer to the user's query is not already in memory or returned from another tool.


    Args:
        dataset_name: Name of the dataset to retrieve from memory 
        group_by: Field to group by (e.g., 'sku').
        agg_field: Field to aggregate (e.g., 'quantity').
        agg_fn: Aggregation function ('count', 'sum', 'avg', 'max', 'min').

    Returns:
        Aggregation result by group key.
    """

    memory = get_agent_memory()
    data = memory.recall(dataset_name)
    if not data:
        return {"error": f"No dataset found in memory with name '{dataset_name}'."}

    grouped = defaultdict(list)
    for row in data:
        key = row.get(group_by)
        val = row.get(agg_field)
        if key is not None and val is not None:
            grouped[key].append(val)

    result = {}
    for key, values in grouped.items():
        try:
            if agg_fn == "count":
                result[key] = len(values)
            elif agg_fn == "sum":
                result[key] = sum(values)
            elif agg_fn == "avg":
                result[key] = round(statistics.mean(values), 2)
            elif agg_fn == "max":
                result[key] = max(values)
            elif agg_fn == "min":
                result[key] = min(values)
            else:
                result[key] = f"Unsupported aggregation: {agg_fn}"
        except Exception as e:
            result[key] = f"Error: {str(e)}"

    return {"dataset": dataset_name, "result": result}