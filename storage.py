"""Gerenciamento de armazenamento - Usuários Simplificados"""
from werkzeug.security import generate_password_hash, check_password_hash

# Usuários em memória (super simples)
_users = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'email': 'admin@example.com',
        'password_hash': generate_password_hash('admin123'),
        'selected_bucket': None  # Bucket selecionado pelo usuário
    }
}

def get_user_by_id(user_id):
    """Obtém usuário por ID"""
    user_id = int(user_id)
    for user_data in _users.values():
        if user_data['id'] == user_id:
            return user_data
    return None

def get_user_by_username(username):
    """Obtém usuário por username"""
    return _users.get(username)

def create_user(username, email, password):
    """Cria novo usuário"""
    if username in _users:
        raise ValueError('Usuário já existe')
    
    # Verificar se email já existe
    for user_data in _users.values():
        if user_data['email'] == email:
            raise ValueError('Email já cadastrado')
    
    # Gerar novo ID
    max_id = max([u['id'] for u in _users.values()]) if _users else 0
    new_id = max_id + 1
    
    _users[username] = {
        'id': new_id,
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'selected_bucket': None  # Bucket selecionado pelo usuário
    }
    return _users[username]

def verify_password(username, password):
    """Verifica senha do usuário"""
    user = _users.get(username)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def set_user_bucket(user_id, bucket_name):
    """Define o bucket selecionado para um usuário"""
    user_id = int(user_id)
    for user_data in _users.values():
        if user_data['id'] == user_id:
            user_data['selected_bucket'] = bucket_name
            return True
    return False

def get_user_bucket(user_id):
    """Obtém o bucket selecionado de um usuário"""
    user_id = int(user_id)
    for user_data in _users.values():
        if user_data['id'] == user_id:
            return user_data.get('selected_bucket')
    return None

def init_storage():
    """Inicializa sistema de armazenamento"""
    print('✅ Sistema de armazenamento inicializado!')
    print('   Usuário padrão: admin / admin123')
