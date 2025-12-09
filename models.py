"""Modelos da aplicação"""
from flask_login import UserMixin
from storage import get_user_by_id

class User(UserMixin):
    """Modelo de usuário para Flask-Login"""
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

def load_user(user_id):
    """Carrega usuário do sistema de armazenamento"""
    try:
        user_data = get_user_by_id(user_id)
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['email'])
        return None
    except Exception as e:
        print(f"Erro ao carregar usuário: {e}")
        return None

