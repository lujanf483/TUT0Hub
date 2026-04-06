from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User, UserSession
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def index():
    users = User.get_all()
    total_sessions = UserSession.count_active()
    return render_template('admin/index.html', users=users,
                           total_sessions=total_sessions, page_title='Panel Admin')


@admin_bp.route('/users/<user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.get_by_id(user_id)
    if not user:
        return redirect(url_for('admin.index'))
    new_role = request.form.get('role')
    if new_role not in ('admin', 'editor', 'user'):
        flash('Rol invalido', 'danger')
        return redirect(url_for('admin.index'))
    if user.id == current_user.id:
        flash('No puedes cambiar tu propio rol', 'danger')
        return redirect(url_for('admin.index'))
    user.role = new_role
    flash(f'Rol de {user.username} actualizado a {new_role}', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/<user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.get_by_id(user_id)
    if not user:
        return redirect(url_for('admin.index'))
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta', 'danger')
        return redirect(url_for('admin.index'))
    user.is_active = not user.is_active
    if not user.is_active:
        UserSession.deactivate_all_for_user(user.id)
        from app.utils.jwt_utils import revoke_all_user_tokens
        revoke_all_user_tokens(user.id)
    status = 'activado' if user.is_active else 'desactivado'
    flash(f'Usuario {user.username} {status}', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/sessions')
@login_required
@admin_required
def all_sessions():
    from app import get_db
    docs = get_db().user_sessions.find({'is_active': True}).sort('last_active', -1)
    sessions = [UserSession(d) for d in docs]
    return render_template('admin/sessions.html', sessions=sessions, page_title='Sesiones Activas')


@admin_bp.route('/sessions/<session_id>/close', methods=['POST'])
@login_required
@admin_required
def close_session(session_id):
    s = UserSession.get_by_id(session_id)
    if s:
        s.is_active = False
    flash('Sesion cerrada', 'success')
    return redirect(url_for('admin.all_sessions'))