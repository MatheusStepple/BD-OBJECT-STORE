"""Gerenciamento de banco de dados"""
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from config import DB_CONFIG
import os

def get_db_connection():
    """Estabelece conexão com o PostgreSQL"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "could not connect" in error_msg.lower():
            raise Exception(
                f"❌ PostgreSQL não está rodando!\n\n"
                f"Por favor:\n"
                f"1. Inicie o serviço PostgreSQL\n"
                f"2. Verifique se o PostgreSQL está instalado\n\n"
                f"Configuração atual:\n"
                f"  Host: {DB_CONFIG['host']}\n"
                f"  Port: {DB_CONFIG['port']}\n"
                f"  Database: {DB_CONFIG['database']}\n"
                f"  User: {DB_CONFIG['user']}"
            )
        raise

def init_db():
    """Inicializa o banco de dados criando tabelas e usuário padrão"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de arquivos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                nome_original VARCHAR(255) NOT NULL,
                nome_arquivo VARCHAR(255) NOT NULL UNIQUE,
                tamanho BIGINT NOT NULL,
                tipo VARCHAR(100),
                categoria VARCHAR(50) DEFAULT 'Aulas',
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hash_md5 VARCHAR(32)
            )
        ''')
        
        # Adicionar coluna categoria se não existir (para bancos já criados)
        try:
            cursor.execute('ALTER TABLE arquivos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT \'Aulas\'')
            cursor.execute("UPDATE arquivos SET categoria = 'Aulas' WHERE categoria IS NULL OR categoria = 'Outros'")
            conn.commit()
        except:
            pass  # Coluna já existe ou erro (ignorar)
        
        conn.commit()
        
        # Criar usuário padrão se não existir
        cursor.execute('SELECT COUNT(*) FROM usuarios WHERE username = %s', ('admin',))
        if cursor.fetchone()[0] == 0:
            password_hash = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO usuarios (username, email, password_hash)
                VALUES (%s, %s, %s)
            ''', ('admin', 'admin@example.com', password_hash))
            conn.commit()
            print('✅ Usuário padrão criado:')
            print('   Usuário: admin')
            print('   Senha: admin123')
        
        conn.close()
        print('✅ Banco de dados inicializado com sucesso!')
    except Exception as e:
        error_msg = str(e)
        print('=' * 60)
        print('❌ ERRO AO CONECTAR COM POSTGRESQL')
        print('=' * 60)
        print(error_msg)
        print('=' * 60)
        print('\n📋 SOLUÇÕES:')
        print('1. Inicie o serviço PostgreSQL')
        print('2. Verifique as credenciais no arquivo .env')
        print('3. Certifique-se de que o banco "upload_system" existe')
        print('=' * 60)
        raise

