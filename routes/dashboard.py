import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.models import db, Diagnosis, Plant, CareLog, ChatSession, ChatMessage, PLANT_TYPES, CARE_ACTIONS
from forms.forms import PlantForm, CareLogForm, ChangePasswordForm
from flask_babel import gettext as _
from config import Config

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    lang = session.get('lang', 'ar')
    total_diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).count()
    total_plants = Plant.query.filter_by(user_id=current_user.id).count()
    total_chats = ChatSession.query.filter_by(user_id=current_user.id).count()

    this_month = datetime.utcnow().replace(day=1)
    month_diagnoses = Diagnosis.query.filter(
        Diagnosis.user_id == current_user.id,
        Diagnosis.timestamp >= this_month
    ).count()

    recent_diagnoses = Diagnosis.query.filter_by(user_id=current_user.id)\
        .order_by(Diagnosis.timestamp.desc()).limit(5).all()

    recent_plants = Plant.query.filter_by(user_id=current_user.id)\
        .order_by(Plant.updated_at.desc()).limit(4).all()

    avg_confidence = db.session.query(db.func.avg(Diagnosis.confidence))\
        .filter(Diagnosis.user_id == current_user.id).scalar() or 0

    return render_template('dashboard/index.html',
                         total_diagnoses=total_diagnoses,
                         total_plants=total_plants,
                         total_chats=total_chats,
                         month_diagnoses=month_diagnoses,
                         recent_diagnoses=[d.to_dict(lang) for d in recent_diagnoses],
                         recent_plants=[p.to_dict() for p in recent_plants],
                         avg_confidence=round(float(avg_confidence) * 100, 1),
                         lang=lang)

@dashboard_bp.route('/diagnoses')
@login_required
def diagnoses():
    lang = session.get('lang', 'ar')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '')
    plant_filter = request.args.get('plant', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Diagnosis.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(
            db.or_(
                Diagnosis.disease_name_ar.ilike(f'%{search}%'),
                Diagnosis.disease_name_en.ilike(f'%{search}%'),
                Diagnosis.disease_name_de.ilike(f'%{search}%'),
                Diagnosis.disease_class.ilike(f'%{search}%')
            )
        )
    if plant_filter:
        query = query.filter(Diagnosis.plant_id == int(plant_filter))
    if date_from:
        query = query.filter(Diagnosis.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Diagnosis.timestamp <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))

    query = query.order_by(Diagnosis.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    diagnoses_list = [d.to_dict(lang) for d in pagination.items]

    user_plants = Plant.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard/diagnoses.html',
                         diagnoses=diagnoses_list,
                         pagination=pagination,
                         user_plants=user_plants,
                         search=search,
                         plant_filter=plant_filter,
                         date_from=date_from,
                         date_to=date_to,
                         lang=lang)

@dashboard_bp.route('/diagnoses/<diagnosis_id>/delete', methods=['POST'])
@login_required
def delete_diagnosis(diagnosis_id):
    diagnosis = Diagnosis.query.filter_by(id=diagnosis_id, user_id=current_user.id).first_or_404()
    if diagnosis.image_path:
        img_path = os.path.join(Config.UPLOAD_FOLDER, diagnosis.image_path)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(diagnosis)
    db.session.commit()
    flash(_('Diagnosis deleted.'), 'success')
    return redirect(url_for('dashboard.diagnoses'))

