from flask import Flask, g
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from config import Config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
import sqlite3
import os
import ssl
from flask_sqlalchemy import SQLAlchemy
from flask_argon2 import Argon2
from flask_wtf import CSRFProtect

# TODO: implement this?
# from flask_wtf.csrf import CSRFProtect #####https://flask-wtf.readthedocs.io/en/stable/csrf.html
import flask_login
import logging as log


# create and configure app
app = Flask(__name__)

# csrf = CSRFProtect()
# csrf.init_app(app)
# csrf.protect()
argon2 = Argon2(app)
Bootstrap(app)

app.config['SECRET_KEY'] = '45w0p5ttuGex5Ktk6KkVDFJ164JSaRr0u'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LcFtLwUAAAAAG4IdRDBHUOg_M5ZwcTijXk2rpB0'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LcFtLwUAAAAAObhd2OvXlY0VeOZtIBzWmjvGKUl'
app.config.from_object(Config)


context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('cert.pem', 'key.pem')


log.basicConfig(level=log.INFO, format="[%(levelname)s] %(message)s", handlers=[
        log.FileHandler('log.log'), log.StreamHandler()])

login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy()


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
def query_db(query, one=False):
    db = get_db()
    cursor = db.execute(query)
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

if __name__ == "__main__":
    app.run(ssl_context=context)
