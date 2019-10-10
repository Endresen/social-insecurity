from flask_wtf import FlaskForm, Recaptcha, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FormField, TextAreaField, FileField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, EqualTo, Length


# defines all forms in the application, these will be instantiated by the template,
# and the routes.py will read the values of the fields

class LoginForm(FlaskForm):
    username = StringField('Username', render_kw={'placeholder': 'Username'}, validators=[InputRequired(
        message='You must enter a username'),
        Length(min=2, max=25, message='Enter a username between 2 and 25 characters')])
    password = PasswordField('Password', render_kw={'placeholder': 'Password'}, validators=[InputRequired(
        message='You must enter a password'),
        Length(min=5, max=25, message='Enter a password between 5 and 25 characters')])
    remember_me = BooleanField(
        'Remember me')

    log_captcha = RecaptchaField(validators=[Recaptcha(message='Prove that you are human to continue')])

    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    first_name = StringField('First Name', render_kw={'placeholder': 'First Name'}, validators=[InputRequired(
        message='You must enter a first name'),
        Length(min=5, max=25, message='Enter a first name between 5 and 25 characters')])
    last_name = StringField('Last Name', render_kw={'placeholder': 'Last Name'}, validators=[InputRequired(
        message='You must enter a last name'),
        Length(min=5, max=25, message='Enter a last name between 5 and 25 characters')])
    username = StringField('Username', render_kw={'placeholder': 'Username'}, validators=[InputRequired(
        message='You must enter a username'),
        Length(min=5, max=25, message='Enter a username between 5 and 25 characters')])
    password = PasswordField('Password', render_kw={'placeholder': 'Password'}, validators=[InputRequired(
        message='You must enter a password'),
        Length(min=5, max=25, message='Enter a password between 5 and 25 characters')])
    confirm_password = PasswordField('Confirm Password', render_kw={'placeholder': 'Confirm Password'},
                                     validators=[EqualTo('password', message='Passwords not identical'),
                                                 InputRequired(message='You must confirm password'),
                                                 Length(min=5, max=25,
                                                        message='Enter a password between 5 and 25 characters')])

    reg_captcha = RecaptchaField(validators=[Recaptcha(message='Prove that you are human to continue')])

    submit = SubmitField('Sign Up')


class IndexForm(FlaskForm):
    login = FormField(LoginForm)
    register = FormField(RegisterForm)
    remember_me = BooleanField('Remember me')

class PostForm(FlaskForm):
    content = TextAreaField('New Post', render_kw={'placeholder': 'What are you thinking about?'})
    image = FileField('Image')
    submit = SubmitField('Post')


class CommentsForm(FlaskForm):
    comment = TextAreaField('New Comment', render_kw={'placeholder': 'What do you have to say?'})
    submit = SubmitField('Comment')


class FriendsForm(FlaskForm):
    username = StringField('Friend\'s username', render_kw={'placeholder': 'Username'})
    submit = SubmitField('Add Friend')


class ProfileForm(FlaskForm):
    education = StringField('Education', render_kw={'placeholder': 'Highest education'})
    employment = StringField('Employment', render_kw={'placeholder': 'Current employment'})
    music = StringField('Favorite song', render_kw={'placeholder': 'Favorite song'})
    movie = StringField('Favorite movie', render_kw={'placeholder': 'Favorite movie'})
    nationality = StringField('Nationality', render_kw={'placeholder': 'Your nationality'})
    birthday = DateField('Birthday')
    submit = SubmitField('Update Profile')
