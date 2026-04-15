"""
Utilidad para generar y validar CAPTCHA simple.
El store usa MongoDB para funcionar correctamente con gunicorn multi-worker.
Si no hay contexto de app (tests, etc.) cae a memoria como fallback.
"""
import random
import string
from datetime import datetime, timedelta


class SimpleCaptcha:
    """Generador de CAPTCHA basado en operaciones matemáticas simples."""

    @staticmethod
    def generate():
        """
        Genera un CAPTCHA con una operación matemática simple.
        Retorna: (pregunta, respuesta_correcta, token)
        """
        operations = [
            ('suma',           '+', lambda a, b: a + b),
            ('resta',          '-', lambda a, b: a - b),
            ('multiplicacion', 'x', lambda a, b: a * b),
        ]

        op_name, op_symbol, op_func = random.choice(operations)

        if op_name == 'suma':
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
        elif op_name == 'resta':
            num1 = random.randint(10, 30)
            num2 = random.randint(1, num1)
        else:
            num1 = random.randint(2, 10)
            num2 = random.randint(2, 10)

        answer  = op_func(num1, num2)
        question = f"Cuanto es {num1} {op_symbol} {num2}?"
        token    = SimpleCaptcha._generate_token()

        return question, answer, token

    @staticmethod
    def _generate_token():
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(16))

    @staticmethod
    def validate(user_answer, correct_answer):
        try:
            return int(user_answer) == int(correct_answer)
        except (ValueError, TypeError):
            return False


class CaptchaStore:
    """
    Store de CAPTCHAs respaldado por MongoDB.
    Funciona correctamente con múltiples workers de gunicorn porque
    todos comparten la misma base de datos en lugar de memoria de proceso.
    """

    # Fallback en memoria (solo para entornos sin contexto Flask)
    _memory_store = {}

    @staticmethod
    def _get_collection():
        """Obtiene la colección de MongoDB. Retorna None si no hay contexto."""
        try:
            from app import get_db
            db = get_db()
            if db is None:
                return None
            return db.captcha_store
        except Exception:
            return None

    @staticmethod
    def _ensure_index():
        """Crea índice TTL la primera vez (MongoDB borra docs expirados solo)."""
        try:
            col = CaptchaStore._get_collection()
            if col is not None:
                col.create_index('expires_at', expireAfterSeconds=0)
        except Exception:
            pass

    @staticmethod
    def save(token, answer, expires_minutes=5):
        """Guarda un CAPTCHA con tiempo de expiración."""
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        col = CaptchaStore._get_collection()

        if col is not None:
            try:
                CaptchaStore._ensure_index()
                col.replace_one(
                    {'token': token},
                    {'token': token, 'answer': answer, 'expires_at': expires_at},
                    upsert=True
                )
                return
            except Exception:
                pass

        # Fallback memoria
        CaptchaStore._memory_store[token] = {
            'answer': answer,
            'expires_at': expires_at
        }

    @staticmethod
    def get(token):
        """Obtiene la respuesta de un CAPTCHA sin eliminarlo."""
        col = CaptchaStore._get_collection()

        if col is not None:
            try:
                doc = col.find_one({'token': token})
                if not doc:
                    return None
                # Verificar expiración manualmente (el TTL de Mongo puede tardar ~60s)
                if datetime.utcnow() > doc['expires_at']:
                    col.delete_one({'token': token})
                    return None
                return doc['answer']
            except Exception:
                pass

        # Fallback memoria
        data = CaptchaStore._memory_store.get(token)
        if not data:
            return None
        if datetime.utcnow() > data['expires_at']:
            CaptchaStore.delete(token)
            return None
        return data['answer']

    @staticmethod
    def delete(token):
        """Elimina un CAPTCHA del store."""
        col = CaptchaStore._get_collection()
        if col is not None:
            try:
                col.delete_one({'token': token})
                return
            except Exception:
                pass
        CaptchaStore._memory_store.pop(token, None)

    @staticmethod
    def cleanup_expired():
        """Limpia CAPTCHAs expirados (solo necesario para el fallback en memoria)."""
        now = datetime.utcnow()
        expired = [t for t, d in CaptchaStore._memory_store.items() if now > d['expires_at']]
        for t in expired:
            del CaptchaStore._memory_store[t]