import os
import io
import zipfile
import csv
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, send_file
from flask_login import login_required, current_user
from flask_babel import gettext as _
from models.models import db, User, Diagnosis, Plant, ChatSession
from config import Config
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash(_('Admin access required'), 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@admin_required
def index():
    total_users = User.query.count()
    total_diagnoses = Diagnosis.query.count()
    total_plants = Plant.query.count()
    total_chats = ChatSession.query.count()
    total_images = len(os.listdir(Config.UPLOAD_FOLDER)) - 1

    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    diagnoses_today = Diagnosis.query.filter(Diagnosis.timestamp >= today).count()
    users_today = User.query.filter(User.created_at >= today).count()

    recent_diagnoses = Diagnosis.query.order_by(Diagnosis.timestamp.desc()).limit(10).all()

    upload_size = sum(
        os.path.getsize(os.path.join(Config.UPLOAD_FOLDER, f))
        for f in os.listdir(Config.UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(Config.UPLOAD_FOLDER, f)) and f != '.gitkeep'
    )

    return render_template('admin/index.html',
        total_users=total_users, total_diagnoses=total_diagnoses,
        total_plants=total_plants, total_chats=total_chats,
        total_images=total_images, diagnoses_today=diagnoses_today,
        users_today=users_today, recent_diagnoses=recent_diagnoses,
        upload_size=upload_size)


@admin_bp.route('/diagnoses')
@admin_required
def diagnoses():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    disease_filter = request.args.get('disease', '').strip()

    query = Diagnosis.query
    if search:
        query = query.filter(
            db.or_(
                Diagnosis.disease_name_ar.ilike(f'%{search}%'),
                Diagnosis.disease_name_en.ilike(f'%{search}%'),
                Diagnosis.disease_class.ilike(f'%{search}%')
            )
        )
    if disease_filter:
        query = query.filter(Diagnosis.disease_class == disease_filter)

    query = query.order_by(Diagnosis.timestamp.desc())
    pagination = query.paginate(page=page, per_page=25, error_out=False)
    diagnoses = pagination.items

    unique_diseases = db.session.query(Diagnosis.disease_class).distinct().order_by(Diagnosis.disease_class).all()

    return render_template('admin/diagnoses.html',
        diagnoses=diagnoses, pagination=pagination,
        search=search, disease_filter=disease_filter,
        unique_diseases=[d[0] for d in unique_diseases])


@admin_bp.route('/images')
@admin_required
def images():
    page = request.args.get('page', 1, type=int)
    per_page = 30
    all_files = sorted([
        f for f in os.listdir(Config.UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(Config.UPLOAD_FOLDER, f)) and f != '.gitkeep'
    ], reverse=True)

    total = len(all_files)
    start = (page - 1) * per_page
    end = start + per_page
    files_page = all_files[start:end]

    # Map files to their diagnoses
    file_diagnoses = {}
    for f in files_page:
        diag = Diagnosis.query.filter_by(image_path=f).first()
        file_diagnoses[f] = diag

    return render_template('admin/images.html',
        files=files_page, file_diagnoses=file_diagnoses,
        page=page, total=total, per_page=per_page)


@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()

    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/users.html',
        users=pagination.items, pagination=pagination,
        search=search)


@admin_bp.route('/users/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': _('Cannot change your own admin status')}), 400
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'success': True, 'is_admin': user.is_admin})


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': _('Cannot delete your own account')}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/diagnoses/delete/<diagnosis_id>', methods=['POST'])
@admin_required
def delete_diagnosis(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    image_path = os.path.join(Config.UPLOAD_FOLDER, diagnosis.image_path)
    if os.path.exists(image_path) and diagnosis.image_path:
        os.remove(image_path)
    db.session.delete(diagnosis)
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/download-images')
@admin_required
def download_images():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        diagnoses = Diagnosis.query.filter(Diagnosis.image_path.isnot(None)).all()
        for d in diagnoses:
            folder = d.disease_class.replace('/', '_').replace('\\', '_')
            src = os.path.join(Config.UPLOAD_FOLDER, d.image_path)
            if os.path.exists(src):
                arcname = f"{folder}/{d.image_path}"
                zf.write(src, arcname)
    buf.seek(0)
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True,
                     download_name=f'verda_images_{datetime.utcnow().strftime("%Y%m%d")}.zip')


@admin_bp.route('/export-users')
@admin_required
def export_users():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Username', 'Email', 'Full Name', 'Phone', 'Language',
                      'Admin', 'Diagnoses', 'Joined', 'Last Login'])
    for u in User.query.order_by(User.created_at.desc()).all():
        writer.writerow([
            u.username, u.email, u.full_name or '', u.phone or '',
            u.language_preference, 'Yes' if u.is_admin else 'No',
            u.diagnoses.count(),
            u.created_at.strftime('%Y-%m-%d') if u.created_at else '',
            u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else ''
        ])
    mem = io.BytesIO(buf.getvalue().encode('utf-8-sig'))
    return send_file(mem, mimetype='text/csv',
                     as_attachment=True,
                     download_name=f'verda_users_{datetime.utcnow().strftime("%Y%m%d")}.csv')


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    diagnoses_over_time = db.session.query(
        db.func.date(Diagnosis.timestamp).label('date'),
        db.func.count(Diagnosis.id).label('count')
    ).filter(Diagnosis.timestamp >= since).group_by(db.func.date(Diagnosis.timestamp)).order_by('date').all()

    disease_distribution = db.session.query(
        Diagnosis.disease_class,
        db.func.count(Diagnosis.id).label('count')
    ).group_by(Diagnosis.disease_class).order_by(db.desc('count')).limit(10).all()

    return jsonify({
        'diagnoses_over_time': [{'date': str(r.date), 'count': r.count} for r in diagnoses_over_time],
        'disease_distribution': [{'name': r.disease_class, 'count': r.count} for r in disease_distribution],
    })
