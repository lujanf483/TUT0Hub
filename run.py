import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print("=" * 50)
    print("🚀 Iniciando TUT0hub")
    print("=" * 50)
    print(f"Modo: {'Desarrollo' if debug else 'Producción'}")
    print(f"Puerto: {port}")
    print(f"URL: http://localhost:{port}")
    print("=" * 50)
    
    app.run(debug=debug, port=port, host='0.0.0.0')