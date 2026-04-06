"""
Script para inicializar la base de datos en MongoDB Atlas.
Crea los indices y los usuarios de prueba (admin y editor).

Uso:
    python recreate_db.py
"""

import os
import sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    sys.path.insert(0, project_dir)

    # Cargar variables de entorno desde .env
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from app import create_app, get_db
        from app.models.user import User

        app = create_app()

        with app.app_context():
            db = get_db()

            print("Conectado a MongoDB.")
            print(f"Base de datos: {db.name}")

            # Opcional: limpiar colecciones para empezar desde cero
            respuesta = input("Deseas limpiar todas las colecciones? (s/N): ").strip().lower()
            if respuesta == 's':
                db.users.drop()
                db.user_sessions.drop()
                db.refresh_tokens.drop()
                db.password_resets.drop()
                db.favorites.drop()
                print("Colecciones eliminadas.")

            # Crear usuarios de prueba si no existen
            if not User.get_by_username('admin'):
                User.create(
                    username='admin',
                    email='admin@tut0hub.com',
                    password='Admin123',
                    role='admin'
                )
                print("Usuario admin creado: admin / Admin123")

            if not User.get_by_username('editor'):
                User.create(
                    username='editor',
                    email='editor@tut0hub.com',
                    password='Editor123',
                    role='editor'
                )
                print("Usuario editor creado: editor / Editor123")

            print("Base de datos lista.")
            return True

    except Exception:
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    sys.exit(0 if main() else 1)