# ==================================================
# ARCHIVO: app/services/youtube_service.py
# ACCIÓN: REEMPLAZAR TODO EL CONTENIDO
# ==================================================

import requests
from flask import current_app
from datetime import datetime, timedelta

YOUTUBE_API_BASE = 'https://www.googleapis.com/youtube/v3'

CATEGORY_MAP = {
    'education': '27',
    'science': '28',
    'entertainment': '24',
    'music': '10',
    'gaming': '20',
    'sports': '17'
}

def search_videos(query, max_results=12):
    """Búsqueda simple de videos en YouTube"""
    api_key = current_app.config.get('YOUTUBE_API_KEY')
    
    if not api_key:
        return []
    
    try:
        url = f'{YOUTUBE_API_BASE}/search'
        params = {
            'q': query,
            'part': 'snippet',
            'maxResults': max_results,
            'type': 'video',
            'key': api_key,
            'order': 'relevance'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            video = {
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description']
            }
            videos.append(video)
        
        return videos
    except Exception as e:
        print(f"Error buscando videos: {e}")
        return []

def advanced_search_videos(query='', category='', duration='', date_filter='', order='relevance', max_results=12):
    """Búsqueda avanzada de videos con filtros"""
    api_key = current_app.config.get('YOUTUBE_API_KEY')
    
    if not api_key:
        return []
    
    try:
        url = f'{YOUTUBE_API_BASE}/search'
        search_query = query if query else (category if category else 'tutorial')
        
        params = {
            'q': search_query,
            'part': 'snippet',
            'maxResults': max_results,
            'type': 'video',
            'key': api_key,
            'order': order
        }
        
        if duration:
            params['videoDuration'] = duration
        
        if date_filter:
            params['publishedAfter'] = _get_date_filter(date_filter)
        
        if category and category in CATEGORY_MAP:
            params['videoCategoryId'] = CATEGORY_MAP[category]
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            video = {
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description']
            }
            videos.append(video)
        
        return videos
    except Exception as e:
        print(f"Error en búsqueda avanzada: {e}")
        return []

def _get_date_filter(filter_type):
    """Convierte el filtro de fecha en formato RFC 3339"""
    now = datetime.utcnow()
    
    if filter_type == 'hour':
        date = now - timedelta(hours=1)
    elif filter_type == 'today':
        date = now - timedelta(days=1)
    elif filter_type == 'week':
        date = now - timedelta(weeks=1)
    elif filter_type == 'month':
        date = now - timedelta(days=30)
    elif filter_type == 'year':
        date = now - timedelta(days=365)
    else:
        return None
    
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_trending_videos(max_results=12):
    """Obtiene videos en tendencia"""
    return search_videos('tutorial web development', max_results)

def get_video_details(video_id):
    """Obtiene detalles de un video específico"""
    api_key = current_app.config.get('YOUTUBE_API_KEY')
    
    if not api_key:
        return None
    
    try:
        url = f'{YOUTUBE_API_BASE}/videos'
        params = {
            'id': video_id,
            'part': 'snippet,statistics',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('items'):
            item = data['items'][0]
            return {
                'id': video_id,
                'title': item['snippet']['title'],
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'channel': item['snippet']['channelTitle'],
                'description': item['snippet']['description'],
                'views': item['statistics'].get('viewCount', 0),
                'likes': item['statistics'].get('likeCount', 0)
            }
        return None
    except Exception as e:
        print(f"Error obteniendo detalles del video: {e}")
        return None