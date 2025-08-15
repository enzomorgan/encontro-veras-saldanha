import os
import signal
import sys
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2 import OperationalError

def create_app():
    load_dotenv()
    app = Flask(
        __name__,
        static_folder=os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../static')
        )
    )
    
    # Configuração de timeout
    def handle_timeout(signum, frame):
        sys.exit(1)
    
    if os.getenv('ENV') == 'production':
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(30)

    # Configurações de Segurança
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-me'),
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        JSONIFY_PRETTYPRINT_REGULAR=True,
        PREFERRED_URL_SCHEME='https'
    )

    # Configuração de logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler('client_errors.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    app.logger.addHandler(handler)

    # CORS Config
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://encontro-veras-saldanha.onrender.com"] + os.getenv('ALLOWED_ORIGINS', '').split(','),
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-CSRFToken"],
            "supports_credentials": True
        }
    })

    # Rotas da API
    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            with psycopg2.connect(
                os.getenv(
                    'DATABASE_URL',
                    "postgresql://app_user:AUQDfocoF0Lbhh0Fb0j7KcTsTVnXzso0@dpg-d2b7pe95pdvs73cgp4bg-a/encontro_prod"
                ),
                connect_timeout=5
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')

            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'database': 'connected'
            })

        except Exception as e:
            app.logger.error(f'Health check failed: {str(e)}')
            return jsonify({'status': 'degraded', 'error': str(e)}), 503

    # Rotas de Autenticação
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            if not data or 'email' not in data or 'password' not in data:
                return jsonify({'error': 'Dados inválidos'}), 400
                
            return jsonify({
                'token': 'jwt-token-gerado',
                'user': {'email': data.get('email')}
            })
            
        except Exception as e:
            app.logger.error(f'Login error: {str(e)}')
            return jsonify({'error': 'Erro no servidor'}), 500

    # Rotas Estáticas
    @app.route('/')
    def home():
        return send_from_directory(app.static_folder, 'index.html')
        
    @app.route('/<path:path>')
    def serve_static(path):
        if path.startswith('api/'):
            return jsonify(error='Endpoint não encontrado'), 404

        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path) and not os.path.isdir(file_path) and path != '':
            return send_from_directory(app.static_folder, path)

        # Para SPA funcionar em rotas como /dashboard, /login, etc
        return send_from_directory(app.static_folder, 'index.html')

    # Tratamento de Erros
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error='Recurso não encontrado'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(error='Erro interno do servidor'), 500

    # Desativa timeout após inicialização
    if os.getenv('ENV') == 'production':
        signal.alarm(0)
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
