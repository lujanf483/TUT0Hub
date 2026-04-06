from datetime import datetime, timedelta
from flask_login import UserMixin
from bson import ObjectId
import bcrypt
import secrets
import hashlib

# Se importa la db desde el modulo principal
from app import get_db


# -------------------------------------------------------
# Clase User compatible con Flask-Login
# -------------------------------------------------------

class User(UserMixin):
    def __init__(self, data: dict):
        self._data = data

    # --- Propiedades que mapean al documento de MongoDB ---

    @property
    def id(self):
        return str(self._data['_id'])

    @property
    def username(self):
        return self._data.get('username', '')

    @property
    def email(self):
        return self._data.get('email', '')

    @property
    def password_hash(self):
        return self._data.get('password_hash', '')

    @property
    def role(self):
        return self._data.get('role', 'user')

    @role.setter
    def role(self, value):
        self._data['role'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'role': value}})

    @property
    def is_active(self):
        return self._data.get('is_active', True)

    @is_active.setter
    def is_active(self, value):
        self._data['is_active'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'is_active': value}})

    @property
    def created_at(self):
        return self._data.get('created_at', datetime.utcnow())

    @property
    def mfa_enabled(self):
        return self._data.get('mfa_enabled', False)

    @mfa_enabled.setter
    def mfa_enabled(self, value):
        self._data['mfa_enabled'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'mfa_enabled': value}})

    @property
    def mfa_secret(self):
        return self._data.get('mfa_secret')

    @mfa_secret.setter
    def mfa_secret(self, value):
        self._data['mfa_secret'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'mfa_secret': value}})

    @property
    def mfa_code(self):
        return self._data.get('mfa_code')

    @mfa_code.setter
    def mfa_code(self, value):
        self._data['mfa_code'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'mfa_code': value}})

    @property
    def mfa_code_expiry(self):
        return self._data.get('mfa_code_expiry')

    @mfa_code_expiry.setter
    def mfa_code_expiry(self, value):
        self._data['mfa_code_expiry'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'mfa_code_expiry': value}})

    @property
    def secret_question(self):
        return self._data.get('secret_question')

    @secret_question.setter
    def secret_question(self, value):
        self._data['secret_question'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'secret_question': value}})

    @property
    def theme(self):
        return self._data.get('theme', 'dark')

    @theme.setter
    def theme(self, value):
        self._data['theme'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'theme': value}})

    @property
    def language(self):
        return self._data.get('language', 'es')

    @language.setter
    def language(self, value):
        self._data['language'] = value
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'language': value}})

    @property
    def favorites(self):
        docs = get_db().favorites.find({'user_id': self.id})
        return [Favorite(d) for d in docs]

    # --- Metodos de contrasena ---

    def set_password(self, password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        self._data['password_hash'] = hashed
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'password_hash': hashed}})

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def set_secret_answer(self, answer):
        hashed = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        self._data['secret_answer_hash'] = hashed
        get_db().users.update_one({'_id': self._data['_id']}, {'$set': {'secret_answer_hash': hashed}})

    def check_secret_answer(self, answer):
        stored = self._data.get('secret_answer_hash')
        if not stored:
            return False
        return stored == hashlib.sha256(answer.lower().strip().encode()).hexdigest()

    def has_role(self, *roles):
        return self.role in roles

    # --- Metodos de consulta (equivalentes a User.query.xxx) ---

    @staticmethod
    def get_by_id(user_id):
        try:
            doc = get_db().users.find_one({'_id': ObjectId(user_id)})
            return User(doc) if doc else None
        except Exception:
            return None

    @staticmethod
    def get_by_username(username):
        doc = get_db().users.find_one({'username': username})
        return User(doc) if doc else None

    @staticmethod
    def get_by_email(email):
        doc = get_db().users.find_one({'email': email})
        return User(doc) if doc else None

    @staticmethod
    def get_by_username_or_email(value):
        doc = get_db().users.find_one({'$or': [{'username': value}, {'email': value}]})
        return User(doc) if doc else None

    @staticmethod
    def get_all():
        docs = get_db().users.find().sort('created_at', -1)
        return [User(d) for d in docs]

    @staticmethod
    def create(username, email, password, role='user'):
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        doc = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'mfa_enabled': False,
            'mfa_secret': None,
            'mfa_code': None,
            'mfa_code_expiry': None,
            'secret_question': None,
            'secret_answer_hash': None,
            'theme': 'dark',
            'language': 'es'
        }
        result = get_db().users.insert_one(doc)
        doc['_id'] = result.inserted_id
        return User(doc)


