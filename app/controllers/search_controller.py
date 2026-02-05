# ==================================================
# ARCHIVO: app/controllers/search_controller.py
# ACCIÓN: REEMPLAZAR TODO EL CONTENIDO
# ==================================================

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app.services.youtube_service import search_videos, advanced_search_videos
from app.models.user import Favorite
import re

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@login_required
def search():
    query = request.args.get('q', '').strip()
    videos = []
    favorite_ids = []
    
    if query:
        if not re.match(r'^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s\-]+$', query):
            flash('La búsqueda contiene caracteres no permitidos', 'danger')
            return render_template('home/search.html', query='', videos=[], favorite_ids=[], page_title='Búsqueda')
        
        if len(query) < 2:
            flash('La búsqueda debe tener al menos 2 caracteres', 'danger')
            return render_template('home/search.html', query='', videos=[], favorite_ids=[], page_title='Búsqueda')
        
        if len(query) > 100:
            flash('La búsqueda es demasiado larga (máximo 100 caracteres)', 'danger')
            return render_template('home/search.html', query='', videos=[], favorite_ids=[], page_title='Búsqueda')
        
        videos = search_videos(query, max_results=12)
        favorite_ids = [fav.video_id for fav in current_user.favorites]
    
    return render_template('home/search.html', query=query, videos=videos, favorite_ids=favorite_ids, page_title='Búsqueda')

@search_bp.route('/advanced')
@login_required
def advanced_search():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    duration = request.args.get('duration', '').strip()
    date_filter = request.args.get('date_filter', '').strip()
    order = request.args.get('order', 'relevance').strip()
    max_results = request.args.get('max_results', '12').strip()
    
    videos = []
    favorite_ids = [fav.video_id for fav in current_user.favorites]
    searched = bool(query or category)
    
    if query:
        if not re.match(r'^[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s\-]+$', query):
            flash('La búsqueda contiene caracteres no permitidos', 'danger')
            query = ''
            searched = False
        
        elif len(query) < 2:
            flash('La búsqueda debe tener al menos 2 caracteres', 'danger')
            query = ''
            searched = False
        
        elif len(query) > 100:
            flash('La búsqueda es demasiado larga (máximo 100 caracteres)', 'danger')
            query = ''
            searched = False
    
    try:
        max_results_int = int(max_results)
        if max_results_int not in [12, 24, 50]:
            max_results_int = 12
    except:
        max_results_int = 12
    
    valid_orders = ['relevance', 'date', 'viewCount', 'rating']
    if order not in valid_orders:
        order = 'relevance'
    
    if searched:
        videos = advanced_search_videos(
            query=query,
            category=category,
            duration=duration,
            date_filter=date_filter,
            order=order,
            max_results=max_results_int
        )
    
    return render_template('home/advanced_search.html', 
                          query=query,
                          category=category,
                          duration=duration,
                          date_filter=date_filter,
                          order=order,
                          max_results=max_results,
                          videos=videos, 
                          favorite_ids=favorite_ids,
                          searched=searched,
                          page_title='Búsqueda Avanzada')