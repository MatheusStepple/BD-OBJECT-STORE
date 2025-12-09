# 📚 Sistema de Gerenciamento de Arquivos Acadêmicos

Sistema web simples para estudantes organizarem trabalhos, provas e materiais de estudo.

## 📖 Caso de Uso

**Problema:** Estudantes precisam organizar arquivos acadêmicos (trabalhos, provas, materiais) de forma centralizada e acessível.

**Solução:** Sistema web que permite:
- Fazer upload de arquivos organizados por categorias
- Buscar arquivos rapidamente
- Baixar arquivos quando necessário
- Ver estatísticas de uso

**Tecnologias:** Python (Flask) + MinIO (Object Storage) + HTML/CSS/JavaScript

## 🚀 Como Usar

### 🐳 Docker (Recomendado)

#### Pré-requisitos
- Docker instalado: https://www.docker.com/get-started
- Docker Compose (geralmente vem com Docker Desktop)

#### Executar

```bash
docker-compose up --build
```

**Acessar:**
- **Backend/API:** http://localhost:5000
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

**Login padrão:**
- **Usuário:** `admin`
- **Senha:** `admin123`

#### Comandos úteis

```bash
# Parar containers
docker-compose down

# Parar e remover volumes (apaga dados)
docker-compose down -v

# Ver logs
docker-compose logs -f

# Ver logs apenas do backend
docker-compose logs -f backend
```

---

## 🗄️ Armazenamento

### MinIO - Object Storage

O sistema usa **MinIO** para armazenamento de objetos (arquivos).

**Bucket:** `dados-privados`

**Importante:** Este bucket, por padrão, é privado. Somente usuários com credenciais válidas e permissões (como nós) podem acessar ou modificar seu conteúdo.

**Configurações:**
- Object Locking: **Desabilitado**
- Versioning: **Desabilitado**
- Acesso: **Privado** (requer autenticação)

### Estrutura de Armazenamento

```
dados-privados/
├── files/
│   └── {user_id}/
│       └── {file_id}/
│           └── {filename}
└── metadata/
    └── {user_id}/
        └── {file_id}.json
```

## 📋 Funcionalidades

- ✅ **Cadastro e Login** - Sistema de autenticação simples
- ✅ **Upload de Arquivos** - Envie trabalhos, provas, materiais
- ✅ **Categorias** - Organize por: Trabalhos, Provas, Materiais, Aulas, Outros
- ✅ **Busca** - Encontre arquivos rapidamente pelo nome
- ✅ **Download** - Baixe seus arquivos quando precisar
- ✅ **Estatísticas** - Veja total de arquivos e espaço usado

## 💻 Tecnologias

- **Backend:** Python + Flask
- **Armazenamento:** MinIO (S3-compatible Object Storage)
- **Cliente S3:** boto3
- **Frontend:** HTML, CSS, JavaScript
- **Autenticação:** Flask-Login

## 📁 Estrutura do Projeto

```
.
├── app.py              # Aplicação Flask principal
├── config.py           # Configurações
├── storage.py          # Gerenciamento de usuários (JSON)
├── minio_client.py     # Cliente MinIO (boto3)
├── models.py           # Modelos (User)
├── utils.py            # Funções utilitárias
├── requirements.txt    # Dependências Python
├── Dockerfile          # Configuração Docker
├── docker-compose.yml  # Orquestração Docker
├── .dockerignore       # Arquivos ignorados no build
├── routes/            # Rotas da aplicação
│   ├── __init__.py
│   ├── auth.py        # Rotas de autenticação
│   ├── files.py        # Rotas de arquivos
│   └── main.py         # Rotas principais (frontend)
├── templates/         # Interface web
│   ├── index.html    # Página principal
│   └── login.html    # Página de login
└── README.md         # Este arquivo
```

## 🔧 Configuração

### Variáveis de Ambiente (opcional)

Crie um arquivo `.env` para personalizar:

```env
# MinIO
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=dados-privados

# Aplicação
PORT=5000
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development
```

## 🔧 Solução de Problemas

**Erro: "port is already allocated"**
- Altere a porta no arquivo `.env` ou `docker-compose.yml`

**Erro ao conectar com MinIO**
- Aguarde alguns segundos após `docker-compose up` - o MinIO precisa inicializar
- Verifique os logs: `docker-compose logs minio`

**Erro ao fazer build**
- Certifique-se de que o Docker está rodando
- Tente: `docker-compose build --no-cache`

## 📝 Notas

- Cada usuário vê apenas seus próprios arquivos
- Arquivos são armazenados no MinIO (bucket `dados-privados`)
- Metadados dos arquivos também são armazenados no MinIO
- Usuários são armazenados em `users.json` (simples, sem banco de dados)
- Categorias disponíveis: Trabalhos, Provas, Materiais, Aulas, Outros
- Usuário padrão criado automaticamente: admin/admin123
