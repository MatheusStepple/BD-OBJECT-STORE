"""Rotas de gerenciamento de buckets - MinIO"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from minio_client import get_minio_client
from storage import set_user_bucket, get_user_bucket
import sys
import logging
import re

# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

buckets_bp = Blueprint('buckets', __name__)

def log(msg):
    """Função para garantir que logs apareçam"""
    logger.info(msg)
    sys.stdout.flush()
    sys.stderr.flush()

def validate_bucket_name(name):
    """Valida nome do bucket"""
    if not name:
        return False, "Nome do bucket não pode ser vazio"
    
    # Nomes de bucket devem ter entre 3 e 63 caracteres
    if len(name) < 3 or len(name) > 63:
        return False, "Nome do bucket deve ter entre 3 e 63 caracteres"
    
    # Deve começar e terminar com letra ou número
    if not (name[0].isalnum() and name[-1].isalnum()):
        return False, "Nome do bucket deve começar e terminar com letra ou número"
    
    # Pode conter apenas letras minúsculas, números, pontos e hífens
    if not re.match(r'^[a-z0-9.-]+$', name):
        return False, "Nome do bucket pode conter apenas letras minúsculas, números, pontos e hífens"
    
    # Não pode ter dois pontos consecutivos
    if '..' in name:
        return False, "Nome do bucket não pode ter dois pontos consecutivos"
    
    # Não pode ser um endereço IP
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', name):
        return False, "Nome do bucket não pode ser um endereço IP"
    
    return True, None

@buckets_bp.route('/api/buckets', methods=['GET'])
@login_required
def listar_buckets():
    """Lista todos os buckets disponíveis"""
    try:
        log("=" * 80)
        log("[BUCKETS] Listando buckets...")
        log(f"[BUCKETS] User ID: {current_user.id}")
        
        minio = get_minio_client()
        buckets = minio.list_buckets()
        
        # Adicionar informações extras para cada bucket
        buckets_info = []
        for bucket in buckets:
            bucket_name = bucket['name']
            try:
                size = minio.get_bucket_size(bucket_name)
                # Todos os buckets são privados
                buckets_info.append({
                    'name': bucket_name,
                    'creation_date': bucket.get('creation_date'),
                    'size': size,
                    'is_selected': bucket_name == get_user_bucket(current_user.id)
                })
            except Exception as e:
                log(f"[BUCKETS] ⚠️ Erro ao obter informações do bucket {bucket_name}: {e}")
                buckets_info.append({
                    'name': bucket_name,
                    'creation_date': bucket.get('creation_date'),
                    'size': 0,
                    'is_selected': bucket_name == get_user_bucket(current_user.id)
                })
        
        log(f"[BUCKETS] ✅ Encontrados {len(buckets_info)} buckets")
        log("=" * 80)
        
        return jsonify({
            'sucesso': True,
            'buckets': buckets_info,
            'selected_bucket': get_user_bucket(current_user.id)
        })
    except Exception as e:
        log(f"[BUCKETS] ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@buckets_bp.route('/api/buckets', methods=['POST'])
@login_required
def criar_bucket():
    """Cria um novo bucket"""
    try:
        log("=" * 80)
        log("[BUCKETS] Criando bucket...")
        log(f"[BUCKETS] User ID: {current_user.id}")
        
        data = request.get_json()
        if not data or 'nome' not in data:
            return jsonify({'sucesso': False, 'erro': 'Nome do bucket não fornecido'}), 400
        
        bucket_name = data['nome'].strip().lower()
        policy_type = 'private'  # Sempre privado
        
        log(f"[BUCKETS] Nome recebido: '{bucket_name}'")
        log(f"[BUCKETS] Criando bucket PRIVADO (sempre privado)")
        
        # Validar nome
        is_valid, error_msg = validate_bucket_name(bucket_name)
        if not is_valid:
            return jsonify({'sucesso': False, 'erro': error_msg}), 400
        
        minio = get_minio_client()
        
        # Criar bucket sempre como privado
        log(f"[BUCKETS] Chamando create_bucket com policy_type='private'")
        created = minio.create_bucket(bucket_name, policy_type='private')
        
        if created:
            log(f"[BUCKETS] ✅ Bucket '{bucket_name}' criado com sucesso!")
            log("=" * 80)
            return jsonify({
                'sucesso': True,
                'mensagem': f'Bucket "{bucket_name}" criado com sucesso!',
                'bucket': {
                    'name': bucket_name,
                    'size': 0
                }
            })
        else:
            log(f"[BUCKETS] ⚠️ Bucket '{bucket_name}' já existe")
            log("=" * 80)
            return jsonify({
                'sucesso': False,
                'erro': f'Bucket "{bucket_name}" já existe'
            }), 400
    except Exception as e:
        log("=" * 80)
        log(f"[BUCKETS] ❌ Erro ao criar bucket: {e}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao criar bucket: {str(e)}'}), 500

@buckets_bp.route('/api/buckets/<bucket_name>', methods=['DELETE'])
@login_required
def deletar_bucket(bucket_name):
    """Deleta um bucket (deve estar vazio)"""
    try:
        log("=" * 80)
        log(f"[BUCKETS] Deletando bucket: {bucket_name}")
        log(f"[BUCKETS] User ID: {current_user.id}")
        
        minio = get_minio_client()
        
        # Verificar se bucket existe
        if not minio.bucket_exists(bucket_name):
            return jsonify({'sucesso': False, 'erro': 'Bucket não encontrado'}), 404
        
        # Deletar bucket (e todos os arquivos dentro dele)
        minio.delete_bucket(bucket_name)
        
        # Se era o bucket selecionado, limpar seleção
        if get_user_bucket(current_user.id) == bucket_name:
            set_user_bucket(current_user.id, None)
        
        log(f"[BUCKETS] ✅ Bucket '{bucket_name}' e todos os seus arquivos foram deletados com sucesso!")
        log("=" * 80)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Bucket "{bucket_name}" e todos os seus arquivos foram deletados com sucesso!'
        })
    except FileNotFoundError:
        return jsonify({'sucesso': False, 'erro': 'Bucket não encontrado'}), 404
    except Exception as e:
        log("=" * 80)
        log(f"[BUCKETS] ❌ Erro ao deletar bucket: {e}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao deletar bucket: {str(e)}'}), 500

@buckets_bp.route('/api/buckets/select', methods=['POST'])
@login_required
def selecionar_bucket():
    """Seleciona um bucket para o usuário"""
    try:
        log("=" * 80)
        log("[BUCKETS] Selecionando bucket...")
        log(f"[BUCKETS] User ID: {current_user.id}")
        
        data = request.get_json()
        if not data or 'nome' not in data:
            return jsonify({'sucesso': False, 'erro': 'Nome do bucket não fornecido'}), 400
        
        bucket_name = data['nome'].strip()
        
        minio = get_minio_client()
        
        # Verificar se bucket existe, se não existir, criar como privado
        if not minio.bucket_exists(bucket_name):
            log(f"[BUCKETS] Bucket não existe, criando...")
            try:
                minio.create_bucket(bucket_name, policy_type='private')
                log(f"[BUCKETS] ✅ Bucket '{bucket_name}' criado automaticamente (privado)")
            except Exception as e:
                log(f"[BUCKETS] ❌ Erro ao criar bucket: {e}")
                return jsonify({'sucesso': False, 'erro': f'Erro ao criar bucket: {str(e)}'}), 500
        
        # Definir bucket selecionado
        set_user_bucket(current_user.id, bucket_name)
        
        log(f"[BUCKETS] ✅ Bucket '{bucket_name}' selecionado para usuário {current_user.id}")
        log("=" * 80)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Bucket "{bucket_name}" selecionado com sucesso!',
            'selected_bucket': bucket_name
        })
    except Exception as e:
        log("=" * 80)
        log(f"[BUCKETS] ❌ Erro ao selecionar bucket: {e}")
        log("=" * 80)
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao selecionar bucket: {str(e)}'}), 500



