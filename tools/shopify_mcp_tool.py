from smolagents.tools import tool
from typing import Optional, Dict, Any
import requests
from datetime import datetime

SHOPIFY_MCP_ENDPOINT = "https://your-mcp-server.com/tool_call"

@tool
def shopify_mcp_tool(query: str) -> Dict[str, Any]:
    """
    Calls the Shopify MCP Server with a natural language query and returns the response.

    Args:
        query (str): The natural language query to send to the Shopify MCP Server.
    """
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(SHOPIFY_MCP_ENDPOINT, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {
            "error": str(e),
            "query": query,
            "timestamp": datetime.utcnow().isoformat()
        }
