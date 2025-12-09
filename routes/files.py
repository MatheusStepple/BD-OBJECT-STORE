"""Rotas de gerenciamento de arquivos - MinIO"""
from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from urllib.parse import quote
from minio_client import get_minio_client
from config import CATEGORIES, MINIO_CONFIG
from storage import get_user_bucket
from utils import (
    allowed_file, sanitize_filename, 
    get_mime_type, generate_unique_filename
)
import json
import hashlib
from datetime import datetime, timedelta
import sys
import logging

# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

files_bp = Blueprint('files', __name__)

def log(msg):
    """Função para garantir que logs apareçam no docker-compose logs"""
    logger.info(msg)
    sys.stdout.flush()
    sys.stderr.flush()

def normalize_file_id(file_id):
    """Normaliza file_id - converte formato sem underscores para formato com underscores"""
    file_id_str = str(file_id).strip()
    
    # Se já tem underscores, retorna como está
    if '_' in file_id_str:
        log(f"[NORMALIZE] Já tem underscores: '{file_id_str}'")
        return file_id_str
    
    # Se não tem underscores, tenta adicionar
    # Formato: 2025120901183519000 -> 20251209_011835_19000
    if len(file_id_str) >= 14:
        date_part = file_id_str[:8]   # YYYYMMDD
        time_part = file_id_str[8:14]  # HHMMSS
        micro_part = file_id_str[14:]  # microseconds (pode ter qualquer tamanho)
        
        normalized = f"{date_part}_{time_part}_{micro_part}"
        log(f"[NORMALIZE] '{file_id_str}' -> '{normalized}'")
        return normalized
    
    log(f"[NORMALIZE] Não foi possível normalizar: '{file_id_str}'")
    return file_id_str

def find_metadata_by_prefix(user_id, prefix_search):
    """Busca metadados por prefixo (data + hora)"""
    log(f"[FIND] Buscando por prefixo: '{prefix_search}_*'")
    minio = get_user_minio_client()
    all_metadata = minio.list_files(prefix=f"metadata/{user_id}/")
    
    for meta in all_metadata:
        parts = meta['key'].split('/')
        if len(parts) >= 3:
            found_id = parts[2].replace('.json', '')
            if found_id.startswith(prefix_search + '_'):
                log(f"[FIND] ✅ ENCONTRADO: '{found_id}'")
                return meta['key'], found_id
    
    log(f"[FIND] ❌ Nenhum arquivo encontrado com prefixo '{prefix_search}_*'")
    return None, None

def get_metadata_key(user_id, file_id):
    """Gera chave para metadados do arquivo"""
    normalized_id = normalize_file_id(file_id)
    key = f"metadata/{user_id}/{normalized_id}.json"
    return key

def get_file_key(user_id, file_id):
    """Gera chave para arquivo no MinIO"""
    normalized_id = normalize_file_id(file_id)
    key = f"files/{user_id}/{normalized_id}"
    return key

def get_user_minio_client():
    """Obtém cliente MinIO com bucket do usuário"""
    bucket_name = get_user_bucket(current_user.id)
    if not bucket_name:
        # Não usar bucket padrão - usuário deve selecionar um bucket
        raise ValueError('Nenhum bucket selecionado. Por favor, selecione um bucket primeiro.')
    
    minio = get_minio_client(bucket_name)
    
    # Verificar se o bucket existe (não criar automaticamente)
    if not minio.bucket_exists(bucket_name):
        raise ValueError(f'Bucket "{bucket_name}" não encontrado. Por favor, selecione outro bucket.')
    
    return minio

def list_user_files(user_id):
    """Lista todos os arquivos do usuário"""
    try:
        log(f"[LIST] Listando arquivos para user_id={user_id}")
        minio = get_user_minio_client()
        metadata_files = minio.list_files(prefix=f"metadata/{user_id}/")
        log(f"[LIST] Encontrados {len(metadata_files)} metadados")
        
        arquivos = []
        for meta_file in metadata_files:
            if meta_file['key'].endswith('.json'):
                try:
                    file_data, _ = minio.download_file(meta_file['key'])
                    metadata = json.loads(file_data.decode('utf-8'))
                    arquivos.append(metadata)
                except Exception as e:
                    log(f"[LIST] ERRO ao carregar {meta_file['key']}: {e}")
                    continue
        
        return arquivos
    except Exception as e:
        log(f"[LIST] ERRO: {e}")
        return []

