from flask import Flask, request, render_template
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import time
import random
import googlemaps

app = Flask(__name__)
app.config['DEBUG'] = True
# Please replace the 'Your_API_Key' with your real Google API Key
gmaps = googlemaps.Client(key='Your_API_Key')


def get_place_id(place_name):
    try:
        place_result = gmaps.places(place_name)
        if place_result and 'results' in place_result and place_result['results']:
            place_id = place_result['results'][0]['place_id']
            print("Place Name: ", place_name)  # Moved this line up
            print("Place ID: ", place_id)  # Moved this line up
            return place_id
        else:
            print(f"No place found for: {place_name}")
            return None
    except Exception as e:
        print(f"Error occurred while fetching place_id for: {place_name}")
        print(f"Exception: {e}")
        return None


def get_all_reviews(place_url):
    # Setup firefox options
    firefox_options = Options()
    # firefox_options.add_argument("--headless")

    # Set path to geckodriver as per your configuration, change it to your path accordingly
    webdriver_service = Service(r'D:\My Files\download\geckodriver.exe')

    # Choose Firefox Browser
    driver = webdriver.Firefox(service=webdriver_service, options=firefox_options)
    driver.get(place_url)

    # Add a delay for the page to load
    time.sleep(5)

    # Find the Reviews button and click it
    reviews_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//button[starts-with(@aria-label, "Reviews for") and @role="tab"]')))

    actions = ActionChains(driver)
    actions.move_to_element(reviews_button).perform()  # Move to the button
    time.sleep(2)  # Wait for a while
    reviews_button.click()  # Click the button

    # Add a delay for the reviews to load
    time.sleep(5)

    # Print page source after click
    print(driver.page_source)

    SCROLL_PAUSE_TIME = 2

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    page = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    reviews_div = page.find_all('div', class_='wiI7pd')
    reviews = []
    for review in reviews_div:
        try:
            author = review.find('div', class_='TSUbDb').text
            rating = review.find('span', class_='Fam1ne EBe2gf').get('aria-label')
            text = review.find('span', class_='jxjCjc').text
            reviews.append((author, rating, text))
        except Exception as e:
            print("Problem occurred while processing a review.")
            print(f"Exception: {e}")
            continue

    return reviews


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        place_name = request.form.get('place_name')
        place_id = get_place_id(place_name)
        if place_id:
            place_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
            print("Place url: ", place_url)  # Moved this line up
            try:
                scraped_reviews = get_all_reviews(place_url)
                return render_template('home.html', reviews=scraped_reviews, place=place_name)
            except Exception as e:
                return str(e)
    return render_template('home.html')


if __name__ == '__main__':
    app.run()
