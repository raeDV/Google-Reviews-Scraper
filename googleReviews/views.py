from flask import Blueprint,render_template,request,flash,redirect,url_for
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException,StaleElementReferenceException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta
from flask import flash
from googleReviews import db
import re
import time
import googlemaps
from flask_login import  login_required,  current_user
import csv
import os
from googleReviews.models import Review

views=Blueprint('views',__name__)
gmaps = googlemaps.Client(key='AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU')
views.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_if_env_var_not_set')

def relative_to_absolute_date(relative_date_str):
    # Look for number and unit
    match = re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year)[s]* ago', relative_date_str)

    if match is None:
        # handle "a month ago" or "an hour ago"
        match = re.search(r'(a|an)\s*(second|minute|hour|day|week|month|year)[s]* ago', relative_date_str)

        if match is None:
            return None
        else:
            number = 1  # "a" or "an" represents one unit
            unit = match.group(2)
    else:
        number = int(match.group(1))
        unit = match.group(2)

    # Calculate the appropriate timedelta
    if unit == "second":
        timedelta_value = timedelta(seconds=number)
    elif unit == "minute":
        timedelta_value = timedelta(minutes=number)
    elif unit == "hour":
        timedelta_value = timedelta(hours=number)
    elif unit == "day":
        timedelta_value = timedelta(days=number)
    elif unit == "week":
        timedelta_value = timedelta(weeks=number)
    elif unit == "month":
        timedelta_value = timedelta(days=30 * number)  # Approximate
    elif unit == "year":
        timedelta_value = timedelta(days=365 * number)  # Approximate

    # Calculate the absolute date
    now = datetime.now()
    absolute_date = now - timedelta_value
    return absolute_date.date()


def get_place_id(place_name):
    try:
        place_result = gmaps.places(place_name)
        if place_result and 'results' in place_result and place_result['results']:
            place_id = place_result['results'][0]['place_id']
            print("Place Name: ", place_name)
            print("Place ID: ", place_id)
            return place_id
        else:
            print(f"No place found for: {place_name}")
            return None
    except Exception as e:
        print(f"Error occurred while fetching place_id for: {place_name}")
        print(f"Exception: {e}")
        return None


def scrape_all_reviews(driver, total_reviews):
    reviews = []

    review_selector = "//div[contains(@class, 'jftiEf fontBodyMedium ')]"

    scraped_count = 0
    while scraped_count < total_reviews:
        current_reviews = driver.find_elements(By.XPATH, review_selector)
        if not current_reviews:
            print("No reviews found. Waiting for the reviews to load...")
            time.sleep(2)
            continue

        # Scroll page to load more reviews
        driver.execute_script('arguments[0].scrollIntoView(true);', current_reviews[-1])
        time.sleep(2)

        # Check if there are owner's responses and scroll to the end of them
        for review in current_reviews:
            try:
                owner_response_elem = review.find_element(By.XPATH, ".//span[text()='Response from the owner']"
                                                                    "/following::div[@class='wiI7pd'][1]")
                driver.execute_script('arguments[0].scrollIntoView(true);', owner_response_elem)
                time.sleep(1)
            except NoSuchElementException:
                # No owner response, continue to the next review
                continue

        new_reviews = driver.find_elements(By.XPATH, review_selector)
        scraped_count = len(new_reviews)
        print(f"{scraped_count}/{total_reviews} reviews scraped, in progress...")

    print(f"{scraped_count}/{total_reviews} reviews scraped, done.\n")

    # Parse each review
    for index, review in enumerate(new_reviews, start=1):
        try:
            username = review.find_element(By.XPATH, ".//div[contains(@class, 'd4r55 ')]").text
            rating_html = review.find_element(By.XPATH, ".//span[contains(@class, 'kvMYJc')]").get_attribute(
                'innerHTML')
            rating_soup = BeautifulSoup(rating_html, 'html.parser')
            rating = len(
                rating_soup.find_all('img', {'src': '//maps.gstatic.com/consumer/images/icons/2x/ic_star_rate_14.png'}))
            # Get review time
            review_time_relative = review.find_element(By.XPATH, ".//span[contains(@class, 'rsqaWe')]").text
            review_time_absolute = relative_to_absolute_date(review_time_relative)  # Approximate

            # Get review content
            try:
                review_content = review.find_element(By.XPATH, ".//span[contains(@class, 'wiI7pd')]").text
                try:
                    read_more_button = review.find_element(By.XPATH, ".//button[text()='More']")
                    if read_more_button:
                        # Click "More" to reveal full text
                        read_more_button.click()
                        review_content = review.find_element(By.XPATH, ".//span[contains(@class, 'wiI7pd')]").text
                except NoSuchElementException:
                    pass  # If no 'More' button is present
            except NoSuchElementException:
                review_content = "No review text provided."

            # Check for owner's response after review content
            try:
                owner_response = review.find_element(By.XPATH,
                                                     ".//span[text()='Response from the owner']"
                                                     "/following::div[@class='wiI7pd'][1]").text
            except NoSuchElementException:
                owner_response = None

            reviews.append({
                'id': index,
                'username': username,
                'rating': rating,
                'review_time': review_time_absolute,
                'review_content': review_content,
                'owner_response': owner_response
            })

            print(f"ID: {index}")
            print(f"Username: {username}")
            print(f"Rating: {rating}")
            print(f"Review Time: {review_time_absolute}")
            print(f"review_content: {review_content}")
            # if owner_response is not None:
            print(f"owner_response: {owner_response}")
            print("\n")  # line break

        except Exception as e:
            print("Problem occurred while processing a review.")
            print(f"Exception: {e}")
            continue

    return reviews



