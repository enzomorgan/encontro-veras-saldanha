import sys
import subprocess
import pkg_resources
import os
import logging
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

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

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import NotFound, InternalServerError

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuração de logging robusta
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)
app.logger.info("✅ Logging configurado")

# Configurações otimizadas para Render
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
    SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'segredo-render-' + os.urandom(16).hex()),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://'),
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True, 'pool_recycle': 300},
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PROPAGATE_EXCEPTIONS=True,
    PREFERRED_URL_SCHEME='https'  # Força HTTPS na Render
)

# Configuração CORS aprimorada
CORS_ORIGINS = [
    "https://encontro-veras-saldanha.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["X-Total-Count"],
        "supports_credentials": True,
        "max_age": 86400
    },
    r"/assets/*": {
        "origins": ["*"],
        "methods": ["GET"],
        "supports_credentials": False,
        "max_age": 31536000  # 1 ano para assets
    }
})

# Rota dedicada para assets com headers CORS
@app.route('/assets/<path:filename>')
def serve_asset(filename):
    try:
        response = send_from_directory(os.path.join(app.static_folder, 'assets'), filename)
        # Headers importantes para assets
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cross-Origin-Resource-Policy'] = 'cross-origin'
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 ano de cache
        return response
    except NotFound:
        return jsonify({"error": "Asset não encontrado"}), 404

# Middleware para log de requisições
@app.after_request
def after_request(response):
    """Log básico para diagnóstico"""
    logger.info(f"[{request.method}] {request.path} - {response.status_code}")
    return response

# Handlers de erro aprimorados
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 - Página não encontrada: {request.path}")
    return jsonify({
        "error": "not_found",
        "message": "Endpoint não existe"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 - Erro interno: {str(e)}")
    return jsonify({
        "error": "internal_server_error",
        "message": "Erro no processamento da requisição"
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handler global para todos os erros"""
    if isinstance(e, HTTPException):
        return e
    
    logger.error(f"⚠️ ERRO NÃO TRATADO: {str(e)}", exc_info=True)
    return jsonify({
        "error": "server_error",
        "message": "Ocorreu um erro inesperado"
    }), 500

# Inicialização do banco de dados
from src.models.user import db
db.init_app(app)

# Blueprints com tratamento de erro
blueprints = [
    ('src.routes.user', 'user_bp', '/api'),
    ('src.routes.auth', 'auth_bp', '/api/auth'),
    ('src.routes.pedidos', 'pedidos_bp', '/api/pedidos'),
    ('src.routes.pagamentos', 'pagamentos_bp', '/api/pagamentos'),
    ('src.routes.reservas', 'reservas_bp', '/api/reservas'),
    ('src.routes.status', 'status_bp', '/api/status'),
    ('src.routes.admin_auth', 'admin_auth_bp', '/api/admin'),
    ('src.routes.admin_dashboard', 'admin_dashboard_bp', '/api/admin/dashboard')
]

for module, bp_name, url_prefix in blueprints:
    try:
        module = __import__(module, fromlist=[bp_name])
        blueprint = getattr(module, bp_name)
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        logger.info(f"✅ Blueprint registrado: {bp_name}")
    except Exception as e:
        logger.error(f"❌ Falha ao registrar {bp_name}: {str(e)}")
        if bp_name == 'status_bp':  # Critical for health checks
            @app.route('/api/status')
            def fallback_status():
                return jsonify({"status": "fallback_ok"}), 200

# Rotas estáticas para o frontend
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except NotFound:
        return send_from_directory(app.static_folder, 'index.html')

# Health check redundante
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "online",
        "database": "postgresql" if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else "sqlite",
        "environment": os.getenv('FLASK_ENV', 'production'),
        "assets_config": "optimized"  # Indica que as novas configurações estão ativas
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))  # Porta padrão da Render
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("\n" + "="*50)
    logger.info(f"🚀 Iniciando servidor na porta {port}")
    logger.info(f"🔗 Banco: {'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
    logger.info(f"🌐 CORS habilitado para: {CORS_ORIGINS}")
    logger.info(f"🔒 Modo debug: {'ON' if debug else 'OFF'}")
    logger.info("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
