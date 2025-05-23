from smolagents import tool
from helium import go_to, click, scroll_down, find_all, Text, kill_browser, get_driver, start_chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import os

# Launch Chrome once and reuse it
def launch_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200x1000")
    options.binary_location = "/usr/bin/google-chrome"  # adjust if needed

    try:
        # Use WebDriverManager to ensure compatible driver
        start_chrome(headless=True, options=options)
        print("✅ Browser started successfully.")
    except Exception as e:
        print(f"❌ Failed to launch browser: {e}")


# Call once at import
launch_browser()

@tool
def go_to_url(url: str) -> str:
    """
    Navigates to the specified URL in the browser.

    Args:
        url (str): The full URL to navigate to, including http(s)://

    Returns:
        str: Confirmation message indicating navigation success.
    """
    go_to(url)
    return f"✅ Navigated to {url}"


@tool
def click_text(text: str) -> str:
    """
    Clicks on the first clickable element that matches the provided text.

    Args:
        text (str): The visible text on the button or link you want to click.

    Returns:
        str: Confirmation message indicating the element was clicked.
    """
    click(text)
    return f"✅ Clicked on text: {text}"


@tool
def scroll_down_viewport() -> str:
    """
    Scrolls down one full viewport in the browser.

    Returns:
        str: Confirmation message indicating scrolling action.
    """
    scroll_down(num_pixels=1000)
    return "✅ Scrolled down one viewport."


@tool
def get_page_text() -> str:
    """
    Extracts and returns all visible text from the current page.

    Returns:
        str: A string containing all visible text on the page, truncated to 4000 characters.
    """
    elements = find_all(Text)
    combined_text = "\n".join([e.web_element.text for e in elements if e.web_element.text.strip()])
    return combined_text[:4000]  # token-safe return


@tool
def close_browser() -> str:
    """
    Closes the current browser session.

    Returns:
        str: Confirmation message indicating the browser has been closed.
    """
    kill_browser()
    return "✅ Browser closed."
