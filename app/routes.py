from flask import render_template, flash, redirect, url_for, request
from app import app, query_db, User
from app.forms import LoginForm, RegisterForm, PostForm, FriendsForm, ProfileForm, CommentsForm, IndexForm
from datetime import datetime
import os

import flask_login
from argon2 import PasswordHasher

ph = PasswordHasher()


# this file contains all the different routes, and the logic for communicating with the database

@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect("/")


def logged_in():
    return flask_login.current_user.is_authenticated


def current_user():
    return flask_login.current_user.id


def this_user(username):
    return username == flask_login.current_user.id


# home page/login/registration
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if logged_in():
        return redirect(url_for('stream', username=current_user()))

    form = IndexForm()

    # if form.validate_on_submit():
    if form.login.submit():
        # sql is broken
        user = query_db('SELECT * FROM Users WHERE username=?;', [form.login.username.data], one=True)
        if user is None:
            flash('Sorry, this user does not exist!')
        # elif user['password'] == form.login.passwordHash.data:
        elif ph.verify(form.login.password.data.encode('utf8'), user['password']):
            currentUser = User()
            currentUser.id = user["username"]
            flask_login.login_user(currentUser, form.remember_me.data)
            return redirect(url_for('stream', username=form.login.username.data))
        else:
            flash('Sorry, wrong password!')

    elif form.register.submit():
        checkUser = query_db('SELECT * FROM Users WHERE username=?', [form.register.username.data],
                             one=True) is not None
        if not checkUser:
            # TODO: argon2 on password and store hash instead
            query_db(
                'INSERT INTO Users (username, first_name, last_name, password) VALUES(?, ?, ?, ?)'.format(
                    form.register.username.data, form.register.first_name.data,
                    form.register.last_name.data, form.register.passwordHash))
            return redirect(url_for('index'))
        flash(form.username.data + " is already taken, try a")
    return render_template('index.html', title='Welcome', form=form)


# content stream page
@app.route('/stream/<username>', methods=['GET', 'POST'])
@flask_login.login_required
def stream(username):
    form = PostForm()
    user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
    if form.validate_on_submit():
        if this_user(username):
            if form.image.data:
                path = os.path.join(app.config['UPLOAD_PATH'], form.image.data.filename)
                form.image.data.save(path)

        query_db(
            'INSERT INTO Posts (u_id, content, image, creation_time) VALUES(?, ?, ?, ?);',
            [user['id'], form.content.data,
             form.image.data.filename,
             datetime.now()])
        return redirect(url_for('stream', username=username))
        flash("This is not your profile to edit")

        if user is None:
            flash(username + " is not registered")
            return redirect(url_for('/stream/' + current_user()))

    # TODO: fix dette/rename
    posts = query_db(
        'SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id '
        'WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id={0}) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id={0}) '
        'OR p.u_id={0} ORDER BY p.creation_time DESC;'.format(
            user['id']))
    return render_template('stream.html', title='Stream', username=username, form=form, posts=posts, current_user=this_user(username))

# comment page for a given post and user.
@app.route('/comments/<username>/<int:p_id>', methods=['GET', 'POST'])
@flask_login.login_required
def comments(username, p_id):
    form = CommentsForm()
    if form.validate_on_submit():
        user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
        query_db('INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES(?,?,?,?);',
                 [p_id, user['id'], form.comment.data, datetime.now()])

    post = query_db('SELECT * FROM Posts WHERE id={};'.format(p_id), one=True)
    all_comments = query_db(
        'SELECT DISTINCT * FROM Comments AS c JOIN Users AS u ON c.u_id=u.id WHERE c.p_id=? ORDER BY c.creation_time DESC;'.format(
            p_id))
    return render_template('comments.html', title='Comments', username=username, form=form, post=post,
                           comments=all_comments)


# page for seeing and adding friends
@app.route('/friends/<username>', methods=['GET', 'POST'])
@flask_login.login_required
def friends(username):
    form = FriendsForm()
    user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
    if form.validate_on_submit():
        friend = query_db('SELECT * FROM Users WHERE username=?;', [form.username.data], one=True)
        if friend is None:
            flash('User does not exist')
        elif not this_user(username):
            flash('Cannot add friends to another person')
        else:
            query_db('INSERT INTO Friends (u_id, f_id) VALUES(?, ?);', [user['id'], friend['id']])

    if user is None:
        flash(username + " does not exist")
        return redirect('/friends/' + current_user())

# TODO: rename
    all_friends = query_db('SELECT * FROM Friends AS f JOIN Users as u ON f.f_id=u.id WHERE f.u_id=? AND f.f_id!=? ;',
                           [user['id'], user['id']])
    return render_template('friends.html', title='Friends', username=username, friends=all_friends, form=form,
                           current_user=this_user(username))


# see and edit detailed profile information of a user
@app.route('/profile/<username>', methods=['GET', 'POST'])
@flask_login.login_required
def profile(username):
    form = ProfileForm()
    if form.validate_on_submit():
        if this_user(username):
            query_db(
                'UPDATE Users SET education=?, employment=?, music=?, movie=?, nationality=?, birthday=? WHERE username=? ;',
                [form.education.data, form.employment.data, form.music.data, form.movie.data, form.nationality.data,
                 form.birthday.data, username])
            return redirect(url_for('profile', username=username))
            flash("This is not your profile to edit")

    user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
    if user is None:
        flash(username + " does not exist")
        return redirect('/profile/' + current_user())

    return render_template('profile.html', title='profile', username=username, user=user, form=form,
                           current_user=this_user(username))
