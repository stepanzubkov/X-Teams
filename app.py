# Импорты Flask и расширений
from flask import Flask, render_template, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# Импорты других библиотек
import os

# Импорты собственных файлов
from db import db, migrate, Users, Groups, GroupsCombinations, Leaders
from forms import RegistrationForm, LoginForm
from login import manager, load_user
from user import User

app = Flask(__name__)
app.config.from_pyfile('config.py')

manager.init_app(app)
db.init_app(app)
migrate.init_app(app, db)

# Обработчик главной страницы


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Обработчик страницы регистрации


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = Users(
                name=form.name.data, email=form.email.data,
                password=generate_password_hash(form.password.data),
                specialization=form.specialization.data, expirience=form.expirience.data,
                github_url=f'https://github.com/{form.github_name.data}'
            )
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        user = Users.query.filter_by(email=form.email.data).first()
        userlogin = User().create(user)
        login_user(userlogin, remember=form.remember.data)
    return render_template('registration.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            userlogin = User().create(user)
            login_user(userlogin, remember=form.remember.data)
    else:
        flash('Такого аккаунта не существует')
    return render_template('login.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)
