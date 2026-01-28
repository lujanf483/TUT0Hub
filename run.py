from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Iniciando TUT0hub")
    print("=" * 50)
    print("Modo: Desarrollo")
    print("Puerto: 5000")
    print("URL: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, port=5000, host='0.0.0.0')