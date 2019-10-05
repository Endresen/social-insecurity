from flask import Flask, g
from flask_wtf import CSRFProtect

from config import Config
from flask_bootstrap import Bootstrap
import sqlite3
import os

# TODO: implement this?
# from flask_wtf.csrf import CSRFProtect #####https://flask-wtf.readthedocs.io/en/stable/csrf.html
import flask_login

# create and configure app
app = Flask(__name__)
csrf = CSRFProtect()
# csrf.init_app(app)
Bootstrap(app)
# TODO: keys are copied, make new ones. maybe with some wtforms stuff?
app.config['SECRET_KEY'] = '78w0o5tuuGex5Ktk8VvVDFJ124JSAD20u'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdT97oUAAAAAIKKsg07xw79ZeG1vLvHEMWSH678'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LdT97oUAAAAAMJU0SXQ-ysOU099fV6dTTO2V7Tr'
app.config.from_object(Config)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(username):
    user_id = query_db('SELECT id FROM Users WHERE username=?', [username], one=True)
    if user_id is None:
        return None

    user = User()
    user.id = username
    return user


# get an instance of the db
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db


# initialize db for the first time
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# TODO: maybe?
# perform generic query, not very secure yet
def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    db.commit()
    return (rv[0] if rv else None) if one else rv


# TODO: Add more specific queries to simplify code

# automatically called when application is closed, and closes db connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# initialize db if it does not exist
if not os.path.exists(app.config['DATABASE']):
    init_db()

if not os.path.exists(app.config['UPLOAD_PATH']):
    os.mkdir(app.config['UPLOAD_PATH'])

from app import routes
