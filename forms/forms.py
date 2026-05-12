from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, DateField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 120)])
    full_name = StringField('Full Name', validators=[Optional(), Length(1, 100)])
    phone = StringField('Phone', validators=[Optional(), Length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 255)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(6, 255)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Optional(), Length(1, 100)])
    phone = StringField('Phone', validators=[Optional(), Length(1, 20)])
    language_preference = SelectField('Language', choices=[('ar', 'العربية'), ('en', 'English'), ('de', 'Deutsch')])
    submit = SubmitField('Save Changes')

class PlantForm(FlaskForm):
    name = StringField('Plant Name', validators=[DataRequired(), Length(1, 100)])
    plant_type = SelectField('Plant Type', choices=[
        ('', 'Select type...'),
        ('Apple', 'Apple'), ('Blueberry', 'Blueberry'), ('Cherry', 'Cherry'),
        ('Corn', 'Corn'), ('Grape', 'Grape'), ('Orange', 'Orange'),
        ('Peach', 'Peach'), ('Pepper', 'Pepper'), ('Potato', 'Potato'),
        ('Raspberry', 'Raspberry'), ('Soybean', 'Soybean'),
        ('Squash', 'Squash'), ('Strawberry', 'Strawberry'), ('Tomato', 'Tomato')
    ], validators=[DataRequired()])
    planting_date = DateField('Planting Date', validators=[Optional()])
    location = StringField('Location', validators=[Optional(), Length(1, 200)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Plant')

class CareLogForm(FlaskForm):
    action_type = SelectField('Action', choices=[
        ('watering', 'Watering'), ('fertilizing', 'Fertilizing'),
        ('pruning', 'Pruning'), ('treatment', 'Treatment'),
        ('repotting', 'Repotting'), ('other', 'Other')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[DataRequired(), Length(1, 500)])
    submit = SubmitField('Add Entry')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(6, 255)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
