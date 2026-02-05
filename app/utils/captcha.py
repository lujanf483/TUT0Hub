"""
Utilidad para generar y validar CAPTCHA simple
Sistema de verificación humana mediante operaciones matemáticas
"""
import random
import string
from datetime import datetime, timedelta

class SimpleCaptcha:
    """
    Generador de CAPTCHA basado en operaciones matemáticas simples
    """
    
    @staticmethod
    def generate():
        """
        Genera un CAPTCHA con una operación matemática simple
        Retorna: (pregunta, respuesta_correcta, token)
        """
        operations = [
            ('suma', '+', lambda a, b: a + b),
            ('resta', '-', lambda a, b: a - b),
            ('multiplicación', '×', lambda a, b: a * b),
        ]
        
        # Seleccionar operación aleatoria
        op_name, op_symbol, op_func = random.choice(operations)
        
        # Generar números según la operación
        if op_name == 'suma':
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
        elif op_name == 'resta':
            num1 = random.randint(10, 30)
            num2 = random.randint(1, num1)  # Asegurar resultado positivo
        else:  # multiplicación
            num1 = random.randint(2, 10)
            num2 = random.randint(2, 10)
        
        # Calcular respuesta
        answer = op_func(num1, num2)
        
        # Generar pregunta
        question = f"¿Cuánto es {num1} {op_symbol} {num2}?"
        
        # Generar token único
        token = SimpleCaptcha._generate_token()
        
        return question, answer, token
    
    @staticmethod
    def _generate_token():
        """Genera un token único para el CAPTCHA"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(16))
    
    @staticmethod
    def validate(user_answer, correct_answer):
        """
        Valida la respuesta del usuario
        """
        try:
            return int(user_answer) == int(correct_answer)
        except (ValueError, TypeError):
            return False


class CaptchaStore:
    """
    Almacén temporal de CAPTCHAs en memoria
    En producción, usar Redis o base de datos
    """
    _store = {}
    
    @staticmethod
    def save(token, answer, expires_minutes=5):
        """Guarda un CAPTCHA con tiempo de expiración"""
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        CaptchaStore._store[token] = {
            'answer': answer,
            'expires_at': expires_at
        }
    
    @staticmethod
    def get(token):
        """Obtiene y elimina un CAPTCHA del almacén"""
        captcha_data = CaptchaStore._store.get(token)
        
        if not captcha_data:
            return None
        
        # Verificar expiración
        if datetime.now() > captcha_data['expires_at']:
            CaptchaStore.delete(token)
            return None
        
        return captcha_data['answer']
    
    @staticmethod
    def delete(token):
        """Elimina un CAPTCHA del almacén"""
        if token in CaptchaStore._store:
            del CaptchaStore._store[token]
    
    @staticmethod
    def cleanup_expired():
        """Limpia CAPTCHAs expirados"""
        now = datetime.now()
        expired_tokens = [
            token for token, data in CaptchaStore._store.items()
            if now > data['expires_at']
        ]
        for token in expired_tokens:
            CaptchaStore.delete(token)