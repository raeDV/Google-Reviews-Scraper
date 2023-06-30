from web import create_app,db
from web.models import Review,User

app=create_app()

#if you want to check if the database has stored the scrapped date, uncomment this:

with app.app_context():
    db.create_all()
    with app.test_request_context():
        # Query the Review table
        reviews = Review.query.all()
        users=User.query.all()

    # Print the retrieved data
    print("Reviews:")
    for review in reviews:
        print("Place: " + review.place + "\n" + "Rating: " + str(review.rating) + "\n" + "Comments: " + review.comment
              + "\n" + "Author: " + review.author_name + "\n" + "Time: " + str(review.time_description) + "\n")
    print("Users:")
    for user in users:
        print("Username: " + user.userName + ", Email: " + user.email)


if __name__=='__main__':
    app.run(debug=True)