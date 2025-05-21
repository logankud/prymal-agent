import os
import importlib
import inspect
from pydantic import BaseModel
from smolagents.tools import tool

@tool
def list_models() -> dict[str, str]:
    """
    Return a dictionary of available Pydantic models and their descriptions.
    The key is the class name and the value is its docstring (or a default message if missing).
    """
    model_info = {}

    models_dir = os.path.join(os.path.dirname(__file__), "../models")
    models_pkg = "models"

    for filename in os.listdir(models_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            full_module = f"{models_pkg}.{module_name}"

            try:
                module = importlib.import_module(full_module)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__module__ == full_module:
                        doc = inspect.getdoc(obj) or "No description available."
                        model_info[name] = doc
            except Exception as e:
                print(f"Error importing {full_module}: {e}")

    return dict(sorted(model_info.items()))
