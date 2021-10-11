# Importing flask and extensions
from operator import itemgetter
from flask import Flask, render_template, flash, make_response, url_for, redirect, request, abort
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# Importing other libraries
import os
from github3api import GitHubAPI
from fuzzywuzzy import fuzz

# Importing my files
from db import TeamNotifications, db, migrate, Users, Teams, Members, Leaders, Stacks, UserNotifications
from forms import CreateTeamForm, EditForm, EditTeamForm, InviteForm, RegistrationForm, LoginForm, SearchTeamForm, TeamRequestForm, SearchUserForm
from login import manager, load_user
from user import User

# Client to interact with api github
client = GitHubAPI()
# Creating app and importing config
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Initialization flask extensions with app
manager.init_app(app)
db.init_app(app)
migrate.init_app(app, db)

# Login manager config
manager.login_view = 'login'
manager.login_message = 'Авторизуйтесь для доступа к закрытым страницам'
manager.login_message_category = 'error'

# Main page


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', current_user=current_user)

# Registration page


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    # Authorization check
    if current_user.is_authenticated:
        return redirect(url_for('profile', github_name=current_user.get_github()))
    # Create form
    form = RegistrationForm()
    # Emails list for check if such an account exists
    emails = [user.email for user in Users.query.all()]
    # POST request
    if form.validate_on_submit():
        # Check the existence of an account
        if form.email.data not in emails:
            try:
                # Interaction with DB
                user = Users(
                    name=form.name.data, email=form.email.data,
                    password=generate_password_hash(form.password.data),
                    specialization=form.specialization.data, expirience=form.expirience.data,
                    github=form.github.data, bio=client.get(
                        f'/users/{form.github.data}', _get='all', _attributes=['bio'])[0]['bio']
                )
                db.session.add(user)
                db.session.commit()
            # Rollback if any error occurs
            except Exception as e:
                print(e)
                db.session.rollback()
            # Login user
            user = Users.query.filter_by(email=form.email.data).first()
            userlogin = User().create(user)
            login_user(userlogin, remember=True)
            # Redirect for new user's profile
            return redirect(url_for('profile', github_name=user.github))
        # Error if such an account already exists
        else:
            flash('Такой аккаунт уже существует', category='error')
    # Return registration page
    return render_template('registration.html', form=form, current_user=current_user)

# Login page


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Authorization check
    if current_user.is_authenticated:
        return redirect(url_for('profile', github_name=current_user.get_github()))
    # Create form
    form = LoginForm()
    # Post request
    if form.validate_on_submit():
        # Login user
        user = Users.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            userlogin = User().create(user)
            login_user(userlogin, remember=form.remember.data)
            # Redirect for new user's profile
            return redirect(url_for('profile', github_name=current_user.get_github()))
        # Error if no such account exists
        else:
            flash('Нет такого аккаунта', category='error')
    # Return login page
    return render_template('login.html', form=form, current_user=current_user)

# User's profile page


@app.route('/user/<github_name>', methods=['GET'])
@login_required
def profile(github_name):
    # Check if this account is yours or someone else's
    if github_name == current_user.get_github():
        return render_template('myprofile.html', user=Users.query.filter_by(github=github_name).first(), current_user=current_user)
    return render_template('profile.html', user=Users.query.filter_by(github=github_name).first(), current_user=current_user)

# User's avatar page


@app.route('/image/<github_name>', methods=['GET'])
@login_required
def avatar(github_name):
    # Getting an avatar from the database
    source = Users.query.filter_by(github=github_name).first().avatar
    # if there is an avatar, we give it as it is, if not, we take the standard one
    image = source if source else app.open_resource(
        app.root_path + url_for('static', filename='images/default.png'), 'rb').read()
    # Create and return png response
    response = make_response(image)
    response.headers['Content-Type'] = 'image/png'
    return response

# Logout function


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Edit profile page


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Create form
    form = EditForm()
    # Selecting the data of the current user
    user = Users.query.get(current_user.get_id())
    # Preparing the current user's technology stack for display
    stack_text = ''
    for i in user.stack:
        stack_text += f'{i.name},'
    # POST request
    if form.validate_on_submit():
        try:
            # Preparing data for the database
            stack = user.stack
            stack_names = [s.name for s in stack] if stack else []
            form_names = form.stack.data.split(',')
            # Removing empty elements from form data
            for name in form_names:
                if name == '' or name == ' ':
                    form_names.remove(name)
            # Checking and sending user data to the database
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
        # Rollback if any error occurs
        except Exception as e:
            print(e)
            db.session.rollback()
        # Return redirect to the modified profile
        return redirect(url_for('profile', github_name=current_user.get_github()))
    # Return edit page
    return render_template('edit-profile.html', form=form, current_user=current_user, user=user, stack_text=stack_text, getattr=getattr)

# Create team page


