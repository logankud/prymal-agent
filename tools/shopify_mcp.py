from smolagents import tool
from mcp.shopify_client import ShopifyMCPClient

mcp = ShopifyMCPClient()

@tool
def search_shopify_docs(prompt: str,top_n:int) -> str:
    """
    Search Shopify developer docs using the MCP 'search_dev_docs' tool.

    Args:
        prompt (str): Natural-language question or keyword.
        top_n (int): Number of top results to return.

    Returns:
        str: Relevant doc content snippets.
    """
    result = mcp.call_tool("search_dev_docs", {"prompt": prompt})

    top_results = result["content"][:top_n]

    # Truncate each result to prevent massive log output
    truncated_results = []
    for r in top_results:
        text = r["text"]
        if len(text) > 500:  # Limit to 500 characters
            text = text[:500] + "... [truncated]"
        truncated_results.append(text)

    return "\n\n".join(truncated_results)


@tool
def introspect_shopify_schema(query: str, top_n: int) -> str:
    """
    Search the Shopify Admin GraphQL schema using a natural language query.
    Use this to understand which fields or types to query for.

    Args:
        query (str): Natural-language query to search the schema.
        top_n (int): Number of top results to return.

    Example: query = "order createdAt and lineItems"
    """

    result = mcp.call_tool("introspect_admin_schema", {"query": query})

    # Filter to only return the top_n results
    top_results = result["content"][:top_n]
    
    return "\n\n".join([r["text"] for r in top_results])


result = search_shopify_docs("fetch all orders from 2025-01-01 to 2025-01-10", 1)
print(result)