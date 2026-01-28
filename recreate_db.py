#!/usr/bin/env python3
"""Script para recrear la base de datos con el nuevo esquema"""

import os
import sys

def main():
    db_path = r"C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean\instance\tut0hub.db"
    
    # Eliminar BD antigua
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✅ Base de datos eliminada: {db_path}")
        else:
            print(f"ℹ️ Base de datos no existe")
    except Exception as e:
        print(f"❌ Error al eliminar BD: {e}")
        return False
    
    # Cambiar directorio
    os.chdir(r"C:\Users\lujan\Downloads\Desarrollo Pagina\TUT0hub_clean")
    sys.path.insert(0, os.getcwd())
    
    # Importar y recrear
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✅ Base de datos recreada con las nuevas columnas")
            print("✅ Listo para registrarse de nuevo")
            return True
    except Exception as e:
        print(f"❌ Error al recrear BD: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
