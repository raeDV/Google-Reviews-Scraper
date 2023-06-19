from flask import Flask, request, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random

app = Flask(__name__)
app.config['DEBUG'] = True


def get_all_reviews(place_url):
    # Setup chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # Set path to chromedriver as per your configuration, change it to your path accordingly
    webdriver_service = Service(r'D:\My Files\download\chromedriver_win32\chromedriver.exe')

    # Choose Chrome Browser
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(place_url)

    while True:
        try:
            # Click on the 'More Reviews' button
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="More reviews"]'))
            )
            driver.execute_script("arguments[0].click();", button)
            # Wait for a random amount of time between 3 and 7 seconds
            time.sleep(random.randint(3, 7))
        except Exception as e:
            print(e)
            break

    page = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    reviews_div = page.find_all('div', class_='WMbnJ')
    reviews = []
    for review in reviews_div:
        try:
            author = review.find('div', class_='TSUbDb').text
            rating = review.find('span', class_='Fam1ne EBe2gf').get('aria-label')
            text = review.find('span', class_='jxjCjc').text
            reviews.append((author, rating, text))
        except Exception as e:
            print(e)
            continue

    return reviews


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        place_name = request.form.get('place_name')
        place_url = 'https://www.google.com/maps/place/' + place_name.replace(" ", "+")
        try:
            scraped_reviews = get_all_reviews(place_url)
            return render_template('index.html', reviews=scraped_reviews, place=place_name)
        except Exception as e:
            return str(e)
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