# -------------------------------------------------------
# UserSession
# -------------------------------------------------------

class UserSession:
    def __init__(self, data: dict):
        self._data = data

    @property
    def id(self):
        return str(self._data['_id'])

    @property
    def user_id(self):
        return self._data.get('user_id')

    @property
    def session_token(self):
        return self._data.get('session_token')

    @property
    def ip_address(self):
        return self._data.get('ip_address')

    @property
    def user_agent(self):
        return self._data.get('user_agent', '')

    @property
    def created_at(self):
        return self._data.get('created_at', datetime.utcnow())

    @property
    def last_active(self):
        return self._data.get('last_active', datetime.utcnow())

    @property
    def is_active(self):
        return self._data.get('is_active', True)

    @is_active.setter
    def is_active(self, value):
        self._data['is_active'] = value
        get_db().user_sessions.update_one({'_id': self._data['_id']}, {'$set': {'is_active': value}})

    @property
    def user(self):
        return User.get_by_id(self.user_id)

    @staticmethod
    def create_session(user_id, ip_address, user_agent):
        token = secrets.token_hex(32)
        doc = {
            'user_id': user_id,
            'session_token': token,
            'ip_address': ip_address,
            'user_agent': (user_agent or '')[:255],
            'created_at': datetime.utcnow(),
            'last_active': datetime.utcnow(),
            'is_active': True
        }
        result = get_db().user_sessions.insert_one(doc)
        doc['_id'] = result.inserted_id
        return UserSession(doc)

    @staticmethod
    def get_by_token(token):
        doc = get_db().user_sessions.find_one({'session_token': token})
        return UserSession(doc) if doc else None

    @staticmethod
    def get_by_id(session_id):
        try:
            doc = get_db().user_sessions.find_one({'_id': ObjectId(session_id)})
            return UserSession(doc) if doc else None
        except Exception:
            return None

    @staticmethod
    def get_active_by_user(user_id):
        docs = get_db().user_sessions.find(
            {'user_id': user_id, 'is_active': True}
        ).sort('last_active', -1)
        return [UserSession(d) for d in docs]

    @staticmethod
    def count_active():
        return get_db().user_sessions.count_documents({'is_active': True})

    @staticmethod
    def deactivate_all_for_user(user_id):
        get_db().user_sessions.update_many(
            {'user_id': user_id, 'is_active': True},
            {'$set': {'is_active': False}}
        )


# -------------------------------------------------------
# RefreshToken
# -------------------------------------------------------

class RefreshToken:
    def __init__(self, data: dict):
        self._data = data

    @property
    def id(self):
        return str(self._data['_id'])

    @property
    def user_id(self):
        return self._data.get('user_id')

    @property
    def token(self):
        return self._data.get('token')

    @property
    def expires_at(self):
        return self._data.get('expires_at')

    @property
    def revoked(self):
        return self._data.get('revoked', False)

    @property
    def user(self):
        return User.get_by_id(self.user_id)

    def is_valid(self):
        return not self.revoked and self.expires_at > datetime.utcnow()

    @staticmethod
    def create(user_id, token, expires_at):
        doc = {
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at,
            'revoked': False,
            'created_at': datetime.utcnow()
        }
        result = get_db().refresh_tokens.insert_one(doc)
        doc['_id'] = result.inserted_id
        return RefreshToken(doc)

    @staticmethod
    def get_by_token(token):
        doc = get_db().refresh_tokens.find_one({'token': token})
        return RefreshToken(doc) if doc else None

    def revoke(self):
        self._data['revoked'] = True
        get_db().refresh_tokens.update_one({'_id': self._data['_id']}, {'$set': {'revoked': True}})

    @staticmethod
    def revoke_all_for_user(user_id):
        get_db().refresh_tokens.update_many(
            {'user_id': user_id, 'revoked': False},
            {'$set': {'revoked': True}}
        )


