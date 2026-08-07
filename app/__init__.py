import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from pymongo import MongoClient

# Cargar .env en desarrollo (en Render las variables vienen del panel)
load_dotenv()

login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
csrf = CSRFProtect()
mail = Mail()

# Cliente y base de datos globales
mongo_client = None
mongo_db = None


def get_db():
    """Retorna la instancia de la base de datos. Usar dentro de contexto de app."""
    return mongo_db


def create_app():
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-fallback')
    app.config['YOUTUBE_API_KEY'] = os.environ.get('YOUTUBE_API_KEY', '')

    app.config['MONGODB_URI'] = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/tut0hub')
    app.config['MONGODB_DBNAME'] = os.environ.get('MONGODB_DBNAME', 'tut0hub')

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # Conectar a MongoDB
    global mongo_client, mongo_db
    try:
        mongo_client = MongoClient(app.config['MONGODB_URI'], serverSelectionTimeoutMS=3000)
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[app.config['MONGODB_DBNAME']]
    except Exception as exc:
        app.logger.warning('No se pudo conectar a MongoDB (%s). Usando un almacenamiento en memoria.', exc)
        mongo_client = None
        mongo_db = _create_in_memory_db()

    # Crear indices necesarios
    with app.app_context():
        _create_indexes(mongo_db)

    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    from app.controllers.auth_controller import auth_bp
    from app.controllers.home_controller import home_bp
    from app.controllers.search_controller import search_bp
    from app.controllers.admin_controller import admin_bp
    from app.controllers.profile_controller import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    return app


def _create_in_memory_db():
    """Crea un objeto con una API mínima compatible con las operaciones de MongoDB usadas por la app."""

    class _Collection:
        def __init__(self, name):
            self.name = name
            self._docs = []

        def create_index(self, *args, **kwargs):
            return None

        def find_one(self, query=None):
            if query is None:
                return None
            for doc in self._docs:
                if self._matches(doc, query):
                    return doc
            return None

        def find(self, query=None):
            docs = self._docs if query is None else [doc for doc in self._docs if self._matches(doc, query)]
            return _Cursor(docs)

        def insert_one(self, doc):
            doc = dict(doc)
            doc['_id'] = len(self._docs) + 1
            self._docs.append(doc)
            return type('InsertResult', (), {'inserted_id': doc['_id']})()

        def update_one(self, query, update):
            for doc in self._docs:
                if self._matches(doc, query):
                    for key, value in update.get('$set', {}).items():
                        doc[key] = value
                    return None
            return None

        def update_many(self, query, update):
            for doc in self._docs:
                if self._matches(doc, query):
                    for key, value in update.get('$set', {}).items():
                        doc[key] = value
            return None

        def delete_one(self, query):
            for index, doc in enumerate(self._docs):
                if self._matches(doc, query):
                    del self._docs[index]
                    break
            return None

        def count_documents(self, query=None):
            return len([doc for doc in self._docs if self._matches(doc, query or {})])

        def _matches(self, doc, query):
            if not query:
                return True
            if isinstance(query, dict):
                for key, value in query.items():
                    if key == '$or':
                        return any(self._matches(doc, item) for item in value)
                    if key == '$and':
                        return all(self._matches(doc, item) for item in value)
                    if key == '$set':
                        continue
                    if isinstance(value, dict):
                        if '$gt' in value and not (doc.get(key, None) is not None and doc.get(key) > value['$gt']):
                            return False
                        if '$lt' in value and not (doc.get(key, None) is not None and doc.get(key) < value['$lt']):
                            return False
                        if '$ne' in value and doc.get(key) == value['$ne']:
                            return False
                        continue
                    if doc.get(key) != value:
                        return False
            return True

    class _Cursor:
        def __init__(self, docs):
            self._docs = docs

        def sort(self, *args, **kwargs):
            return self

        def __iter__(self):
            return iter(self._docs)

        def __len__(self):
            return len(self._docs)

        def __getitem__(self, item):
            return self._docs[item]

    class _DB:
        def __init__(self):
            self.users = _Collection('users')
            self.user_sessions = _Collection('user_sessions')
            self.refresh_tokens = _Collection('refresh_tokens')
            self.password_resets = _Collection('password_resets')
            self.favorites = _Collection('favorites')
            self.captcha_store = _Collection('captcha_store')

    return _DB()


def _create_indexes(db):
    """Crea los indices de MongoDB para mejorar el rendimiento."""
    db.users.create_index('username', unique=True)
    db.users.create_index('email', unique=True)

    db.user_sessions.create_index('session_token', unique=True)
    db.user_sessions.create_index('user_id')
    db.user_sessions.create_index('is_active')

    db.refresh_tokens.create_index('token', unique=True)
    db.refresh_tokens.create_index('user_id')

    db.password_resets.create_index('token', unique=True)
    db.password_resets.create_index('user_id')

    db.favorites.create_index([('user_id', 1), ('video_id', 1)], unique=True)