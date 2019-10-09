import flask_login
from flask import render_template, flash, redirect, url_for
from app import app, query_db, User, argon2
from app.forms import IndexForm, PostForm, FriendsForm, ProfileForm, CommentsForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename


# this file contains all the different routes, and the logic for communicating with the database

@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect("/")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def is_logged_in():
    return flask_login.current_user.is_authenticated


def current_user():
    return flask_login.current_user.id


def this_user(username):
    return username == flask_login.current_user.id


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if is_logged_in():
        return redirect(url_for('stream', username=current_user()))
    form = IndexForm()

    if form.login.validate_on_submit():
        user = query_db('SELECT * FROM Users WHERE username=?;', [form.login.username.data], one=True)
        pw_hash = argon2.generate_password_hash(form.login.data)
        db_hash = user['password']
        if argon2.check_password_hash(pw_hash, db_hash):
            currentuser = User()
            currentuser.id = user["username"]
            flask_login.login_user(currentuser, form.remember_me.data)
            app.logger.info('%s logged in', form.login.data.id)
            return redirect(url_for('stream', username=form.login.username.data))
        else:
            app.logger.warning('%s typed wrong password', user["username"])
            flash('Wrong login information')

    if form.register.validate_on_submit():
        check_user = query_db('SELECT * FROM Users WHERE username=?', [form.register.username.data],
                             one=True) is not None
        if not check_user:
            query_db(
                'INSERT INTO Users (username, first_name, last_name, password) VALUES(?, ?, ?, ?)'.format(
                    form.register.username.data, form.register.first_name.data,
                    form.register.last_name.data, argon2.generate_password_hash(form.register.password.data)))
            return redirect(url_for('index'))
        flash(form.username.data + " is already taken")
    return render_template('index.html', title='Welcome', form=form)


# content stream page
@app.route('/stream/<username>', methods=['GET', 'POST'])
@flask_login.login_required
def stream(username):
    form = PostForm()
    user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
    if form.validate_on_submit():
        if this_user(username):
            if allowed_file(form.image.data) and form.image.data is not None:
                path = os.path.join(app.config['UPLOAD_PATH'], form.image.data.filename)
                form.image.data.filename = secure_filename(form.image.data.filename)
                form.image.data.save(path)
                app.logger.info('\'%s\' successfully uploaded \'%s\'', current_user(),
                                form.image.data.filename)
                flash('File uploaded')
            else:
                app.logger.warning('\'%s\' tried to upload non whitelisted filetype', current_user())
                flash('Cannot uplad files of that type')

        query_db(
            'INSERT INTO Posts (u_id, content, image, creation_time) VALUES(?, ?, ?, ?);',
            [user['id'], form.content.data,
             form.image.data.filename,
             datetime.now()])
        return redirect(url_for('stream', username=username))
        flash("This is not your profile to edit")

    if user is None:
        app.logger.warning('User \'%s\' entered unregistered user in url and tried to access stream \'%s\'',
                           current_user(), username)
        flash(username + " does not exist")
        return redirect('/stream/' + current_user())

    posts = query_db(
        'SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id=?) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id=?) OR p.u_id=? ORDER BY p.creation_time DESC;',
        [user['id'], user['id'], user['id']])
    return render_template('stream.html', title='Stream', username=username, form=form, posts=posts,
                           is_current_user=is_current_user(username))


# comment page for a given post and user.
@app.route('/comments/<username>/<int:p_id>', methods=['GET', 'POST'])
@flask_login.login_required
def comments(username, p_id):
    form = CommentsForm()
    if form.validate_on_submit():
        if this_user(username):
            user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
            query_db('INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES(?,?,?,?);',
                     [p_id, user['id'], form.comment.data, datetime.now()])
        else:
            app.logger.warning('\'%s\' tried to comment as %s', current_user(), username)
            flash("Can't comment on this post")
            return redirect(url_for('stream', username=username))

    post = query_db('SELECT * FROM Posts WHERE id=?;', [p_id], one=True)
    all_comments = query_db(
        'SELECT DISTINCT * FROM Comments AS c JOIN Users AS u ON c.u_id=u.id WHERE c.p_id=? ORDER BY c.creation_time DESC;',
        [p_id])
    return render_template('comments.html', title='Comments', username=username, form=form, post=post,
                           comments=all_comments)


# page for seeing and adding friends
@app.route('/friends/<username>', methods=['GET', 'POST'])
@flask_login.login_required
def friends(username):
    user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
    if user is None:
        app.logger.warning('\'%s\' tried to access friends of non-existent user \'%s\'', current_user(), username)
        flash(username + " does not exist")
        return redirect('/friends/' + current_user())

    all_friends = query_db('SELECT * FROM Friends AS f JOIN Users as u ON f.f_id=u.id WHERE f.u_id=? AND f.f_id!=? ;',
                           [user['id'], user['id']])

    form = FriendsForm()
    if form.validate_on_submit():
        friend = query_db('SELECT * FROM Users WHERE username=?;', [form.username.data], one=True)
        if friend is None:
            app.logger.warning('\'%s\' atttempted to add unregistered friend', current_user(), username)
            flash('User does not exist')
        elif not this_user(username):
            app.logger.warning('\'%s\' tried to add \'%s\' as friend to %s\'s profile', current_user(),
                               friend['username'], username)
            flash('Cannot force people to be friends')
        elif username == form.username.data:
            app.logger.warning('\'%s\' got lonely and added himself as a friend', username)
            flash('You cant add yourself as a friend')
        else:
            is_friended = False
            for f in all_friends:
                if friend['username'] == f['username']:
                    is_friended = True
                    break

            if is_friended:
                app.logger.warning('\'%s\' tried to add existing friend \'%s\' as friend again',
                                   username, friend['username'])
                flash(friend['username'] + ' is already your friend')
            else:
                app.logger.info('\'%s\' successfully added friend \'%s\'', current_user(), friend['username'])
                query_db('INSERT INTO Friends (u_id, f_id) VALUES(?, ?);', [user['id'], friend['id']])
                all_friends.append(friend)

    return render_template('friends.html', title='Friends', username=username, friends=all_friends, form=form,
                           current_user=current_user(username))


# see and edit detailed profile information of a user
@app.route('/profile/<username>', methods=['GET', 'POST'])
@flask_login.login_required
def profile(username):
    form = ProfileForm()
    if form.validate_on_submit():
        if this_user(username):
            query_db(
                'UPDATE Users SET education=?, employment=?, music=?, movie=?, nationality=?, birthday=? WHERE'
                ' username=? ;',
                [form.education.data, form.employment.data, form.music.data, form.movie.data, form.nationality.data,
                 form.birthday.data, username])
            app.logger.info('\'%s\' edited his own profile', current_user())
            return redirect(url_for('profile', username=username))
        app.logger.warning('\'%s\' tried to edit %s\'s profile', current_user(), username)

        flash("This is not your profile to edit")

    user = query_db('SELECT * FROM Users WHERE username=?;', [username], one=True)
    if user is None:
        flash(username + " does not exist")
        return redirect('/profile/' + current_user())

    return render_template('profile.html', title='profile', username=username, user=user, form=form,
                           current_user=this_user(username))
