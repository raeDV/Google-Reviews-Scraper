from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class DBUser(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.Text())
    email = db.Column(db.Text(), nullable=False)
    phone = db.Column(db.Text())
    password = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return "<DBUser {}: {} {} >".format(self.username, self.email, self.phone)


class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reviewer = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Text(), nullable=False)
    comments = db.Column(db.Text(), nullable=False)
    owner_response = db.Column(db.Text, nullable=False)
    place_name = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return "<Reviews {}: {} {} >".format(self.user_id, self.place_name, self.rating)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


def create_all(app):
    with app.app_context():
        db.create_all()