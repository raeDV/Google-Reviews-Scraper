from flask import Blueprint,render_template,request,flash,redirect,url_for
from flask_login import  login_required,  current_user
from . import db
import json
import requests
import datetime


views=Blueprint('views',__name__)

def calculate_time_description(time_seconds):
    current_time = datetime.datetime.now()
    review_time = datetime.datetime.fromtimestamp(time_seconds)
    time_diff = current_time - review_time
    days = time_diff.days
    if days > 0:
        return f"{days} days ago"
    else:
        seconds = time_diff.seconds
        hours = seconds // 3600
        minutes = (seconds // 60) % 60
        if hours > 0:
            return f"{hours} hours ago"
        elif minutes > 0:
            return f"{minutes} minutes ago"
        else:
            return "Just now"


def get_google_reviews(place):
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
    params = {
        'input': place,
        'inputtype': 'textquery',
        'fields': 'name,formatted_address,place_id',
        # Replace 'Your_API_Key' with your real google API key for testing
        'key': 'AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU'
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'candidates' in data and len(data['candidates']) > 0:
        place_id = data['candidates'][0]['place_id']
        return fetch_reviews(place_id)
    else:
        return []


def fetch_reviews(place_id):
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'fields': 'name,rating,reviews',
        # Replace 'Your_API_Key' with your real google API key for testing
        'key': 'AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU'
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
        return extracted_reviews
    else:
        return []

@views.context_processor
def inject_user():
    return dict(user=current_user)

@views.context_processor
def inject_user():
    return dict(user=current_user)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        place = request.form.get('place')
        if place:
            reviews = get_google_reviews(place)
            return render_template('home.html', reviews=reviews, place=place)

    return render_template('home.html',user=current_user)
