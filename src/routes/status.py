from flask import Blueprint, jsonify
from datetime import datetime
from src.routes.auth import token_required
from src.utils.pricing import get_info_preco
from functools import wraps
import logging

# Configuração de logging
logger = logging.getLogger(__name__)
status_bp = Blueprint('status_bp', __name__)  # Nome deve bater com o registrado no main.py

def handle_status_errors(f):
    """Decorator para tratamento centralizado de erros"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validação falhou: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
            return jsonify({'error': 'Erro interno no servidor'}), 500
    return wrapper

@status_bp.route('/status', methods=['GET'])
@handle_status_errors
def verificar_status():
    """Rota pública para verificar status do sistema"""
    data_limite_compra = datetime(2026, 6, 10, 23, 59, 59)
    data_atual = datetime.now()
    dias_restantes = max((data_limite_compra - data_atual).days, 0)
    
    return jsonify({
        'sistema_ativo': True,
        'timestamps': {
            'server': data_atual.isoformat(),
            'limite_compra': data_limite_compra.isoformat()
        },
        'compra_camisas': {
            'ativa': data_atual <= data_limite_compra,
            'dias_restantes': dias_restantes
        },
        'evento': {
            'nome': 'VI Encontro da Família Veras & Saldanha',
            'data': '11 de julho de 2026',
            'local': 'Requinte Buffet',
            'cidade': 'Mossoró - RN'
        }
    })

@status_bp.route('/status/compra', methods=['GET'])
@token_required
@handle_status_errors
def verificar_status_compra(current_user):
    """Rota protegida para status de compra do usuário"""
    data_limite = datetime(2026, 6, 10, 23, 59, 59)
    
    return jsonify({
        'pode_comprar': datetime.now() <= data_limite,
        'usuario': {
            'id': current_user.id,
            'nome': current_user.nome_completo[:50]  # Prevenção contra overflow
        }
    })

@status_bp.route('/status/preco/<int:idade>', methods=['GET'])
@handle_status_errors
def calcular_preco_por_idade(idade):
    """Calcula preço com validação robusta"""
    if not 0 <= idade <= 120:
        raise ValueError("Idade deve estar entre 0 e 120 anos")
    
    return jsonify({
        'preco': get_info_preco(idade),
        'idade_validada': idade
    })
