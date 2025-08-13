import os
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static')

# Configurações do Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret-temp')

db = SQLAlchemy(app)
CORS(app)

# Modelo de Usuário (simplificado)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

# Rotas
@app.route('/api/auth/cadastro', methods=['POST'])
def cadastro():
    try:
        data = request.json
        novo_usuario = User(
            nome=data.get('nome'),
            email=data.get('email'),
            senha=data.get('senha')  # Na prática, você deve hashear a senha
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
