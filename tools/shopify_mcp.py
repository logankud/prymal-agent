from smolagents import tool
from mcp.shopify_client import ShopifyMCPClient

mcp = ShopifyMCPClient()

@tool
def search_shopify_docs(prompt: str) -> str:
    """
    Search Shopify developer docs using the MCP 'search_dev_docs' tool.

    Args:
        prompt (str): Natural-language question or keyword.

    Returns:
        str: Relevant doc content snippets.
    """
    result = mcp.call_tool("search_dev_docs", {"prompt": prompt})
    return "\n\n".join([r["text"] for r in result["content"]])

@tool
def introspect_shopify_schema(prompt: str) -> str:
    """
    Search Shopify Admin GraphQL schema.

    Args:
        prompt (str): Search terms (e.g. 'product createdAt field').

    Returns:
        str: Relevant schema output.
    """
    result = mcp.call_tool("introspect_admin_schema", {"prompt": prompt})
    return "\n\n".join([r["text"] for r in result["content"]])

shopify_tools = [search_shopify_docs, introspect_shopify_schema]
