from smolagents import tool
import requests
from bs4 import BeautifulSoup

@tool
def scraper(url: str = "https://shopify.dev/docs/api/admin-graphql/2025-07/objects/Order") -> str:
    """
    Scrapes text content from the Shopify GraphQL Order API documentation page.

    Args:
        url (str): The Shopify API docs URL to scrape.

    Returns:
        str: Extracted plain text of the page.
    """
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")

    # Remove nav/sidebar
    for tag in soup(["nav", "aside", "script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text


content = scraper()

print(content)