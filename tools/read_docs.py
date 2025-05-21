from smolagents import tool
from computers import LocalPlaywrightBrowser


def main(user_input=None):
    with LocalPlaywrightBrowser() as computer:


@tool
def read_docs(url: str) -> str:
    """Tool that cna 