from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services.youtube_service import search_videos
from app.models.user import Favorite

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@login_required
def search():
    query = request.args.get('q', '')
    videos = []
    favorite_ids = []
    
    if query:
        videos = search_videos(query, max_results=12)
        favorite_ids = [fav.video_id for fav in current_user.favorites]
    
    return render_template('home/search.html', query=query, videos=videos, favorite_ids=favorite_ids, page_title='Búsqueda')