from flask import Blueprint,render_template,request,redirect,flash,url_for
from flask_login import login_required, current_user
from app import db
from iroha_sdk import IrohaSDK,get_assets
import os
from iroha_sdk import User as IrohaUser
from functools import wraps
from werkzeug.utils import secure_filename
from models import Journal

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
        return func(*args,**kwargs)
    return init

@main.route('/')
@initialize
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
@initialize
def profile():
    return render_template('profile.html', name=current_user.name,iroha=iroha)

@main.route('/browse')
@initialize
def browse():
    items = get_items('public')
    return render_template('browse.html', items=items)

@main.route('/author')
@initialize
def author():
    if iroha.is_author():
        return render_template('author.html')
    return redirect('/')

UPLOAD_FOLDER = 'static/files'
ALLOWED_EXTENSIONS = {'docx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/author', methods=['POST'])
def author_post():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_location = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_location)
        title = request.form.get('title')
        keywords = request.form.get('keywords')
        add_journal(title, file.filename, keywords,file_location)
        flash('File submitted')
    return redirect(request.url)

@main.route('/reviewer')
@initialize
def reviewer():
    if iroha.is_reviewer:
        items = get_items('reviewer')
        return render_template('reviewer.html',items=items)
    else:
        redirect('/')

@main.route('/rejected')
@initialize
def rejected():
    if iroha.is_admin():
        items = get_items('private')
        return render_template('rejected.html',items=items)
    else:
        redirect('')

@main.route('/review/<id>/<approval>')
@initialize
def review(id,approval):
    if iroha.is_reviewer():
        journal_id = f'j{id}'
        if approval == "approve":
            print(iroha.approve_journal(journal_id))
        else:
            print(iroha.reject_journal(journal_id))
        return redirect('/reviewer')
    else:
        return redirect('/')


def add_journal(title, filename, tags, file_location):
    result = os.popen(f'ipfs add {file_location}')
    hash = result.read().split()[1]
    new_journal = Journal(hash=hash,url=file_location, filename=filename, keywords=tags, title=title)
    db.session.add(new_journal)
    db.session.commit()
    send_for_approval(f'j{new_journal.id}')

@initialize
def send_for_approval(journal_id):
    print(iroha.create_asset(journal_id))
    print(iroha.send_for_approval(journal_id))


def get_items(name):
    ids = get_assets(name)
    return [Journal.query.get(int(i)) for i in ids]

def set_iroha_none():
    global iroha 
    iroha = None