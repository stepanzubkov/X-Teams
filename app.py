# Импорты Flask и расширений
from flask import Flask, render_template
from werkzeug.security import generate_password_hash, check_password_hash
# Импорты других библиотек
import os

# Импорты собственных файлов
from db import db, migrate, Users, Groups, GroupsCombinations, Leaders
from forms import RegistrationForm

app = Flask(__name__)
app.config.from_pyfile('config.py')

db.init_app(app)
migrate.init_app(app,db)

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
    return render_template('registration.html', form=form)

if __name__ == "__main__":
    app.run(debug = True)