import random
import string
from datetime import datetime, timedelta

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False


def generate_otp_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def otp_expiry(minutes=10):
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_otp_valid(code, stored_code, expiry):
    if not stored_code or not expiry:
        return False
    if datetime.utcnow() > expiry:
        return False
    return code.strip() == stored_code.strip()


def generate_totp_secret():
    if not PYOTP_AVAILABLE:
        return None
    return pyotp.random_base32()


def get_totp_uri(secret, username, issuer='TUT0hub'):
    if not PYOTP_AVAILABLE or not secret:
        return None
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def verify_totp(secret, code):
    if not PYOTP_AVAILABLE or not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)