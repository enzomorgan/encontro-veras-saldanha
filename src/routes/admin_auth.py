from flask import Blueprint, jsonify, request
from src.models.user import db
from src.models.admin import Admin, AuditLog
import jwt
import datetime
import re
from functools import wraps

admin_auth_bp = Blueprint('admin_auth', __name__)

# Chave secreta para JWT (em produção, usar variável de ambiente)
JWT_SECRET = 'encontro-veras-saldanha-2026-admin-secret-key'

def validate_email(email):
    """Valida formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida se a senha tem pelo menos 8 caracteres"""
    return len(password) >= 8

def generate_admin_token(admin_id):
    """Gera token JWT para o administrador"""
    payload = {
        'admin_id': admin_id,
        'type': 'admin',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # Token válido por 8 horas
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def admin_token_required(f):
    """Decorator para proteger rotas administrativas"""
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
            return jsonify({'error': 'Token de acesso administrativo necessário'}), 401
        
        try:
            # Decodificar token
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            admin_id = payload['admin_id']
            token_type = payload.get('type')
            
            if token_type != 'admin':
                return jsonify({'error': 'Token não é administrativo'}), 401
            
            # Buscar administrador
            current_admin = Admin.query.get(admin_id)
            if not current_admin or not current_admin.is_active:
                return jsonify({'error': 'Token administrativo inválido'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token administrativo expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token administrativo inválido'}), 401
        except Exception as e:
            return jsonify({'error': 'Erro na validação do token administrativo'}), 401
        
        return f(current_admin, *args, **kwargs)
    
    return decorated

def log_admin_action(admin_id, acao, descricao, tabela_afetada=None, registro_id=None, 
                    dados_anteriores=None, dados_novos=None):
    """Registra ação administrativa no log de auditoria"""
    try:
        import json
        
        log = AuditLog(
            admin_id=admin_id,
            acao=acao,
            descricao=descricao,
            tabela_afetada=tabela_afetada,
            registro_id=registro_id,
            dados_anteriores=json.dumps(dados_anteriores) if dados_anteriores else None,
            dados_novos=json.dumps(dados_novos) if dados_novos else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log de auditoria: {e}")

@admin_auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        
        # Validação dos campos obrigatórios
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Buscar administrador
        admin = Admin.query.filter_by(email=email).first()
        
        if not admin or not admin.check_password(password):
            return jsonify({'error': 'E-mail ou senha incorretos'}), 401
        
        if not admin.is_active:
            return jsonify({'error': 'Conta administrativa desativada'}), 401
        
        # Atualizar último login
        admin.last_login = datetime.datetime.utcnow()
        db.session.commit()
        
        # Registrar login no log
        log_admin_action(
            admin.id, 
            'LOGIN', 
            f'Administrador {admin.nome_completo} fez login'
        )
        
        # Gerar token
        token = generate_admin_token(admin.id)
        
        return jsonify({
            'message': 'Login administrativo realizado com sucesso',
            'admin': admin.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_auth_bp.route('/admin/verify-token', methods=['POST'])
def verify_admin_token():
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 400
        
        # Decodificar token
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        admin_id = payload['admin_id']
        token_type = payload.get('type')
        
        if token_type != 'admin':
            return jsonify({'error': 'Token não é administrativo'}), 401
        
        # Buscar administrador
        admin = Admin.query.get(admin_id)
        if not admin or not admin.is_active:
            return jsonify({'error': 'Token administrativo inválido'}), 401
        
        return jsonify({
            'valid': True,
            'admin': admin.to_dict()
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token administrativo expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token administrativo inválido'}), 401
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_auth_bp.route('/admin/create-admin', methods=['POST'])
@admin_token_required
def create_admin(current_admin):
    try:
        # Apenas super_admin pode criar novos admins
        if current_admin.nivel_acesso != 'super_admin':
            return jsonify({'error': 'Acesso negado. Apenas super administradores podem criar novos administradores'}), 403
        
        data = request.json
        
        # Validação dos campos obrigatórios
        required_fields = ['nome_completo', 'email', 'password', 'nivel_acesso']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        nome_completo = data['nome_completo'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        nivel_acesso = data['nivel_acesso']
        
        # Validações
        if not nome_completo:
            return jsonify({'error': 'Nome completo é obrigatório'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'E-mail inválido'}), 400
        
        if not validate_password(password):
            return jsonify({'error': 'Senha deve ter pelo menos 8 caracteres'}), 400
        
        if nivel_acesso not in ['admin', 'super_admin']:
            return jsonify({'error': 'Nível de acesso deve ser "admin" ou "super_admin"'}), 400
        
        # Verificar se email já existe
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            return jsonify({'error': 'E-mail já cadastrado'}), 400
        
        # Criar novo administrador
        admin = Admin(
            nome_completo=nome_completo,
            email=email,
            nivel_acesso=nivel_acesso,
            created_by=current_admin.id
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        # Registrar criação no log
        log_admin_action(
            current_admin.id,
            'CREATE_ADMIN',
            f'Criou novo administrador: {admin.nome_completo} ({admin.email})',
            'admins',
            admin.id,
            None,
            admin.to_dict()
        )
        
        return jsonify({
            'message': 'Administrador criado com sucesso',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@admin_auth_bp.route('/admin/logout', methods=['POST'])
@admin_token_required
def admin_logout(current_admin):
    try:
        # Registrar logout no log
        log_admin_action(
            current_admin.id,
            'LOGOUT',
            f'Administrador {current_admin.nome_completo} fez logout'
        )
        
        return jsonify({'message': 'Logout realizado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

