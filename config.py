import os

# contains application-wide configuration, and is loaded in __init__.py

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret' # TODO: Use this with wtforms
    # ^ https://overiq.com/flask-101/form-handling-in-flask/
    DATABASE = 'database.db'
    UPLOAD_PATH = 'app/static/uploads'
    ALLOWED_EXTENSIONS = {} # Might use this at some point, probably don't want people to upload any file type
    # TODO: implement this?
    ## example = https://gist.github.com/dAnjou/2874714