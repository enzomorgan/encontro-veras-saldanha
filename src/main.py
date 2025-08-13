import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db


# Cria a app Flask
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuração do banco de dados
# Render fornece a variável de ambiente DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///db.sqlite3'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração da chave secreta JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')

# Inicializa o banco
db.init_app(app)

# Configura CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Importa e registra as rotas
from routes.auth import auth_bp
from routes.user import user_bp
from routes.reservas import reservas_bp
from routes.pedidos import pedidos_bp
from routes.pagamentos import pagamentos_bp
from routes.admin_auth import admin_auth_bp
from routes.admin_dashboard import admin_dashboard_bp
from routes.status import status_bp

# Registra os blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(reservas_bp, url_prefix='/api/reservas')
app.register_blueprint(pedidos_bp, url_prefix='/api/pedidos')
app.register_blueprint(pagamentos_bp, url_prefix='/api/pagamentos')
app.register_blueprint(admin_auth_bp, url_prefix='/api/admin/auth')
app.register_blueprint(admin_dashboard_bp, url_prefix='/api/admin')
app.register_blueprint(status_bp, url_prefix='/api')

# Rotas para arquivos estáticos
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

# Rota raiz (home)
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Rota de health check para o Render
@app.route('/api/health')
def health_check():
    return {'status': 'healthy', 'message': 'API funcionando corretamente'}, 200

if __name__ == '__main__':
    # Rodando localmente, mas no Render o gunicorn vai usar o app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

