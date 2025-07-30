from datetime import datetime
from src.models.user import db

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados do pedido
    total_camisas = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)  # preço por camisa baseado na idade
    camisas_json = db.Column(db.Text, nullable=False)  # JSON com tamanhos e quantidades
    
    # Status e datas
    status = db.Column(db.String(50), nullable=False, default='pendente')  # pendente, pago, cancelado
    data_pedido = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    usuario = db.relationship('User', backref=db.backref('pedidos', lazy=True))
    pagamentos = db.relationship('Pagamento', backref='pedido', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pedido {self.id} - Usuario {self.usuario_id} - R$ {self.valor_total}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'total_camisas': self.total_camisas,
            'valor_total': self.valor_total,
            'preco_unitario': self.preco_unitario,
            'camisas_json': self.camisas_json,
            'status': self.status,
            'data_pedido': self.data_pedido.isoformat() if self.data_pedido else None,
            'data_pagamento': self.data_pagamento.isoformat() if self.data_pagamento else None,
            'usuario': self.usuario.to_dict() if self.usuario else None
        }