@dashboard_bp.route('/diagnoses/export')
@login_required
def export_diagnoses():
    import csv
    import io
    lang = session.get('lang', 'ar')
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id)\
        .order_by(Diagnosis.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Disease', 'Confidence', 'Latitude', 'Longitude', 'Rating'])
    for d in diagnoses:
        name = d.disease_name_ar if lang == 'ar' else d.disease_name_en if lang == 'en' else d.disease_name_de
        writer.writerow([d.id, d.timestamp.strftime('%Y-%m-%d %H:%M'), name,
                        f'{d.confidence:.2%}', d.latitude, d.longitude, d.user_rating])

    response_headers = {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=diagnoses_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    }
    return output.getvalue(), response_headers

@dashboard_bp.route('/plants')
@login_required
def plants():
    lang = session.get('lang', 'ar')
    user_plants = Plant.query.filter_by(user_id=current_user.id)\
        .order_by(Plant.updated_at.desc()).all()
    return render_template('dashboard/plants.html',
                         plants=[p.to_dict() for p in user_plants],
                         lang=lang)

@dashboard_bp.route('/plants/add', methods=['GET', 'POST'])
@login_required
def add_plant():
    form = PlantForm()
    if form.validate_on_submit():
        plant = Plant(
            user_id=current_user.id,
            name=form.name.data,
            plant_type=form.plant_type.data,
            planting_date=form.planting_date.data,
            location=form.location.data,
            notes=form.notes.data
        )
        db.session.add(plant)
        db.session.commit()
        flash(_('Plant added successfully!'), 'success')
        return redirect(url_for('dashboard.plant_detail', plant_id=plant.id))
    return render_template('dashboard/add_plant.html', form=form)

@dashboard_bp.route('/plants/<int:plant_id>')
@login_required
def plant_detail(plant_id):
    lang = session.get('lang', 'ar')
    plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    diagnoses = Diagnosis.query.filter_by(plant_id=plant.id)\
        .order_by(Diagnosis.timestamp.desc()).all()
    care_logs = CareLog.query.filter_by(plant_id=plant.id)\
        .order_by(CareLog.timestamp.desc()).all()
    health_chart = get_plant_health_chart(plant.id)
    return render_template('dashboard/plant_detail.html',
                         plant=plant.to_dict(),
                         diagnoses=[d.to_dict(lang) for d in diagnoses],
                         care_logs=[c.to_dict() for c in care_logs],
                         health_chart=json.dumps(health_chart),
                         lang=lang)

@dashboard_bp.route('/plants/<int:plant_id>/edit', methods=['POST'])
@login_required
def edit_plant(plant_id):
    plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if data:
        plant.name = data.get('name', plant.name)
        plant.plant_type = data.get('plant_type', plant.plant_type)
        plant.location = data.get('location', plant.location)
        plant.notes = data.get('notes', plant.notes)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@dashboard_bp.route('/plants/<int:plant_id>/delete', methods=['POST'])
@login_required
def delete_plant(plant_id):
    plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    db.session.delete(plant)
    db.session.commit()
    flash(_('Plant deleted.'), 'success')
    return redirect(url_for('dashboard.plants'))

@dashboard_bp.route('/plants/<int:plant_id>/care/add', methods=['POST'])
@login_required
def add_care_log(plant_id):
    plant = Plant.query.filter_by(id=plant_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if data:
        log = CareLog(
            plant_id=plant.id,
            action_type=data.get('action_type'),
            notes=data.get('notes')
        )
        db.session.add(log)
        if data.get('action_type') == 'treatment':
            plant.health_status = 'recovering'
        db.session.commit()
        return jsonify({'success': True, 'log': log.to_dict()})
    return jsonify({'success': False}), 400

@dashboard_bp.route('/chats')
@login_required
def chats():
    lang = session.get('lang', 'ar')
    user_sessions = ChatSession.query.filter_by(user_id=current_user.id)\
        .order_by(ChatSession.updated_at.desc()).all()
    return render_template('dashboard/chats.html',
                         sessions=[s.to_dict() for s in user_sessions],
                         lang=lang)

@dashboard_bp.route('/chats/<session_id>')
@login_required
def chat_detail(session_id):
    lang = session.get('lang', 'ar')
    chat_session = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.id).first_or_404()
    messages = ChatMessage.query.filter_by(session_id=chat_session.id)\
        .order_by(ChatMessage.timestamp).all()
    return render_template('dashboard/chat_detail.html',
                         chat_session=chat_session.to_dict(),
                         messages=[m.to_dict() for m in messages],
                         lang=lang)

@dashboard_bp.route('/chats/<session_id>/delete', methods=['POST'])
@login_required
def delete_chat(session_id):
    chat_session = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.id).first_or_404()
    ChatMessage.query.filter_by(session_id=chat_session.id).delete()
    db.session.delete(chat_session)
    db.session.commit()
    flash(_('Chat deleted.'), 'success')
    return redirect(url_for('dashboard.chats'))

