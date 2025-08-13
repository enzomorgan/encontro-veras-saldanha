import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db  # SQLAlchemy importado do módulo user

# Cria a app Flask
app = Flask(__name__, static_folder='src/static', template_folder='src/templates')

# Configuração do banco de dados
# Render fornece a variável de ambiente DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///db.sqlite3'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco
db.init_app(app)

# Configura CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Permite requisições do seu frontend

# Rotas para arquivos estáticos
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

# Rota raiz (home)
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Aqui você pode adicionar suas rotas API, importando de src/routes ou módulos correspondentes

if __name__ == '__main__':
    # Rodando localmente, mas no Render o gunicorn vai usar o app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
