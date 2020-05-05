from flask import Blueprint,render_template
from flask_login import login_required, current_user
from app import db
from iroha_sdk import IrohaSDK
from iroha_sdk import User as IrohaUser
from functools import wraps
main = Blueprint('main', __name__)
if current_user:
    iroha = IrohaSDK(IrohaUser(current_user.name+"@test",current_user.private_key))
else:
    iroha = None

def initialize(func):
    @wraps(func)
    def init(*args,**kwargs):
        global iroha
        if not iroha and current_user.is_authenticated:
            iroha = IrohaSDK(IrohaUser(current_user.name+"@test",current_user.private_key))
        return func()
    return init

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
@initialize
def profile():
    return render_template('profile.html', name=current_user.name,is_admin = iroha.is_admin(),is_author=iroha.is_author())

@main.route('/browse')
def browse():
    return 'Browse'