@dashboard_bp.route('/statistics')
@login_required
def statistics():
    lang = session.get('lang', 'ar')
    return render_template('dashboard/statistics.html', lang=lang)

@dashboard_bp.route('/api/statistics')
@login_required
def api_statistics():
    lang = session.get('lang', 'ar')
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id)\
        .order_by(Diagnosis.timestamp).all()

    disease_distribution = {}
    monthly_trend = {}
    plant_type_dist = {}
    confidence_dist = []

    for d in diagnoses:
        name = d.disease_name_ar if lang == 'ar' else d.disease_name_en if lang == 'en' else d.disease_name_de
        disease_distribution[name] = disease_distribution.get(name, 0) + 1

        month_key = d.timestamp.strftime('%Y-%m')
        monthly_trend[month_key] = monthly_trend.get(month_key, 0) + 1

        plant_name = d.disease_class.split('___')[0] if '___' in d.disease_class else 'Unknown'
        plant_type_dist[plant_name] = plant_type_dist.get(plant_name, 0) + 1

        confidence_dist.append(round(float(d.confidence) * 100, 1))

    top_diseases = dict(sorted(disease_distribution.items(), key=lambda x: x[1], reverse=True)[:10])

    return jsonify({
        'total': len(diagnoses),
        'disease_distribution': [{'label': k, 'value': v} for k, v in top_diseases.items()],
        'monthly_trend': [{'label': k, 'value': v} for k, v in sorted(monthly_trend.items())],
        'plant_distribution': [{'label': k, 'value': v} for k, v in sorted(plant_type_dist.items(), key=lambda x: x[1], reverse=True)],
        'confidence_distribution': confidence_dist,
        'avg_confidence': round(sum(confidence_dist) / len(confidence_dist), 1) if confidence_dist else 0
    })

@dashboard_bp.route('/api/locations')
@login_required
def api_locations():
    diagnoses = Diagnosis.query.filter(
        Diagnosis.user_id == current_user.id,
        Diagnosis.latitude.isnot(None),
        Diagnosis.longitude.isnot(None)
    ).all()
    return jsonify([{
        'lat': d.latitude,
        'lng': d.longitude,
        'name': d.disease_name_en,
        'date': d.timestamp.strftime('%Y-%m-%d') if d.timestamp else '',
        'id': d.id
    } for d in diagnoses])

@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash(_('Password changed successfully!'), 'success')
            return redirect(url_for('dashboard.settings'))
        flash(_('Current password is incorrect.'), 'danger')
    return render_template('dashboard/settings.html', form=form)

@dashboard_bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    from flask_login import logout_user
    ChatMessage.query.filter(ChatMessage.session.has(user_id=current_user.id)).delete()
    ChatSession.query.filter_by(user_id=current_user.id).delete()
    CareLog.query.filter(CareLog.plant.has(user_id=current_user.id)).delete()
    Plant.query.filter_by(user_id=current_user.id).delete()
    Diagnosis.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash(_('Your account has been deleted.'), 'info')
    return redirect(url_for('index'))

def get_plant_health_chart(plant_id):
    diagnoses = Diagnosis.query.filter_by(plant_id=plant_id)\
        .order_by(Diagnosis.timestamp).all()
    healthy_count = sum(1 for d in diagnoses if 'healthy' in d.disease_class.lower())
    sick_count = len(diagnoses) - healthy_count
    return {
        'healthy': healthy_count,
        'sick': sick_count,
        'total': len(diagnoses)
    }
