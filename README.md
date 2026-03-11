# Pet Flow Premium

## Fase 1
Base do sistema com:

- FastAPI
- PostgreSQL
- autenticação
- usuários
- empresas
- permissões
- configurações
- auditoria
- layout premium base

## Como rodar

### 1. copiar variáveis
cp .env.example .env

### 2. subir containers
docker compose up --build

### 3. em outro terminal, executar bootstrap
docker compose exec app python scripts/bootstrap.py

### 4. abrir
http://localhost:8000

## Login inicial
- e-mail: admin@petflow.com
- senha: admin123
