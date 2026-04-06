# ==================================================
# ARCHIVO: app/controllers/home_controller.py
# ==================================================

from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app.services.youtube_service import search_videos, get_trending_videos, search_videos_paginated
from app import db
from app.models.user import Favorite

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    return redirect(url_for('auth.login'))

@home_bp.route('/dashboard')
@login_required
def dashboard():
    videos = get_trending_videos(max_results=12)
    favorite_ids = [fav.video_id for fav in current_user.favorites]
    return render_template('home/dashboard.html', videos=videos, favorite_ids=favorite_ids, page_title='Dashboard')

@home_bp.route('/api/videos', methods=['GET'])
@login_required
def api_videos():
    """Retorna videos en JSON para infinite scroll con paginación real"""
    per_page = request.args.get('per_page', 12, type=int)
    page_token = request.args.get('page_token', None, type=str)
    
    # Validar per_page
    if per_page not in [12, 24, 50]:
        per_page = 12
    
    # Buscar usand paginación de YouTube
    result = search_videos_paginated('tutorial', max_results=per_page, page_token=page_token)
    
    favorite_ids = [fav.video_id for fav in current_user.favorites]
    
    return jsonify({
        'videos': [
            {
                'id': v['id'],
                'title': v['title'],
                'thumbnail': v['thumbnail'],
                'channel': v['channel'],
                'description': v['description']
            }
            for v in result['videos']
        ],
        'nextPageToken': result.get('nextPageToken'),
        'prevPageToken': result.get('prevPageToken'),
        'has_more': bool(result.get('nextPageToken')),
        'favorite_ids': favorite_ids
    })

@home_bp.route('/favorites')
@login_required
def favorites():
    favorite_records = Favorite.query.filter_by(user_id=current_user.id).all()
    videos = []
    for fav in favorite_records:
        videos.append({
            'id': fav.video_id,
            'title': fav.title,
            'thumbnail': fav.thumbnail or '',
            'channel': fav.channel or '',
            'description': fav.description or ''
        })
    favorite_ids = [fav.video_id for fav in current_user.favorites]
    return render_template('home/dashboard.html', videos=videos, favorite_ids=favorite_ids, page_title='Favoritos')

@home_bp.route('/toggle-favorite/<video_id>', methods=['POST'])
@login_required
def toggle_favorite(video_id):
    """
    Agrega o elimina un video de favoritos
    Recibe: video_id en URL y datos del video en JSON
    Retorna: JSON con success: true
    """
    existing = Favorite.query.filter_by(user_id=current_user.id, video_id=video_id).first()
    
    if existing:
        # Si ya existe, eliminarlo
        db.session.delete(existing)
    else:
        # Si no existe, agregarlo
        data = request.get_json()
        favorite = Favorite(
            user_id=current_user.id,
            video_id=video_id,
            title=data.get('title', ''),
            channel=data.get('channel', ''),
            description=data.get('description', ''),
            thumbnail=data.get('thumbnail', '')
        )
        db.session.add(favorite)
    
    db.session.commit()
    return jsonify({'success': True})

@home_bp.route('/test-i18n')
@login_required
def test_i18n():
    """Página de prueba del sistema de traducción"""
    return render_template('test_i18n.html')