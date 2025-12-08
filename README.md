# 📚 Sistema de Gerenciamento de Arquivos Acadêmicos

Sistema web simples para estudantes organizarem trabalhos, provas e materiais de estudo.

## 📖 Caso de Uso

**Problema:** Estudantes precisam organizar arquivos acadêmicos (trabalhos, provas, materiais) de forma centralizada e acessível.

**Solução:** Sistema web que permite:
- Fazer upload de arquivos organizados por categorias
- Buscar arquivos rapidamente
- Baixar arquivos quando necessário
- Ver estatísticas de uso

**Tecnologias:** Python (Flask) + PostgreSQL + HTML/CSS/JavaScript

## 🚀 Como Usar

### 1. Instalar PostgreSQL

**Windows:**
- Baixe em: https://www.postgresql.org/download/windows/
- Ou: `winget install PostgreSQL.PostgreSQL`
- Durante instalação, defina senha (anote para usar no .env)

### 2. Criar Banco de Dados

Abra o PostgreSQL e execute:
```sql
CREATE DATABASE upload_system;
```

### 3. Configurar Credenciais

Crie o arquivo `.env` na raiz do projeto com:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_NAME=upload_system
FLASK_ENV=development
PORT=5000
SECRET_KEY=770f5dc8-ec89-46b7-adf9-5ed1ec19b682
```

### 4. Executar o Sistema

**Windows:**
```bash
run.bat
```

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

### 5. Acessar

- Abra: http://localhost:5000
- Faça login com:
  - **Usuário:** `admin`
  - **Senha:** `admin123`

## 📋 Funcionalidades

- ✅ **Cadastro e Login** - Sistema de autenticação
- ✅ **Upload de Arquivos** - Envie trabalhos, provas, materiais
- ✅ **Categorias** - Organize por: Trabalhos, Provas, Materiais, Aulas
- ✅ **Busca** - Encontre arquivos rapidamente pelo nome
- ✅ **Download** - Baixe seus arquivos quando precisar
- ✅ **Estatísticas** - Veja total de arquivos e espaço usado

## 🗄️ Banco de Dados

### Tabelas Criadas Automaticamente

**usuarios:**
- Armazena usuários do sistema
- Campos: id, username, email, password_hash, data_criacao

**arquivos:**
- Armazena metadados dos arquivos
- Campos: id, user_id, nome_original, nome_arquivo, tamanho, tipo, categoria, data_upload, hash_md5
- Relacionamento: Cada arquivo pertence a um usuário

### Operações Disponíveis

- **CREATE:** Cadastrar usuário, fazer upload de arquivo
- **READ:** Listar arquivos, buscar por nome, filtrar por categoria
- **DELETE:** Deletar arquivo (remove do banco e do servidor)

## 💻 Tecnologias

- **Backend:** Python + Flask
- **Banco de Dados:** PostgreSQL
- **Frontend:** HTML, CSS, JavaScript
- **Autenticação:** Flask-Login

## 📁 Estrutura do Projeto

```
.
├── app.py              # Aplicação Flask principal
├── config.py           # Configurações e constantes
├── database.py         # Gerenciamento do banco de dados
├── models.py           # Modelos (User)
├── utils.py            # Funções utilitárias
├── requirements.txt    # Dependências Python
├── .env               # Configurações (crie manualmente)
├── routes/            # Rotas da aplicação
│   ├── __init__.py
│   ├── auth.py        # Rotas de autenticação
│   ├── files.py       # Rotas de arquivos
│   └── main.py        # Rotas principais (frontend)
├── templates/         # Interface web
│   ├── index.html    # Página principal
│   └── login.html    # Página de login
├── run.bat           # Executar no Windows
├── run.sh            # Executar no Linux/macOS
└── README.md         # Este arquivo
```

## 🔧 Solução de Problemas

**Erro: "PostgreSQL não está rodando"**
- Inicie manualmente o serviço PostgreSQL (services.msc no Windows)

**Erro: "database does not exist"**
- Crie o banco manualmente: `CREATE DATABASE upload_system;`

**Erro: "password authentication failed"**
- Verifique a senha no arquivo `.env`

## 📝 Notas

- Cada usuário vê apenas seus próprios arquivos
- Arquivos são salvos na pasta `uploads/`
- Categorias disponíveis: Trabalhos, Provas, Materiais, Aulas
- Usuário padrão criado automaticamente: admin/admin123