# -------------------------------------------------------
# PasswordReset
# -------------------------------------------------------

class PasswordReset:
    def __init__(self, data: dict):
        self._data = data

    @property
    def id(self):
        return str(self._data['_id'])

    @property
    def user_id(self):
        return self._data.get('user_id')

    @property
    def token(self):
        return self._data.get('token')

    @property
    def method(self):
        return self._data.get('method')

    @property
    def code(self):
        return self._data.get('code')

    @property
    def expires_at(self):
        return self._data.get('expires_at')

    @property
    def used(self):
        return self._data.get('used', False)

    @used.setter
    def used(self, value):
        self._data['used'] = value
        get_db().password_resets.update_one({'_id': self._data['_id']}, {'$set': {'used': value}})

    @property
    def attempts(self):
        return self._data.get('attempts', 0)

    @attempts.setter
    def attempts(self, value):
        self._data['attempts'] = value
        get_db().password_resets.update_one({'_id': self._data['_id']}, {'$set': {'attempts': value}})

    def is_valid(self):
        return not self.used and self.expires_at > datetime.utcnow() and self.attempts < 5

    @staticmethod
    def create(user_id, token, method, expires_at, code=None):
        doc = {
            'user_id': user_id,
            'token': token,
            'method': method,
            'code': code,
            'expires_at': expires_at,
            'used': False,
            'attempts': 0,
            'created_at': datetime.utcnow()
        }
        result = get_db().password_resets.insert_one(doc)
        doc['_id'] = result.inserted_id
        return PasswordReset(doc)

    @staticmethod
    def get_by_token(token):
        doc = get_db().password_resets.find_one({'token': token})
        return PasswordReset(doc) if doc else None

    @staticmethod
    def invalidate_pending_for_user(user_id):
        get_db().password_resets.update_many(
            {'user_id': user_id, 'used': False},
            {'$set': {'used': True}}
        )


# -------------------------------------------------------
# Favorite
# -------------------------------------------------------

class Favorite:
    def __init__(self, data: dict):
        self._data = data

    @property
    def id(self):
        return str(self._data['_id'])

    @property
    def user_id(self):
        return self._data.get('user_id')

    @property
    def video_id(self):
        return self._data.get('video_id')

    @property
    def title(self):
        return self._data.get('title', '')

    @property
    def thumbnail(self):
        return self._data.get('thumbnail', '')

    @property
    def channel(self):
        return self._data.get('channel', '')

    @property
    def description(self):
        return self._data.get('description', '')

    @property
    def created_at(self):
        return self._data.get('created_at', datetime.utcnow())

    @staticmethod
    def get_by_user(user_id):
        docs = get_db().favorites.find({'user_id': user_id})
        return [Favorite(d) for d in docs]

    @staticmethod
    def get_by_user_and_video(user_id, video_id):
        doc = get_db().favorites.find_one({'user_id': user_id, 'video_id': video_id})
        return Favorite(doc) if doc else None

    @staticmethod
    def create(user_id, video_id, title='', channel='', description='', thumbnail=''):
        doc = {
            'user_id': user_id,
            'video_id': video_id,
            'title': title,
            'channel': channel,
            'description': description,
            'thumbnail': thumbnail,
            'created_at': datetime.utcnow()
        }
        result = get_db().favorites.insert_one(doc)
        doc['_id'] = result.inserted_id
        return Favorite(doc)

    def delete(self):
        get_db().favorites.delete_one({'_id': self._data['_id']})