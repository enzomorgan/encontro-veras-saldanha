from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    descendencia = db.Column(db.String(20), nullable=False)  # 'veras' ou 'saldanha'
    idade = db.Column(db.Integer, nullable=False)  # idade do usuário
    cidade_residencia = db.Column(db.String(100), nullable=False)  # cidade onde reside
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.nome_completo}>'

    def set_password(self, password):
        """Define a senha do usuário com hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'nome_completo': self.nome_completo,
            'email': self.email,
            'descendencia': self.descendencia,
            'idade': self.idade,
            'cidade_residencia': self.cidade_residencia,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
