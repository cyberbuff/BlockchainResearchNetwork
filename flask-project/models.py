from flask_login import UserMixin
from app import db
from iroha_sdk import IrohaSDK
from iroha_sdk import User as IrohaUser

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    private_key = db.Column(db.String(1000),unique=True)


class Journal(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(1000))
    title = db.Column(db.String(1000))
    filename = db.Column(db.String(1000))
    url = db.Column(db.String(1000))
    keywords = db.Column(db.String(1000))