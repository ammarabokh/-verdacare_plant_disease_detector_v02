import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, gettext as _
from flask_session import Session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from config import Config
from utils.image_processor import preprocess_image, check_image_quality
from utils.model_loader import model_loader
from utils.report_generator import generate_report
from chatbot.chatbot_logic import chatbot

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs('flask_session', exist_ok=True)
os.makedirs('instance', exist_ok=True)
# Initialize extensions
db = SQLAlchemy()
babel = Babel()
sess = Session()

db.init_app(app)
babel.init_app(app)
sess.init_app(app)

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Babel locale selector
def get_locale():
    return session.get(
        'lang',
        request.accept_languages.best_match(Config.LANGUAGES) or 'ar'
    )

babel.init_app(app, locale_selector=get_locale)
# Database Models
class Diagnosis(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disease_class = db.Column(db.String(100))
    disease_name_ar = db.Column(db.String(200))
    disease_name_en = db.Column(db.String(200))
    confidence = db.Column(db.Float)
    image_path = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M'),
            'disease_class': self.disease_class,
            'disease_name': self.disease_name_ar if get_locale() == 'ar' else self.disease_name_en,
            'confidence': self.confidence
        }

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html', lang=get_locale())

@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in Config.LANGUAGES:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/diagnose', methods=['POST'])
def diagnose():
    """Handle image upload and diagnosis"""
    if 'image' not in request.files:
        return jsonify({'error': _('No image uploaded')}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': _('No file selected')}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': _('Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, WEBP)')}), 400

    # Save file
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Check image quality
    is_valid, message = check_image_quality(filepath)
    if not is_valid:
        os.remove(filepath)
        return jsonify({'error': message}), 400

    # Process image and predict
    try:
        preprocessed = preprocess_image(filepath)
        predicted_class, confidence, disease_info = model_loader.predict(preprocessed)

        # Get disease names
        info_ar = disease_info.get('ar', {}) if disease_info else {}
        info_en = disease_info.get('en', {}) if disease_info else {}

        disease_name_ar = info_ar.get('name', predicted_class)
        disease_name_en = info_en.get('name', predicted_class)

        # Save to database
        diagnosis = Diagnosis(
            disease_class=predicted_class,
            disease_name_ar=disease_name_ar,
            disease_name_en=disease_name_en,
            confidence=confidence,
            image_path=filename
        )
        db.session.add(diagnosis)
        db.session.commit()

        # Store diagnosis context for chatbot
        session['last_diagnosis'] = {
            'class': predicted_class,
            'name_ar': disease_name_ar,
            'name_en': disease_name_en,
            'confidence': confidence
        }

        # Redirect to result page
        return redirect(url_for('result', diagnosis_id=diagnosis.id))

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

@app.route('/result/<diagnosis_id>')
def result(diagnosis_id):
    """Show diagnosis result"""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)

    # Get disease info
    disease_info = model_loader.get_disease_info(diagnosis.disease_class)

    if not disease_info:
        return render_template('result.html',
                             diagnosis_id=diagnosis_id,
                             disease_name=diagnosis.disease_name_ar if get_locale() == 'ar' else diagnosis.disease_name_en,
                             confidence=diagnosis.confidence,
                             uploaded_image=url_for('static', filename=f'uploads/{diagnosis.image_path}'),
                             description=_('No information available'),
                             symptoms=_('No information available'),
                             treatment=_('No information available'),
                             prevention=_('No information available'),
                             products=[],
                             lang=get_locale())

    info = disease_info.get(get_locale(), disease_info.get('en', {}))

    return render_template('result.html',
                         diagnosis_id=diagnosis_id,
                         disease_name=info.get('name', diagnosis.disease_name_ar if get_locale() == 'ar' else diagnosis.disease_name_en),
                         confidence=diagnosis.confidence,
                         uploaded_image=url_for('static', filename=f'uploads/{diagnosis.image_path}'),
                         description=info.get('description', _('No description available')),
                         symptoms=info.get('symptoms', _('No symptoms information')),
                         treatment=info.get('treatment', _('No treatment information')),
                         prevention=info.get('prevention', _('No prevention information')),
                         products=info.get('products', []),
                         lang=get_locale())

@app.route('/report/<diagnosis_id>')
def report(diagnosis_id):
    """Generate printable HTML report"""
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    disease_info = model_loader.get_disease_info(diagnosis.disease_class)

    if not disease_info:
        return "Report not available", 404

    info = disease_info.get(get_locale(), disease_info.get('en', {}))

    html_report = generate_report(disease_info, diagnosis.confidence, get_locale())
    return html_report

# Chatbot Routes
@app.route('/chat', methods=['POST'])
def chat():
    """Handle chatbot messages"""
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': _('Empty message')}), 400

    # Get session ID for memory
    session_id = session.get('chat_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['chat_session_id'] = session_id

    # Get context from last diagnosis
    context = None
    last_diag = session.get('last_diagnosis')
    if last_diag:
        context = last_diag['name_ar'] if get_locale() == 'ar' else last_diag['name_en']

    # Process message
    response = chatbot.process_message(
        message=message,
        session_id=session_id,
        lang=get_locale(),
        context=context
    )

    return jsonify({'response': response})

@app.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    session_id = session.get('chat_session_id')
    if session_id:
        chatbot.clear_conversation(session_id)
    return jsonify({'status': 'ok'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', lang=get_locale()), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': _('Internal server error')}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
