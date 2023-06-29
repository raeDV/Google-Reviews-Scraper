import csv
import time

import googlemaps
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
app.config['DEBUG'] = True
# Please replace the 'Your_API_Key' with your real Google API Key
gmaps = googlemaps.Client(key='AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU')


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
    # Set up Chrome options
    chrome_options = ChromeOptions()
    # chrome_options.add_argument("--headless")

    # Set path to chromedriver as per your configuration, change it to your path accordingly
    webdriver_service = ChromeService(r'C:\Users\RAE\chromedriver_win32\chromedriver.exe')

    # Choose Chrome Browser
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    driver.get(place_url)

    # Add a delay for the page to load
    time.sleep(5)

    # Find the Reviews button and click it
    wait = WebDriverWait(driver, 10)
    reviews_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[starts-with(@aria-label, "Reviews for") and @role="tab"]')))
    reviews_button.click()

    # Add a delay for the reviews to load
    time.sleep(5)

    # Manually click and scroll to load more reviews
    print("Please manually click and scroll to load all reviews.")
    input("Press Enter when you have loaded all the reviews.")

    # Get the page source
    page = BeautifulSoup(driver.page_source, 'html.parser')

    reviews_div = page.find_all('div', class_='section-review')
    reviews = []
    for review in reviews_div:
        try:
            author = review.find('div', class_='section-review-title').text
            rating = review.find('span', class_='section-review-stars')['aria-label']
            text = review.find('span', class_='section-review-text').text
            reviews.append((author, rating, text))
        except Exception as e:
            print("Problem occurred while processing a review.")
            print(f"Exception: {e}")
            continue

    # Write reviews to CSV file
    with open('reviews.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Author', 'Rating', 'Text'])  # Write header row
        writer.writerows(reviews)  # Write review rows

    driver.quit()

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
