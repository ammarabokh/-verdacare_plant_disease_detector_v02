import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_babel import Babel, gettext as _
from flask_session import Session
from flask_login import LoginManager, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from config import Config
from models.models import db, User, Diagnosis, ChatSession, ChatMessage
from utils.image_processor import preprocess_image, check_image_quality
from utils.model_loader import get_model_loader
from utils.report_generator import generate_report
from chatbot.chatbot_logic import chatbot

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

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

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(dashboard_bp)

with app.app_context():
    db.create_all()

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
    if 'image' not in request.files:
        return jsonify({'error': _('No image uploaded')}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': _('No file selected')}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': _('Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, WEBP)')}), 400

    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    is_valid, message = check_image_quality(filepath)
    if not is_valid:
        os.remove(filepath)
        return jsonify({'error': message}), 400

    try:
        model_loader = get_model_loader()
        preprocessed = preprocess_image(filepath)
        predicted_class, confidence, disease_info = model_loader.predict(preprocessed)

        info_ar = disease_info.get('ar', {}) if disease_info else {}
        info_en = disease_info.get('en', {}) if disease_info else {}
        info_de = disease_info.get('de', {}) if disease_info else {}

        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        plant_id = request.form.get('plant_id', type=int)

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
            longitude=longitude
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

        return redirect(url_for('result', diagnosis_id=diagnosis.id))
    except RuntimeError as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e), 'code': 'MODEL_NOT_READY'}), 503
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

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
    debug_mode = True
    # In debug mode, initialize once only in Werkzeug's reloader child process.
    if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        get_model_loader()
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
