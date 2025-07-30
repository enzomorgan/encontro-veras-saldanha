import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.pedidos import pedidos_bp
from src.routes.pagamentos import pagamentos_bp
from src.routes.reservas import reservas_bp
from src.routes.status import status_bp
from src.routes.admin_auth import admin_auth_bp
from src.routes.admin_dashboard import admin_dashboard_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuração para produção
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'encontro-veras-saldanha-2026-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Habilitar CORS para permitir requisições do frontend
CORS(app, origins=['*'])

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(pedidos_bp)
app.register_blueprint(pagamentos_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(status_bp)
app.register_blueprint(admin_auth_bp, url_prefix='/api')
app.register_blueprint(admin_dashboard_bp, url_prefix='/api')

# Configuração do banco de dados
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Produção - usar PostgreSQL do Render
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Desenvolvimento - usar SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Importar modelos na ordem correta (primeiro User, depois os que dependem dele)
    from src.models.user import User
    from src.models.pedido import Pedido
    from src.models.pagamento import Pagamento
    from src.models.reserva import Reserva
    from src.models.admin import Admin, AuditLog
    
    # Criar todas as tabelas
    db.create_all()
    print("Banco de dados criado com sucesso!")
    
    # Criar super admin padrão se não existir
    super_admin = Admin.query.filter_by(email='admin@encontroveras.com').first()
    if not super_admin:
        super_admin = Admin(
            nome_completo='Super Administrador',
            email='admin@encontroveras.com',
            nivel_acesso='super_admin'
        )
        super_admin.set_password('admin123456')  # Senha padrão - DEVE SER ALTERADA
        db.session.add(super_admin)
        db.session.commit()
        print("Super administrador criado: admin@encontroveras.com / admin123456")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
