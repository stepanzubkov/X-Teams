# Импорты Flask и расширений
import re
from flask import Flask, render_template, flash, make_response, url_for, redirect, request, abort
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# Импорты других библиотек
import os
from github3api import GitHubAPI

# Импорты собственных файлов
from db import TeamNotifications, db, migrate, Users, Teams, Members, Leaders, Stacks
from forms import CreateTeamForm, EditForm, EditTeamForm, RegistrationForm, LoginForm, TeamRequestForm
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


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
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
    return render_template('edit-profile.html', form=form, current_user=current_user, user=user, stack_text=stack_text, getattr=getattr)


@app.route('/create-team', methods=['POST', 'GET'])
@login_required
def create_team():
    form = CreateTeamForm()
    form.github.choices = choices = [(repo['name'], repo['name']) for repo in client.get(
        f'/users/{current_user.get_github()}/repos', _get='all', _attributes=['name', 'full_name'])]
    if form.validate_on_submit():
        try:
            group = Teams(name=form.name.data, descripton=form.description.data,
                          github=form.github.data, state='Создана', product_type=form.product_type.data)

            db.session.add(group)
            db.session.commit()

            group = Teams.query.filter_by(name=group.name).first()

            leader = Leaders(team_id=group.id, leader_id=current_user.get_id())
            member = Members(team_id=group.id, member_id=current_user.get_id())

            db.session.add_all([leader, member])
            db.session.commit()

            return redirect(url_for('team', github_name=team.github))
        except:
            db.session.rollback()

    return render_template('create-team.html', current_user=current_user, form=form)


@app.route('/team/<github_name>', methods=['GET'])
@login_required
def team(github_name):
    team = Teams.query.filter_by(github=github_name).first()
    members_githubs = [member.user.github for member in team.members]
    if github_name in current_user.get_teams_names():
        return render_template('myteam.html', current_user=current_user, team=team)
    return render_template('team.html', current_user=current_user, team=team, members_githubs=members_githubs)


@app.route('/edit-team/<github_name>', methods=['GET', 'POST'])
@login_required
def edit_team(github_name):
    if github_name not in current_user.get_teams_names():
        abort(404)
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
    return render_template('edit-team.html', current_user=current_user,
                           form=form, team=team, getattr=getattr)


@app.route('/team-request/<github_name>', methods=['GET', 'POST'])
@login_required
def team_request(github_name):
    if github_name in current_user.get_teams_names():
        abort(404)
    form = TeamRequestForm()
    team = Teams.query.filter_by(github=github_name).first()
    if current_user.get_github() in [member.user.github for member in team.members]:
        abort(404)
    if form.validate_on_submit():
        try:
            notification = TeamNotifications(
                name=form.heading.data, text=form.comment.data, team_id=team.id, _from=current_user.get_id(), state='Активна')

            db.session.add(notification)
            db.session.commit()

            return redirect(url_for('requests'))
        except Exception as e:
            print(e)
            db.session.rollback()
    return render_template('team-request.html', current_user=current_user, form=form, team=team)


@app.route('/user-requests', methods=['GET'])
@login_required
def user_requests():
    reqs = Users.query.get(current_user.get_id()).sended_notifications
    return render_template('user-requests.html', current_user=current_user, reqs=reqs)


@app.route('/team-requests/<github_name>', methods=['GET'])
@login_required
def team_requests(github_name):
    if github_name not in current_user.get_teams_names():
        abort(404)
    reqs = Teams.query.filter_by(github=github_name).first().notifications
    return render_template('team-requests.html',  current_user=current_user, reqs=reqs)


@app.route('/accept', methods=['GET'])
@login_required
def accept():
    try:
        team_id = int(request.args.get('team', None))
        request_id = int(request.args.get('request', None))
        user_id = int(request.args.get('user', None))
    except:
        abort(404)
    if team_id is not None and request_id is not None and user_id is not None:
        try:
            req = TeamNotifications.query.filter_by(
                id=int(request_id)).first()
            req.state = 'Принята'

            member = Members(team_id=team_id, member_id=user_id)

            db.session.add(member)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
    return redirect(url_for('team_requests', github_name=Teams.query.get(team_id).github))


@app.route('/reject', methods=['GET'])
@login_required
def reject():
    try:
        team_id = int(request.args.get('team', None))
        request_id = int(request.args.get('request', None))
    except:
        abort(404)
    if team_id is not None and request_id is not None:
        try:
            req = TeamNotifications.query.filter_by(
                id=int(request_id)).first()
            req.state = 'Отклонена'

            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
    return redirect(url_for('team_requests', github_name=Teams.query.get(team_id).github))


if __name__ == "__main__":
    app.run(debug=True)