@app.route('/create-team', methods=['POST', 'GET'])
@login_required
def create_team():
    # Create form
    form = CreateTeamForm()
    # Add choices to github repos
    form.github.choices = choices = [(repo['name'], repo['name']) for repo in client.get(
        f'/users/{current_user.get_github()}/repos', _get='all', _attributes=['name', 'full_name'])]
    # POST request
    if form.validate_on_submit():
        try:
            # Add team, leader, member to DB
            group = Teams(name=form.name.data, descripton=form.description.data,
                          github=form.github.data, state='Создана', product_type=form.product_type.data)

            db.session.add(group)
            db.session.commit()

            group = Teams.query.filter_by(name=group.name).first()

            leader = Leaders(team_id=group.id, leader_id=current_user.get_id())
            member = Members(team_id=group.id, member_id=current_user.get_id())

            db.session.add_all([leader, member])
            db.session.commit()
            # Return redirect to new team
            return redirect(url_for('team', github_name=team.github))
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    # Return create team page
    return render_template('create-team.html', current_user=current_user, form=form)

# Team page


@app.route('/team/<github_name>', methods=['GET'])
@login_required
def team(github_name):
    # Taking team data from the database
    team = Teams.query.filter_by(github=github_name).first()
    # Create members' github profiles list
    members_githubs = [member.user.github for member in team.members]
    # Check if this team is yours or someone else's
    if github_name in current_user.get_teams_names():
        return render_template('myteam.html', current_user=current_user, team=team)
    return render_template('team.html', current_user=current_user, team=team, members_githubs=members_githubs)

# Edit team page


@app.route('/edit-team/<github_name>', methods=['GET', 'POST'])
@login_required
def edit_team(github_name):
    # If this team is not yours abort error 404
    if github_name not in current_user.get_teams_names():
        abort(404)
    # Taking team data from the database
    team = Teams.query.filter_by(github=github_name).first()
    # Create form
    form = EditTeamForm()
    # Add choices to github repos
    form.github.choices = [('-', '-')] + [(repo['name'], repo['name']) for repo in client.get(
        f'/users/{current_user.get_github()}/repos', _get='all', _attributes=['name', 'full_name'])]
    # POST request
    if form.validate_on_submit():
        try:
            # Checking and sending team data to the database
            team.name = form.name.data
            team.descripton = form.description.data
            if form.github.data != '-':
                team.github = form.github.data
            if form.state.data != '-':
                team.state = form.state.data
            if form.product_type.data != '-':
                team.product_type = form.product_type.data

            db.session.commit()
            # Return redirect to the modified team
            return redirect(url_for('team', github_name=team.github))
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    # Return edit team page
    return render_template('edit-team.html', current_user=current_user,
                           form=form, team=team, getattr=getattr)

# Request to the team page


@app.route('/team-request/<github_name>', methods=['GET', 'POST'])
@login_required
def team_request(github_name):
    # If this team is yours abort error 404
    if github_name in current_user.get_teams_names():
        abort(404)
    # Create form
    form = TeamRequestForm()
    # Taking team data by github name
    team = Teams.query.filter_by(github=github_name).first()
    # If you are in this team abort error 404
    if current_user.get_github() in [member.user.github for member in team.members]:
        abort(404)
    # POST request
    if form.validate_on_submit():
        try:
            # Add team notification to DB
            notification = TeamNotifications(
                name=form.heading.data, text=form.comment.data, team_id=team.id, _from=current_user.get_id(), state='Активна')

            db.session.add(notification)
            db.session.commit()
            # Return redirect to user requests list page
            return redirect(url_for('user_requests'))
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    # Return request to the team page
    return render_template('team-request.html', current_user=current_user, form=form, team=team)

# User requests list page


@app.route('/user-requests', methods=['GET'])
@login_required
def user_requests():
    # Taking requests data from DB
    reqs = Users.query.get(current_user.get_id()).sended_notifications
    # Return user requests list page
    return render_template('user-requests.html', current_user=current_user, reqs=reqs)

# Team requests list page


@app.route('/team-requests/<github_name>', methods=['GET'])
@login_required
def team_requests(github_name):
    # If this team is not yours abort error 404
    if github_name not in current_user.get_teams_names():
        abort(404)
    # Taking requests data from DB
    reqs = Teams.query.filter_by(github=github_name).first().notifications
    # Return team requests list page
    return render_template('team-requests.html',  current_user=current_user, reqs=reqs)

# Accept request function


@app.route('/accept', methods=['GET'])
@login_required
def accept():
    try:
        # Get data from url
        team_id = int(request.args.get('team', None))
        request_id = int(request.args.get('request', None))
        user_id = int(request.args.get('user', None))
    # Abort if data is wrong
    except:
        abort(404)
    if team_id is not None and request_id is not None and user_id is not None:
        try:
            # Change request state and add user to team's members
            req = TeamNotifications.query.filter_by(
                id=int(request_id)).first()
            req.state = 'Принята'

            member = Members(team_id=team_id, member_id=user_id)

            db.session.add(member)
            db.session.commit()
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    return redirect(url_for('team_requests', github_name=Teams.query.get(team_id).github))

# Reject request function


