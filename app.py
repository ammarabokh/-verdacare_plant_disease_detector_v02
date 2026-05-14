import os
import uuid
import traceback
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_babel import Babel, gettext as _
from flask_session import Session
from flask_login import LoginManager, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from config import Config
from models.models import db, User, Diagnosis, ChatSession, ChatMessage
from utils.image_processor import (
    preprocess_image,
    enhanced_preprocess_image,
    check_image_quality,
)
from utils.model_loader import get_model_loader
from utils.report_generator import generate_report
from chatbot.chatbot_logic import chatbot

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Persist server-side errors when terminal output is not visible (e.g., IDE run panel).
log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app_errors.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)


def _is_ajax():
    """Check if request is AJAX (via form field or X-Requested-With header)."""
    return (
        request.form.get('_ajax') == '1' or
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )


os.makedirs('flask_session', exist_ok=True)
os.makedirs('instance', exist_ok=True)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

babel = Babel()
sess = Session()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

db.init_app(app)
babel.init_app(app)
sess.init_app(app)
login_manager.init_app(app)

app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_locale():
    return session.get(
        'lang',
        request.accept_languages.best_match(Config.LANGUAGES) or 'ar'
    )

babel.init_app(app, locale_selector=get_locale)

# Register blueprints
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)


def bootstrap_admin_user():
    """Create or promote an admin user once using environment variables."""
    if not Config.ADMIN_BOOTSTRAP_ENABLED:
        return

    if User.query.filter_by(is_admin=True).first():
        app.logger.info("[admin-bootstrap] skipped: admin already exists")
        return

    username = Config.ADMIN_BOOTSTRAP_USERNAME
    email = Config.ADMIN_BOOTSTRAP_EMAIL
    password = Config.ADMIN_BOOTSTRAP_PASSWORD
    full_name = Config.ADMIN_BOOTSTRAP_FULL_NAME

    if not username or not email or not password:
        app.logger.warning(
            "[admin-bootstrap] skipped: missing required env vars "
            "(ADMIN_BOOTSTRAP_USERNAME/EMAIL/PASSWORD)"
        )
        return

    user = User.query.filter(
        db.or_(User.username == username, User.email == email)
    ).first()

    if user:
        user.is_admin = True
        user.username = username
        user.email = email
        user.set_password(password)
        if full_name:
            user.full_name = full_name
        db.session.commit()
        app.logger.info(f"[admin-bootstrap] existing user promoted to admin: {username}")
        return

    user = User(
        username=username,
        email=email,
        full_name=full_name or None,
        is_admin=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    app.logger.info(f"[admin-bootstrap] admin user created: {username}")


with app.app_context():
    db.create_all()
    bootstrap_admin_user()

@app.before_request
def before_request():
    if current_user.is_authenticated:
        if 'lang' not in session:
            session['lang'] = current_user.language_preference

@app.route('/')
def index():
    return render_template('index.html', lang=get_locale())

@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in Config.LANGUAGES:
        session['lang'] = lang
        if current_user.is_authenticated:
            current_user.language_preference = lang
            db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/diagnose', methods=['POST'])
def diagnose():
    request_id = str(uuid.uuid4())
    if 'image' not in request.files:
        return jsonify({'error': _('No image uploaded')}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': _('No file selected')}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': _('Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, WEBP)')}), 400

    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    app.logger.info(f"[diagnose:{request_id}] saving upload to: {filepath}")
    file.save(filepath)

    is_valid, reason = check_image_quality(filepath)
    if not is_valid:
        os.remove(filepath)
        quality_tips = {
            'too_small': '📏 ' + _('Get closer to the leaf so it fills the frame'),
            'too_dark': '🌑 ' + _('Lighting is too weak. Photograph in daylight'),
            'too_bright': '☀️ ' + _('Image is overexposed. Avoid direct sunlight or shoot in shade'),
            'blurry': '📷 ' + _('Image is blurry. Steady the camera and avoid hand shake'),
            'error': '⚠️ ' + _('Could not process the image. Try another photo'),
        }
        error_message = quality_tips.get(reason, _('Image quality is insufficient. Please try again.'))
        if _is_ajax():
            return jsonify({'error': error_message, 'code': reason}), 400
        return jsonify({'error': error_message}), 400

    try:
        app.logger.info(f"[diagnose:{request_id}] quality ok, start preprocessing")
        model_loader = get_model_loader()
        preprocessed = enhanced_preprocess_image(
            filepath,
            max_dim=Config.MAX_IMAGE_DIMENSION,
            working_size=Config.WORKING_IMAGE_SIZE,
            use_segmentation=Config.USE_BACKGROUND_SEGMENTATION,
            green_hue_low=Config.GREEN_HUE_LOW,
            green_hue_high=Config.GREEN_HUE_HIGH,
            saturation_min=Config.SATURATION_THRESHOLD,
            value_min=Config.VALUE_THRESHOLD,
            padding_ratio=Config.PADDING_RATIO,
            min_contour_ratio=Config.MIN_CONTOUR_AREA_RATIO,
            background_color=Config.BACKGROUND_COLOR,
            clahe_clip=Config.CLAHE_CLIP_LIMIT,
            clahe_tile=Config.CLAHE_TILE_SIZE,
            gaussian_ksize=Config.GAUSSIAN_BLUR_KSIZE,
            gaussian_sigma=Config.GAUSSIAN_BLUR_SIGMA,
        )
        app.logger.info(f"[diagnose:{request_id}] preprocessing done, start prediction")
        predicted_class, confidence, disease_info = model_loader.predict(preprocessed)
        app.logger.info(f"[diagnose:{request_id}] prediction done class={predicted_class} confidence={confidence}")

        info_ar = disease_info.get('ar', {}) if disease_info else {}
        info_en = disease_info.get('en', {}) if disease_info else {}
        info_de = disease_info.get('de', {}) if disease_info else {}

        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        location_name = request.form.get('location_name', '').strip()
        plant_id = request.form.get('plant_id', type=int)

        # Reverse geocode if we have coordinates but no location_name
        if latitude and longitude and not location_name:
            try:
                import requests
                resp = requests.get(
                    'https://nominatim.openstreetmap.org/reverse',
                    params={'format': 'json', 'lat': latitude, 'lon': longitude,
                            'accept-language': get_locale()},
                    headers={'User-Agent': 'VerdaCare/2.0'},
                    timeout=5
                )
                if resp.ok:
                    data = resp.json()
                    location_name = data.get('display_name', '')
            except Exception:
                pass

        diagnosis = Diagnosis(
            user_id=current_user.id if current_user.is_authenticated else None,
            plant_id=plant_id if plant_id else None,
            disease_class=predicted_class,
            disease_name_ar=info_ar.get('name', predicted_class),
            disease_name_en=info_en.get('name', predicted_class),
            disease_name_de=info_de.get('name', predicted_class),
            confidence=confidence,
            image_path=filename,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name or None
        )
        db.session.add(diagnosis)
        db.session.commit()

        session['last_diagnosis'] = {
            'id': diagnosis.id,
            'class': predicted_class,
            'name_ar': info_ar.get('name', predicted_class),
            'name_en': info_en.get('name', predicted_class),
            'name_de': info_de.get('name', predicted_class),
            'confidence': confidence
        }

        if _is_ajax():
            return jsonify({
                'success': True,
                'diagnosis_id': diagnosis.id,
                'disease_class': predicted_class,
                'disease_name_ar': info_ar.get('name', predicted_class),
                'disease_name_en': info_en.get('name', predicted_class),
                'disease_name_de': info_de.get('name', predicted_class),
                'confidence': confidence,
                'location_name': location_name or '',
                'description': info_ar.get('description', '') if get_locale() == 'ar' else info_en.get('description', ''),
                'symptoms': info_ar.get('symptoms', '') if get_locale() == 'ar' else info_en.get('symptoms', ''),
                'treatment': info_ar.get('treatment', '') if get_locale() == 'ar' else info_en.get('treatment', ''),
                'prevention': info_ar.get('prevention', '') if get_locale() == 'ar' else info_en.get('prevention', ''),
                'products': info_ar.get('products', []) if get_locale() == 'ar' else info_en.get('products', []),
            })

        return redirect(url_for('result', diagnosis_id=diagnosis.id))
    except RuntimeError as e:
        app.logger.error(f"[diagnose:{request_id}] runtime error: {e}")
        app.logger.error(traceback.format_exc())
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e), 'code': 'MODEL_NOT_READY', 'request_id': request_id}), 503
    except Exception as e:
        app.logger.error(f"[diagnose:{request_id}] unexpected error: {e}")
        app.logger.error(traceback.format_exc())
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e), 'request_id': request_id}), 500

