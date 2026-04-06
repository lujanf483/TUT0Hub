from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models.user import UserSession
from app.utils.mfa_utils import generate_otp_code, otp_expiry, is_otp_valid
from app.utils.email_utils import send_mfa_code
from app.utils.jwt_utils import revoke_all_user_tokens
import re

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def index():
    sessions = UserSession.get_active_by_user(current_user.id)
    return render_template('profile/index.html', sessions=sessions, page_title='Mi Perfil')


@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_pass = request.form.get('current_password', '').strip()
    new_pass = request.form.get('new_password', '').strip()
    confirm_pass = request.form.get('confirm_password', '').strip()

    if not current_user.check_password(current_pass):
        flash('Contrasena actual incorrecta', 'danger')
        return redirect(url_for('profile.index'))
    if len(new_pass) < 8:
        flash('La nueva contrasena debe tener al menos 8 caracteres', 'danger')
        return redirect(url_for('profile.index'))
    if not re.search(r'[A-Za-z]', new_pass) or not re.search(r'[0-9]', new_pass):
        flash('La contrasena debe tener letras y numeros', 'danger')
        return redirect(url_for('profile.index'))
    if new_pass != confirm_pass:
        flash('Las contrasenas no coinciden', 'danger')
        return redirect(url_for('profile.index'))

    current_user.set_password(new_pass)
    revoke_all_user_tokens(current_user.id)
    flash('Contrasena actualizada. Vuelve a iniciar sesion por seguridad.', 'success')
    return redirect(url_for('auth.logout'))


@profile_bp.route('/toggle-mfa', methods=['POST'])
@login_required
def toggle_mfa():
    action = request.form.get('action')
    if action == 'enable':
        code = generate_otp_code()
        current_user.mfa_code = code
        current_user.mfa_code_expiry = otp_expiry(10)
        send_mfa_code(current_user.email, code)
        session['mfa_setup_pending'] = True
        flash('Se envio un codigo a tu correo para confirmar la activacion', 'info')
        return redirect(url_for('profile.confirm_mfa'))
    elif action == 'disable':
        current_user.mfa_enabled = False
        current_user.mfa_code = None
        current_user.mfa_secret = None
        flash('MFA desactivado', 'info')
    return redirect(url_for('profile.index'))


@profile_bp.route('/confirm-mfa', methods=['GET', 'POST'])
@login_required
def confirm_mfa():
    if not session.get('mfa_setup_pending'):
        return redirect(url_for('profile.index'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if is_otp_valid(code, current_user.mfa_code, current_user.mfa_code_expiry):
            current_user.mfa_enabled = True
            current_user.mfa_code = None
            current_user.mfa_code_expiry = None
            session.pop('mfa_setup_pending', None)
            flash('MFA activado exitosamente', 'success')
        else:
            flash('Codigo incorrecto o expirado', 'danger')
        return redirect(url_for('profile.index'))

    return render_template('profile/confirm_mfa.html')


@profile_bp.route('/sessions/close/<session_id>', methods=['POST'])
@login_required
def close_session(session_id):
    s = UserSession.get_by_id(session_id)
    if s and s.user_id == current_user.id:
        s.is_active = False
        flash('Sesion cerrada', 'success')
    return redirect(url_for('profile.index'))


@profile_bp.route('/sessions/close-all', methods=['POST'])
@login_required
def close_all_sessions():
    UserSession.deactivate_all_for_user(current_user.id)
    revoke_all_user_tokens(current_user.id)
    flash('Todas las sesiones han sido cerradas', 'success')
    return redirect(url_for('auth.logout'))


@profile_bp.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    theme = request.form.get('theme', 'dark')
    language = request.form.get('language', 'es')
    if theme in ('dark', 'light'):
        current_user.theme = theme
    if language in ('es', 'en'):
        current_user.language = language
    flash('Preferencias actualizadas', 'success')
    return redirect(url_for('profile.index'))


@profile_bp.route('/secret-question', methods=['POST'])
@login_required
def update_secret_question():
    question = request.form.get('secret_question', '').strip()
    answer = request.form.get('secret_answer', '').strip()
    if not question or not answer:
        flash('Pregunta y respuesta son requeridas', 'danger')
        return redirect(url_for('profile.index'))
    current_user.secret_question = question
    current_user.set_secret_answer(answer)
    flash('Pregunta secreta actualizada', 'success')
    return redirect(url_for('profile.index'))