@files_bp.route('/api/arquivos', methods=['GET'])
@login_required
def listar_arquivos():
    """Lista arquivos do usuário com filtros opcionais"""
    try:
        log("=" * 80)
        log("[LISTAR] INICIANDO")
        log(f"[LISTAR] User ID: {current_user.id}")
        
        busca = request.args.get('busca', '').strip()
        categoria = request.args.get('categoria', '').strip()
        
        arquivos = list_user_files(current_user.id)
        
        # Aplicar filtros
        if categoria and categoria in CATEGORIES:
            arquivos = [a for a in arquivos if a.get('categoria') == categoria]
        
        if busca:
            busca_lower = busca.lower()
            arquivos = [a for a in arquivos if busca_lower in a.get('nome_original', '').lower()]
        
        arquivos.sort(key=lambda x: x.get('data_upload', ''), reverse=True)
        
        log(f"[LISTAR] Retornando {len(arquivos)} arquivos")
        log("=" * 80)
        return jsonify({'sucesso': True, 'arquivos': arquivos})
    except ValueError as e:
        # Erro de bucket não selecionado - retornar sucesso mas com mensagem
        log(f"[LISTAR] ⚠️ {e}")
        return jsonify({
            'sucesso': True, 
            'arquivos': [],
            'mensagem': str(e)
        })
    except Exception as e:
        log(f"[LISTAR] ERRO: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@files_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_arquivo():
    """Endpoint para upload de arquivo"""
    try:
        log("=" * 80)
        log("[UPLOAD] ========== INICIANDO UPLOAD ==========")
        log(f"[UPLOAD] User ID: {current_user.id}")
        
        # Verificar se há bucket selecionado
        bucket_name = get_user_bucket(current_user.id)
        if not bucket_name:
            return jsonify({
                'sucesso': False, 
                'erro': 'Nenhum bucket selecionado. Por favor, selecione um bucket primeiro.'
            }), 400
        
        if 'arquivo' not in request.files:
            return jsonify({'sucesso': False, 'erro': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        log(f"[UPLOAD] Arquivo: {arquivo.filename}")
        
        if arquivo.filename == '' or not arquivo.filename:
            return jsonify({'sucesso': False, 'erro': 'Nome de arquivo vazio'}), 400
        
        if not allowed_file(arquivo.filename):
            return jsonify({'sucesso': False, 'erro': 'Tipo de arquivo não permitido'}), 400
        
        # Ler arquivo
        file_data = arquivo.read()
        log(f"[UPLOAD] Tamanho: {len(file_data)} bytes")
        
        if len(file_data) == 0:
            return jsonify({'sucesso': False, 'erro': 'Arquivo vazio não permitido'}), 400
        
        # Calcular hash
        hash_md5 = hashlib.md5(file_data).hexdigest()
        
        # Informações
        nome_original = arquivo.filename
        tamanho = len(file_data)
        tipo_mime = get_mime_type(nome_original, arquivo.content_type)
        categoria = request.form.get('categoria', 'Outros')
        if categoria not in CATEGORIES:
            categoria = 'Outros'
        
        # Gerar ID
        timestamp = datetime.now()
        file_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{timestamp.microsecond}"
        log(f"[UPLOAD] File ID gerado: {file_id}")
        
        # Chaves
        file_key = get_file_key(current_user.id, file_id)
        metadata_key = get_metadata_key(current_user.id, file_id)
        
        # Upload para MinIO
        minio = get_user_minio_client()
        
        log(f"[UPLOAD] Fazendo upload do arquivo...")
        minio.upload_file(
            file_data,
            file_key,
            metadata={
                'nome-original': nome_original,
                'user-id': str(current_user.id),
                'categoria': categoria
            },
            content_type=tipo_mime
        )
        log(f"[UPLOAD] ✅ Arquivo enviado: {file_key}")
        
        # Verificar
        if not minio.file_exists(file_key):
            log(f"[UPLOAD] ❌ ERRO: Arquivo não encontrado após upload!")
        
        # Criar metadados
        metadata = {
            'id': file_id,
            'user_id': current_user.id,
            'nome_original': nome_original,
            'file_key': file_key,
            'tamanho': tamanho,
            'tipo': tipo_mime,
            'categoria': categoria,
            'data_upload': timestamp.isoformat(),
            'hash_md5': hash_md5
        }
        
        # Salvar metadados
        metadata_json = json.dumps(metadata, ensure_ascii=False).encode('utf-8')
        minio.upload_file(
            metadata_json,
            metadata_key,
            content_type='application/json'
        )
        log(f"[UPLOAD] ✅ Metadados salvos: {metadata_key}")
        
        # Verificar metadados
        if not minio.file_exists(metadata_key):
            log(f"[UPLOAD] ❌ ERRO: Metadados não encontrados após upload!")
        
        log("=" * 80)
        log(f"[UPLOAD] ✅✅✅ UPLOAD CONCLUÍDO: {file_id}")
        log("=" * 80)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Arquivo enviado com sucesso!',
            'arquivo': {
                'id': file_id,
                'nome_original': nome_original,
                'tamanho': tamanho,
                'hash_md5': hash_md5
            }
        })
    except ValueError as e:
        # Erro de bucket não selecionado
        log(f"[UPLOAD] ❌ {e}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 400
    except Exception as e:
        log("=" * 80)
        log(f"[UPLOAD] ❌❌❌ ERRO NO UPLOAD ❌❌❌")
        log(f"[UPLOAD] Erro: {str(e)}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao processar upload: {str(e)}'}), 500

@files_bp.route('/api/arquivos/<file_id>', methods=['DELETE'])
@login_required
def deletar_arquivo(file_id):
    """Endpoint para deletar arquivo"""
    try:
        log("=" * 80)
        log("[DELETE] ========== INICIANDO DELETE ==========")
        log(f"[DELETE] File ID recebido: '{file_id}'")
        log(f"[DELETE] User ID: {current_user.id}")
        
        minio = get_user_minio_client()
        
        # Normalizar file_id
        normalized_file_id = normalize_file_id(file_id)
        log(f"[DELETE] File ID normalizado: '{normalized_file_id}'")
        
        # Tentar buscar metadados exatos primeiro
        metadata_key = get_metadata_key(current_user.id, normalized_file_id)
        log(f"[DELETE] Buscando metadados: {metadata_key}")
        
        # Se não encontrar, buscar por prefixo
        if not minio.file_exists(metadata_key):
            log(f"[DELETE] ❌ Metadados não encontrados exatamente!")
            # Extrair prefixo (data + hora)
            prefix_parts = normalized_file_id.split('_')
            if len(prefix_parts) >= 2:
                prefix_search = '_'.join(prefix_parts[:2])  # YYYYMMDD_HHMMSS
                log(f"[DELETE] Tentando busca por prefixo: {prefix_search}_*")
                
                found_key, found_id = find_metadata_by_prefix(current_user.id, prefix_search)
                if found_key:
                    log(f"[DELETE] ✅ ENCONTRADO POR PREFIXO: {found_id}")
                    metadata_key = found_key
                    normalized_file_id = found_id
                else:
                    log(f"[DELETE] ❌ Nenhum arquivo encontrado!")
                    return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
            else:
                return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        log(f"[DELETE] ✅ Metadados encontrados!")
        
        # Carregar metadados
        file_data, _ = minio.download_file(metadata_key)
        metadata = json.loads(file_data.decode('utf-8'))
        log(f"[DELETE] Metadados: file_key={metadata.get('file_key')}")
        
        # Verificar permissão
        if metadata.get('user_id') != current_user.id:
            log(f"[DELETE] ❌ Arquivo não pertence ao usuário!")
            return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        # Deletar arquivo
        file_key = metadata.get('file_key')
        if file_key:
            log(f"[DELETE] Deletando arquivo: {file_key}")
            try:
                if minio.file_exists(file_key):
                    minio.delete_file(file_key)
                    log(f"[DELETE] ✅ Arquivo deletado")
            except Exception as e:
                log(f"[DELETE] ⚠️ Erro ao deletar arquivo: {e}")
        
        # Deletar metadados
        minio.delete_file(metadata_key)
        log(f"[DELETE] ✅ Metadados deletados")
        
        log("=" * 80)
        log(f"[DELETE] ✅✅✅ DELETE CONCLUÍDO")
        log("=" * 80)
        
        return jsonify({'sucesso': True, 'mensagem': 'Arquivo deletado com sucesso!'})
    except FileNotFoundError:
        return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado'}), 404
    except ValueError as e:
        # Erro de bucket não selecionado
        log(f"[DELETE] ❌ {e}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 400
    except Exception as e:
        log("=" * 80)
        log(f"[DELETE] ❌❌❌ ERRO NO DELETE ❌❌❌")
        log(f"[DELETE] Erro: {str(e)}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@files_bp.route('/api/arquivos/<file_id>/download', methods=['GET'])
@login_required
def download_arquivo(file_id):
    """Endpoint para download de arquivo"""
    try:
        log("=" * 80)
        log("[DOWNLOAD] ========== INICIANDO DOWNLOAD ==========")
        log(f"[DOWNLOAD] File ID recebido: '{file_id}'")
        log(f"[DOWNLOAD] User ID: {current_user.id}")
        
        minio = get_user_minio_client()
        
        # Normalizar file_id
        normalized_file_id = normalize_file_id(file_id)
        log(f"[DOWNLOAD] File ID normalizado: '{normalized_file_id}'")
        
        # Tentar buscar metadados exatos primeiro
        metadata_key = get_metadata_key(current_user.id, normalized_file_id)
        log(f"[DOWNLOAD] Buscando metadados: {metadata_key}")
        
        # Se não encontrar, buscar por prefixo
        if not minio.file_exists(metadata_key):
            log(f"[DOWNLOAD] ❌ Metadados não encontrados exatamente!")
            # Extrair prefixo (data + hora)
            prefix_parts = normalized_file_id.split('_')
            if len(prefix_parts) >= 2:
                prefix_search = '_'.join(prefix_parts[:2])  # YYYYMMDD_HHMMSS
                log(f"[DOWNLOAD] Tentando busca por prefixo: {prefix_search}_*")
                
                found_key, found_id = find_metadata_by_prefix(current_user.id, prefix_search)
                if found_key:
                    log(f"[DOWNLOAD] ✅ ENCONTRADO POR PREFIXO: {found_id}")
                    metadata_key = found_key
                    normalized_file_id = found_id
                else:
                    log(f"[DOWNLOAD] ❌ Nenhum arquivo encontrado!")
                    return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
            else:
                return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        log(f"[DOWNLOAD] ✅ Metadados encontrados!")
        
        # Carregar metadados
        file_data, _ = minio.download_file(metadata_key)
        metadata = json.loads(file_data.decode('utf-8'))
        log(f"[DOWNLOAD] Metadados: file_key={metadata.get('file_key')}, nome={metadata.get('nome_original')}")
        
        # Verificar permissão
        if metadata.get('user_id') != current_user.id:
            log(f"[DOWNLOAD] ❌ Arquivo não pertence ao usuário!")
            return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        # Baixar arquivo
        file_key = metadata.get('file_key')
        if not file_key:
            log(f"[DOWNLOAD] ❌ Chave do arquivo não encontrada!")
            return jsonify({'sucesso': False, 'erro': 'Chave do arquivo não encontrada'}), 404
        
        log(f"[DOWNLOAD] Buscando arquivo: {file_key}")
        
        if not minio.file_exists(file_key):
            log(f"[DOWNLOAD] ❌ Arquivo não encontrado no MinIO!")
            return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado no armazenamento'}), 404
        
        log(f"[DOWNLOAD] ✅ Arquivo encontrado! Fazendo download...")
        file_content, content_type = minio.download_file(file_key)
        log(f"[DOWNLOAD] ✅ Arquivo baixado: {len(file_content)} bytes")
        
        nome_original = metadata.get('nome_original', 'arquivo')
        nome_sanitizado = sanitize_filename(nome_original)
        nome_encoded = quote(nome_sanitizado.encode('utf-8'))
        
        response = Response(
            file_content,
            mimetype=content_type or metadata.get('tipo', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{nome_sanitizado}"; filename*=UTF-8\'\'{nome_encoded}',
                'Content-Length': str(len(file_content)),
                'Content-Type': content_type or metadata.get('tipo', 'application/octet-stream'),
                'X-Content-Type-Options': 'nosniff'
            }
        )
        
        log("=" * 80)
        log(f"[DOWNLOAD] ✅✅✅ DOWNLOAD CONCLUÍDO: {nome_original}")
        log("=" * 80)
        return response
    except FileNotFoundError as e:
        log("=" * 80)
        log(f"[DOWNLOAD] ❌❌❌ FileNotFoundError ❌❌❌")
        log(f"[DOWNLOAD] Erro: {e}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado'}), 404
    except ValueError as e:
        # Erro de bucket não selecionado
        log(f"[DOWNLOAD] ❌ {e}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 400
    except Exception as e:
        log("=" * 80)
        log(f"[DOWNLOAD] ❌❌❌ ERRO NO DOWNLOAD ❌❌❌")
        log(f"[DOWNLOAD] Erro: {str(e)}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao processar download: {str(e)}'}), 500

@files_bp.route('/api/arquivos/<file_id>/share', methods=['POST'])
@login_required
def compartilhar_arquivo(file_id):
    """Gera URL pré-assinada para compartilhamento de arquivo"""
    try:
        log("=" * 80)
        log("[SHARE] ========== GERANDO LINK DE COMPARTILHAMENTO ==========")
        log(f"[SHARE] File ID recebido: '{file_id}'")
        log(f"[SHARE] User ID: {current_user.id}")
        
        data = request.get_json() or {}
        expiration = data.get('expiration', 3600)  # Padrão: 1 hora
        
        # Validar expiração (entre 60 segundos e 7 dias)
        if expiration < 60:
            expiration = 60
        elif expiration > 604800:  # 7 dias
            expiration = 604800
        
        minio = get_user_minio_client()
        
        # Normalizar file_id
        normalized_file_id = normalize_file_id(file_id)
        log(f"[SHARE] File ID normalizado: '{normalized_file_id}'")
        
        # Buscar metadados
        metadata_key = get_metadata_key(current_user.id, normalized_file_id)
        log(f"[SHARE] Buscando metadados: {metadata_key}")
        
        # Se não encontrar, buscar por prefixo
        if not minio.file_exists(metadata_key):
            log(f"[SHARE] ❌ Metadados não encontrados exatamente!")
            prefix_parts = normalized_file_id.split('_')
            if len(prefix_parts) >= 2:
                prefix_search = '_'.join(prefix_parts[:2])
                log(f"[SHARE] Tentando busca por prefixo: {prefix_search}_*")
                
                found_key, found_id = find_metadata_by_prefix(current_user.id, prefix_search)
                if found_key:
                    log(f"[SHARE] ✅ ENCONTRADO POR PREFIXO: {found_id}")
                    metadata_key = found_key
                    normalized_file_id = found_id
                else:
                    log(f"[SHARE] ❌ Nenhum arquivo encontrado!")
                    return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
            else:
                return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        log(f"[SHARE] ✅ Metadados encontrados!")
        
        # Carregar metadados
        file_data, _ = minio.download_file(metadata_key)
        metadata = json.loads(file_data.decode('utf-8'))
        log(f"[SHARE] Metadados: file_key={metadata.get('file_key')}, nome={metadata.get('nome_original')}")
        
        # Verificar permissão
        if metadata.get('user_id') != current_user.id:
            log(f"[SHARE] ❌ Arquivo não pertence ao usuário!")
            return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        # Gerar URL pré-assinada
        file_key = metadata.get('file_key')
        if not file_key:
            log(f"[SHARE] ❌ Chave do arquivo não encontrada!")
            return jsonify({'sucesso': False, 'erro': 'Chave do arquivo não encontrada'}), 404
        
        log(f"[SHARE] Gerando URL pré-assinada para: {file_key}")
        presigned_url = minio.generate_presigned_url(file_key, expiration=expiration)
        log(f"[SHARE] ✅ URL pré-assinada gerada")
        
        # Calcular data de expiração
        expires_at = datetime.now() + timedelta(seconds=expiration)
        
        log("=" * 80)
        log(f"[SHARE] ✅✅✅ LINK DE COMPARTILHAMENTO GERADO")
        log("=" * 80)
        
        return jsonify({
            'sucesso': True,
            'url': presigned_url,
            'expires_at': expires_at.isoformat(),
            'expiration_seconds': expiration,
            'arquivo': {
                'id': metadata.get('id'),
                'nome_original': metadata.get('nome_original'),
                'tamanho': metadata.get('tamanho')
            }
        })
    except FileNotFoundError as e:
        log("=" * 80)
        log(f"[SHARE] ❌❌❌ FileNotFoundError ❌❌❌")
        log(f"[SHARE] Erro: {e}")
        log("=" * 80)
        return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado'}), 404
    except ValueError as e:
        # Erro de bucket não selecionado
        log(f"[SHARE] ❌ {e}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 400
    except Exception as e:
        log("=" * 80)
        log(f"[SHARE] ❌❌❌ ERRO AO GERAR LINK ❌❌❌")
        log(f"[SHARE] Erro: {str(e)}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao gerar link de compartilhamento: {str(e)}'}), 500
