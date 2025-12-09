FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta da aplicação
EXPOSE 5000

# Comando para executar a aplicação
CMD ["python", "app.py"]

