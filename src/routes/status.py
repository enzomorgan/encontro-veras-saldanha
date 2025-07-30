from flask import Blueprint, jsonify
from datetime import datetime
from src.routes.auth import token_required

status_bp = Blueprint('status', __name__)

@status_bp.route('/api/status', methods=['GET'])
def verificar_status():
    """Rota pública para verificar status do sistema e prazos"""
    try:
        # Data limite para compra de camisas
        data_limite_compra = datetime(2026, 6, 10, 23, 59, 59)  # 10/06/2026 às 23:59:59
        data_atual = datetime.now()
        
        # Calcular dias restantes
        dias_restantes = (data_limite_compra - data_atual).days if data_atual <= data_limite_compra else 0
        
        # Status da compra de camisas
        compra_ativa = data_atual <= data_limite_compra
        
        return jsonify({
            'sistema_ativo': True,
            'data_atual': data_atual.strftime('%d/%m/%Y %H:%M:%S'),
            'compra_camisas': {
                'ativa': compra_ativa,
                'data_limite': data_limite_compra.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes,
                'prazo_encerrado': not compra_ativa
            },
            'evento': {
                'nome': 'VI Encontro da Família Veras & Saldanha',
                'data': '11 de julho de 2026',
                'local': 'Requinte Buffet',
                'cidade': 'Mossoró - RN',
                'ano': '2026'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@status_bp.route('/api/status/compra', methods=['GET'])
@token_required
def verificar_status_compra(current_user):
    """Rota protegida para verificar se usuário pode comprar"""
    try:
        # Data limite para compra de camisas
        data_limite_compra = datetime(2026, 6, 10, 23, 59, 59)  # 10/06/2026 às 23:59:59
        data_atual = datetime.now()
        
        # Status da compra
        pode_comprar = data_atual <= data_limite_compra
        
        return jsonify({
            'pode_comprar': pode_comprar,
            'data_limite': data_limite_compra.strftime('%d/%m/%Y'),
            'data_atual': data_atual.strftime('%d/%m/%Y %H:%M:%S'),
            'usuario_id': current_user.id,
            'usuario_nome': current_user.nome_completo
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@status_bp.route('/api/status/preco/<int:idade>', methods=['GET'])
def calcular_preco_por_idade(idade):
    """Rota pública para calcular preço da camisa baseado na idade"""
    try:
        from src.utils.pricing import get_info_preco
        
        # Validar idade
        if idade < 0 or idade > 120:
            return jsonify({'error': 'Idade deve estar entre 0 e 120 anos'}), 400
        
        info_preco = get_info_preco(idade)
        
        return jsonify({
            'success': True,
            'pricing': info_preco
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