def get_all_reviews(place_url):
    # Setup  options
    chrome_options = ChromeOptions()

    chrome_driver_path = r'C:\chromedriver_win32\chromedriver.exe'
    driver = webdriver.Chrome( options=chrome_options)
    driver.get(place_url)

    # Add a delay for the page to load
    time.sleep(5)

    # Find the Reviews button and click it
    try:
        reviews_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[starts-with(@aria-label, "Reviews for") and @role="tab"]')))
    except TimeoutException:
        print("No reviews to scrape. The location does not have any reviews.")
        driver.quit()
        return [], None, None

    actions = ActionChains(driver)
    actions.move_to_element(reviews_button).perform()
    reviews_button.click()
    time.sleep(2)

    # Get overall rating after clicking the Reviews button
    try:
        rating_overall_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="fontDisplayLarge"]')))
        rating_overall = float(rating_overall_element.text)
        total_reviews_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="fontBodySmall" and contains(text(), "reviews")]'))
        )
        total_reviews = int(total_reviews_element.text.split()[0])
        print(f"Overall rating: {rating_overall}\n")
        print(f"Total reviews: {total_reviews}\n")
    except TimeoutException:
        print("Could not find the overall rating or total reviews number.")
        driver.quit()
        return [], None, None

    # Add a delay for the reviews to load
    time.sleep(5)

    reviews = scrape_all_reviews(driver, total_reviews)

    driver.quit()
    # If no reviews found...
    if len(reviews) == 0:
        return [], None, None
    return reviews, rating_overall, total_reviews


@views.context_processor
def inject_user():
    return dict(user=current_user)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    reviews = []
    place_name = ''
    place_id = ''
    place_url = ''
    error_message = ''
    overall_rating = ''
    total_reviews = ''
    flash("Please wait for the reviews to be scraped.", category="success")
    flash("The time it takes depends on how many reviews the place have.", category="success")
    flash("Please double check the place url to confirm it's the right place you want to check", category="success")
    if request.method == 'POST':
        place_name = request.form.get('place_name')
        place_id = get_place_id(place_name)
        if place_id:
            place_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
            print("Place url: ", place_url)
            reviews, overall_rating, total_reviews = get_all_reviews(place_url)
            flash("Scraping finished!")
            if not reviews and overall_rating is None and total_reviews is None:
                error_message = f"No reviews found for: {place_name}"

        else:
            error_message = f"No place found for: {place_name}"

        save_reviews(place_name, reviews)
        save_reviews_database(place_name, reviews)

    return render_template('home.html', place_name=place_name, place_id=place_id, place_url=place_url,
                           error_message=error_message, overall_rating=overall_rating, total_reviews=total_reviews,
                           reviews=reviews )

def save_reviews(place_name, reviews):
    try:
        if len(reviews) > 0:
            folder_path = "csv_files"
            os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
            # Save reviews to a CSV file in the specified folder
            filename = os.path.join(folder_path, f"{place_name}_reviews.csv")
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Id','User Name','Rating', 'Review Time','Review Content', 'Owner Response']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for review in reviews:
                    writer.writerow({
                        'Id': review['id'],
                        'User Name': review['username'],
                        "Rating": review['rating'],
                        'Review Time': review['review_time'],
                        'Review Content': review['review_content'],
                        'Owner Response': review['owner_response']
                    })
            print(f"Reviews for {place_name} saved to {filename}.")
    except Exception as e:
        print(f"Error while writing to file: {e}")


def save_reviews_database(place_name, reviews):
    # Get the latest review for the place, if it exists
    existing_reviews = Review.query.filter_by(place_name=place_name).all()
    for existing_review in existing_reviews:
        db.session.delete(existing_review)

    for review in reviews:
        id = review['id']
        username = review['username']
        rating = review['rating']
        review_time = review['review_time']
        review_content = review['review_content']
        owner_response = review['owner_response']

        existing_review = Review.query.filter_by(place_name=place_name).first()
        if existing_review:
            # Update the existing review with the new information
            existing_review.username = username
            existing_review.rating = rating
            existing_review.review_time = review_time
            existing_review.review_content = review_content
            existing_review.owner_response = owner_response
        else:
            # Create a new review
            new_review = Review(
                place_name=place_name,
                username=username,
                rating=rating,
                review_time=review_time,
                review_content=review_content,
                owner_response=owner_response,
                user_id = current_user.id
            )
            db.session.add(new_review)

    db.session.commit()
    print(f"Reviews for {place_name} saved to database.")



