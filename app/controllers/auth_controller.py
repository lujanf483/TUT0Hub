from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify)
from flask_login import login_user, logout_user, current_user
from app import db, limiter
from app.models.user import User, UserSession, PasswordReset
from app.utils.captcha import SimpleCaptcha, CaptchaStore
from app.utils.jwt_utils import (generate_access_token, generate_refresh_token,
                                  revoke_all_user_tokens, revoke_refresh_token,
                                  validate_access_token)
from app.utils.email_utils import (send_mfa_code, send_password_reset_email,
                                    send_sms_code, send_call_code_simulated)
from app.utils.mfa_utils import generate_otp_code, otp_expiry, is_otp_valid
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _complete_login(user):
    login_user(user)
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    db_session = UserSession.create_session(user.id, ip, ua)
    access_token = generate_access_token(user.id, user.role)
    refresh_token = generate_refresh_token(user.id)
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    session['session_db_token'] = db_session.session_token


# ──────────────────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Usuario y contrasena son requeridos', 'danger')
            return render_template('auth/login.html')

        if len(username) < 3 or len(password) < 8:
            flash('Credenciales invalidas', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password) and user.is_active:
            if user.mfa_enabled:
                session['mfa_user_id'] = user.id
                session['mfa_pending'] = True
                code = generate_otp_code()
                user.mfa_code = code
                user.mfa_code_expiry = otp_expiry(minutes=10)
                db.session.commit()
                send_mfa_code(user.email, code)
                flash('Se envio un codigo MFA a tu correo', 'info')
                return redirect(url_for('auth.mfa_verify'))
            _complete_login(user)
            flash(f'Bienvenido, {user.username}!', 'success')
            return redirect(url_for('home.dashboard'))
        else:
            flash('Credenciales invalidas o cuenta desactivada', 'danger')

    return render_template('auth/login.html')


# ──────────────────────────────────────────────────────────
# MFA
# ──────────────────────────────────────────────────────────
@auth_bp.route('/mfa-verify', methods=['GET', 'POST'])
def mfa_verify():
    if not session.get('mfa_pending'):
        return redirect(url_for('auth.login'))

    user = User.query.get(session.get('mfa_user_id'))
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('mfa_code', '').strip()

        if is_otp_valid(code, user.mfa_code, user.mfa_code_expiry):
            user.mfa_code = None
            user.mfa_code_expiry = None
            db.session.commit()
            session.pop('mfa_pending', None)
            session.pop('mfa_user_id', None)
            _complete_login(user)
            flash(f'Bienvenido, {user.username}!', 'success')
            return redirect(url_for('home.dashboard'))

        from app.utils.mfa_utils import verify_totp
        if user.mfa_secret and verify_totp(user.mfa_secret, code):
            session.pop('mfa_pending', None)
            session.pop('mfa_user_id', None)
            _complete_login(user)
            flash(f'Bienvenido, {user.username}!', 'success')
            return redirect(url_for('home.dashboard'))

        flash('Codigo MFA incorrecto o expirado', 'danger')

    return render_template('auth/mfa_verify.html')


@auth_bp.route('/mfa-resend', methods=['POST'])
def mfa_resend():
    user = User.query.get(session.get('mfa_user_id'))
    if user and session.get('mfa_pending'):
        code = generate_otp_code()
        user.mfa_code = code
        user.mfa_code_expiry = otp_expiry(minutes=10)
        db.session.commit()
        send_mfa_code(user.email, code)
        flash('Codigo reenviado a tu correo', 'info')
    return redirect(url_for('auth.mfa_verify'))


