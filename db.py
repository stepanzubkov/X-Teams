
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData
from sqlalchemy.orm import backref


convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s'
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    expirience = db.Column(db.String(20), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.LargeBinary, nullable=True)
    github = db.Column(db.String(100), nullable=False)
    stack = db.relationship('Stacks', backref='users',
                            lazy='dynamic', uselist=True)
    teams = db.relationship('Members', backref='user',
                            lazy='dynamic', uselist=True)
    lead_teams = db.relationship('Leaders', backref='user',
                                 lazy='dynamic', uselist=True)
    sended_notifications = db.relationship('TeamNotifications', backref='user',
                                           lazy='dynamic', uselist=True)
    notifications = db.relationship('UserNotifications', backref='user',
                                    lazy='dynamic', uselist=True)


class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    descripton = db.Column(db.Text, nullable=False)
    product_type = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    github = db.Column(db.String(200), nullable=False)
    members = db.relationship('Members', backref='info',
                              lazy='dynamic', uselist=True)
    leader = db.relationship('Leaders', backref='info',
                             uselist=False)
    notifications = db.relationship('TeamNotifications', backref='team',
                                    lazy='dynamic', uselist=True)
    sended_notifications = db.relationship('UserNotifications', backref='team',
                                           lazy='dynamic', uselist=True)


class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Leaders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Stacks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)


class TeamNotifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    _from = db.Column(db.Integer, db.ForeignKey('users.id'))
    state = db.Column(db.String(50), nullable=False)


class UserNotifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    _from = db.Column(db.Integer, db.ForeignKey('teams.id'))
    state = db.Column(db.String(50), nullable=False)
