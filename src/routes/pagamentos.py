import json
import os
from flask import Blueprint, request, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename
from src.models.user import db, User
from src.models.pedido import Pedido
from src.models.pagamento import Pagamento
from src.routes.auth import token_required

pagamentos_bp = Blueprint('pagamentos', __name__)

# Configuração para upload de arquivos
UPLOAD_FOLDER = 'uploads/comprovantes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@pagamentos_bp.route('/api/pagamentos', methods=['POST'])
@token_required
def processar_pagamento(current_user):
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['pedido_id', 'metodo_pagamento', 'valor']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se pedido existe e pertence ao usuário
        pedido = Pedido.query.filter_by(id=data['pedido_id'], usuario_id=current_user.id).first()
        if not pedido:
            return jsonify({'error': 'Pedido não encontrado'}), 404
        
        if pedido.status != 'pendente':
            return jsonify({'error': 'Pedido já foi processado'}), 400
        
        # Validar método de pagamento
        if data['metodo_pagamento'] not in ['pix', 'cartao']:
            return jsonify({'error': 'Método de pagamento inválido'}), 400
        
        # Validar valor
        if data['valor'] != pedido.valor_total:
            return jsonify({'error': 'Valor do pagamento não confere com o pedido'}), 400
        
        # Criar pagamento
        novo_pagamento = Pagamento(
            pedido_id=pedido.id,
            usuario_id=current_user.id,
            metodo_pagamento=data['metodo_pagamento'],
            valor=data['valor']
        )
        
        # Processar dados específicos do método
        if data['metodo_pagamento'] == 'pix':
            # Validar dados do PIX
            if 'pix_pagamentos' not in data:
                return jsonify({'error': 'Dados dos pagamentos PIX são obrigatórios'}), 400
            
            novo_pagamento.pix_pagamentos_json = json.dumps(data['pix_pagamentos'])
            novo_pagamento.status = 'pendente'  # PIX precisa de confirmação manual
            
        elif data['metodo_pagamento'] == 'cartao':
            # Validar dados do cartão
            if 'parcelas' not in data:
                return jsonify({'error': 'Número de parcelas é obrigatório'}), 400
            
            parcelas = data['parcelas']
            if parcelas < 1 or parcelas > 10:
                return jsonify({'error': 'Número de parcelas deve ser entre 1 e 10'}), 400
            
            novo_pagamento.parcelas = parcelas
            novo_pagamento.valor_parcela = data['valor'] / parcelas
            novo_pagamento.status = 'confirmado'  # Cartão é confirmado automaticamente (simulação)
            novo_pagamento.data_confirmacao = datetime.utcnow()
            
            # Atualizar status do pedido
            pedido.status = 'pago'
            pedido.data_pagamento = datetime.utcnow()
        
        db.session.add(novo_pagamento)
        db.session.commit()
        
        return jsonify({
            'message': 'Pagamento processado com sucesso',
            'pagamento': novo_pagamento.to_dict(),
            'pedido': pedido.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@pagamentos_bp.route('/api/pagamentos/<int:pagamento_id>/comprovante', methods=['POST'])
@token_required
def upload_comprovante(current_user, pagamento_id):
    try:
        # Verificar se pagamento existe e pertence ao usuário
        pagamento = Pagamento.query.filter_by(id=pagamento_id, usuario_id=current_user.id).first()
        if not pagamento:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        if pagamento.metodo_pagamento != 'pix':
            return jsonify({'error': 'Upload de comprovante só é necessário para PIX'}), 400
        
        # Verificar se arquivo foi enviado
        if 'comprovante' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['comprovante']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Formato de arquivo não permitido'}), 400
        
        # Salvar arquivo
        ensure_upload_folder()
        filename = secure_filename(f"{current_user.id}_{pagamento_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Atualizar pagamento
        pagamento.comprovante_filename = filename
        db.session.commit()
        
        return jsonify({
            'message': 'Comprovante enviado com sucesso',
            'filename': filename,
            'pagamento': pagamento.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@pagamentos_bp.route('/api/pagamentos', methods=['GET'])
@token_required
def listar_pagamentos(current_user):
    try:
        pagamentos = Pagamento.query.filter_by(usuario_id=current_user.id).order_by(Pagamento.data_pagamento.desc()).all()
        
        return jsonify({
            'pagamentos': [pagamento.to_dict() for pagamento in pagamentos]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# Rotas administrativas
@pagamentos_bp.route('/api/admin/pagamentos', methods=['GET'])
@token_required
def listar_todos_pagamentos(current_user):
    try:
        # Em produção, adicionar verificação de permissão de admin
        pagamentos = Pagamento.query.order_by(Pagamento.data_pagamento.desc()).all()
        
        return jsonify({
            'pagamentos': [pagamento.to_dict() for pagamento in pagamentos]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@pagamentos_bp.route('/api/admin/pagamentos/<int:pagamento_id>/confirmar', methods=['POST'])
@token_required
def confirmar_pagamento(current_user, pagamento_id):
    try:
        # Em produção, adicionar verificação de permissão de admin
        pagamento = Pagamento.query.get(pagamento_id)
        if not pagamento:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        
        if pagamento.status != 'pendente':
            return jsonify({'error': 'Pagamento já foi processado'}), 400
        
        # Confirmar pagamento
        pagamento.status = 'confirmado'
        pagamento.data_confirmacao = datetime.utcnow()
        
        # Atualizar status do pedido
        pedido = pagamento.pedido
        pedido.status = 'pago'
        pedido.data_pagamento = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Pagamento confirmado com sucesso',
            'pagamento': pagamento.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

