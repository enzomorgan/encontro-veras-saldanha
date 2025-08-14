import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2 import OperationalError



# Configuração inicial
load_dotenv()
app = Flask(__name__, static_folder='static')

# Configurações de Segurança
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-me'),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    JSONIFY_PRETTYPRINT_REGULAR=True
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

#Rotas da API
@app.route('/api/health', methods=['GET'])
def health_check():
    db_status = 'disconnected'
    try:
        # Tenta estabelecer conexão e executar uma query simples
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        db_status = 'connected'
    except OperationalError as e:
        app.logger.error(f'Erro na conexão com o banco: {str(e)}')
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'database': db_status,
        'details': {
            'db_server': os.getenv('DATABASE_URL').split('@')[1].split('/')[0] if os.getenv('DATABASE_URL') else 'unknown',
            'db_name': os.getenv('DATABASE_URL').split('/')[-1] if os.getenv('DATABASE_URL') else 'unknown'
        }
    }), 200 if db_status == 'connected' else 503

# Rotas de Autenticação
@app.route('/api/auth/csrf-token', methods=['GET'])
def get_csrf_token():
    return jsonify({
        'token': 'gerar-token-seguro-aqui'  # Implementar geração real
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    # Implementar lógica real de login
    return jsonify({
        'token': 'jwt-token-gerado',
        'user': {'email': data.get('email')}
    })

@app.route('/api/auth/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()
    
    # Validação básica
    if data.get('password') != data.get('confirmPassword'):
        return jsonify({'error': 'Senhas não coincidem'}), 400
        
    # Implementar criação de usuário
    return jsonify({
        'success': True,
        'message': 'Usuário criado com sucesso'
    }), 201

# Rota de Log de Erros
@app.route('/api/log-client-error', methods=['POST'])
def log_client_error():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415
            
        data = request.get_json()
        
        app.logger.error(f"""
        ERRO NO CLIENTE:
        Mensagem: {data.get('error')}
        URL: {data.get('url')}
        Timestamp: {data.get('timestamp')}
        Stack: {data.get('stack')}
        """)
        
        return jsonify({
            'status': 'error_logged',
            'received_data': data
        }), 200
        
    except Exception as e:
        app.logger.error(f'Erro ao processar log do cliente: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

# Rotas Estáticas
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    response = send_from_directory(
        os.path.join(app.static_folder, 'assets'),
        filename
    )
    # Force MIME type para JS e CSS
    if filename.endswith('.js'):
        response.headers.set('Content-Type', 'application/javascript')
    elif filename.endswith('.css'):
        response.headers.set('Content-Type', 'text/css')
    return response

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('api/'):
        return jsonify(error='Endpoint não encontrado'), 404
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return app.send_static_file('index.html')


# Tratamento de erros
@app.errorhandler(404)
def not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error='Erro interno do servidor'), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
