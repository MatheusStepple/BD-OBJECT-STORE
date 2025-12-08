"""Modelos da aplicação"""
from flask_login import UserMixin
from psycopg2.extras import RealDictCursor
from database import get_db_connection

class User(UserMixin):
    """Modelo de usuário para Flask-Login"""
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

def load_user(user_id):
    """Carrega usuário do banco de dados"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, username, email FROM usuarios WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data['id'], user_data['username'], user_data['email'])
        return None
    except Exception as e:
        print(f"Erro ao carregar usuário: {e}")
        return None

