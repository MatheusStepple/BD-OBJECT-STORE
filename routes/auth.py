"""Rotas de autenticação"""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Endpoint de login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'sucesso': False, 'erro': 'Usuário e senha são obrigatórios'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, username, email, password_hash FROM usuarios WHERE username = %s', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['email'])
            login_user(user, remember=True)
            return jsonify({
                'sucesso': True,
                'mensagem': 'Login realizado com sucesso!',
                'usuario': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return jsonify({'sucesso': False, 'erro': 'Usuário ou senha incorretos'}), 401
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Endpoint de logout"""
    logout_user()
    return jsonify({'sucesso': True, 'mensagem': 'Logout realizado com sucesso!'})

@auth_bp.route('/api/registro', methods=['POST'])
def registro():
    """Endpoint de registro de novo usuário"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'sucesso': False, 'erro': 'Todos os campos são obrigatórios'}), 400
        
        if len(password) < 6:
            return jsonify({'sucesso': False, 'erro': 'A senha deve ter pelo menos 6 caracteres'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se usuário já existe
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE username = %s OR email = %s', (username, email))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'sucesso': False, 'erro': 'Usuário ou email já cadastrado'}), 400
        
        # Criar novo usuário
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO usuarios (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', (username, email, password_hash))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Usuário cadastrado com sucesso! Faça login para continuar.'
        })
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@auth_bp.route('/api/usuario', methods=['GET'])
@login_required
def get_usuario():
    """Endpoint para obter dados do usuário atual"""
    return jsonify({
        'sucesso': True,
        'usuario': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        }
    })

