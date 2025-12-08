"""Configurações da aplicação"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'upload_system'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

# Configurações da aplicação
SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'mp4', 'mp3'}
PORT = int(os.getenv('PORT', 5000))
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# Categorias disponíveis
CATEGORIES = ['Trabalhos', 'Provas', 'Materiais', 'Aulas', 'Outros']

# Tipos MIME
MIME_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'pdf': 'application/pdf',
    'txt': 'text/plain',
    'zip': 'application/zip',
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4'
}