@app.route('/reject', methods=['GET'])
@login_required
def reject():
    try:
        # Get data from url
        team_id = int(request.args.get('team', None))
        request_id = int(request.args.get('request', None))
    # Abort if data is wrong
    except:
        abort(404)
    if team_id is not None and request_id is not None:
        try:
            # Change request state
            req = TeamNotifications.query.filter_by(
                id=int(request_id)).first()
            req.state = 'Отклонена'

            db.session.commit()
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    # Return redirect to team requests list page
    return redirect(url_for('team_requests', github_name=Teams.query.get(team_id).github))

# Invite user page


@app.route('/invite/<github_name>', methods=['GET', 'POST'])
@login_required
def invite(github_name):
    # Create form
    form = InviteForm()
    # Get user data
    user = Users.query.filter_by(github=github_name).first()
    # Add choices team field
    form.team.choices = [(name, name)
                         for name in current_user.get_teams_names()]
    if form.validate_on_submit():
        try:
            # Add team notification to DB
            notification = UserNotifications(
                name=form.heading.data, text=form.comment.data, user_id=user.id, _from=Teams.query.filter_by(github=form.team.data).first().id, state='Активна')

            db.session.add(notification)
            db.session.commit()
            # Return redirect to user requests list page
            return redirect(url_for('team_invites', github_name=github_name))
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    # Return user invite page
    return render_template('invite.html', current_user=current_user, form=form, user=user)

# Team invites list page


@app.route('/team-invites/<github_name>', methods=['GET'])
@login_required
def team_invites(github_name):
    # If this team is not yours abort error 404
    if github_name not in current_user.get_teams_names():
        abort(404)
    # Taking invites data from DB
    reqs = Teams.query.filter_by(
        github=github_name).first().sended_notifications
    # Return team invites list page
    return render_template('team-invites.html', current_user=current_user, reqs=reqs)

# User invites list page


@app.route('/user-invites', methods=['GET'])
@login_required
def user_invites():
    # Taking invites data from DB
    reqs = Users.query.get(current_user.get_id()).notifications
    # Return user invites list page
    return render_template('user-invites.html',  current_user=current_user, reqs=reqs)

# Accept invite function


@app.route('/accept-invite', methods=['GET'])
@login_required
def accept_invite():
    try:
        # Get data from url
        team_id = int(request.args.get('team', None))
        request_id = int(request.args.get('request', None))
        user_id = int(request.args.get('user', None))
        assert user_id == current_user.get_id()
    # Abort if data is wrong
    except:
        abort(404)
    if team_id is not None and request_id is not None and user_id is not None:
        try:
            # Change invite state and add user to team's members
            req = UserNotifications.query.filter_by(
                id=int(request_id)).first()
            req.state = 'Принята'

            member = Members(team_id=team_id, member_id=user_id)

            db.session.add(member)
            db.session.commit()
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    return redirect(url_for('user_invites'))

# Reject invite function


@app.route('/reject-invite', methods=['GET'])
@login_required
def reject_invite():
    try:
        # Get data from url
        team_id = int(request.args.get('team', None))
        request_id = int(request.args.get('request', None))
        user_id = int(request.args.get('user', None))
        assert user_id == current_user.get_id()
    # Abort if data is wrong
    except:
        abort(404)
    if team_id is not None and request_id is not None:
        try:
            # Change request state
            req = UserNotifications.query.filter_by(
                id=request_id).first()
            req.state = 'Отклонена'

            db.session.commit()
        # Rollback if any occurs
        except Exception as e:
            print(e)
            db.session.rollback()
    # Return redirect to user invites list page
    return redirect(url_for('user_invites'))

# Users search page


@app.route('/users', methods=['GET', 'POST'])
def search_users():
    # Create form
    form = SearchUserForm()
    # Get users filtered by expirience, specialization, stack
    users = Users.query.filter(Users.expirience.like(str(request.args.get('expirience')) if str(request.args.get('expirience')) != '-' and str(request.args.get('expirience')) != 'None' else '%'),
                               Users.specialization.like(str(request.args.get('specialization')) if str(request.args.get('specialization')) != '-' and str(request.args.get('specialization')) != 'None' else '%'))
    users = list(map(lambda i: (fuzz.ratio(
        str([x.name for x in i.stack]), str(request.args.get('stack')).split(',')), i), users))
    users = list(map(lambda i: i[1], sorted(
        users, key=itemgetter(0), reverse=True)))
    # Return users search page
    return render_template('users.html', current_user=current_user, form=form, users=users)

# Teams search page


@app.route('/teams', methods=['GET', 'POST'])
def search_teams():
    # Create form
    form = SearchTeamForm()
    # Get teams filtered by product_type, state
    teams = Teams.query.filter(Teams.product_type.like(str(request.args.get('product_type')) if str(request.args.get('product_type')) != '-' and str(request.args.get('product_type')) != 'None' else '%'),
                               Teams.state.like(str(request.args.get('state')) if str(request.args.get('state')) != '-' and str(request.args.get('state')) != 'None' else '%'))
    # Return teams search page
    return render_template('teams.html', current_user=current_user, form=form, teams=teams)


# Run app
if __name__ == "__main__":
    app.run(debug=True)
