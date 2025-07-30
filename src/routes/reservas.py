from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db, User
from src.models.reserva import Reserva
from src.routes.auth import token_required

reservas_bp = Blueprint('reservas', __name__)

# Dados das mesas (em produção, isso viria de uma tabela separada)
MESAS_DISPONIVEIS = [
    # Mesas VIP
    {'numero': 'VIP-01', 'tipo': 'VIP', 'capacidade': 8, 'localizacao': 'Frente do palco'},
    {'numero': 'VIP-02', 'tipo': 'VIP', 'capacidade': 8, 'localizacao': 'Frente do palco'},
    {'numero': 'VIP-03', 'tipo': 'VIP', 'capacidade': 8, 'localizacao': 'Frente do palco'},
    {'numero': 'VIP-04', 'tipo': 'VIP', 'capacidade': 8, 'localizacao': 'Frente do palco'},
    
    # Mesas Premium
    {'numero': 'P-01', 'tipo': 'Premium', 'capacidade': 10, 'localizacao': 'Área central'},
    {'numero': 'P-02', 'tipo': 'Premium', 'capacidade': 10, 'localizacao': 'Área central'},
    {'numero': 'P-03', 'tipo': 'Premium', 'capacidade': 10, 'localizacao': 'Área central'},
    {'numero': 'P-04', 'tipo': 'Premium', 'capacidade': 10, 'localizacao': 'Área central'},
    {'numero': 'P-05', 'tipo': 'Premium', 'capacidade': 10, 'localizacao': 'Área central'},
    {'numero': 'P-06', 'tipo': 'Premium', 'capacidade': 10, 'localizacao': 'Área central'},
    
    # Mesas Standard
    {'numero': 'S-01', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-02', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-03', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-04', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-05', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-06', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-07', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
    {'numero': 'S-08', 'tipo': 'Standard', 'capacidade': 12, 'localizacao': 'Área geral'},
]

@reservas_bp.route('/api/mesas', methods=['GET'])
@token_required
def listar_mesas(current_user):
    try:
        # Obter reservas ativas
        reservas_ativas = Reserva.query.filter_by(status='confirmada').all()
        mesas_reservadas = {reserva.mesa_numero for reserva in reservas_ativas}
        
        # Preparar lista de mesas com status
        mesas_com_status = []
        for mesa in MESAS_DISPONIVEIS:
            mesa_info = mesa.copy()
            if mesa['numero'] in mesas_reservadas:
                mesa_info['status'] = 'reservada'
            else:
                mesa_info['status'] = 'disponivel'
            mesas_com_status.append(mesa_info)
        
        return jsonify({
            'mesas': mesas_com_status
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reservas_bp.route('/api/reservas', methods=['POST'])
@token_required
def criar_reserva(current_user):
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['mesa_numero', 'mesa_tipo', 'mesa_capacidade', 'mesa_localizacao']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se usuário já tem reserva ativa
        reserva_existente = Reserva.query.filter_by(
            usuario_id=current_user.id,
            status='confirmada'
        ).first()
        
        if reserva_existente:
            return jsonify({'error': 'Você já possui uma reserva ativa'}), 400
        
        # Verificar se mesa existe
        mesa_valida = None
        for mesa in MESAS_DISPONIVEIS:
            if mesa['numero'] == data['mesa_numero']:
                mesa_valida = mesa
                break
        
        if not mesa_valida:
            return jsonify({'error': 'Mesa não encontrada'}), 404
        
        # Verificar se mesa já está reservada
        reserva_mesa = Reserva.query.filter_by(
            mesa_numero=data['mesa_numero'],
            status='confirmada'
        ).first()
        
        if reserva_mesa:
            return jsonify({'error': 'Mesa já está reservada'}), 400
        
        # Validar dados da mesa
        if (data['mesa_tipo'] != mesa_valida['tipo'] or 
            data['mesa_capacidade'] != mesa_valida['capacidade'] or
            data['mesa_localizacao'] != mesa_valida['localizacao']):
            return jsonify({'error': 'Dados da mesa não conferem'}), 400
        
        # Criar nova reserva
        nova_reserva = Reserva(
            usuario_id=current_user.id,
            mesa_numero=data['mesa_numero'],
            mesa_tipo=data['mesa_tipo'],
            mesa_capacidade=data['mesa_capacidade'],
            mesa_localizacao=data['mesa_localizacao'],
            status='confirmada'
        )
        
        db.session.add(nova_reserva)
        db.session.commit()
        
        return jsonify({
            'message': 'Reserva criada com sucesso',
            'reserva': nova_reserva.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reservas_bp.route('/api/reservas', methods=['GET'])
@token_required
def listar_reservas(current_user):
    try:
        reservas = Reserva.query.filter_by(usuario_id=current_user.id).order_by(Reserva.data_reserva.desc()).all()
        
        return jsonify({
            'reservas': [reserva.to_dict() for reserva in reservas]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reservas_bp.route('/api/reservas/<int:reserva_id>/cancelar', methods=['POST'])
@token_required
def cancelar_reserva(current_user, reserva_id):
    try:
        reserva = Reserva.query.filter_by(id=reserva_id, usuario_id=current_user.id).first()
        
        if not reserva:
            return jsonify({'error': 'Reserva não encontrada'}), 404
        
        if reserva.status != 'confirmada':
            return jsonify({'error': 'Apenas reservas confirmadas podem ser canceladas'}), 400
        
        reserva.status = 'cancelada'
        reserva.data_cancelamento = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Reserva cancelada com sucesso',
            'reserva': reserva.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reservas_bp.route('/api/reservas/minha', methods=['GET'])
@token_required
def obter_minha_reserva(current_user):
    try:
        reserva = Reserva.query.filter_by(
            usuario_id=current_user.id,
            status='confirmada'
        ).first()
        
        if not reserva:
            return jsonify({'reserva': None}), 200
        
        return jsonify({
            'reserva': reserva.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# Rotas administrativas
@reservas_bp.route('/api/admin/reservas', methods=['GET'])
@token_required
def listar_todas_reservas(current_user):
    try:
        # Em produção, adicionar verificação de permissão de admin
        reservas = Reserva.query.order_by(Reserva.data_reserva.desc()).all()
        
        return jsonify({
            'reservas': [reserva.to_dict() for reserva in reservas]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@reservas_bp.route('/api/admin/mesas/status', methods=['GET'])
@token_required
def status_mesas(current_user):
    try:
        # Em produção, adicionar verificação de permissão de admin
        reservas_ativas = Reserva.query.filter_by(status='confirmada').all()
        
        # Estatísticas
        total_mesas = len(MESAS_DISPONIVEIS)
        mesas_reservadas = len(reservas_ativas)
        mesas_disponiveis = total_mesas - mesas_reservadas
        
        # Detalhes por tipo
        tipos_stats = {}
        for mesa in MESAS_DISPONIVEIS:
            tipo = mesa['tipo']
            if tipo not in tipos_stats:
                tipos_stats[tipo] = {'total': 0, 'reservadas': 0, 'disponiveis': 0}
            tipos_stats[tipo]['total'] += 1
        
        for reserva in reservas_ativas:
            tipo = reserva.mesa_tipo
            if tipo in tipos_stats:
                tipos_stats[tipo]['reservadas'] += 1
        
        for tipo in tipos_stats:
            tipos_stats[tipo]['disponiveis'] = tipos_stats[tipo]['total'] - tipos_stats[tipo]['reservadas']
        
        return jsonify({
            'total_mesas': total_mesas,
            'mesas_reservadas': mesas_reservadas,
            'mesas_disponiveis': mesas_disponiveis,
            'tipos_stats': tipos_stats,
            'reservas_ativas': [reserva.to_dict() for reserva in reservas_ativas]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

