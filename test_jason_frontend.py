import requests
from flask import Flask, render_template, request
import datetime

app = Flask(__name__)


def calculate_time_description(time_seconds):
    review_time = datetime.datetime.fromtimestamp(time_seconds)
    return review_time.strftime('%Y-%m-%d')


def get_google_reviews(place):
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
    params = {
        'input': place,
        'inputtype': 'textquery',
        'fields': 'name,formatted_address,place_id',
        # Replace 'Your_API_Key' with your real google API key for testing
        'key': 'Your_API_Key'
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
        'key': 'Your_API_Key'
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
