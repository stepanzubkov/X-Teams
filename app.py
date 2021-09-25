# Импорты Flask и расширений
from flask import Flask, render_template, flash, make_response, url_for, redirect, request
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# Импорты других библиотек
import os
from github3api import GitHubAPI

# Импорты собственных файлов
from db import db, migrate, Users, Teams, Members, Leaders, Stacks
from forms import CreateTeamForm, EditForm, EditTeamForm, RegistrationForm, LoginForm
from login import manager, load_user
from user import User

client = GitHubAPI()

app = Flask(__name__)
app.config.from_pyfile('config.py')

manager.init_app(app)
db.init_app(app)
migrate.init_app(app, db)

manager.login_view = 'login'
manager.login_message = 'Авторизуйтесь для доступа к закрытым страницам'
manager.login_message_category = 'error'


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', current_user=current_user)

# Обработчик страницы регистрации


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('profile', github_name=current_user.get_github()))
    form = RegistrationForm()
    emails = [user.email for user in Users.query.all()]
    if form.validate_on_submit():
        if form.email.data not in emails:
            try:
                user = Users(
                    name=form.name.data, email=form.email.data,
                    password=generate_password_hash(form.password.data),
                    specialization=form.specialization.data, expirience=form.expirience.data,
                    github=form.github.data, bio=client.get(
                        f'/users/{form.github.data}', _get='all', _attributes=['bio'])[0]['bio']
                )
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
            user = Users.query.filter_by(email=form.email.data).first()
            userlogin = User().create(user)
            login_user(userlogin, remember=True)
            return redirect(url_for('profile', github_name=user.github))
        else:
            flash('Такой аккаунт уже существует', category='error')
    return render_template('registration.html', form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile', github_name=current_user.get_github()))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            userlogin = User().create(user)
            login_user(userlogin, remember=form.remember.data)
            return redirect(url_for('profile', github_name=current_user.get_github()))
        else:
            flash('Нет такого аккаунта', category='error')
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/user/<github_name>', methods=['GET'])
@login_required
def profile(github_name):
    if github_name == current_user.get_github():
        return render_template('myprofile.html', user=Users.query.filter_by(github=github_name).first(), current_user=current_user)
    return render_template('profile.html', user=Users.query.filter_by(github=github_name).first(), current_user=current_user)


@app.route('/image/<github_name>', methods=['GET'])
@login_required
def avatar(github_name):
    source = Users.query.filter_by(github=github_name).first().avatar
    image = source if source else app.open_resource(
        app.root_path + url_for('static', filename='images/default.png'), 'rb').read()
    response = make_response(image)
    response.headers['Content-Type'] = 'image/png'
    return response


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    user = Users.query.get(current_user.get_id())
    stack_text = ''
    for i in user.stack:
        stack_text += f'{i.name},'
    if form.validate_on_submit():
        try:
            stack = Stacks.query.filter_by(user_id=current_user.get_id())
            stack_names = [s.name for s in stack] if stack else []
            form_names = form.stack.data.split(',')
            for name in form_names:
                if name == '' or name == ' ':
                    form_names.remove(name)

            user.name = form.name.data
            user.email = form.email.data
            user.expirience = form.expirience.data
            user.github = form.github.data
            user.bio = form.bio.data
            if form.password.data is not None:
                user.password = generate_password_hash(form.password.data)
            if form.specialization.data != '-':
                user.specialization = form.specialization.data
            if form.avatar.data:
                user.avatar = request.files[form.avatar.name].read()
            if stack_names != form_names:
                for name in stack_names:
                    deleted = Stacks.query.filter_by(name=name).first()
                    db.session.delete(deleted)
                for name in form_names:
                    inserted = Stacks(name=name, user_id=current_user.get_id())
                    db.session.add(inserted)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
        return redirect(url_for('profile', github_name=current_user.get_github()))
    return render_template('edit.html', form=form, current_user=current_user, user=user, stack_text=stack_text, getattr=getattr)


@app.route('/createteam', methods=['POST', 'GET'])
@login_required
def creategroup():
    form = CreateTeamForm()
    form.github.choices = choices = [(repo['name'], repo['name']) for repo in client.get(
        f'/users/{current_user.get_github()}/repos', _get='all', _attributes=['name', 'full_name'])]
    if form.validate_on_submit():
        try:
            group = Teams(name=form.name.data, descripton=form.description.data,
                          github=form.github.data, state='Создана', product_type=form.product_type.data)

            db.session.add(group)
            db.session.commit()

            group_id = Teams.query.filter_by(name=group.name).first().id

            leader = Leaders(team_id=group_id, leader_id=current_user.get_id())
            member = Members(team_id=group_id, member_id=current_user.get_id())

            db.session.add_all([leader, member])
            db.session.commit()

            redirect(url_for('index'))
        except:
            db.session.rollback()

    return render_template('creategroup.html', current_user=current_user, form=form)


@app.route('/team/<github_name>', methods=['GET'])
@login_required
def team(github_name):
    team = Teams.query.filter_by(github=github_name).first()
    if github_name in current_user.get_teams_names():
        return render_template('myteam.html', current_user=current_user, team=team)
    return render_template('team.html', current_user=current_user, team=team)


@app.route('/editteam/<github_name>', methods=['GET', 'POST'])
def edit_team(github_name):
    if github_name not in current_user.get_teams_names():
        return redirect(url_for('index'))
    team = Teams.query.filter_by(github=github_name).first()
    form = EditTeamForm()
    form.github.choices = [('-', '-')] + [(repo['name'], repo['name']) for repo in client.get(
        f'/users/{current_user.get_github()}/repos', _get='all', _attributes=['name', 'full_name'])]
    if form.validate_on_submit():
        try:
            team.name = form.name.data
            team.descripton = form.description.data
            if form.github.data != '-':
                team.github = form.github.data
            if form.state.data != '-':
                team.state = form.state.data
            if form.product_type.data != '-':
                team.product_type = form.product_type.data

            db.session.commit()
            return redirect(url_for('team', github_name=team.github))
        except Exception as e:
            print(e)
            db.session.rollback()
    return render_template('editteam.html', current_user=current_user,
                           form=form, team=team, getattr=getattr)


if __name__ == "__main__":
    app.run(debug=True)
