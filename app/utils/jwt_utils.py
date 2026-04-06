import jwt
import secrets
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models.user import RefreshToken


def generate_access_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'type': 'access',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def generate_refresh_token(user_id):
    token = secrets.token_hex(64)
    expires_at = datetime.utcnow() + timedelta(days=7)
    rt = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.session.add(rt)
    db.session.commit()
    return token


def validate_access_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        if payload.get('type') != 'access':
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def refresh_access_token(refresh_token_str):
    rt = RefreshToken.query.filter_by(token=refresh_token_str).first()
    if not rt or not rt.is_valid():
        return None, None
    rt.revoked = True
    db.session.commit()
    new_access = generate_access_token(rt.user_id, rt.user.role)
    new_refresh = generate_refresh_token(rt.user_id)
    return new_access, new_refresh


def revoke_refresh_token(token_str):
    rt = RefreshToken.query.filter_by(token=token_str).first()
    if rt:
        rt.revoked = True
        db.session.commit()


def revoke_all_user_tokens(user_id):
    RefreshToken.query.filter_by(user_id=user_id, revoked=False).update({'revoked': True})
    db.session.commit()