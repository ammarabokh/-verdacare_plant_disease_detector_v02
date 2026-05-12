import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    language_preference = db.Column(db.String(5), default='ar')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    diagnoses = db.relationship('Diagnosis', backref='user', lazy='dynamic')
    plants = db.relationship('Plant', backref='owner', lazy='dynamic')
    chat_sessions = db.relationship('ChatSession', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'profile_image': self.profile_image,
            'language_preference': self.language_preference,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else '',
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M') if self.last_login else ''
        }

class Plant(db.Model):
    __tablename__ = 'plant'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    plant_type = db.Column(db.String(50))
    planting_date = db.Column(db.Date)
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    image = db.Column(db.String(255))
    health_status = db.Column(db.String(20), default='healthy')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    diagnoses = db.relationship('Diagnosis', backref='plant', lazy='dynamic')
    care_logs = db.relationship('CareLog', backref='plant', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'plant_type': self.plant_type,
            'planting_date': self.planting_date.strftime('%Y-%m-%d') if self.planting_date else '',
            'location': self.location,
            'notes': self.notes,
            'image': self.image,
            'health_status': self.health_status,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else '',
            'diagnosis_count': self.diagnoses.count() if hasattr(self, 'diagnoses') else 0
        }

class CareLog(db.Model):
    __tablename__ = 'care_log'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    action_type = db.Column(db.String(50))
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'notes': self.notes,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else ''
        }

class ChatSession(db.Model):
    __tablename__ = 'chat_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(36), unique=True)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic',
                               order_by='ChatMessage.timestamp')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else '',
            'message_count': self.messages.count() if hasattr(self, 'messages') else 0
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%H:%M') if self.timestamp else ''
        }

class Diagnosis(db.Model):
    __tablename__ = 'diagnosis'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disease_class = db.Column(db.String(100))
    disease_name_ar = db.Column(db.String(200))
    disease_name_en = db.Column(db.String(200))
    disease_name_de = db.Column(db.String(200))
    confidence = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_name = db.Column(db.String(255), nullable=True)
    user_rating = db.Column(db.Integer, nullable=True)

    def to_dict(self, lang='ar'):
        name = self.disease_name_ar
        if lang == 'en':
            name = self.disease_name_en
        elif lang == 'de':
            name = self.disease_name_de
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else '',
            'disease_class': self.disease_class,
            'disease_name': name,
            'confidence': self.confidence,
            'image_path': self.image_path,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_name': self.location_name,
            'user_rating': self.user_rating,
            'plant_id': self.plant_id
        }

PLANT_TYPES = [
    'Apple', 'Blueberry', 'Cherry', 'Corn', 'Grape', 'Orange',
    'Peach', 'Pepper', 'Potato', 'Raspberry', 'Soybean',
    'Squash', 'Strawberry', 'Tomato'
]

HEALTH_STATUSES = ['healthy', 'sick', 'recovering']

CARE_ACTIONS = ['watering', 'fertilizing', 'pruning', 'treatment', 'repotting', 'other']
