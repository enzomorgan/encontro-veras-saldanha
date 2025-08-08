import sys
import subprocess
import pkg_resources
import os

# =============================================
# VERIFICAÇÃO AUTOMÁTICA DE DEPENDÊNCIAS
# =============================================
DEPENDENCIAS_NECESSARIAS = [
    'flask',
    'flask-cors',
    'python-dotenv',
    'werkzeug',
    'pyjwt',
    'sqlalchemy'
]

def verificar_dependencias():
    """Verifica e instala automaticamente as dependências faltantes"""
    faltantes = []
    for pacote in DEPENDENCIAS_NECESSARIAS:
        try:
            pkg_resources.get_distribution(pacote)
        except pkg_resources.DistributionNotFound:
            faltantes.append(pacote)
    
    if faltantes:
        print(f"🔍 Instalando dependências faltantes: {', '.join(faltantes)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *faltantes])
            print("✅ Dependências instaladas com sucesso!")
        except subprocess.CalledProcessError:
            print("❌ Erro ao instalar dependências. Execute manualmente:")
            print(f"pip install {' '.join(faltantes)}")
            sys.exit(1)

# Executa a verificação antes de tudo
verificar_dependencias()

# =============================================
# CÓDIGO ORIGINAL DO SEU MAIN.PY (MODIFICADO)
# =============================================
from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import NotFound

# Cria a instância do Flask primeiro
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurações básicas
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuração do SECRET_KEY
secret_key = os.environ.get('JWT_SECRET_KEY')
if not secret_key:
    raise RuntimeError("JWT_SECRET_KEY não definida")
app.config['SECRET_KEY'] = secret_key

# Habilitar CORS
CORS(app, origins=['*'])

# Configuração do banco de dados (modificado para funcionar no Render)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Corrige para PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://')
else:
    # Caminho absoluto para SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(db_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_path, "app.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Importações relativas após configurações
from src.models.user import db
db.init_app(app)

# Registrar blueprints
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.pedidos import pedidos_bp
from src.routes.pagamentos import pagamentos_bp
from src.routes.reservas import reservas_bp
from src.routes.status import status_bp
from src.routes.admin_auth import admin_auth_bp
from src.routes.admin_dashboard import admin_dashboard_bp

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(pedidos_bp)
app.register_blueprint(pagamentos_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(status_bp)
app.register_blueprint(admin_auth_bp, url_prefix='/api')
app.register_blueprint(admin_dashboard_bp, url_prefix='/api')

# Criação das tabelas com tratamento de erros
with app.app_context():
    from src.models.user import User
    from src.models.pedido import Pedido
    from src.models.pagamento import Pagamento
    from src.models.reserva import Reserva
    from src.models.admin import Admin, AuditLog
    
    try:
        db.create_all()
        print("✅ Banco de dados criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {str(e)}")
        if 'unable to open database file' in str(e):
            print("🔧 Dica: Verifique as permissões do diretório 'instance'")
        elif 'already exists' in str(e):
            print("ℹ️ As tabelas já existem no banco de dados.")
        else:
            print("⚠️ Erro desconhecido ao acessar o banco de dados")

# Rotas
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except NotFound:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health_check():
    return {'status': 'ok', 'database': 'connected' if database_url else 'sqlite'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"🚀 Servidor iniciando na porta {port} (debug={'ON' if debug else 'OFF'})")
    app.run(host='0.0.0.0', port=port, debug=debug)
