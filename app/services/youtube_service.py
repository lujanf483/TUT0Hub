import requests
from flask import current_app

YOUTUBE_API_BASE = 'https://www.googleapis.com/youtube/v3'

def search_videos(query, max_results=12):
    """
    Busca videos en YouTube usando la API Key
    """
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
        
        response = requests.get(url, params=params)
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

def get_trending_videos(max_results=12):
    """
    Obtiene videos en tendencia
    """
    return search_videos('tutorial web development', max_results)

def get_video_details(video_id):
    """
    Obtiene detalles de un video específico
    """
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
        
        response = requests.get(url, params=params)
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
