import re
import bcrypt
from flask import Blueprint, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import NoResultFound, IntegrityError
from googleReviews.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from googleReviews import db
from flask_login import login_user, login_required, logout_user, current_user
from googleReviews.forms import LoginForm, RegisterForm, AccountForm


auth=Blueprint('auth',__name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # user = find_user(form.username.data)
        user = User.query.filter_by(username=form.username.data).first()
        # user could be None
        # passwords are kept in hashed form, using the bcrypt algorithm
        if user and bcrypt.checkpw(form.password.data.encode(), user.password.encode()):
            login_user(user)
            flash('Logged in successfully.')

            return redirect(url_for('views.home'))
        else:
            flash('Incorrect username/password!')
    return render_template('login.html', form=form,user=current_user)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Thank you for using our service!')
    return redirect(url_for('auth.login'))



@auth.route("/register",methods=['POST','GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # check first if user already exists
        # user = find_user(form.username.data)
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(form.password.data.encode(), salt)
            user = User(username=form.username.data, email=form.email.data, phone=form.phone.data,
                          password=password.decode())
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash('Registered successfully.')
            return redirect(url_for('auth.login'))
            # return redirect('/login')
        else:
            flash('This username already exists, choose another one')
    return render_template('register.html', form=form, user=current_user)


@auth.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = AccountForm(obj=current_user)
    # form.username.data = current_user.id  # Set the current username in the form
    form.username.data = current_user.username  # Set the current username in the form

    if form.validate_on_submit():
        if bcrypt.checkpw(form.oldPassword.data.encode(), current_user.password.encode()):
            try:
                user = User.query.filter_by(username=current_user.username).one()
                user.email = form.email.data
                user.phone = form.phone.data
                if form.newPassword.data:
                    password_hash = bcrypt.hashpw(form.newPassword.data.encode(), bcrypt.gensalt())
                    user.password = password_hash.decode()
                db.session.commit()  # Save the changes to the database
                flash('Your account has been updated!')
                return redirect(url_for('views.home'))
            except NoResultFound:
                flash('User not found in the database.')
        else:
            flash('Incorrect old password. Please try again.')

    return render_template('account.html', form=form,user=current_user)
