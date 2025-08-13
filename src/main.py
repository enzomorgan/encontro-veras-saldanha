import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

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

# CORS Config
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', '').split(','),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-CSRFToken"],
        "supports_credentials": True
    }
})

# Blueprints
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

# Rotas estáticas
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
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
