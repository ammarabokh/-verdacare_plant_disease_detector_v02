import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.models import db, User, Diagnosis, Plant, ChatSession
from forms.forms import ProfileForm, ChangePasswordForm
from flask_babel import gettext as _
from config import Config

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def view():
    diagnoses_count = Diagnosis.query.filter_by(user_id=current_user.id).count()
    plants_count = Plant.query.filter_by(user_id=current_user.id).count()
    chats_count = ChatSession.query.filter_by(user_id=current_user.id).count()
    last_diagnosis = Diagnosis.query.filter_by(user_id=current_user.id)\
        .order_by(Diagnosis.timestamp.desc()).first()

    return render_template('profile/view.html',
                         diagnoses_count=diagnoses_count,
                         plants_count=plants_count,
                         chats_count=chats_count,
                         last_diagnosis=last_diagnosis)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.language_preference = form.language_preference.data
        db.session.commit()
        flash(_('Profile updated successfully!'), 'success')
        return redirect(url_for('profile.view'))
    return render_template('profile/edit.html', form=form)

@profile_bp.route('/profile/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        flash(_('No file selected.'), 'danger')
        return redirect(url_for('profile.edit'))
    file = request.files['photo']
    if file.filename == '':
        flash(_('No file selected.'), 'danger')
        return redirect(url_for('profile.edit'))
    if file:
        filename = secure_filename(f"user_{current_user.id}_{uuid.uuid4()}.jpg")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        if current_user.profile_image:
            old_path = os.path.join(Config.UPLOAD_FOLDER, current_user.profile_image)
            if os.path.exists(old_path):
                os.remove(old_path)
        current_user.profile_image = filename
        db.session.commit()
        flash(_('Profile photo updated!'), 'success')
    return redirect(url_for('profile.view'))
