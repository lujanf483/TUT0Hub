from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from app import db, limiter
from app.models.user import User
from app.utils.captcha import SimpleCaptcha, CaptchaStore
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validación de campos requeridos
        if not username or not password:
            flash('Usuario y contraseña son requeridos', 'danger')
            return render_template('auth/login.html')
        
        # Validación de longitud
        if len(username) < 3:
            flash('El usuario debe tener al menos 3 caracteres', 'danger')
            return render_template('auth/login.html')
        
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
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
    
    # Generar CAPTCHA para GET request
    if request.method == 'GET':
        captcha_question, captcha_answer, captcha_token = SimpleCaptcha.generate()
        CaptchaStore.save(captcha_token, captcha_answer)
        session['captcha_token'] = captcha_token
        
        return render_template('auth/register.html', 
                             captcha_question=captcha_question)
    
    # POST - Procesar registro
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    password_confirm = request.form.get('password_confirm', '').strip()
    captcha_answer = request.form.get('captcha_answer', '').strip()
    captcha_token = session.get('captcha_token', '')
    
    # Generar nuevo CAPTCHA para mostrar en caso de error
    new_captcha_question, new_captcha_answer, new_captcha_token = SimpleCaptcha.generate()
    CaptchaStore.save(new_captcha_token, new_captcha_answer)
    session['captcha_token'] = new_captcha_token
    
    # ==========================================
    # VALIDACIONES EN BACKEND
    # ==========================================
    
    # 1. Validar CAPTCHA (Verificación humana)
    stored_answer = CaptchaStore.get(captcha_token)
    if not stored_answer or not SimpleCaptcha.validate(captcha_answer, stored_answer):
        flash('CAPTCHA incorrecto. Por favor, intenta de nuevo.', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # Limpiar CAPTCHA usado
    CaptchaStore.delete(captcha_token)
    
    # 2. Validar campos requeridos
    if not username or not email or not password or not password_confirm:
        flash('Todos los campos son requeridos', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 3. Validar longitud de usuario
    if len(username) < 3:
        flash('El usuario debe tener al menos 3 caracteres', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    if len(username) > 80:
        flash('El usuario no puede tener más de 80 caracteres', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 4. Validar caracteres permitidos en usuario
    if not re.match(r'^[A-Za-z0-9_\-]+$', username):
        flash('El usuario solo puede contener letras, números, guiones y guiones bajos', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 5. Validar formato de email
    try:
        validate_email(email)
    except EmailNotValidError as e:
        flash(f'Email inválido: {str(e)}', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 6. Validar longitud de email
    if len(email) > 120:
        flash('El email es demasiado largo (máximo 120 caracteres)', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 7. Validar contraseña
    if len(password) < 8:
        flash('La contraseña debe tener al menos 8 caracteres', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    if len(password) > 255:
        flash('La contraseña es demasiado larga', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 8. Validar complejidad de contraseña
    if not re.search(r'[A-Za-z]', password):
        flash('La contraseña debe contener al menos una letra', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    if not re.search(r'[0-9]', password):
        flash('La contraseña debe contener al menos un número', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 9. Validar que contraseña no sea igual al usuario
    if password.lower() == username.lower():
        flash('La contraseña no puede ser igual al usuario', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 10. Validar que las contraseñas coincidan
    if password != password_confirm:
        flash('Las contraseñas no coinciden', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 11. Validar usuario no existe (unicidad)
    if User.query.filter_by(username=username).first():
        flash('El usuario ya existe', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # 12. Validar email no existe (unicidad)
    if User.query.filter_by(email=email).first():
        flash('El email ya está registrado', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    
    # ==========================================
    # CREAR USUARIO
    # ==========================================
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('¡Cuenta creada exitosamente! Bienvenido a TUT0hub', 'success')
        return redirect(url_for('home.dashboard'))
        
    except IntegrityError:
        db.session.rollback()
        flash('Error: El usuario o email ya existe', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)
    except Exception as e:
        db.session.rollback()
        print(f"Error de registro: {e}")
        flash('Error al crear la cuenta. Por favor intenta de nuevo.', 'danger')
        return render_template('auth/register.html', 
                             captcha_question=new_captcha_question)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('auth.login'))