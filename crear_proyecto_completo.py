"""
Script Maestro - Crea TODO el proyecto TUT0hub
Ejecuta este archivo y se creará el proyecto completo
"""
import os
from pathlib import Path

# Definir todos los archivos del proyecto
ARCHIVOS = {
    # === CONFIGURACIÓN ===
    '.env': '''FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-cambia-en-produccion

DATABASE_URL=sqlite:///tut0hub.db
YOUTUBE_API_KEY=

SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600

RATELIMIT_STORAGE_URL=memory://''',

    'requirements.txt': '''Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
bcrypt==4.1.2
python-dotenv==1.0.0
google-api-python-client==2.108.0
email-validator==2.1.0
WTForms==3.1.1
isodate==0.6.1''',

    'run.py': '''from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Iniciando TUT0hub")
    print("=" * 50)
    print("Modo: Desarrollo")
    print("Puerto: 5000")
    print("URL: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, port=5000, host='0.0.0.0')''',

    # === APP INIT ===
    'app/__init__.py': '''from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tut0hub.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
    
    from app.controllers.auth_controller import auth_bp
    from app.controllers.home_controller import home_bp
    from app.controllers.search_controller import search_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(search_bp)
    
    return app''',

    # === MODELOS ===
    'app/models/__init__.py': '',
    
    'app/models/user.py': '''from datetime import datetime
from flask_login import UserMixin
from app import db
import bcrypt

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    video_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)''',

    # === CONTROLADORES ===
    'app/controllers/__init__.py': '',
    
    'app/controllers/auth_controller.py': '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app import db, limiter
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Bienvenido!', 'success')
            return redirect(url_for('home.dashboard'))
        else:
            flash('Credenciales inválidas', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe', 'danger')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Cuenta creada!', 'success')
        return redirect(url_for('home.dashboard'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('auth.login'))''',

    'app/controllers/home_controller.py': '''from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    return redirect(url_for('auth.login'))

@home_bp.route('/dashboard')
@login_required
def dashboard():
    videos = []  # Por ahora vacío
    return render_template('home/dashboard.html', videos=videos, favorite_ids=[], page_title='Dashboard')

@home_bp.route('/favorites')
@login_required
def favorites():
    return render_template('home/dashboard.html', videos=[], favorite_ids=[], page_title='Favoritos')''',

    'app/controllers/search_controller.py': '''from flask import Blueprint, render_template, request
from flask_login import login_required

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@login_required
def search():
    query = request.args.get('q', '')
    videos = []  # Por ahora vacío
    return render_template('home/search.html', query=query, videos=videos, favorite_ids=[], page_title='Búsqueda')''',

    # === SERVICIOS ===
    'app/services/__init__.py': '',
    'app/utils/__init__.py': '',

    # === TEMPLATES ===
    'templates/base.html': '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}TUT0hub{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
    {% block header %}{% endblock %}
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="flash-container">
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">
                        {{ message }}
                        <button onclick="this.parentElement.remove()">×</button>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    
    <main>{% block content %}{% endblock %}</main>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>''',

    'templates/auth/login.html': '''{% extends "base.html" %}
{% block extra_css %}<link rel="stylesheet" href="{{ url_for('static', filename='css/auth.css') }}">{% endblock %}
{% block body_class %}page-login{% endblock %}
{% block content %}
<div class="login-container">
    <div class="brand-logo">TUT<span>0</span>HUB</div>
    <h2>Iniciar Sesión</h2>
    
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <div class="input-group">
            <label>Usuario o Email</label>
            <input type="text" name="username" required>
        </div>
        <div class="input-group">
            <label>Contraseña</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn-primary">ENTRAR</button>
    </form>
    
    <p>¿No tienes cuenta? <a href="{{ url_for('auth.register') }}">Regístrate</a></p>
</div>
{% endblock %}''',

    'templates/auth/register.html': '''{% extends "base.html" %}
{% block extra_css %}<link rel="stylesheet" href="{{ url_for('static', filename='css/auth.css') }}">{% endblock %}
{% block body_class %}page-login{% endblock %}
{% block content %}
<div class="login-container">
    <div class="brand-logo">TUT<span>0</span>HUB</div>
    <h2>Crear Cuenta</h2>
    
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <div class="input-group">
            <label>Usuario</label>
            <input type="text" name="username" required minlength="3">
        </div>
        <div class="input-group">
            <label>Email</label>
            <input type="email" name="email" required>
        </div>
        <div class="input-group">
            <label>Contraseña</label>
            <input type="password" name="password" required minlength="8">
        </div>
        <button type="submit" class="btn-primary">REGISTRARSE</button>
    </form>
    
    <p>¿Ya tienes cuenta? <a href="{{ url_for('auth.login') }}">Inicia sesión</a></p>
</div>
{% endblock %}''',

    'templates/home/dashboard.html': '''{% extends "base.html" %}
{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
{% endblock %}
{% block body_class %}page-dashboard{% endblock %}
{% block header %}{% include 'components/navbar.html' %}{% endblock %}
{% block content %}
<div class="dashboard-content">
    <h1>{{ page_title }}</h1>
    {% if videos %}
        <div class="video-grid">
        {% for video in videos %}
            <div class="card">{{ video.title }}</div>
        {% endfor %}
        </div>
    {% else %}
        <p>No hay videos disponibles. Configura tu YouTube API Key.</p>
    {% endif %}
</div>
{% endblock %}''',

    'templates/home/search.html': '''{% extends "home/dashboard.html" %}''',

    'templates/components/navbar.html': '''<header class="header">
    <a href="{{ url_for('home.dashboard') }}" class="logo">TUT<span>0</span>HUB</a>
    <form action="{{ url_for('search.search') }}" method="GET">
        <input type="text" name="q" placeholder="Buscar..." value="{{ query or '' }}">
        <button type="submit">🔍</button>
    </form>
    <nav>
        <a href="{{ url_for('home.dashboard') }}">Inicio</a>
        <a href="{{ url_for('home.favorites') }}">Favoritos</a>
        <a href="{{ url_for('auth.logout') }}">Salir</a>
    </nav>
</header>''',
}

# CSS Archivos
CSS_FILES = {
    'static/css/base.css': '''* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #fff; }
.flash-container { position: fixed; top: 20px; right: 20px; z-index: 9999; }
.flash { padding: 15px 20px; margin-bottom: 10px; border-radius: 8px; background: #1e1e1e; }
.flash-success { border-left: 4px solid #4caf50; }
.flash-danger { border-left: 4px solid #f44336; }
.flash-info { border-left: 4px solid #2196f3; }
.flash button { background: none; border: none; color: #fff; cursor: pointer; float: right; }''',

    'static/css/auth.css': '''.page-login { display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.login-container { background: #1e1e1e; padding: 40px; border-radius: 20px; width: 400px; text-align: center; }
.brand-logo { font-size: 2.5rem; font-weight: 900; margin-bottom: 20px; }
.brand-logo span { color: #ffb700; }
.input-group { margin-bottom: 20px; text-align: left; }
.input-group label { display: block; margin-bottom: 8px; color: #aaa; }
.input-group input { width: 100%; padding: 12px; background: #121212; border: 2px solid transparent; border-radius: 8px; color: #fff; }
.input-group input:focus { outline: none; border-color: #ffb700; }
.btn-primary { width: 100%; padding: 14px; background: #ffb700; color: #000; border: none; border-radius: 50px; font-weight: 800; cursor: pointer; }
.btn-primary:hover { background: #ffa000; }
.login-container p { margin-top: 20px; color: #aaa; }
.login-container a { color: #ffb700; }''',

    'static/css/dashboard.css': '''.header { position: fixed; top: 0; left: 0; right: 0; height: 65px; background: rgba(15,15,15,0.98); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 1000; border-bottom: 1px solid #333; }
.logo { font-size: 1.75rem; font-weight: 900; color: #fff; text-decoration: none; }
.logo span { color: #ffb700; }
.header form { display: flex; gap: 10px; }
.header input { padding: 8px 15px; background: #121212; border: 1px solid #333; border-radius: 20px; color: #fff; }
.header nav { display: flex; gap: 15px; }
.header nav a { color: #aaa; text-decoration: none; }
.header nav a:hover { color: #ffb700; }
.page-dashboard { padding-top: 65px; }
.dashboard-content { max-width: 1400px; margin: 0 auto; padding: 40px 20px; }
.video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.card { background: #1e1e1e; padding: 20px; border-radius: 12px; }''',

    'static/js/main.js': '''console.log("TUT0hub cargado");
setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => f.remove());
}, 5000);''',
}

def crear_archivo(ruta, contenido):
    """Crea un archivo con su contenido"""
    path = Path(ruta)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"✅ {ruta}")

def main():
    print("\n" + "="*60)
    print("🚀 CREANDO PROYECTO TUT0HUB COMPLETO")
    print("="*60 + "\n")
    
    # Crear archivos principales
    print("📄 Creando archivos principales...")
    for ruta, contenido in ARCHIVOS.items():
        crear_archivo(ruta, contenido)
    
    # Crear archivos CSS y JS
    print("\n🎨 Creando archivos CSS y JS...")
    for ruta, contenido in CSS_FILES.items():
        crear_archivo(ruta, contenido)
    
    print("\n" + "="*60)
    print("✅ ¡PROYECTO CREADO EXITOSAMENTE!")
    print("="*60)
    print("\n📋 SIGUIENTES PASOS:")
    print("1. Activa el entorno virtual: venv\\Scripts\\activate")
    print("2. Instala dependencias: pip install -r requirements.txt")
    print("3. Ejecuta: python run.py")
    print("4. Abre: http://localhost:5000")
    print("\n💡 Usuario de prueba: crea uno en /auth/register")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()