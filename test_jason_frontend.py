import requests
import time
from flask import Flask, render_template, request
import datetime

app = Flask(__name__)

API_KEY = 'AIzaSyDMNj_iWsB2-HoZT_grWBjZyqD4KsmR0aU'


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
        time.sleep(2)  # Add a delay of 2 seconds before making the next request

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


@app.route('/', methods=['GET', 'POST'])
def index():
    reviews = []
    place = ''
    no_reviews = False
    if request.method == 'POST':
        place = request.form.get('place')
        if place:
            reviews = get_google_reviews(place)
            if not reviews:
                no_reviews = True
    return render_template('index.html', reviews=reviews, place=place, no_reviews=no_reviews)


if __name__ == '__main__':
    app.run(debug=True)
