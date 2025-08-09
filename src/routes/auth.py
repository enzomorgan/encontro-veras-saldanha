import os
from flask import Blueprint, jsonify, request
from src.models.user import User, db
import jwt
import datetime
import re
from functools import wraps
from flask_cors import cross_origin

auth_bp = Blueprint('auth', __name__)

# Configurações seguras (usando variáveis de ambiente)
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
TOKEN_EXPIRATION_DAYS = 7

def validate_email(email):
    """Valida formato do email com regex atualizado"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validação de senha mais robusta"""
    return len(password) >= 8 and any(c.isupper() for c in password) and any(c.isdigit() for c in password)

def generate_token(user_id):
    """Gera token JWT seguro"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_EXPIRATION_DAYS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

@auth_bp.route('/cadastro', methods=['POST'])
@cross_origin(origins=["https://encontro-veras-saldanha.onrender.com"])
def cadastro():
    try:
        # Verifica se o conteúdo é JSON
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 415

        data = request.get_json()
        
        # Validação dos campos obrigatórios
        required_fields = {
            'nomeCompleto': str,
            'email': str,
            'password': str,
            'confirmPassword': str,
            'descendencia': str,
            'idade': int,
            'cidadeResidencia': str
        }

        missing_fields = []
        type_errors = []
        
        for field, field_type in required_fields.items():
            if field not in data:
                missing_fields.append(field)
            elif not isinstance(data[field], field_type):
                type_errors.append(f"{field} deve ser do tipo {field_type.__name__}")

        if missing_fields:
            return jsonify({'error': f'Campos obrigatórios faltando: {", ".join(missing_fields)}'}), 400
        if type_errors:
            return jsonify({'error': f'Erros de tipo: {"; ".join(type_errors)}'}), 400

        # Processamento dos dados
        email = data['email'].strip().lower()
        
        # Validações específicas
        if not validate_email(email):
            return jsonify({'error': 'Formato de e-mail inválido'}), 400
            
        if data['password'] != data['confirmPassword']:
            return jsonify({'error': 'As senhas não coincidem'}), 400
            
        if not validate_password(data['password']):
            return jsonify({
                'error': 'Senha deve ter pelo menos 8 caracteres, incluindo maiúsculas e números',
                'requirements': {
                    'min_length': 8,
                    'needs_upper': True,
                    'needs_digit': True
                }
            }), 400

        if data['descendencia'].lower() not in ['veras', 'saldanha']:
            return jsonify({'error': 'Descendência deve ser "veras" ou "saldanha"'}), 400

        if not 6 <= data['idade'] <= 120:
            return jsonify({'error': 'Idade deve estar entre 6 e 120 anos'}), 400

        # Verifica se usuário já existe
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'E-mail já cadastrado'}), 409

        # Criação do usuário
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

        # Resposta de sucesso
        return jsonify({
            'message': 'Cadastro realizado com sucesso',
            'user': user.to_dict(),
            'token': generate_token(user.id)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Erro interno no servidor',
            'details': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
@cross_origin(origins=["https://encontro-veras-saldanha.onrender.com"])
def login():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 415

        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenciais inválidas'}), 401

        if not user.is_active:
            return jsonify({'error': 'Conta desativada'}), 403

        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': generate_token(user.id)
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Erro interno no servidor',
            'details': str(e)
        }), 500

@auth_bp.route('/verify-token', methods=['POST'])
@cross_origin(origins=["https://encontro-veras-saldanha.onrender.com"])
def verify_token():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 415

        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'error': 'Token não fornecido'}), 400

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            
            if not user or not user.is_active:
                raise jwt.InvalidTokenError

            return jsonify({
                'valid': True,
                'user': user.to_dict()
            }), 200

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

    except Exception as e:
        return jsonify({
            'error': 'Erro interno no servidor',
            'details': str(e)
        }), 500

def token_required(f):
    """Decorator para rotas protegidas"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Obter token do header Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token de acesso necessário'}), 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            
            if not current_user or not current_user.is_active:
                raise jwt.InvalidTokenError
                
            return f(current_user, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({
                'error': 'Erro na validação do token',
                'details': str(e)
            }), 401

    return decorated
