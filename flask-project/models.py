from flask_login import UserMixin
from app import db
from iroha_sdk import IrohaSDK
from iroha_sdk import User as IrohaUser

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    private_key = db.Column(db.String(1000),unique=True)


class Journal(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    hash = db.Column(db.String(1000),unique=True)
    title = db.Column(db.String(1000))