@app.route('/result/<diagnosis_id>')
def result(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    model_loader = get_model_loader()
    disease_info = model_loader.get_disease_info(diagnosis.disease_class)
    lang = get_locale()

    disease_name = diagnosis.disease_name_ar
    if lang == 'en':
        disease_name = diagnosis.disease_name_en
    elif lang == 'de':
        disease_name = diagnosis.disease_name_de

    if not disease_info:
        return render_template('result.html',
                             diagnosis_id=diagnosis_id,
                             disease_name=disease_name,
                             confidence=diagnosis.confidence,
                             uploaded_image=url_for('static', filename=f'uploads/{diagnosis.image_path}'),
                             description=_('No information available'),
                             symptoms=_('No information available'),
                             treatment=_('No information available'),
                             prevention=_('No information available'),
                             products=[], user_rating=diagnosis.user_rating, lang=lang)

    info = disease_info.get(lang, disease_info.get('en', {}))
    return render_template('result.html',
                         diagnosis_id=diagnosis_id,
                         disease_name=info.get('name', disease_name),
                         confidence=diagnosis.confidence,
                         uploaded_image=url_for('static', filename=f'uploads/{diagnosis.image_path}'),
                         description=info.get('description', ''),
                         symptoms=info.get('symptoms', ''),
                         treatment=info.get('treatment', ''),
                         prevention=info.get('prevention', ''),
                         products=info.get('products', []),
                         user_rating=diagnosis.user_rating, lang=lang)

@app.route('/rate/<diagnosis_id>', methods=['POST'])
def rate_diagnosis(diagnosis_id):
    data = request.get_json()
    rating = data.get('rating')
    if rating not in [1, 2, 3, 4, 5]:
        return jsonify({'error': 'Invalid rating'}), 400
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    diagnosis.user_rating = rating
    db.session.commit()
    return jsonify({'success': True, 'message': _('Thank you for your feedback!')})

@app.route('/report/<diagnosis_id>')
def report(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    model_loader = get_model_loader()
    disease_info = model_loader.get_disease_info(diagnosis.disease_class)
    if not disease_info:
        return "Report not available", 404
    info = disease_info.get(get_locale(), disease_info.get('en', {}))
    return generate_report(disease_info, diagnosis.confidence, get_locale())

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': _('Empty message')}), 400

    session_id = session.get('chat_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['chat_session_id'] = session_id

    db_session = None
    if current_user.is_authenticated:
        db_session = ChatSession.query.filter_by(session_id=session_id).first()
        if not db_session:
            db_session = ChatSession(
                user_id=current_user.id,
                session_id=session_id,
                title=message[:100]
            )
            db.session.add(db_session)
            db.session.commit()

    context = None
    last_diag = session.get('last_diagnosis')
    if last_diag:
        lang = get_locale()
        if lang == 'ar':
            context = last_diag['name_ar']
        elif lang == 'de':
            context = last_diag.get('name_de', last_diag['name_en'])
        else:
            context = last_diag['name_en']

    response = chatbot.process_message(message, session_id, get_locale(), context)

    if db_session:
        for role, content in [('user', message), ('assistant', response)]:
            msg = ChatMessage(session_id=db_session.id, role=role, content=content)
            db.session.add(msg)
        db.session.commit()

    return jsonify({'response': response})

@app.route('/chat/clear', methods=['POST'])
def clear_chat():
    session_id = session.get('chat_session_id')
    if session_id:
        chatbot.clear_conversation(session_id)
    return jsonify({'status': 'ok'})

@app.route('/plant-types')
def plant_types_api():
    from models.models import PLANT_TYPES
    return jsonify(PLANT_TYPES)

@app.context_processor
def utility_processor():
    return dict(current_year=datetime.utcnow().year)

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', lang=get_locale()), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': _('Internal server error')}), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    # In debug mode, initialize once only in Werkzeug's reloader child process.
    if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        get_model_loader()
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
