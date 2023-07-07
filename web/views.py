from flask import Blueprint,render_template,request,flash,redirect,url_for
from flask_login import  login_required,  current_user
from web import db
import json
import requests
import datetime
import csv
import os
from web.models import Review

views=Blueprint('views',__name__)


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
        reviews = fetch_reviews(place_id, place)
        result = {
            'place_id': place_id,
            'reviews': reviews
        }
        return result
    else:
        return []


def fetch_reviews(place_id,place):
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
        return place,[]


@views.context_processor
def inject_user():
    return dict(user=current_user)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    reviews = []
    place = ''
    no_reviews = False
    if request.method == 'POST':
        place = request.form.get('place')
        if place:
            reviews = get_google_reviews(place)
            if reviews:
                save_reviews(place, reviews['reviews'])
                save_reviews_database(place, reviews['reviews'])
                return render_template('home.html', reviews=reviews['reviews'], place=place)
            else:
                no_reviews = True
                flash("We found no reviews for this place, please check the place and try again", category='error')
    return render_template('home.html', user=current_user)


#save to csv file
def save_reviews(place, reviews):
    folder_path = "csv_files"
    os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
    # Save reviews to a CSV file in the specified folder
    filename = os.path.join(folder_path, f"{place}_reviews.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Rating', 'Comment', 'Author', 'Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for review in reviews:
            writer.writerow({
                'Rating': review['rating'],
                'Comment': review['comment'],
                'Author': review['author_name'],
                'Time': review['time_description']
            })
    print(f"Reviews for {place} saved to {filename}.")


#save to database
def save_reviews_database(place, reviews):
    # Get the latest review for the place, if it exists
    existing_reviews = Review.query.filter_by(place=place).all()
    for existing_review in existing_reviews:
        db.session.delete(existing_review)

    for review in reviews:

        rating = review['rating']
        comment = review['comment']
        author_name = review['author_name']
        time_description = review['time_description']

        existing_review = Review.query.filter_by(place=place).first()
        if existing_review:
            # Update the existing review with the new information
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.author_name = author_name
            existing_review.time_description = time_description
        else:
            # Create a new review
            new_review = Review(
                place=place,
                rating=rating,
                comment=comment,
                author_name=author_name,
                time_description=time_description
            )
            db.session.add(new_review)

        # Save the review to the database
        # new_review = Review(place=place, rating=rating, comment=comment, author_name=author_name,
        #                     time_description=time_description)
        # db.session.add(new_review)
    db.session.commit()


