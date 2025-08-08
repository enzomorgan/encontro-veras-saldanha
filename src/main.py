import sys
import subprocess
import pkg_resources
import os
from werkzeug.exceptions import HTTPException


DEPENDENCIAS_NECESSARIAS = [
    'flask',
    'flask-cors',
    'python-dotenv',
    'werkzeug',
    'pyjwt',
    'sqlalchemy',
    'psycopg2-binary',
    'gunicorn'
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

verificar_dependencias()


from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from werkzeug.exceptions import NotFound

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurações críticas para produção
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
    SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'segredo-desenvolvimento'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 
    f'sqlite:///{os.path.join(os.path.dirname(__file__), "instance", "app.db")}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PROPAGATE_EXCEPTIONS=True
)

# CORS para produção (ajuste os domínios)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://encontro-veras-saldanha.onrender.com",
            "http://localhost:*"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Handler global de erros
@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify({
        "error": str(e),
        "message": "Ocorreu um erro no servidor"
    }), code


from src.models.user import db
db.init_app(app)

# Garante que a pasta instance existe para SQLite
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

# Criação das tabelas
with app.app_context():
    try:
        db.create_all()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro no banco de dados: {str(e)}")
        if 'already exists' not in str(e):
            sys.exit(1)


blueprints = [
    ('src.routes.user', 'user_bp', '/api'),
    ('src.routes.auth', 'auth_bp', '/api/auth'),
    ('src.routes.pedidos', 'pedidos_bp', None),
    ('src.routes.pagamentos', 'pagamentos_bp', None),
    ('src.routes.reservas', 'reservas_bp', None),
    ('src.routes.status', 'status_bp', None),
    ('src.routes.admin_auth', 'admin_auth_bp', '/api'),
    ('src.routes.admin_dashboard', 'admin_dashboard_bp', '/api')
]

for module, bp_name, url_prefix in blueprints:
    try:
        module = __import__(module, fromlist=[bp_name])
        blueprint = getattr(module, bp_name)
        app.register_blueprint(blueprint, url_prefix=url_prefix)
    except Exception as e:
        print(f"⚠️ Erro ao registrar {bp_name}: {str(e)}")


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
    return jsonify({
        "status": "online",
        "database": "postgresql" if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else "sqlite"
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("\n" + "="*50)
    print(f"🚀 Iniciando servidor na porta {port}")
    print(f"🔗 Banco: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
    print(f"🔒 Modo debug: {'ON' if debug else 'OFF'}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
