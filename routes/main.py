"""Rotas principais (frontend)"""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@main_bp.route('/login')
def login_page():
    """Página de login"""
    return render_template('login.html')


