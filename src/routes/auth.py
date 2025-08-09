import os
from flask import Blueprint, jsonify, request
from src.models.user import User, db
import jwt
import datetime
import re
from functools import wraps
from werkzeug.exceptions import BadRequest, Unauthorized, Conflict
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth_bp', __name__)  # Nome consistente com main.py

# Configurações (melhor prática para constantes)
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRATION_HOURS = 24 * 7  # 7 dias em horas

class AuthValidation:
    """Classe dedicada para validações de autenticação"""
    
    @staticmethod
    def validate_email(email):
        """Validação robusta de email com regex atualizado"""
        if not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}$'
        return re.fullmatch(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validação de senha com requisitos de segurança"""
        if not isinstance(password, str):
            return False
        return (len(password) >= 8 and 
                any(c.isupper() for c in password) and 
                any(c.isdigit() for c in password))
    
    @staticmethod
    def validate_user_data(data):
        """Validação centralizada dos dados do usuário"""
        errors = {}
        
        # Campos obrigatórios
        required_fields = {
            'nomeCompleto': str,
            'email': str,
            'password': str,
            'confirmPassword': str,
            'descendencia': str,
            'idade': int,
            'cidadeResidencia': str
        }
        
        for field, field_type in required_fields.items():
            if field not in data:
                errors[field] = 'Campo obrigatório'
            elif not isinstance(data[field], field_type):
                errors[field] = f'Deve ser {field_type.__name__}'
        
        # Validações específicas
        if 'email' in data and not AuthValidation.validate_email(data['email']):
            errors['email'] = 'Formato inválido'
            
        if 'password' in data and not AuthValidation.validate_password(data['password']):
            errors['password'] = 'Requisitos não atendidos'
            
        if all(f in data for f in ['password', 'confirmPassword']) and data['password'] != data['confirmPassword']:
            errors['confirmPassword'] = 'Senhas não coincidem'
            
        if 'descendencia' in data and data['descendencia'].lower() not in ['veras', 'saldanha']:
            errors['descendencia'] = 'Deve ser "veras" ou "saldanha"'
            
        if 'idade' in data and not (6 <= data['idade'] <= 120):
            errors['idade'] = 'Deve estar entre 6 e 120 anos'
            
        return errors

def generate_token(user_id):
    """Geração segura de token JWT"""
    try:
        payload = {
            'sub': user_id,  # Standard JWT claim
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS),
            'iat': datetime.datetime.utcnow(),
            'iss': 'encontro-veras-saldanha-api'  # Identificador da aplicação
        }
        return jwt.encode(payload, os.getenv('JWT_SECRET_KEY'), algorithm=JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"Falha na geração de token: {str(e)}")
        raise

def handle_auth_errors(f):
    """Decorator para tratamento centralizado de erros"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BadRequest as e:
            logger.warning(f"Requisição inválida: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Unauthorized as e:
            logger.warning(f"Não autorizado: {str(e)}")
            return jsonify({'error': str(e)}), 401
        except Conflict as e:
            logger.warning(f"Conflito: {str(e)}")
            return jsonify({'error': str(e)}), 409
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
            return jsonify({'error': 'Erro interno no servidor'}), 500
    return wrapper

@auth_bp.route('/cadastro', methods=['POST'])
@handle_auth_errors
def cadastro():
    """Endpoint de cadastro com validação robusta"""
    if not request.is_json:
        raise BadRequest('Content-Type deve ser application/json')
    
    data = request.get_json()
    validation_errors = AuthValidation.validate_user_data(data)
    
    if validation_errors:
        return jsonify({
            'error': 'Dados inválidos',
            'details': validation_errors
        }), 400
    
    email = data['email'].strip().lower()
    
    # Verificação de e-mail existente
    if User.query.filter_by(email=email).first():
        raise Conflict('E-mail já cadastrado')
    
    try:
        user = User(
            nome_completo=data['nomeCompleto'].strip(),
            email=email,
            descendencia=data['descendencia'].lower(),
            idade=data['idade'],
            cidade_residencia=data['cidadeResidencia'].strip()
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Cadastro realizado com sucesso',
            'user': user.to_dict(),
            'token': generate_token(user.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no cadastro: {str(e)}")
        raise

@auth_bp.route('/login', methods=['POST'])
@handle_auth_errors
def login():
    """Endpoint de login seguro"""
    if not request.is_json:
        raise BadRequest('Content-Type deve ser application/json')
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        raise BadRequest('E-mail e senha são obrigatórios')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        raise Unauthorized('Credenciais inválidas')
    
    if not user.is_active:
        raise Unauthorized('Conta desativada')
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user.id)
    }), 200

@auth_bp.route('/verify-token', methods=['POST'])
@handle_auth_errors
def verify_token():
    """Validação de token com tratamento seguro"""
    if not request.is_json:
        raise BadRequest('Content-Type deve ser application/json')
    
    token = request.get_json().get('token')
    if not token:
        raise BadRequest('Token não fornecido')
    
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=[JWT_ALGORITHM])
        user = User.query.get(payload['sub'])  # Usa claim standard 'sub'
        
        if not user or not user.is_active:
            raise Unauthorized('Token inválido')
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except jwt.ExpiredSignatureError:
        raise Unauthorized('Token expirado')
    except jwt.InvalidTokenError:
        raise Unauthorized('Token inválido')

def token_required(f):
    """Decorator para rotas protegidas com JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Unauthorized('Token de acesso necessário')
            
        token = auth_header.split(" ")[1]
        
        try:
            payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=[JWT_ALGORITHM])
            current_user = User.query.get(payload['sub'])
            
            if not current_user or not current_user.is_active:
                raise Unauthorized('Token inválido')
                
            return f(current_user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            raise Unauthorized('Token expirado')
        except jwt.InvalidTokenError:
            raise Unauthorized('Token inválido')
            
    return decorated
