#!/bin/bash

echo "========================================"
echo "Sistema de Upload de Arquivos"
echo "========================================"
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python não encontrado!"
    echo "Por favor, instale o Python 3.8 ou superior."
    exit 1
fi

# Verificar se as dependências estão instaladas
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Instalando dependências..."
pip install -q -r requirements.txt

echo ""
echo "========================================"
echo "Iniciando servidor..."
echo "========================================"
echo ""
echo "Acesse: http://localhost:5000"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

python app.py