# ──────────────────────────────────────────────────────────
# REGISTRO
# ──────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))

    if request.method == 'GET':
        q, a, t = SimpleCaptcha.generate()
        CaptchaStore.save(t, a)
        session['captcha_token'] = t
        return render_template('auth/register.html', captcha_question=q)

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    password_confirm = request.form.get('password_confirm', '').strip()
    captcha_answer = request.form.get('captcha_answer', '').strip()
    captcha_token = session.get('captcha_token', '')
    secret_question = request.form.get('secret_question', '').strip()
    secret_answer = request.form.get('secret_answer', '').strip()

    new_q, new_a, new_t = SimpleCaptcha.generate()
    CaptchaStore.save(new_t, new_a)
    session['captcha_token'] = new_t

    def err(msg):
        flash(msg, 'danger')
        return render_template('auth/register.html', captcha_question=new_q)

    stored = CaptchaStore.get(captcha_token)
    if not stored or not SimpleCaptcha.validate(captcha_answer, stored):
        return err('CAPTCHA incorrecto')
    CaptchaStore.delete(captcha_token)

    if not all([username, email, password, password_confirm]):
        return err('Todos los campos son requeridos')
    if len(username) < 3 or len(username) > 80:
        return err('El usuario debe tener entre 3 y 80 caracteres')
    if not re.match(r'^[A-Za-z0-9_\-]+$', username):
        return err('El usuario solo puede contener letras, numeros, guiones y guiones bajos')
    try:
        validate_email(email)
    except EmailNotValidError:
        return err('Email invalido')
    if len(email) > 120:
        return err('Email demasiado largo')
    if len(password) < 8 or len(password) > 255:
        return err('La contrasena debe tener entre 8 y 255 caracteres')
    if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        return err('La contrasena debe tener letras y numeros')
    if password.lower() == username.lower():
        return err('La contrasena no puede ser igual al usuario')
    if password != password_confirm:
        return err('Las contrasenas no coinciden')
    if User.query.filter_by(username=username).first():
        return err('El usuario ya existe')
    if User.query.filter_by(email=email).first():
        return err('El email ya esta registrado')

    try:
        user = User(username=username, email=email)
        user.set_password(password)
        if secret_question and secret_answer:
            user.secret_question = secret_question
            user.set_secret_answer(secret_answer)
        db.session.add(user)
        db.session.commit()
        _complete_login(user)
        flash('Cuenta creada exitosamente! Bienvenido a TUT0hub', 'success')
        return redirect(url_for('home.dashboard'))
    except IntegrityError:
        db.session.rollback()
        return err('Error: El usuario o email ya existe')
    except Exception as e:
        db.session.rollback()
        print(f"Error de registro: {e}")
        return err('Error al crear la cuenta. Intenta de nuevo.')


# ──────────────────────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        rt = session.get('refresh_token')
        if rt:
            revoke_refresh_token(rt)
        st = session.get('session_db_token')
        if st:
            s = UserSession.query.filter_by(session_token=st).first()
            if s:
                s.is_active = False
                db.session.commit()
    logout_user()
    session.clear()
    flash('Sesion cerrada', 'info')
    return redirect(url_for('auth.login'))


