"""Aplicação Flask principal"""
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from config import SECRET_KEY, PORT, MINIO_CONFIG
from storage import init_storage
from minio_client import get_minio_client
from models import load_user
from routes.auth import auth_bp
from routes.files import files_bp
from routes.main import main_bp
from routes.buckets import buckets_bp

# Criar aplicação Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = SECRET_KEY

# Configurar limites de upload
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_TIMEOUT'] = 300  # 5 minutos

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login_page'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.user_loader(load_user)

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(files_bp)
app.register_blueprint(main_bp)
app.register_blueprint(buckets_bp)

if __name__ == '__main__':
    # Inicializar sistema de armazenamento (usuários)
    init_storage()
    
    # Verificar conexão com MinIO (sem criar bucket padrão)
    try:
        minio = get_minio_client()
        # Apenas verificar conexão, não criar bucket
        minio.list_buckets()
        print('✅ MinIO conectado com sucesso!')
    except Exception as e:
        print(f'⚠️  Aviso: Erro ao conectar com MinIO: {e}')
        print('   Certifique-se de que o MinIO está rodando')
    
    # Informações de inicialização
    print('=' * 50)
    print('Servidor iniciado!')
    print(f'Acesse: http://localhost:{PORT}')
    print('=' * 50)
    print('Usuário padrão: admin')
    print('Senha padrão: admin123')
    print('=' * 50)
    print(f'MinIO Endpoint: {MINIO_CONFIG["endpoint"]}')
    print('=' * 50)
    
    # Executar aplicação
    app.run(host='0.0.0.0', port=PORT, debug=True)
