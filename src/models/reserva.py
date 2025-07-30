from datetime import datetime
from src.models.user import db

class Reserva(db.Model):
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados da mesa
    mesa_numero = db.Column(db.String(20), nullable=False)
    mesa_tipo = db.Column(db.String(20), nullable=False)  # VIP, Premium, Standard
    mesa_capacidade = db.Column(db.Integer, nullable=False)
    mesa_localizacao = db.Column(db.String(100), nullable=False)
    
    # Status e datas
    status = db.Column(db.String(50), nullable=False, default='confirmada')  # confirmada, cancelada
    data_reserva = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_cancelamento = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    usuario = db.relationship('User', backref=db.backref('reservas', lazy=True))
    
    def __repr__(self):
        return f'<Reserva {self.id} - Mesa {self.mesa_numero} - Usuario {self.usuario_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'mesa_numero': self.mesa_numero,
            'mesa_tipo': self.mesa_tipo,
            'mesa_capacidade': self.mesa_capacidade,
            'mesa_localizacao': self.mesa_localizacao,
            'status': self.status,
            'data_reserva': self.data_reserva.isoformat() if self.data_reserva else None,
            'data_cancelamento': self.data_cancelamento.isoformat() if self.data_cancelamento else None,
            'usuario': self.usuario.to_dict() if self.usuario else None
        }

