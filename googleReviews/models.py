from googleReviews import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text(), nullable=False)
    email = db.Column(db.Text(), nullable=False)
    phone = db.Column(db.Text())
    password = db.Column(db.Text(), nullable=False)
    reviews = db.relationship('Review', backref='user',lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    place_name = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review_time = db.Column(db.String(100), nullable=False)
    review_content = db.Column(db.Text, nullable=False)
    owner_response = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


