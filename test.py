from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

# Navigate to a website
driver.get("https://google.com")

# Print the page title
print(driver.title)

# Close the browser
driver.quit()