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
    """Factory function para criar e configurar a aplicação Flask"""
    load_dotenv()
    
    # Inicialização do app Flask
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
        static_url_path='/static'
    )
    
    # Handler para timeout
    def handle_timeout(signum, frame):
        app.logger.error("Tempo limite de inicialização excedido")
        sys.exit(1)

    # Configuração de ambiente
    if os.getenv('ENV') == 'production':
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(30)

    # Configurações de segurança
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-me'),
        SESSION_COOKIE_SECURE=os.getenv('ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        JSONIFY_PRETTYPRINT_REGULAR=False,  # Desativado para melhor performance
        PREFERRED_URL_SCHEME='https',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB
    )

    # Configuração de logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Formato aprimorado para logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler para arquivo
    file_handler = logging.FileHandler('client_errors.log')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # Configuração CORS melhorada
    allowed_origins = [
        "https://encontro-veras-saldanha.onrender.com",
        "http://localhost:3000"
    ]
    
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 86400
        }
    })

    # Helper para conexão com o banco
    def get_db_connection():
        return psycopg2.connect(
            os.getenv('DATABASE_URL'),
            connect_timeout=5
        )

    # Rotas da API
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Endpoint de verificação de saúde"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
            
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'database': 'connected'
            })

        except OperationalError as e:
            app.logger.error(f'Falha na conexão com o banco: {str(e)}')
            return jsonify({'status': 'degraded', 'error': 'Database connection failed'}), 503
        except Exception as e:
            app.logger.error(f'Health check failed: {str(e)}')
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Endpoint de autenticação"""
        try:
            data = request.get_json()
            
            if not data or 'email' not in data or 'password' not in data:
                return jsonify({'error': 'Credenciais inválidas'}), 400
                
            # TODO: Implementar lógica real de autenticação
            return jsonify({
                'token': 'jwt-token-gerado',
                'user': {'email': data.get('email')}
            })
            
        except Exception as e:
            app.logger.error(f'Erro no login: {str(e)}')
            return jsonify({'error': 'Erro interno no servidor'}), 500

    # Rotas para arquivos estáticos
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_static(path):
        """Serve arquivos estáticos e lida com roteamento SPA"""
        if path.startswith('api/'):
            return jsonify(error='Endpoint não encontrado'), 404
            
        static_file = os.path.join(app.static_folder, path)
        
        if path and os.path.exists(static_file) and not os.path.isdir(static_file):
            return send_from_directory(app.static_folder, path)
            
        return send_from_directory(app.static_folder, 'index.html')

    # Tratamento de erros
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error='Recurso não encontrado'), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Erro interno: {str(e)}')
        return jsonify(error='Erro interno do servidor'), 500

    # Desativa timeout após inicialização
    if os.getenv('ENV') == 'production':
        signal.alarm(0)
    
    return app

# Cria a aplicação
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
