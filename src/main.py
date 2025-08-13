import sys
import subprocess
import pkg_resources
import os
import logging
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

# Carrega variáveis de ambiente primeiro
load_dotenv()

# Configuração antecipada do logging básico para ver erros de inicialização
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        faltantes = []
        for pacote in DEPENDENCIAS_NECESSARIAS:
            try:
                pkg_resources.get_distribution(pacote)
            except pkg_resources.DistributionNotFound:
                faltantes.append(pacote)
        
        if faltantes:
            logger.info(f"Instalando dependências faltantes: {', '.join(faltantes)}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *faltantes])
    except Exception as e:
        logger.error(f"Falha na instalação de dependências: {str(e)}")
        raise

verificar_dependencias()

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import NotFound, InternalServerError

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuração de logging robusta
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'api.log',
            'formatter': 'default',
        },
    },
    'root': {
        'level': logging.INFO,
        'handlers': ['console', 'file'],
    },
})

# Configurações otimizadas
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SECRET_KEY=os.getenv('JWT_SECRET_KEY', os.urandom(24).hex()),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///local.db').replace('postgres://', 'postgresql://'),
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30
    },
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PROPAGATE_EXCEPTIONS=True,
    PREFERRED_URL_SCHEME='https'
)

# Configuração CORS aprimorada
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') or [
    "https://encontro-veras-saldanha.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 86400
    },
    r"/static/*": {
        "origins": ["*"],
        "methods": ["GET"]
    }
})

# Inicialização do banco de dados
from src.models.user import db
db.init_app(app)

# Criar tabelas se não existirem (apenas para desenvolvimento)
with app.app_context():
    try:
        db.create_all()
        logger.info("Tabelas do banco de dados verificadas/criadas")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")

# Importação segura de blueprints
BLUEPRINTS = [
    ('src.routes.auth', 'auth_bp', '/api/auth'),
    ('src.routes.user', 'user_bp', '/api/users'),
    ('src.routes.status', 'status_bp', '/api/status')
]

for module_path, bp_name, url_prefix in BLUEPRINTS:
    try:
        module = __import__(module_path, fromlist=[bp_name])
        blueprint = getattr(module, bp_name)
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        logger.info(f"Blueprint registrado: {url_prefix}")
    except Exception as e:
        logger.error(f"Falha ao registrar {bp_name}: {str(e)}")
        if bp_name == 'status_bp':  # Fallback crítico
            @app.route('/api/status')
            def status_fallback():
                return jsonify({"status": "ok"}), 200

# Handlers de erro
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not_found", "message": "Recurso não encontrado"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Erro interno: {str(e)}", exc_info=True)
    return jsonify({"error": "internal_error", "message": "Erro no servidor"}), 500

# Middleware para log de requisições
@app.after_request
def log_request(response):
    logger.info(f"{request.method} {request.path} - {response.status_code}")
    return response

# Rotas básicas
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    try:
        return send_from_directory(app.static_folder, path)
    except NotFound:
        return send_from_directory(app.static_folder, 'index.html')

# Health check
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "database": "connected" if db.session.query('1').from_statement(db.text('SELECT 1')).first() else "disconnected",
        "environment": os.getenv('FLASK_ENV', 'production')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Iniciando servidor na porta {port}")
    logger.info(f"Modo debug: {'ON' if debug else 'OFF'}")
    logger.info(f"Banco de dados: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info(f"Origins CORS: {CORS_ORIGINS}")
    logger.info(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
