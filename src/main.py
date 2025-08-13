from flask import Flask
from flask_cors import CORS
import os

# Importando módulos locais
from models.user import db
from src.routes.auth import auth_bp  # Ajuste relativo à pasta src

# Criação da app Flask
app = Flask(__name__)
CORS(app)

# Configurações do banco de dados (PostgreSQL no Render)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://usuario:senha@localhost:5432/banco_local'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do banco
db.init_app(app)

# Registro de blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Rota de teste
@app.route('/')
def index():
    return "Olá! O site está funcionando."

# Comando para rodar localmente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
