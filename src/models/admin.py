from datetime import datetime
from src.models.user import db

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(20), nullable=False, default='admin')  # 'admin', 'super_admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    def __repr__(self):
        return f'<Admin {self.nome_completo}>'
    
    def set_password(self, password):
        """Define a senha do administrador com hash"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'nome_completo': self.nome_completo,
            'email': self.email,
            'nivel_acesso': self.nivel_acesso,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tabela_afetada = db.Column(db.String(50), nullable=True)
    registro_id = db.Column(db.Integer, nullable=True)
    dados_anteriores = db.Column(db.Text, nullable=True)  # JSON
    dados_novos = db.Column(db.Text, nullable=True)  # JSON
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    admin = db.relationship('Admin', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.acao} by Admin {self.admin_id}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_nome': self.admin.nome_completo if self.admin else None,
            'acao': self.acao,
            'descricao': self.descricao,
            'tabela_afetada': self.tabela_afetada,
            'registro_id': self.registro_id,
            'dados_anteriores': self.dados_anteriores,
            'dados_novos': self.dados_novos,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

