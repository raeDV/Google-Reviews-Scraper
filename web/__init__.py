from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db=SQLAlchemy()
DB_NAME='database1.db'
def create_app():
    app= Flask(__name__)
    app.config['SECRET_KEY']="God bless me"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from web.views import views
    from web.auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/') #'/' means no prefix

    from web.models import User,Review
    create_database(app, DB_NAME, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) #get the primary key by default

    return app

def create_database(app, db_name, db):
    if not path.exists('web/' + db_name):
        with app.app_context():
            db.create_all()
        print(f'Created {db_name} Database!')





