"""Cliente MinIO para gerenciamento de objetos"""
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
from config import MINIO_CONFIG
import json
from datetime import datetime
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

def log(msg):
    """Função para garantir que logs apareçam"""
    logger.info(msg)
    sys.stdout.flush()
    sys.stderr.flush()

class MinIOClient:
    """Cliente para interagir com MinIO"""
    
    def __init__(self):
        """Inicializa cliente MinIO"""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_CONFIG['endpoint'],
            aws_access_key_id=MINIO_CONFIG['access_key'],
            aws_secret_access_key=MINIO_CONFIG['secret_key'],
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self.bucket_name = MINIO_CONFIG['bucket_name']
    
    def init_bucket(self):
        """Inicializa o bucket se não existir"""
        try:
            log(f"[MINIO] Verificando bucket: {self.bucket_name}")
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            log(f"[MINIO] ✅ Bucket '{self.bucket_name}' já existe")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404' or error_code == '403':
                log(f"[MINIO] Bucket não existe, criando...")
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    log(f"[MINIO] ✅ Bucket '{self.bucket_name}' criado!")
                    log(f"[MINIO] 📝 Este bucket é privado por padrão")
                except ClientError as create_error:
                    log(f"[MINIO] ❌ Erro ao criar bucket: {create_error}")
                    raise
            else:
                log(f"[MINIO] ❌ Erro ao verificar bucket: {e}")
                raise
        except Exception as e:
            log(f"[MINIO] ⚠️ Aviso: {e}")
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                log(f"[MINIO] ✅ Bucket '{self.bucket_name}' criado!")
            except:
                pass
    
    def upload_file(self, file_data, object_name, metadata=None, content_type=None):
        """Faz upload de arquivo para MinIO"""
        try:
            log(f"[MINIO] Upload: {object_name} ({len(file_data)} bytes)")
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_data,
                **extra_args
            )
            log(f"[MINIO] ✅ Upload concluído: {object_name}")
            return True
        except Exception as e:
            log(f"[MINIO] ❌ Erro no upload: {e}")
            raise
    
    def download_file(self, object_name):
        """Baixa arquivo do MinIO"""
        try:
            log(f"[MINIO] Download: {object_name}")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            data = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            log(f"[MINIO] ✅ Download concluído: {object_name} ({len(data)} bytes)")
            return data, content_type
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                log(f"[MINIO] ❌ Arquivo não encontrado: {object_name}")
                raise FileNotFoundError(f'Arquivo {object_name} não encontrado')
            log(f"[MINIO] ❌ Erro no download: {e}")
            raise
    
    def delete_file(self, object_name):
        """Deleta arquivo do MinIO"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return True
        except Exception as e:
            print(f'❌ Erro ao deletar arquivo: {e}')
            raise
    
    def list_files(self, prefix=''):
        """Lista arquivos no bucket com prefixo"""
        try:
            log(f"[MINIO] Listando arquivos com prefix: '{prefix}'")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            log(f"[MINIO] ✅ Encontrados {len(files)} arquivos")
            return files
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao listar: {e}")
            raise
    
    def file_exists(self, object_name):
        """Verifica se arquivo existe"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
            log(f"[MINIO] ✅ Arquivo existe: {object_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404' or error_code == 'NoSuchKey':
                log(f"[MINIO] ❌ Arquivo não existe: {object_name}")
                return False
            log(f"[MINIO] ⚠️ Erro ao verificar: {object_name} - {error_code}")
            return False
        except Exception as e:
            log(f"[MINIO] ⚠️ Erro ao verificar: {object_name} - {e}")
            return False
    
    def get_file_metadata(self, object_name):
        """Obtém metadados do arquivo"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return {
                'size': response['ContentLength'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response['LastModified'].isoformat(),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise
    
    def set_bucket(self, bucket_name):
        """Define o bucket a ser usado"""
        self.bucket_name = bucket_name
    
    def create_bucket(self, bucket_name, policy_type='private'):
        """Cria um novo bucket com política opcional"""
        try:
            log(f"[MINIO] Criando bucket: {bucket_name} (política: {policy_type})")
            # Verificar se bucket já existe
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                log(f"[MINIO] ⚠️ Bucket '{bucket_name}' já existe")
                return False
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404' or error_code == '403':
                    # Bucket não existe, criar
                    self.s3_client.create_bucket(Bucket=bucket_name)
                    log(f"[MINIO] ✅ Bucket '{bucket_name}' criado com sucesso!")
                    
                    # Aplicar política sempre (mesmo se for private, para garantir que está correto)
                    log(f"[MINIO] Aplicando política '{policy_type}' ao bucket '{bucket_name}'...")
                    try:
                        self.set_bucket_policy(bucket_name, policy_type)
                        log(f"[MINIO] ✅ Política '{policy_type}' aplicada com sucesso!")
                    except Exception as policy_error:
                        log(f"[MINIO] ⚠️ Erro ao aplicar política: {policy_error}")
                        # Não falhar a criação do bucket se a política falhar
                    
                    return True
                else:
                    log(f"[MINIO] ❌ Erro ao verificar bucket: {e}")
                    raise
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao criar bucket: {e}")
            raise
    
    def list_buckets(self):
        """Lista todos os buckets disponíveis"""
        try:
            log(f"[MINIO] Listando buckets...")
            response = self.s3_client.list_buckets()
            buckets = []
            for bucket in response.get('Buckets', []):
                buckets.append({
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat() if 'CreationDate' in bucket else None
                })
            log(f"[MINIO] ✅ Encontrados {len(buckets)} buckets")
            return buckets
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao listar buckets: {e}")
            raise
    
    def delete_bucket(self, bucket_name):
        """Deleta um bucket e todos os seus arquivos"""
        try:
            log(f"[MINIO] Deletando bucket: {bucket_name}")
            # Verificar se bucket existe
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    log(f"[MINIO] ❌ Bucket '{bucket_name}' não existe")
                    raise FileNotFoundError(f'Bucket {bucket_name} não encontrado')
                raise
            
            # Deletar todos os arquivos do bucket primeiro
            log(f"[MINIO] Deletando todos os arquivos do bucket '{bucket_name}'...")
            deleted_count = 0
            
            # Listar e deletar todos os objetos
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects_to_delete = []
                    for obj in page['Contents']:
                        objects_to_delete.append({'Key': obj['Key']})
                    
                    if objects_to_delete:
                        # Deletar em lotes (até 1000 objetos por vez)
                        self.s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={
                                'Objects': objects_to_delete,
                                'Quiet': True
                            }
                        )
                        deleted_count += len(objects_to_delete)
                        log(f"[MINIO] Deletados {len(objects_to_delete)} arquivos...")
            
            if deleted_count > 0:
                log(f"[MINIO] ✅ Total de {deleted_count} arquivos deletados do bucket '{bucket_name}'")
            else:
                log(f"[MINIO] Bucket '{bucket_name}' já estava vazio")
            
            # Deletar bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            log(f"[MINIO] ✅ Bucket '{bucket_name}' deletado com sucesso!")
            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao deletar bucket: {e}")
            raise
    
    def bucket_exists(self, bucket_name):
        """Verifica se um bucket existe"""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404' or error_code == '403':
                return False
            raise
        except Exception as e:
            log(f"[MINIO] ⚠️ Erro ao verificar bucket: {e}")
            return False
    
    def get_bucket_size(self, bucket_name):
        """Obtém o tamanho total de um bucket"""
        try:
            total_size = 0
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj.get('Size', 0)
            return total_size
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket':
                log(f"[MINIO] ⚠️ Bucket não existe: {bucket_name}")
                return 0
            log(f"[MINIO] ⚠️ Erro ao calcular tamanho do bucket: {e}")
            return 0
        except Exception as e:
            log(f"[MINIO] ⚠️ Erro ao calcular tamanho do bucket: {e}")
            return 0
    
    def set_bucket_policy(self, bucket_name, policy_type='private'):
        """Define política de acesso do bucket (private ou public)"""
        try:
            log(f"[MINIO] ========== DEFININDO POLÍTICA ==========")
            log(f"[MINIO] Bucket: {bucket_name}")
            log(f"[MINIO] Tipo: {policy_type}")
            
            if policy_type == 'public':
                # Política pública - permite leitura anônima
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }
                policy_json = json.dumps(policy)
                log(f"[MINIO] Política JSON: {policy_json}")
                
                self.s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=policy_json
                )
                log(f"[MINIO] ✅ Política PÚBLICA aplicada ao bucket '{bucket_name}'")
                
                # Verificar se foi aplicada corretamente
                try:
                    verify_policy = self.get_bucket_policy(bucket_name)
                    if verify_policy.get('is_public', False):
                        log(f"[MINIO] ✅✅✅ VERIFICAÇÃO: Bucket '{bucket_name}' está PÚBLICO")
                    else:
                        log(f"[MINIO] ⚠️⚠️⚠️ VERIFICAÇÃO: Bucket '{bucket_name}' NÃO está público (problema!)")
                except Exception as verify_error:
                    log(f"[MINIO] ⚠️ Erro ao verificar política: {verify_error}")
                
                return True
            else:
                # Política privada - remove política pública (deleta a política)
                try:
                    self.s3_client.delete_bucket_policy(Bucket=bucket_name)
                    log(f"[MINIO] ✅ Política removida (bucket privado)")
                    return True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                        log(f"[MINIO] ✅ Bucket já é privado (sem política)")
                        return True
                    raise
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao definir política: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_bucket_policy(self, bucket_name):
        """Obtém a política atual do bucket"""
        try:
            log(f"[MINIO] Verificando política do bucket: {bucket_name}")
            response = self.s3_client.get_bucket_policy(Bucket=bucket_name)
            policy = json.loads(response['Policy'])
            
            # Verificar se é público (tem statement que permite GetObject)
            is_public = False
            statements = policy.get('Statement', [])
            log(f"[MINIO] Bucket '{bucket_name}' tem {len(statements)} statements")
            
            for statement in statements:
                effect = statement.get('Effect')
                actions = statement.get('Action', [])
                principal = statement.get('Principal', {})
                
                # Normalizar actions para lista
                if isinstance(actions, str):
                    actions = [actions]
                
                # Normalizar principal AWS
                aws_principal = principal.get('AWS', '')
                if isinstance(aws_principal, list):
                    aws_principal = aws_principal[0] if aws_principal else ''
                
                # Verificar se permite GetObject para todos
                allows_getobject = 's3:GetObject' in actions
                allows_all = '*' in str(aws_principal) or aws_principal == '*'
                
                log(f"[MINIO] Statement: Effect={effect}, Actions={actions}, Principal={aws_principal}")
                log(f"[MINIO] allows_getobject={allows_getobject}, allows_all={allows_all}")
                
                if effect == 'Allow' and allows_getobject and allows_all:
                    is_public = True
                    log(f"[MINIO] ✅ Bucket '{bucket_name}' é PÚBLICO")
                    break
            
            if not is_public:
                log(f"[MINIO] ✅ Bucket '{bucket_name}' é PRIVADO")
            
            return {
                'is_public': is_public,
                'policy': policy
            }
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucketPolicy':
                log(f"[MINIO] Bucket '{bucket_name}' não tem política (PRIVADO)")
                return {'is_public': False, 'policy': None}
            log(f"[MINIO] ⚠️ Erro ClientError ao obter política: {e}")
            raise
        except Exception as e:
            log(f"[MINIO] ⚠️ Erro ao obter política: {e}")
            import traceback
            traceback.print_exc()
            return {'is_public': False, 'policy': None}
    
    def generate_presigned_url(self, object_name, expiration=3600):
        """Gera URL pré-assinada para acesso temporário ao arquivo"""
        try:
            log(f"[MINIO] Gerando URL pré-assinada para: {object_name} (expira em {expiration}s)")
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            log(f"[MINIO] ✅ URL pré-assinada gerada")
            return url
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao gerar URL pré-assinada: {e}")
            raise
    
    def generate_presigned_upload_url(self, object_name, expiration=3600):
        """Gera URL pré-assinada para upload de arquivo"""
        try:
            log(f"[MINIO] Gerando URL pré-assinada para upload: {object_name} (expira em {expiration}s)")
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            log(f"[MINIO] ✅ URL pré-assinada de upload gerada")
            return url
        except Exception as e:
            log(f"[MINIO] ❌ Erro ao gerar URL pré-assinada de upload: {e}")
            raise
    

# Instância global do cliente
minio_client = None

def get_minio_client(bucket_name=None):
    """Obtém instância do cliente MinIO (sem criar bucket padrão)"""
    global minio_client
    if minio_client is None:
        minio_client = MinIOClient()
        if bucket_name:
            minio_client.set_bucket(bucket_name)
        # Não criar bucket padrão automaticamente
    elif bucket_name:
        minio_client.set_bucket(bucket_name)
    return minio_client

