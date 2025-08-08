import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import NotFound

# Cria a instância do Flask primeiro
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static')

# Configuração do SECRET_KEY obrigatória no ambiente
secret_key = os.environ.get('JWT_SECRET_KEY')
if not secret_key:
    raise RuntimeError("JWT_SECRET_KEY não definida. Defina essa variável no ambiente de produção.")
app.config['SECRET_KEY'] = secret_key

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Habilitar CORS para permitir requisições do frontend
CORS(app, origins=['*'])

# Importações relativas após a criação do app
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.pedidos import pedidos_bp
from src.routes.pagamentos import pagamentos_bp
from src.routes.reservas import reservas_bp
from src.routes.status import status_bp
from src.routes.admin_auth import admin_auth_bp
from src.routes.admin_dashboard import admin_dashboard_bp

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
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Criação das tabelas do banco de dados
with app.app_context():
    from src.models.user import User
    from src.models.pedido import Pedido
    from src.models.pagamento import Pagamento
    from src.models.reserva import Reserva
    from src.models.admin import Admin, AuditLog
    
    db.create_all()
    print("Banco de dados criado com sucesso!")

# Rotas para servir arquivos estáticos
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    try:
        return send_from_directory(app.static_folder, path)
    except NotFound:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
