# task_service/auth.py
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import bcrypt

def generate_token(username):
    """Generar token JWT con expiración de 5 minutos"""
    payload = {
        'exp': datetime.utcnow() + timedelta(minutes=5),
        'iat': datetime.utcnow(),
        'sub': username
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def hash_password(password):
    """Hashear contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, user_password):
    """Verificar contraseña hasheada"""
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

def token_required(f):
    """Decorador para requerir token JWT válido"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                # Formato esperado: "Bearer <token>"
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({"error": "Formato de token inválido. Use: Bearer <token>"}), 401
        
        if not token:
            return jsonify({"error": "Token requerido"}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado. Por favor, inicie sesión nuevamente"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated