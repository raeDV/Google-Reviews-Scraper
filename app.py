import csv
import os
import re
import time
from datetime import datetime, timedelta

import bcrypt
import googlemaps
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.exc import NoResultFound

from forms import LoginForm, RegisterForm, AccountForm
from models import db, DBUser, Reviews, create_all

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///users.sqlite'
app.config['DEBUG'] = True
db.init_app(app)
gmaps = googlemaps.Client(key='AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU')
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_if_env_var_not_set')

if not os.path.isfile("users.sqlite"):
    create_all(app)


class User(UserMixin):
    def __init__(self, username, email, phone, password=None):
        self.id = username
        self.email = email
        self.phone = phone
        self.password = password


# this is used by flask_login to get a user object for the current user
@login_manager.user_loader
def load_user(user_id):
    user = find_user(user_id)
    if user:
        db_user = DBUser.query.filter_by(username=user_id).first()
        user.password = db_user.password
    return user


def find_user(username):
    res = DBUser.query.filter_by(username=username).first()
    if res:
        user = User(res.username, res.email, res.phone, res.password)
    else:
        user = None
    return user


def relative_to_absolute_date(relative_date_str):
    # Current date
    now = datetime.now()

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

    # Subtract the appropriate amount of time
    if unit == "second":
        return (now - timedelta(seconds=number)).date()
    elif unit == "minute":
        return (now - timedelta(minutes=number)).date()
    elif unit == "hour":
        return (now - timedelta(hours=number)).date()
    elif unit == "day":
        return (now - timedelta(days=number)).date()
    elif unit == "week":
        return (now - timedelta(weeks=number)).date()
    elif unit == "month":
        return (now - timedelta(days=30 * number)).date()  # Approximate
    elif unit == "year":
        return (now - timedelta(days=365 * number)).date()  # Approximate
    return None


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
            reviewer = review.find_element(By.XPATH, ".//div[contains(@class, 'd4r55 ')]").text
            rating_html = review.find_element(By.XPATH, ".//span[contains(@class, 'kvMYJc')]").get_attribute(
                'innerHTML')
            rating_soup = BeautifulSoup(rating_html, 'html.parser')
            rating = len(
                rating_soup.find_all('img', {'src': '//maps.gstatic.com/consumer/images/icons/2x/ic_star_rate_14.png'}))
            # Get review time
            review_time_relative = review.find_element(By.XPATH, ".//span[contains(@class, 'rsqaWe')]").text
            review_time = relative_to_absolute_date(review_time_relative)  # Approximate

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
                'reviewer': reviewer,
                'rating': rating,
                'review_time': review_time,
                'review_content': review_content,
                'owner_response': owner_response
            })

            print(f"ID: {index}")
            print(f"Reviewer: {reviewer}")
            print(f"Rating: {rating}")
            print(f"Review Time: {review_time}")
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
    # Setup Chrome options
    chrome_options = Options()

    # Set path to chromedriver as per your configuration, change it to your path accordingly
    chrome_driver_path = r'C:\Users\RAE\chromedriver_win32\chromedriver.exe'

    # Choose Chrome Browser
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)
    driver.get(place_url)

    # Add a delay for the page to load
    time.sleep(6)

    # Find the Reviews button and click it
    try:
        reviews_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//button[starts-with(@aria-label, "Reviews for") and @role="tab"]')))
    except TimeoutException:
        print("No reviews to scrape. The location does not have any reviews.")
        driver.quit()
        return [], None, None

    actions = ActionChains(driver)
    actions.move_to_element(reviews_button).perform()
    reviews_button.click()
    time.sleep(3)

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
    time.sleep(3)

    reviews = scrape_all_reviews(driver, total_reviews)

    driver.quit()

    # If no reviews found...
    if len(reviews) == 0:
        return [], None, None
    return reviews, rating_overall, total_reviews


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    reviews = []
    place_name = ''
    place_id = ''
    place_url = ''
    error_message = ''
    overall_rating = ''
    total_reviews = ''

    if request.method == 'POST':
        place_name = request.form.get('place_name')
        place_id = get_place_id(place_name)
        if place_id:
            place_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
            print("Place url: ", place_url)
            reviews, overall_rating, total_reviews = get_all_reviews(place_url)
            flash("Scraping finished! Reviews saved to csv and database!")
            if not reviews and overall_rating is None and total_reviews is None:
                error_message = f"No reviews found for: {place_name}"

        else:
            error_message = f"No place found for: {place_name}"

        # Save to Database
        if len(reviews) > 0:
            for review in reviews:
                save_review(review)

        # Write to CSV
        try:
            if len(reviews) > 0:
                # Specify the folder path
                folder = 'output_data'

                # Create the folder if it doesn't exist
                os.makedirs(folder, exist_ok=True)

                filename = f"{place_name.replace(' ', '_')}_reviews.csv"
                filepath = os.path.join(folder, filename)

                with open(filepath, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Reviewer", "Rating", "Review Time", "Review Content", "Owner Response"])

                    for review in reviews:
                        writer.writerow([
                            review['id'],
                            review['reviewer'],
                            review['rating'],
                            review['review_time'],
                            review['review_content'],
                            review['owner_response']
                        ])

            print(f"Reviews exported to {filepath}")
        except Exception as e:
            print(f"Error while writing to file: {e}")

    return render_template('home.html', place_name=place_name, place_id=place_id, place_url=place_url,
                           error_message=error_message, overall_rating=overall_rating, total_reviews=total_reviews,
                           reviews=reviews)


def save_review(review_data):
    try:
        review = Reviews(
            reviewer=review_data['reviewer'],
            rating=review_data['rating'],
            review_time=review_data['review_time'],
            review_content=review_data['review_content'],
            owner_response=review_data['owner_response']
        )
        db.session.add(review)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error while saving review in the database: {e}")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user(form.username.data)
        # user could be None
        # passwords are kept in hashed form, using the bcrypt algorithm
        if user and bcrypt.checkpw(form.password.data.encode(), user.password.encode()):
            login_user(user)
            flash('Logged in successfully.')

            return redirect(url_for('home'))
        else:
            flash('Incorrect username/password!')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # flash(str(session))
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # check first if user already exists
        user = find_user(form.username.data)
        if not user:
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(form.password.data.encode(), salt)
            user = DBUser(username=form.username.data, email=form.email.data, phone=form.phone.data,
                          password=password.decode())
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully.')
            return redirect('/login')
        else:
            flash('This username already exists, choose another one')
    return render_template('register.html', form=form)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = AccountForm(obj=current_user)
    form.username.data = current_user.id  # Set the current username in the form

    if form.validate_on_submit():
        if bcrypt.checkpw(form.oldPassword.data.encode(), current_user.password.encode()):
            try:
                user = DBUser.query.filter_by(username=current_user.id).one()
                user.email = form.email.data
                user.phone = form.phone.data
                if form.newPassword.data:
                    password_hash = bcrypt.hashpw(form.newPassword.data.encode(), bcrypt.gensalt())
                    user.password = password_hash.decode()
                db.session.commit()  # Save the changes to the database
                flash('Your account has been updated!')
                return redirect(url_for('home'))
            except NoResultFound:
                flash('User not found in the database.')
        else:
            flash('Incorrect old password. Please try again.')

    return render_template('account.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)