from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from app.services.youtube_service import search_videos, get_trending_videos, search_videos_paginated
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
    favorite_ids = [fav.video_id for fav in Favorite.get_by_user(current_user.id)]
    return render_template('home/dashboard.html', videos=videos, favorite_ids=favorite_ids, page_title='Dashboard')


@home_bp.route('/api/videos', methods=['GET'])
@login_required
def api_videos():
    per_page = request.args.get('per_page', 12, type=int)
    page_token = request.args.get('page_token', None, type=str)

    if per_page not in [12, 24, 50]:
        per_page = 12

    result = search_videos_paginated('tutorial', max_results=per_page, page_token=page_token)
    favorite_ids = [fav.video_id for fav in Favorite.get_by_user(current_user.id)]

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
    favorite_records = Favorite.get_by_user(current_user.id)
    videos = [
        {
            'id': fav.video_id,
            'title': fav.title,
            'thumbnail': fav.thumbnail or '',
            'channel': fav.channel or '',
            'description': fav.description or ''
        }
        for fav in favorite_records
    ]
    favorite_ids = [fav.video_id for fav in favorite_records]
    return render_template('home/dashboard.html', videos=videos, favorite_ids=favorite_ids, page_title='Favoritos')


@home_bp.route('/toggle-favorite/<video_id>', methods=['POST'])
@login_required
def toggle_favorite(video_id):
    existing = Favorite.get_by_user_and_video(current_user.id, video_id)

    if existing:
        existing.delete()
    else:
        data = request.get_json()
        Favorite.create(
            user_id=current_user.id,
            video_id=video_id,
            title=data.get('title', ''),
            channel=data.get('channel', ''),
            description=data.get('description', ''),
            thumbnail=data.get('thumbnail', '')
        )

    return jsonify({'success': True})