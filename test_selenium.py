from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

# Setup firefox options
firefox_options = Options()
# firefox_options.add_argument("--headless")

# Set path to geckodriver as per your configuration
webdriver_service = Service(r'C:\Users\RAE\chromedriver_win32\chromedriver.exe')

# Choose Firefox Browser
driver = webdriver.Firefox(service=webdriver_service, options=firefox_options)
driver.get("http://www.google.com")
print(driver.title)
driver.quit()