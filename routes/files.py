"""Rotas de gerenciamento de arquivos"""
from flask import Blueprint, request, jsonify, send_file, make_response, Response
from flask_login import login_required, current_user
from urllib.parse import quote
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from config import UPLOAD_FOLDER, CATEGORIES
from utils import (
    allowed_file, calcular_hash, sanitize_filename, 
    get_mime_type, generate_unique_filename, ensure_upload_folder
)
import os

files_bp = Blueprint('files', __name__)

@files_bp.route('/api/arquivos', methods=['GET'])
@login_required
def listar_arquivos():
    """Lista arquivos do usuário com filtros opcionais"""
    try:
        # Obter parâmetros de busca e filtro
        busca = request.args.get('busca', '').strip()
        categoria = request.args.get('categoria', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Construir query com filtros
        query = 'SELECT * FROM arquivos WHERE user_id = %s'
        params = [current_user.id]
        
        if categoria and categoria in CATEGORIES:
            query += ' AND categoria = %s'
            params.append(categoria)
        
        if busca:
            query += ' AND nome_original ILIKE %s'
            params.append(f'%{busca}%')
        
        query += ' ORDER BY data_upload DESC'
        
        cursor.execute(query, params)
        arquivos = []
        for row in cursor.fetchall():
            arquivos.append({
                'id': row['id'],
                'nome_original': row['nome_original'],
                'nome_arquivo': row['nome_arquivo'],
                'tamanho': row['tamanho'],
                'tipo': row['tipo'],
                'categoria': row.get('categoria', 'Outros'),
                'data_upload': row['data_upload'].isoformat() if row['data_upload'] else None,
                'hash_md5': row['hash_md5']
            })
        conn.close()
        return jsonify({'sucesso': True, 'arquivos': arquivos})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@files_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_arquivo():
    """Endpoint para upload de arquivo"""
    try:
        # Verificar se arquivo foi enviado
        if 'arquivo' not in request.files:
            return jsonify({'sucesso': False, 'erro': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        
        if arquivo.filename == '' or not arquivo.filename:
            return jsonify({'sucesso': False, 'erro': 'Nome de arquivo vazio'}), 400
        
        if not allowed_file(arquivo.filename):
            return jsonify({'sucesso': False, 'erro': 'Tipo de arquivo não permitido'}), 400
        
        # Obter informações do arquivo
        nome_original = arquivo.filename
        nome_arquivo = generate_unique_filename(current_user.id, nome_original)
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        # Garantir que a pasta existe
        ensure_upload_folder()
        
        # Salvar arquivo
        arquivo.save(caminho_arquivo)
        
        # Verificar se arquivo foi salvo corretamente
        if not os.path.exists(caminho_arquivo):
            return jsonify({'sucesso': False, 'erro': 'Erro ao salvar arquivo no servidor'}), 500
        
        # Calcular hash e tamanho do arquivo salvo
        tamanho = os.path.getsize(caminho_arquivo)
        if tamanho == 0:
            os.remove(caminho_arquivo)
            return jsonify({'sucesso': False, 'erro': 'Arquivo vazio não permitido'}), 400
        
        hash_md5 = calcular_hash(caminho_arquivo)
        
        # Obter tipo MIME
        tipo_mime = get_mime_type(nome_original, arquivo.content_type)
        
        # Obter categoria (se enviada)
        categoria = request.form.get('categoria', 'Outros')
        if categoria not in CATEGORIES:
            categoria = 'Outros'
        
        # Salvar no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO arquivos (user_id, nome_original, nome_arquivo, tamanho, tipo, categoria, hash_md5)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (current_user.id, nome_original, nome_arquivo, tamanho, tipo_mime, categoria, hash_md5))
            arquivo_id = cursor.fetchone()[0]
            conn.commit()
        except Exception as db_error:
            conn.rollback()
            # Se falhar ao salvar no banco, remover arquivo físico
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
            raise db_error
        finally:
            conn.close()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Arquivo enviado com sucesso!',
            'arquivo': {
                'id': arquivo_id,
                'nome_original': nome_original,
                'nome_arquivo': nome_arquivo,
                'tamanho': tamanho,
                'hash_md5': hash_md5
            }
        })
    except Exception as e:
        print(f"Erro no upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao processar upload: {str(e)}'}), 500

@files_bp.route('/api/arquivos/<int:arquivo_id>', methods=['DELETE'])
@login_required
def deletar_arquivo(arquivo_id):
    """Endpoint para deletar arquivo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar se o arquivo pertence ao usuário
        cursor.execute('SELECT nome_arquivo FROM arquivos WHERE id = %s AND user_id = %s', (arquivo_id, current_user.id))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        nome_arquivo = resultado['nome_arquivo']
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        # Deletar do banco de dados
        cursor.execute('DELETE FROM arquivos WHERE id = %s AND user_id = %s', (arquivo_id, current_user.id))
        conn.commit()
        conn.close()
        
        # Deletar arquivo físico
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        return jsonify({'sucesso': True, 'mensagem': 'Arquivo deletado com sucesso!'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@files_bp.route('/api/arquivos/<int:arquivo_id>/download', methods=['GET'])
@login_required
def download_arquivo(arquivo_id):
    """Endpoint para download de arquivo"""
    try:
        # Buscar informações do arquivo no banco
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT nome_original, nome_arquivo, tipo, tamanho, hash_md5
            FROM arquivos 
            WHERE id = %s AND user_id = %s
        ''', (arquivo_id, current_user.id))
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return jsonify({'sucesso': False, 'erro': 'Arquivo não encontrado ou sem permissão'}), 404
        
        nome_original = resultado['nome_original']
        nome_arquivo = resultado['nome_arquivo']
        tipo_mime = resultado.get('tipo') or 'application/octet-stream'
        
        # Construir caminho completo do arquivo
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        caminho_arquivo = os.path.normpath(caminho_arquivo)
        
        # Verificar se arquivo existe
        if not os.path.exists(caminho_arquivo):
            print(f"ERRO: Arquivo não encontrado: {caminho_arquivo}")
            return jsonify({
                'sucesso': False, 
                'erro': f'Arquivo físico não encontrado no servidor. Caminho: {caminho_arquivo}'
            }), 404
        
        # Verificar tamanho do arquivo
        tamanho_real = os.path.getsize(caminho_arquivo)
        if tamanho_real == 0:
            return jsonify({'sucesso': False, 'erro': 'Arquivo está vazio'}), 500
        
        # Sanitizar nome do arquivo para Windows
        nome_sanitizado = sanitize_filename(nome_original)
        
        # Ler arquivo e enviar
        try:
            # Usar send_file com headers explícitos para forçar download
            response = make_response(send_file(
                caminho_arquivo,
                mimetype=tipo_mime,
                as_attachment=True,
                download_name=nome_sanitizado
            ))
            
            # Garantir headers corretos para forçar download
            nome_encoded = quote(nome_sanitizado.encode('utf-8'))
            response.headers['Content-Disposition'] = f'attachment; filename="{nome_sanitizado}"; filename*=UTF-8\'\'{nome_encoded}'
            response.headers['Content-Type'] = tipo_mime
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            return response
        except Exception as send_error:
            print(f"Erro ao usar send_file: {send_error}")
            # Fallback: ler arquivo e enviar manualmente
            try:
                with open(caminho_arquivo, 'rb') as f:
                    file_data = f.read()
                
                nome_encoded = quote(nome_sanitizado.encode('utf-8'))
                
                response = Response(
                    file_data,
                    mimetype=tipo_mime,
                    headers={
                        'Content-Disposition': f'attachment; filename="{nome_sanitizado}"; filename*=UTF-8\'\'{nome_encoded}',
                        'Content-Length': str(len(file_data)),
                        'Content-Type': tipo_mime
                    }
                )
                return response
            except Exception as read_error:
                print(f"Erro ao ler arquivo: {read_error}")
                return jsonify({
                    'sucesso': False, 
                    'erro': f'Erro ao ler arquivo: {str(read_error)}'
                }), 500
            
    except Exception as e:
        print(f"Erro no download: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro ao processar download: {str(e)}'}), 500

