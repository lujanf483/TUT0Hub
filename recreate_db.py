import os, sys

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_dir, 'instance', 'tut0hub.db')

    if os.path.exists(db_path):
        os.remove(db_path)
        print("Base de datos eliminada")

    os.chdir(project_dir)
    sys.path.insert(0, project_dir)

    try:
        from app import create_app, db
        from app.models.user import User

        app = create_app()
        with app.app_context():
            db.create_all()
            print("Tablas creadas")

            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', email='admin@tut0hub.com', role='admin')
                admin.set_password('Admin123')
                db.session.add(admin)

                editor = User(username='editor', email='editor@tut0hub.com', role='editor')
                editor.set_password('Editor123')
                db.session.add(editor)

                db.session.commit()
                print("Usuarios de prueba creados:")
                print("  admin / Admin123  (rol: admin)")
                print("  editor / Editor123  (rol: editor)")

        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)