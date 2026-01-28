#!/usr/bin/env python3
# Script para actualizar los archivos de la aplicación con validaciones

import os

# Actualizar auth_controller.py
auth_controller_content = """from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app import db, limiter
from app.models.user import User
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Usuario y contraseña son requeridos', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('home.dashboard'))
        else:
            flash('Credenciales inválidas', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()
        
        # Validar campos requeridos
        if not username or not email or not password or not password_confirm:
            flash('Todos los campos son requeridos', 'danger')
            return render_template('auth/register.html')
        
        # Validar longitud de usuario
        if len(username) < 3:
            flash('El usuario debe tener al menos 3 caracteres', 'danger')
            return render_template('auth/register.html')
        
        if len(username) > 80:
            flash('El usuario no puede tener más de 80 caracteres', 'danger')
            return render_template('auth/register.html')
        
        # Validar formato de email
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Email inválido', 'danger')
            return render_template('auth/register.html')
        
        # Validar contraseña
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return render_template('auth/register.html')
        
        if len(password) > 255:
            flash('La contraseña es demasiado larga', 'danger')
            return render_template('auth/register.html')
        
        if password == username:
            flash('La contraseña no puede ser igual al usuario', 'danger')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/register.html')
        
        # Validar usuario no existe
        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe', 'danger')
            return render_template('auth/register.html')
        
        # Validar email no existe
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return render_template('auth/register.html')
        
        # Crear usuario
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('¡Cuenta creada exitosamente!', 'success')
            return redirect(url_for('home.dashboard'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: El usuario o email ya existe', 'danger')
            return render_template('auth/register.html')
        except Exception as e:
            db.session.rollback()
            print(f"Error de registro: {e}")
            flash('Error al crear la cuenta. Por favor intenta de nuevo.', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('auth.login'))
"""

register_html_content = """{% extends "base.html" %}
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
            <input type="text" name="username" required minlength="3" maxlength="80" placeholder="Mínimo 3 caracteres">
        </div>
        <div class="input-group">
            <label>Email</label>
            <input type="email" name="email" required placeholder="tu@email.com">
        </div>
        <div class="input-group">
            <label>Contraseña</label>
            <input type="password" name="password" required minlength="8" placeholder="Mínimo 8 caracteres">
        </div>
        <div class="input-group">
            <label>Confirmar Contraseña</label>
            <input type="password" name="password_confirm" required minlength="8" placeholder="Repite tu contraseña">
        </div>
        <button type="submit" class="btn-primary">REGISTRARSE</button>
    </form>
    
    <p>¿Ya tienes cuenta? <a href="{{ url_for('auth.login') }}">Inicia sesión</a></p>
</div>
{% endblock %}
"""

# Escribir archivos
auth_path = r"C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean\app\controllers\auth_controller.py"
register_path = r"C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean\templates\auth\register.html"

with open(auth_path, 'w', encoding='utf-8') as f:
    f.write(auth_controller_content)
print(f"✅ Actualizado: {auth_path}")

with open(register_path, 'w', encoding='utf-8') as f:
    f.write(register_html_content)
print(f"✅ Actualizado: {register_path}")

# Actualizar __init__.py
init_path = r"C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean\app\__init__.py"
with open(init_path, 'r', encoding='utf-8') as f:
    init_content = f.read()

# Reemplazar las líneas de configuración
init_content = init_content.replace(
    "app.config['SECRET_KEY'] = 'dev-secret-key'",
    "app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))"
)
init_content = init_content.replace(
    "app.config['YOUTUBE_API_KEY'] = 'AIzaSyBDxvMwbKwBdx-UkbtFywAICI-43OtEnbY'",
    "app.config['YOUTUBE_API_KEY'] = os.environ.get('YOUTUBE_API_KEY', '')"
)

with open(init_path, 'w', encoding='utf-8') as f:
    f.write(init_content)
print(f"✅ Actualizado: {init_path}")

print("\n✅ Todos los archivos han sido actualizados correctamente")
