import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models.models import db, User
from forms.forms import LoginForm, RegistrationForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from flask_babel import gettext as _

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        session['lang'] = user.language_preference
        flash(_('Registration successful! Welcome to VerdaCare!'), 'success')
        return redirect(url_for('dashboard.index'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            session['lang'] = user.language_preference
            next_page = request.args.get('next')
            flash(_('Welcome back, %(name)s!', name=user.full_name or user.username), 'success')
            return redirect(next_page or url_for('dashboard.index'))
        flash(_('Invalid username or password.'), 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('index'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash(_('Password changed successfully!'), 'success')
            return redirect(url_for('profile.view'))
        flash(_('Current password is incorrect.'), 'danger')
    return render_template('auth/change_password.html', form=form)
