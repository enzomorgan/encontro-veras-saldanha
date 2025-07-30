from flask import Blueprint, jsonify, request
from src.models.user import User, db
import jwt
import datetime
import re

auth_bp = Blueprint('auth', __name__)

# Chave secreta para JWT (em produção, usar variável de ambiente)
JWT_SECRET = 'encontro-veras-saldanha-2026-secret-key'

def validate_email(email):
    """Valida formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida se a senha tem pelo menos 6 caracteres"""
    return len(password) >= 6

def generate_token(user_id):
    """Gera token JWT para o usuário"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # Token válido por 7 dias
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

@auth_bp.route('/cadastro', methods=['POST'])
def cadastro():
    try:
        data = request.json
        
        # Validação dos campos obrigatórios
        required_fields = ['nomeCompleto', 'email', 'password', 'confirmPassword', 'descendencia', 'idade', 'cidadeResidencia']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        nome_completo = data['nomeCompleto'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        confirm_password = data['confirmPassword']
        descendencia = data['descendencia']
        idade = data['idade']
        cidade_residencia = data['cidadeResidencia'].strip()
        
        # Validações
        if not nome_completo:
            return jsonify({'error': 'Nome completo é obrigatório'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'E-mail inválido'}), 400
        
        if not validate_password(password):
            return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Senhas não coincidem'}), 400
        
        if descendencia not in ['veras', 'saldanha']:
            return jsonify({'error': 'Descendência deve ser "veras" ou "saldanha"'}), 400
        
        # Validar idade
        try:
            idade = int(idade)
            if idade < 6 or idade > 120:
                return jsonify({'error': 'Idade deve estar entre 6 e 120 anos'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Idade deve ser um número válido'}), 400
        
        # Validar cidade
        if not cidade_residencia or len(cidade_residencia.strip()) < 2:
            return jsonify({'error': 'Cidade de residência deve ter pelo menos 2 caracteres'}), 400
        
        # Verificar se email já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'E-mail já cadastrado'}), 400
        
        # Criar novo usuário
        user = User(
            nome_completo=nome_completo,
            email=email,
            descendencia=descendencia,
            idade=idade,
            cidade_residencia=cidade_residencia
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Gerar token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Usuário cadastrado com sucesso',
            'user': user.to_dict(),
            'token': token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        # Validação dos campos obrigatórios
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'E-mail ou senha incorretos'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Conta desativada'}), 401
        
        # Gerar token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 400
        
        # Decodificar token
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Buscar usuário
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'Token inválido'}), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500


from functools import wraps

def token_required(f):
    """Decorator para proteger rotas que precisam de autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Verificar se token está no header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401
        
        if not token:
            return jsonify({'error': 'Token de acesso necessário'}), 401
        
        try:
            # Decodificar token
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Buscar usuário
            current_user = User.query.get(user_id)
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Token inválido'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'error': 'Erro na validação do token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

