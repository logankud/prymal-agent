import inspect
from smolagents import tool

@tool
def describe_tool(tool_name: str) -> str:
    """Return the argument names and types required for the given tool.
    
    Args:
        tool_name (str): The name of the tool to describe. Must be a tool that is available to the agent. """
    import tools
    tool_func = getattr(tools, tool_name, None)

    if not tool_func:
        return f"Tool '{tool_name}' not found."

    sig = inspect.signature(tool_func)
    params = [
        f"{name}: {param.annotation.__name__ if param.annotation != inspect._empty else 'Any'}"
        for name, param in sig.parameters.items()
    ]
    return f"{tool_name}({', '.join(params)})"