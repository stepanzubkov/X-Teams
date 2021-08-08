from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, migrate
from sqlalchemy import MetaData

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention = convention)
db = SQLAlchemy(metadata = metadata)
migrate = Migrate()

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), nullable = False)
    password = db.Column(db.String(1000), nullable = False)
    specialization = db.Column(db.String(100), nullable = False)
    experience = db.Column(db.String(20), nullable = False)
    avatar = db.Column(db.LargeBinary, nullable = True)
    rating = db.Column(db.Integer, nullable = True)
    groups = db.relationship("GroupsCombinations", backref = "users",
                            lazy = "dynamic", uselist = True)
    lead_groups = db.relationship("Leaders", backref = "users",
                                lazy = "dynamic", uselist = True)
    
class Groups(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(150), nullable = False)
    descripton = db.Column(db.Text, nullable = False)
    state = db.Column(db.String(50), nullable = False)
    github = db.Column(db.String(200), nullable = True)
    users = db.relationship("GroupsCombinations", backref = "groups",
                            lazy = "dynamic", uselist = True)
    leader = db.relationship("Leaders", backref = "groups",
                            lazy = "dynamic")
    
class GroupsCombinations(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
class Leaders(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))