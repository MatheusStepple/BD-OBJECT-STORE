"""Aplicação Flask principal"""
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from config import SECRET_KEY, PORT, DB_CONFIG
from database import init_db
from models import load_user
from routes.auth import auth_bp
from routes.files import files_bp
from routes.main import main_bp

# Criar aplicação Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = SECRET_KEY

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

if __name__ == '__main__':
    # Inicializar banco de dados
    init_db()
    
    # Informações de inicialização
    print('=' * 50)
    print('Servidor iniciado!')
    print(f'Acesse: http://localhost:{PORT}')
    print('=' * 50)
    print('Usuário padrão: admin')
    print('Senha padrão: admin123')
    print('=' * 50)
    print(f'DB Config: {DB_CONFIG["user"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}')
    print('=' * 50)
    
    # Executar aplicação
    app.run(host='0.0.0.0', port=PORT, debug=True)
