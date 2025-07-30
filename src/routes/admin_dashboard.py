from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from src.models.user import db, User
from src.models.admin import Admin, AuditLog
from src.models.pedido import Pedido
from src.models.pagamento import Pagamento
from src.models.reserva import Reserva
from src.routes.admin_auth import admin_token_required, log_admin_action
import json

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)

@admin_dashboard_bp.route('/admin/dashboard/stats', methods=['GET'])
@admin_token_required
def get_dashboard_stats(current_admin):
    try:
        # Estatísticas gerais
        total_usuarios = User.query.filter_by(is_active=True).count()
        total_pedidos = Pedido.query.count()
        total_reservas = Reserva.query.filter_by(status='confirmada').count()
        
        # Receita total
        pedidos_pagos = Pedido.query.filter(Pedido.status.in_(['pago', 'confirmado'])).all()
        receita_total = sum(pedido.valor_total for pedido in pedidos_pagos)
        
        # Camisas vendidas
        camisas_vendidas = sum(pedido.total_camisas for pedido in pedidos_pagos)
        
        # Estatísticas por descendência
        usuarios_veras = User.query.filter_by(descendencia='veras', is_active=True).count()
        usuarios_saldanha = User.query.filter_by(descendencia='saldanha', is_active=True).count()
        
        # Pedidos por status
        pedidos_pendentes = Pedido.query.filter_by(status='pendente').count()
        pedidos_pagos = Pedido.query.filter_by(status='pago').count()
        pedidos_confirmados = Pedido.query.filter_by(status='confirmado').count()
        pedidos_cancelados = Pedido.query.filter_by(status='cancelado').count()
        
        # Mesas por tipo
        reservas_vip = Reserva.query.filter_by(mesa_tipo='VIP', status='confirmada').count()
        reservas_premium = Reserva.query.filter_by(mesa_tipo='Premium', status='confirmada').count()
        reservas_standard = Reserva.query.filter_by(mesa_tipo='Standard', status='confirmada').count()
        
        # Atividade recente (últimos 7 dias)
        data_limite = datetime.utcnow() - timedelta(days=7)
        novos_usuarios = User.query.filter(User.created_at >= data_limite).count()
        novos_pedidos = Pedido.query.filter(Pedido.data_pedido >= data_limite).count()
        novas_reservas = Reserva.query.filter(Reserva.data_reserva >= data_limite).count()
        
        # Verificar prazo de compra
        data_limite_compra = datetime(2026, 6, 10, 23, 59, 59)
        dias_restantes = (data_limite_compra - datetime.now()).days if datetime.now() <= data_limite_compra else 0
        compra_ativa = datetime.now() <= data_limite_compra
        
        return jsonify({
            'geral': {
                'total_usuarios': total_usuarios,
                'total_pedidos': total_pedidos,
                'total_reservas': total_reservas,
                'receita_total': receita_total,
                'camisas_vendidas': camisas_vendidas
            },
            'usuarios': {
                'veras': usuarios_veras,
                'saldanha': usuarios_saldanha,
                'total': total_usuarios
            },
            'pedidos': {
                'pendentes': pedidos_pendentes,
                'pagos': pedidos_pagos,
                'confirmados': pedidos_confirmados,
                'cancelados': pedidos_cancelados
            },
            'reservas': {
                'vip': reservas_vip,
                'premium': reservas_premium,
                'standard': reservas_standard,
                'total': total_reservas
            },
            'atividade_recente': {
                'novos_usuarios': novos_usuarios,
                'novos_pedidos': novos_pedidos,
                'novas_reservas': novas_reservas
            },
            'prazo_compra': {
                'ativo': compra_ativa,
                'dias_restantes': dias_restantes,
                'data_limite': data_limite_compra.strftime('%d/%m/%Y')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/usuarios', methods=['GET'])
@admin_token_required
def get_usuarios(current_admin):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        descendencia = request.args.get('descendencia', '')
        
        query = User.query
        
        # Filtros
        if search:
            query = query.filter(or_(
                User.nome_completo.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            ))
        
        if descendencia:
            query = query.filter_by(descendencia=descendencia)
        
        # Paginação
        usuarios = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'usuarios': [user.to_dict() for user in usuarios.items],
            'total': usuarios.total,
            'pages': usuarios.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/pedidos', methods=['GET'])
@admin_token_required
def get_pedidos(current_admin):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        
        query = Pedido.query
        
        # Filtro por status
        if status:
            query = query.filter_by(status=status)
        
        # Paginação
        pedidos = query.order_by(Pedido.data_pedido.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Incluir dados do usuário
        pedidos_data = []
        for pedido in pedidos.items:
            pedido_dict = pedido.to_dict()
            user = User.query.get(pedido.usuario_id)
            pedido_dict['usuario'] = user.to_dict() if user else None
            pedidos_data.append(pedido_dict)
        
        return jsonify({
            'pedidos': pedidos_data,
            'total': pedidos.total,
            'pages': pedidos.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/reservas', methods=['GET'])
@admin_token_required
def get_reservas(current_admin):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        tipo = request.args.get('tipo', '')
        status = request.args.get('status', '')
        
        query = Reserva.query
        
        # Filtros
        if tipo:
            query = query.filter_by(mesa_tipo=tipo)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginação
        reservas = query.order_by(Reserva.data_reserva.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Incluir dados do usuário
        reservas_data = []
        for reserva in reservas.items:
            reserva_dict = reserva.to_dict()
            user = User.query.get(reserva.usuario_id)
            reserva_dict['usuario'] = user.to_dict() if user else None
            reservas_data.append(reserva_dict)
        
        return jsonify({
            'reservas': reservas_data,
            'total': reservas.total,
            'pages': reservas.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/logs', methods=['GET'])
@admin_token_required
def get_audit_logs(current_admin):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        acao = request.args.get('acao', '')
        admin_id = request.args.get('admin_id', type=int)
        
        query = AuditLog.query
        
        # Filtros
        if acao:
            query = query.filter_by(acao=acao)
        
        if admin_id:
            query = query.filter_by(admin_id=admin_id)
        
        # Paginação
        logs = query.order_by(AuditLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/usuario/<int:user_id>/toggle-status', methods=['POST'])
@admin_token_required
def toggle_user_status(current_admin, user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Salvar estado anterior
        dados_anteriores = user.to_dict()
        
        # Alternar status
        user.is_active = not user.is_active
        db.session.commit()
        
        # Registrar ação no log
        acao = 'ACTIVATE_USER' if user.is_active else 'DEACTIVATE_USER'
        descricao = f'{"Ativou" if user.is_active else "Desativou"} usuário: {user.nome_completo} ({user.email})'
        
        log_admin_action(
            current_admin.id,
            acao,
            descricao,
            'users',
            user.id,
            dados_anteriores,
            user.to_dict()
        )
        
        return jsonify({
            'message': f'Usuário {"ativado" if user.is_active else "desativado"} com sucesso',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/pedido/<int:pedido_id>/update-status', methods=['POST'])
@admin_token_required
def update_pedido_status(current_admin, pedido_id):
    try:
        data = request.json
        novo_status = data.get('status')
        
        if not novo_status or novo_status not in ['pendente', 'pago', 'confirmado', 'cancelado']:
            return jsonify({'error': 'Status inválido'}), 400
        
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        
        # Salvar estado anterior
        dados_anteriores = pedido.to_dict()
        status_anterior = pedido.status
        
        # Atualizar status
        pedido.status = novo_status
        db.session.commit()
        
        # Registrar ação no log
        user = User.query.get(pedido.usuario_id)
        descricao = f'Alterou status do pedido #{pedido.id} de "{status_anterior}" para "{novo_status}" - Usuário: {user.nome_completo if user else "N/A"}'
        
        log_admin_action(
            current_admin.id,
            'UPDATE_PEDIDO_STATUS',
            descricao,
            'pedidos',
            pedido.id,
            dados_anteriores,
            pedido.to_dict()
        )
        
        return jsonify({
            'message': 'Status do pedido atualizado com sucesso',
            'pedido': pedido.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@admin_dashboard_bp.route('/admin/dashboard/reserva/<int:reserva_id>/cancel', methods=['POST'])
@admin_token_required
def cancel_reserva(current_admin, reserva_id):
    try:
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            return jsonify({'error': 'Reserva não encontrada'}), 404
        
        if reserva.status != 'confirmada':
            return jsonify({'error': 'Apenas reservas confirmadas podem ser canceladas'}), 400
        
        # Salvar estado anterior
        dados_anteriores = reserva.to_dict()
        
        # Cancelar reserva
        reserva.status = 'cancelada'
        reserva.data_cancelamento = datetime.utcnow()
        db.session.commit()
        
        # Registrar ação no log
        user = User.query.get(reserva.usuario_id)
        descricao = f'Cancelou reserva da mesa {reserva.mesa_numero} - Usuário: {user.nome_completo if user else "N/A"}'
        
        log_admin_action(
            current_admin.id,
            'CANCEL_RESERVA',
            descricao,
            'reservas',
            reserva.id,
            dados_anteriores,
            reserva.to_dict()
        )
        
        return jsonify({
            'message': 'Reserva cancelada com sucesso',
            'reserva': reserva.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

