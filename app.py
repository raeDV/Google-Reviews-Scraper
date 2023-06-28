import datetime
import time

import bcrypt
import requests
from flask import Flask, render_template, request
from flask import redirect, flash, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import NoResultFound, IntegrityError

from forms import LoginForm, RegisterForm, AccountForm
from models import DBUser, db, Reviews

app = Flask(__name__)
app.secret_key = 'scraper'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['USE_SESSION_FOR_NEXT'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///users.sqlite'
db.init_app(app)

API_KEY = 'AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU'


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


def calculate_time_description(time_seconds):
    review_time = datetime.datetime.fromtimestamp(time_seconds)
    return review_time.strftime('%Y-%m-%d')


def get_google_reviews(place):
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
    params = {
        'input': place,
        'inputtype': 'textquery',
        'fields': 'name,formatted_address,place_id',
        'key': API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'candidates' in data and len(data['candidates']) > 0:
        place_id = data['candidates'][0]['place_id']
        return fetch_all_reviews(place_id)
    else:
        return []


def fetch_all_reviews(place_id):
    reviews = []
    page_token = None
    while True:
        review_data, page_token = fetch_reviews(place_id, page_token)
        reviews.extend(review_data)
        if page_token is None:
            break
        time.sleep(2)  # Add delay before making the next request

    return reviews


def fetch_reviews(place_id, page_token=None):
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'fields': 'name,rating,reviews',
        'key': API_KEY,
        'pagetoken': page_token
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'result' in data and 'reviews' in data['result']:
        reviews = data['result']['reviews']
        extracted_reviews = []
        for review in reviews:
            rating = review.get('rating', None)
            comment = review.get('text', None)
            if rating and comment:
                author_name = review.get('author_name', None)
                time_seconds = review.get('time', None)
                time_description = calculate_time_description(time_seconds)
                extracted_reviews.append({
                    'rating': rating,
                    'comment': comment,
                    'author_name': author_name,
                    'time_description': time_description
                })

        next_page_token = data.get('next_page_token', None)
        return extracted_reviews, next_page_token
    else:
        return [], None


def save_reviews_to_database(user_id, place, reviews):
    existing_reviews = Reviews.query.filter_by(user_id=user_id, company=place).all()

    for review in reviews:
        # Check if the review already exists in the database
        if any(existing_review.comments == review['comment']
               for existing_review in existing_reviews):
            flash('Review already exists! Review not saved!')
        else:
            db_review = Reviews(
                user_id=user_id,
                company=place,
                rating=review['rating'],
                comments=review['comment'],
                author=review['author_name'],
                date=review['time_description']
            )
            db.session.add(db_review)
            flash('Reviews saved successfully.')
    db.session.commit()


@app.route('/save-reviews', methods=['POST'])
@login_required
def save_reviews():
    if request.method == 'POST':
        user_id = current_user.id  # Get the current user's ID
        place = request.form.get('place')  # Get the place name from the form
        reviews = get_google_reviews(place)  # Scrape reviews for the place
        save_reviews_to_database(user_id, place, reviews)  # Save the reviews to the database
    return redirect(url_for('home'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    reviews = []
    place = ''
    if request.method == 'POST':
        place = request.form.get('place')
        if place:
            reviews = get_google_reviews(place)
    return render_template('home.html', reviews=reviews, place=place)


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
    app.run()
