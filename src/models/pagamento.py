from datetime import datetime
from src.models.user import db

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados do pagamento
    metodo_pagamento = db.Column(db.String(20), nullable=False)  # pix, cartao
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pendente')  # pendente, confirmado, rejeitado
    
    # Dados específicos do PIX
    pix_pagamentos_json = db.Column(db.Text, nullable=True)  # JSON com múltiplos pagamentos PIX
    comprovante_filename = db.Column(db.String(255), nullable=True)
    
    # Dados específicos do cartão
    parcelas = db.Column(db.Integer, nullable=True)
    valor_parcela = db.Column(db.Float, nullable=True)
    
    # Datas
    data_pagamento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_confirmacao = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    usuario = db.relationship('User', backref=db.backref('pagamentos', lazy=True))
    
    def __repr__(self):
        return f'<Pagamento {self.id} - {self.metodo_pagamento} - R$ {self.valor}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'usuario_id': self.usuario_id,
            'metodo_pagamento': self.metodo_pagamento,
            'valor': self.valor,
            'status': self.status,
            'pix_pagamentos_json': self.pix_pagamentos_json,
            'comprovante_filename': self.comprovante_filename,
            'parcelas': self.parcelas,
            'valor_parcela': self.valor_parcela,
            'data_pagamento': self.data_pagamento.isoformat() if self.data_pagamento else None,
            'data_confirmacao': self.data_confirmacao.isoformat() if self.data_confirmacao else None
        }

