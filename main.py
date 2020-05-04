from flask import Blueprint,render_template
from flask_login import login_required, current_user
from app import db
from brn-iroha-sdk import login

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

@main.route('/browse')
def browse():
    return 'Browse'