# src/main.py

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.status import status_bp
import os

app = Flask(__name__, static_folder="src/static", static_url_path="/static")

# Configuração do banco de dados (substitua pelo URL do seu banco no Render)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o SQLAlchemy
db.init_app(app)

# Configuração do CORS para aceitar requisições do frontend hospedado
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Pode colocar o domínio específico do frontend

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(status_bp, url_prefix='/api')

# Rota para servir os arquivos estáticos
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

# Rota raiz para servir o index.html
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Comando para criar as tabelas se não existirem
with app.app_context():
    db.create_all()

# Inicialização do app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