# ──────────────────────────────────────────────────────────
# RECUPERACION DE CONTRASENA
# ──────────────────────────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        method = request.form.get('method', 'email')
        success_msg = 'Si el correo existe, recibiras instrucciones en breve.'

        user = User.query.filter_by(email=email).first()
        if not user:
            flash(success_msg, 'info')
            return redirect(url_for('auth.forgot_password'))

        PasswordReset.query.filter_by(user_id=user.id, used=False).update({'used': True})
        db.session.commit()

        token = secrets.token_urlsafe(48)
        expiry = datetime.utcnow() + timedelta(minutes=30)

        if method in ('sms', 'call'):
            code = generate_otp_code()
            pr = PasswordReset(user_id=user.id, token=token, method=method,
                               code=code, expires_at=expiry)
            db.session.add(pr)
            db.session.commit()
            if method == 'sms':
                send_sms_code(email, code)
            else:
                send_call_code_simulated(email, code)
            session['reset_token'] = token
            session['reset_method'] = method
            flash(f'Codigo enviado. Revisa tu correo (simulacion de {"SMS" if method == "sms" else "llamada"}).', 'info')
            return redirect(url_for('auth.verify_reset_code'))

        elif method == 'question':
            if not user.secret_question:
                flash('No tienes pregunta secreta configurada', 'danger')
                return redirect(url_for('auth.forgot_password'))
            pr = PasswordReset(user_id=user.id, token=token, method='question',
                               expires_at=expiry)
            db.session.add(pr)
            db.session.commit()
            session['reset_token'] = token
            return redirect(url_for('auth.reset_by_question'))

        else:
            pr = PasswordReset(user_id=user.id, token=token, method='email',
                               expires_at=expiry)
            db.session.add(pr)
            db.session.commit()
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            send_password_reset_email(email, reset_link)

        flash(success_msg, 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/verify-reset-code', methods=['GET', 'POST'])
def verify_reset_code():
    reset_token = session.get('reset_token')
    if not reset_token:
        return redirect(url_for('auth.forgot_password'))

    pr = PasswordReset.query.filter_by(token=reset_token).first()
    if not pr or not pr.is_valid():
        flash('El codigo ha expirado o es invalido', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        pr.attempts += 1
        db.session.commit()

        if pr.attempts > 5:
            pr.used = True
            db.session.commit()
            flash('Demasiados intentos. Solicita un nuevo codigo.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if code == pr.code and pr.is_valid():
            return redirect(url_for('auth.reset_password', token=reset_token))
        else:
            flash(f'Codigo incorrecto. Intentos restantes: {5 - pr.attempts}', 'danger')

    return render_template('auth/verify_reset_code.html', method=pr.method)


@auth_bp.route('/reset-by-question', methods=['GET', 'POST'])
def reset_by_question():
    reset_token = session.get('reset_token')
    if not reset_token:
        return redirect(url_for('auth.forgot_password'))

    pr = PasswordReset.query.filter_by(token=reset_token, method='question').first()
    if not pr or not pr.is_valid():
        flash('Token invalido o expirado', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(pr.user_id)

    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        pr.attempts += 1
        db.session.commit()

        if pr.attempts > 5:
            pr.used = True
            db.session.commit()
            flash('Demasiados intentos', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if user.check_secret_answer(answer):
            return redirect(url_for('auth.reset_password', token=reset_token))
        else:
            flash('Respuesta incorrecta', 'danger')

    return render_template('auth/reset_by_question.html', question=user.secret_question)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    pr = PasswordReset.query.filter_by(token=token).first()
    if not pr or not pr.is_valid():
        flash('El enlace ha expirado o es invalido', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(pr.user_id)

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('password_confirm', '').strip()

        if len(new_password) < 8:
            flash('La contrasena debe tener al menos 8 caracteres', 'danger')
            return render_template('auth/reset_password.html', token=token)
        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'[0-9]', new_password):
            flash('La contrasena debe tener letras y numeros', 'danger')
            return render_template('auth/reset_password.html', token=token)
        if new_password != confirm_password:
            flash('Las contrasenas no coinciden', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(new_password)
        pr.used = True
        revoke_all_user_tokens(user.id)
        db.session.commit()
        session.pop('reset_token', None)
        flash('Contrasena restablecida exitosamente. Inicia sesion.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ──────────────────────────────────────────────────────────
# API JWT
# ──────────────────────────────────────────────────────────
@auth_bp.route('/api/refresh-token', methods=['POST'])
def api_refresh_token():
    data = request.get_json()
    rt_str = data.get('refresh_token') if data else None
    if not rt_str:
        return jsonify({'error': 'Refresh token requerido'}), 400
    from app.utils.jwt_utils import refresh_access_token
    new_access, new_refresh = refresh_access_token(rt_str)
    if not new_access:
        return jsonify({'error': 'Refresh token invalido o expirado'}), 401
    return jsonify({'access_token': new_access, 'refresh_token': new_refresh})


# ──────────────────────────────────────────────────────────
# SSO SIMULADO
# ──────────────────────────────────────────────────────────
@auth_bp.route('/sso/token', methods=['GET'])
def sso_get_token():
    if not current_user.is_authenticated:
        return jsonify({'error': 'No autenticado'}), 401
    sso_token = generate_access_token(current_user.id, current_user.role)
    return jsonify({'sso_token': sso_token, 'expires_in': 900})


@auth_bp.route('/sso/verify', methods=['POST'])
def sso_verify():
    data = request.get_json()
    token = data.get('sso_token') if data else None
    if not token:
        return jsonify({'valid': False, 'error': 'Token requerido'}), 400
    payload = validate_access_token(token)
    if not payload:
        return jsonify({'valid': False, 'error': 'Token invalido o expirado'}), 401
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'valid': False}), 404
    return jsonify({'valid': True, 'user_id': user.id, 'username': user.username, 'role': user.role})