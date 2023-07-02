from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from sqlalchemy import text, inspect


db=SQLAlchemy()
DB_NAME='database.db'
def create_app():
    app= Flask(__name__)
    app.config['SECRET_KEY']="God bless me"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from allReviews.views import views
    from allReviews.auth import auth

    app.register_blueprint(views, url_prefix='/')

    app.register_blueprint(auth, url_prefix='/') #'/' means no prefix

    from allReviews.models import User,Review
    create_database(app, DB_NAME, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) #get the primary key by default
    return app


# def create_database(app, db_name, db):
#     if not path.exists('web/' + db_name):
#         with app.app_context():
#             db.create_all()
#         print(f'Created {db_name} Database!')


def create_database(app, db_name, db):
    if not path.exists('web/' + db_name):
        with app.app_context():
            db.create_all()

            # Check if the column exists
            inspector = inspect(db.engine)
            columns = inspector.get_columns('review')
            column_names = [column['name'] for column in columns]
            if 'user_id' not in column_names:
                # Modify the table by adding a new column
                db.session.execute(text("ALTER TABLE review ADD COLUMN user_id INTEGER"))
                db.session.commit()
                print("Added 'user_id' column to the 'review' table.")
            else:
                print("Column 'user_id' already exists in the 'review' table.")

        print(f'Created {db_name} Database!')




