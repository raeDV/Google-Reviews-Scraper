import csv
import requests
import click
import datetime
import re
import os


def calculate_date(time_seconds):
    review_time = datetime.datetime.fromtimestamp(time_seconds)
    formatted_date = review_time.strftime('%Y-%m-%d')
    return formatted_date


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
        print("Place ID: ", place_id)  # Moved this line up
        place_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
        print("Place url: ", place_url)  # Moved this line up
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

        # Fetch additional pages if available
        while 'next_page_token' in data:
            params['pagetoken'] = data['next_page_token']
            response = requests.get(url, params=params)
            data = response.json()

            if 'result' in data and 'reviews' in data['result']:
                reviews.extend(data['result']['reviews'])

        for idx, review in enumerate(reviews, start=1):
            rating = review.get('rating')
            comment = review.get('text')
            if rating and comment:
                author_name = review.get('author_name')
                time_seconds = review.get('time')
                date = calculate_date(time_seconds)
                extracted_reviews.append({
                    'id': idx,
                    'rating': rating,
                    'comment': comment.replace('\n', ' '),
                    'author_name': author_name,
                    'date': date
                })
        extracted_reviews = sorted(extracted_reviews, key=lambda x: x['id'])
        return extracted_reviews
    else:
        return []


def sanitize_comment(comment):
    # Remove line breaks within the comment
    comment = re.sub(r'\n+', ' ', comment)
    # Remove leading and trailing whitespaces
    comment = comment.strip()
    return comment


def format_filename(place):
    # Properly case the place name and remove spaces
    formatted_place = ''.join(place.title().split())
    # Combine the filename
    filename = f"{formatted_place}Reviews.csv"
    return filename


@click.command()
def scrape_reviews():
    while True:
        place = click.prompt('Enter a place name (or type "quit" to exit)', default='')
        if place.lower() == 'quit':
            break

        reviews = get_google_reviews(place)

        if reviews:
            # Sort reviews by ID in ascending order
            sorted_reviews = sorted(reviews, key=lambda x: x['id'])

            # Generate CSV data
            csv_data = 'id,rating,comment,author_name,date\n'
            for review in sorted_reviews:
                csv_data += f"{review['id']},{review['rating']},{review['comment']},{review['author_name']},{review['date']}\n"

            # Format the filename
            filename = format_filename(place)

            # Specify the folder path
            folder = 'output_data'

            # Create the folder if it doesn't exist
            os.makedirs(folder, exist_ok=True)

            # Save reviews to a CSV file in the specified folder
            full_path = os.path.join(folder, filename)
            with open(full_path, 'w', encoding='utf-8', newline='') as file:
                file.write(csv_data)

            print('Reviews have been successfully scraped, you could check it at', full_path, 'after you exit')
        else:
            print('No reviews found for the specified place.')


if __name__ == '__main__':
    scrape_reviews()
