"""Funções utilitárias"""
import os
import re
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, MIME_TYPES, UPLOAD_FOLDER

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calcular_hash(file_path):
    """Calcula hash MD5 de um arquivo"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def sanitize_filename(filename):
    """Sanitiza nome de arquivo para Windows"""
    # Remover caracteres inválidos
    nome_sanitizado = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    nome_sanitizado = nome_sanitizado.strip('. ')
    
    # Se o nome ficou vazio, criar um nome padrão preservando extensão
    if not nome_sanitizado:
        extensao = ''
        if '.' in filename:
            extensao = '.' + filename.rsplit('.', 1)[1]
        nome_sanitizado = f"arquivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extensao}"
    
    # Limitar tamanho do nome (Windows tem limite de 255 caracteres)
    if len(nome_sanitizado) > 200:
        extensao = ''
        if '.' in nome_sanitizado:
            extensao = '.' + nome_sanitizado.rsplit('.', 1)[1]
        nome_sanitizado = nome_sanitizado[:200-len(extensao)] + extensao
    
    return nome_sanitizado

def get_mime_type(filename, content_type=None):
    """Obtém tipo MIME do arquivo"""
    if content_type:
        return content_type
    
    # Tentar detectar pelo nome do arquivo
    extensao = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return MIME_TYPES.get(extensao, 'application/octet-stream')

def generate_unique_filename(user_id, original_filename):
    """Gera nome único para arquivo"""
    nome_seguro = secure_filename(original_filename)
    
    # Se secure_filename retornar vazio, usar nome original sanitizado manualmente
    if not nome_seguro:
        nome_seguro = re.sub(r'[^a-zA-Z0-9._-]', '_', original_filename)
        if not nome_seguro:
            nome_seguro = f"arquivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Adicionar timestamp e user_id para evitar conflitos
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return f"{user_id}_{timestamp}_{nome_seguro}"

def ensure_upload_folder():
    """Garante que a pasta de uploads existe"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

