import re
from flask import Blueprint, render_template, request, flash, redirect, url_for
from allReviews.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from allReviews import db
from flask_login import login_user, login_required, logout_user, current_user

auth=Blueprint('auth',__name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))

            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Thank you for using our service', category='success')
    return redirect(url_for('auth.login'))

@auth.route("/signup",methods=['POST','GET'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        userName = request.form.get('userName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email)<4:
           flash("Email must be greater than 4 characters.", category="error")
        elif len(userName)<3:
            flash('User name must be greater than 3 character.', category='error')
        elif len(password1) <7:
            flash('Password must be at least 7 characters.', category='error')
        elif not validate_password(password1):
            flash('Password must contain at least one uppercase letter, one lowercase letter, one digit,'
                  ' and one special character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            new_user = User(email=email, userName=userName, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))
    return render_template('signup.html',user=current_user)

def validate_password(password):
    # Check if the password contains at least one uppercase letter, one lowercase letter, and one special character
    if re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$", password):
        return True
    else:
        return False