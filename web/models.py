from web import db # from . means from this package or from web (web is the package name)import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String(100), unique=True)
    userName = db.Column(db.String(100))
    password=db.Column(db.String(100))
    # searches=db.relationship('Search')




