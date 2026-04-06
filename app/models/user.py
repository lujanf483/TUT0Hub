from datetime import datetime
from flask_login import UserMixin
from app import db
import bcrypt
import secrets
import hashlib


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    mfa_code = db.Column(db.String(10))
    mfa_code_expiry = db.Column(db.DateTime)

    secret_question = db.Column(db.String(200))
    secret_answer_hash = db.Column(db.String(255))

    theme = db.Column(db.String(20), default='dark')
    language = db.Column(db.String(10), default='es')

    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    refresh_tokens = db.relationship('RefreshToken', backref='user', lazy=True, cascade='all, delete-orphan')
    password_resets = db.relationship('PasswordReset', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def set_secret_answer(self, answer):
        self.secret_answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()

    def check_secret_answer(self, answer):
        if not self.secret_answer_hash:
            return False
        return self.secret_answer_hash == hashlib.sha256(answer.lower().strip().encode()).hexdigest()

    def has_role(self, *roles):
        return self.role in roles


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def create_session(user_id, ip_address, user_agent):
        token = secrets.token_hex(32)
        s = UserSession(
            user_id=user_id,
            session_token=token,
            ip_address=ip_address,
            user_agent=(user_agent or '')[:255]
        )
        db.session.add(s)
        db.session.commit()
        return s


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        return not self.revoked and self.expires_at > datetime.utcnow()


class PasswordReset(db.Model):
    __tablename__ = 'password_resets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    method = db.Column(db.String(20))
    code = db.Column(db.String(10))
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attempts = db.Column(db.Integer, default=0)

    def is_valid(self):
        return not self.used and self.expires_at > datetime.utcnow() and self.attempts < 5


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200))
    thumbnail = db.Column(db.String(500))
    channel = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)