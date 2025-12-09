"""Rotas de autenticação - Simplificado"""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from storage import verify_password, create_user
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Endpoint de login simplificado"""
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        
        if not username or not password:
            return jsonify({'sucesso': False, 'erro': 'Usuário e senha são obrigatórios'}), 400
        
        user_data = verify_password(username, password)
        
        if user_data:
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
        print(f"Erro no login: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro ao processar login'}), 500

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Endpoint de logout"""
    logout_user()
    return jsonify({'sucesso': True, 'mensagem': 'Logout realizado com sucesso!'})

@auth_bp.route('/api/registro', methods=['POST'])
def registro():
    """Endpoint de registro"""
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = (data.get('password') or '').strip()
        
        if not username or not email or not password:
            return jsonify({'sucesso': False, 'erro': 'Todos os campos são obrigatórios'}), 400
        
        if len(password) < 6:
            return jsonify({'sucesso': False, 'erro': 'A senha deve ter pelo menos 6 caracteres'}), 400
        
        try:
            user_data = create_user(username, email, password)
            return jsonify({
                'sucesso': True,
                'mensagem': 'Usuário cadastrado com sucesso! Faça login para continuar.'
            })
        except ValueError as e:
            return jsonify({'sucesso': False, 'erro': str(e)}), 400
    except Exception as e:
        print(f"Erro no registro: {e}")
        return jsonify({'sucesso': False, 'erro': 'Erro ao processar registro'}), 500

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
