from smolagents import tool
from mcp.shopify_client import ShopifyMCPClient

mcp = ShopifyMCPClient()

@tool
def search_shopify_docs(query: str) -> str:
    """
    Search Shopify documentation for information on APIs, Polaris components, and other dev topics.

    Args:
        query (str): The search string to query Shopify documentation.

    Returns:
        str: A relevant snippet or result from the Shopify developer documentation.
    """
    return mcp.call_tool("search_dev_docs", {"query": query})["output"]

@tool
def introspect_shopify_admin_schema(query: str) -> str:
    """
    Introspect the Shopify Admin GraphQL schema to find available fields, types, or mutations.

    Args:
        query (str): The search string for schema exploration.

    Returns:
        str: Matching schema elements or descriptions from the Admin GraphQL API.
    """
    return mcp.call_tool("introspect_admin_schema", {"query": query})["output"]

# Register tools
shopify_tools = [search_shopify_docs, introspect_shopify_admin_schema]
