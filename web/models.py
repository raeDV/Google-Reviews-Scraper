from web import db # from . means from this package or from web (web is the package name)import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(100), unique=True)
    userName = db.Column(db.String(100))
    password=db.Column(db.String(100))
    # reviews = db.relationship('Review', backref='user',lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(100), nullable=False,unique=True)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    time_description = db.Column(db.String(100), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)

