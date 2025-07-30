import json
from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db, User
from src.models.pedido import Pedido
from src.models.pagamento import Pagamento
from src.routes.auth import token_required

pedidos_bp = Blueprint('pedidos', __name__)

@pedidos_bp.route('/api/pedidos', methods=['POST'])
@token_required
def criar_pedido(current_user):
    try:
        # Verificar data limite para compra de camisas
        data_limite = datetime(2026, 6, 10, 23, 59, 59)  # 10/06/2026 às 23:59:59
        data_atual = datetime.now()
        
        if data_atual > data_limite:
            return jsonify({
                'error': 'Prazo para compra de camisas encerrado',
                'message': 'O prazo para compra de camisas encerrou em 10/06/2026. Não é mais possível realizar novos pedidos.',
                'data_limite': data_limite.strftime('%d/%m/%Y'),
                'prazo_encerrado': True
            }), 400
        
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['camisas', 'total_camisas', 'valor_total']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Validar se há camisas no pedido
        if data['total_camisas'] <= 0:
            return jsonify({'error': 'Pedido deve ter pelo menos uma camisa'}), 400
        
        # Calcular preço baseado na idade do usuário
        from src.utils.pricing import calcular_preco_camisa
        preco_unitario = calcular_preco_camisa(current_user.idade)
        
        # Validar se usuário pode comprar (idade mínima 6 anos)
        if preco_unitario == 0:
            return jsonify({'error': 'Crianças menores de 6 anos não precisam de camisa'}), 400
        
        # Validar valor total
        valor_esperado = data['total_camisas'] * preco_unitario
        if abs(data['valor_total'] - valor_esperado) > 0.01:
            return jsonify({
                'error': 'Valor total incorreto',
                'valor_esperado': valor_esperado,
                'preco_unitario': preco_unitario,
                'idade_usuario': current_user.idade
            }), 400
        
        # Verificar se usuário já tem pedido pendente
        pedido_existente = Pedido.query.filter_by(
            usuario_id=current_user.id,
            status='pendente'
        ).first()
        
        if pedido_existente:
            return jsonify({'error': 'Você já possui um pedido pendente'}), 400
        
        # Criar novo pedido
        novo_pedido = Pedido(
            usuario_id=current_user.id,
            total_camisas=data['total_camisas'],
            valor_total=data['valor_total'],
            preco_unitario=preco_unitario,
            camisas_json=json.dumps(data['camisas']),
            status='pendente'
        )
        
        db.session.add(novo_pedido)
        db.session.commit()
        
        return jsonify({
            'message': 'Pedido criado com sucesso',
            'pedido': novo_pedido.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@pedidos_bp.route('/api/pedidos', methods=['GET'])
@token_required
def listar_pedidos(current_user):
    try:
        pedidos = Pedido.query.filter_by(usuario_id=current_user.id).order_by(Pedido.data_pedido.desc()).all()
        
        return jsonify({
            'pedidos': [pedido.to_dict() for pedido in pedidos]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@pedidos_bp.route('/api/pedidos/<int:pedido_id>', methods=['GET'])
@token_required
def obter_pedido(current_user, pedido_id):
    try:
        pedido = Pedido.query.filter_by(id=pedido_id, usuario_id=current_user.id).first()
        
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        
        return jsonify({
            'pedido': pedido.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@pedidos_bp.route('/api/pedidos/<int:pedido_id>/cancelar', methods=['POST'])
@token_required
def cancelar_pedido(current_user, pedido_id):
    try:
        pedido = Pedido.query.filter_by(id=pedido_id, usuario_id=current_user.id).first()
        
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        
        if pedido.status != 'pendente':
            return jsonify({'error': 'Apenas pedidos pendentes podem ser cancelados'}), 400
        
        pedido.status = 'cancelado'
        db.session.commit()
        
        return jsonify({
            'message': 'Pedido cancelado com sucesso',
            'pedido': pedido.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# Rotas administrativas (para listar todos os pedidos)
@pedidos_bp.route('/api/admin/pedidos', methods=['GET'])
@token_required
def listar_todos_pedidos(current_user):
    try:
        # Em produção, adicionar verificação de permissão de admin
        pedidos = Pedido.query.order_by(Pedido.data_pedido.desc()).all()
        
        return jsonify({
            'pedidos': [pedido.to_dict() for pedido in pedidos]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

