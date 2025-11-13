# API Starke ST

API backend desenvolvida em Python para o sistema Starke ST, hospedada na Vercel.

## 🚀 Tecnologias

- **Python 3.11**
- **Vercel Serverless Functions**
- **SQLite** (armazenamento em `/tmp` para funções serverless)
- **JWT** (JSON Web Tokens) para autenticação
- **BaseHTTPRequestHandler** (HTTP server padrão do Python)

## 📁 Estrutura do Projeto

```
API-STAKE_ST/
├── api/
│   ├── health.py          # Endpoint de health check
│   ├── login.py           # Autenticação e login
│   ├── messages.py        # CRUD de mensagens
│   ├── budgets.py         # CRUD de orçamentos
│   ├── _jwt_helper.py     # Helper para JWT
│   ├── _shared.py         # Utilitários compartilhados
│   └── requirements.txt    # Dependências Python
├── admin.html             # Interface administrativa
├── vercel.json            # Configuração do Vercel
├── Pipfile                # Especificação Python (opcional)
└── README.md              # Este arquivo
```

## 📋 Endpoints da API

### Autenticação

#### `POST /api/login`
Realiza login e retorna um token JWT.

**Request:**
```json
{
  "email": "seu-email@example.com",
  "password": "sua-senha"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### `POST /api/logout`
Logout (client-side - apenas remove token do cliente).

**Response (200):**
```json
{
  "success": true
}
```

### Mensagens

#### `POST /api/messages`
Cria uma nova mensagem.

**Request:**
```json
{
  "name": "Nome do Remetente",
  "email": "email@example.com",
  "subject": "Assunto da Mensagem",
  "message": "Conteúdo da mensagem"
}
```

**Response (201):**
```json
{
  "success": true
}
```

#### `GET /api/messages`
Lista mensagens (requer autenticação JWT).

**Headers:**
```
Authorization: Bearer {seu-token-jwt}
```

**Query Parameters:**
- `page` (opcional): Número da página (padrão: 1)
- `page_size` (opcional): Itens por página (padrão: 10, máximo: 100)

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Nome",
      "email": "email@example.com",
      "subject": "Assunto",
      "message": "Mensagem",
      "created_at": "2025-11-05T22:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

### Orçamentos

#### `POST /api/budgets`
Cria um novo orçamento.

**Request:**
```json
{
  "name": "Nome do Cliente",
  "email": "email@example.com",
  "phone": "(11) 99999-9999",
  "service": "Tipo de Serviço",
  "details": "Detalhes do serviço solicitado",
  "company": "Nome da Empresa (opcional)",
  "city": "São Paulo/SP"
}
```

**Response (201):**
```json
{
  "success": true
}
```

#### `GET /api/budgets`
Lista orçamentos (requer autenticação JWT).

**Headers:**
```
Authorization: Bearer {seu-token-jwt}
```

**Query Parameters:**
- `page` (opcional): Número da página (padrão: 1)
- `page_size` (opcional): Itens por página (padrão: 10, máximo: 100)

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Nome",
      "email": "email@example.com",
      "phone": "(11) 99999-9999",
      "service": "Serviço",
      "details": "Detalhes",
      "company": "Empresa",
      "city": "São Paulo/SP",
      "created_at": "2025-11-05T22:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

### Health Check

#### `GET /api/health`
Verifica o status da API.

**Response (200):**
```json
{
  "status": "ok"
}
```

### Interface Admin

#### `GET /admin`
Acessa a interface administrativa para gerenciar mensagens e orçamentos.

## 🔐 Autenticação

A API utiliza JWT (JSON Web Tokens) para autenticação. 

1. Faça login em `/api/login` para obter um token JWT
2. Use o token no header `Authorization: Bearer {token}` para acessar endpoints protegidos
3. O token expira em 24 horas

**Nota:** Configure a variável de ambiente `JWT_SECRET_KEY` no Vercel para produção.

## 🛠️ Configuração e Deploy

### Pré-requisitos

- Conta no [Vercel](https://vercel.com)
- Vercel CLI instalado (`npm i -g vercel`)

### Deploy Local

1. Instale as dependências:
```bash
pip install -r api/requirements.txt
```

2. Teste localmente com Vercel Dev:
```bash
vercel dev
```

3. Acesse `http://localhost:3000` para testar localmente

### Deploy em Produção

1. Faça login no Vercel:
```bash
vercel login
```

2. Deploy para produção:
```bash
vercel --prod
```

### Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no dashboard do Vercel:

- `JWT_SECRET_KEY`: Chave secreta para assinatura JWT (obrigatório em produção)
- `STARKE_ADMIN_PASSWORD`: Senha do administrador (opcional, tem padrão)
- `ALLOWED_ORIGINS`: Origens permitidas para CORS (opcional, padrão: `*`)

## 📦 Dependências

- `PyJWT==2.8.0`: Biblioteca para manipulação de JWT

## 🗄️ Banco de Dados

O projeto utiliza SQLite com uma configuração otimizada para funcionar tanto localmente quanto no Vercel serverless.

### Configuração

- **Desenvolvimento local**: Usa `database.sqlite3` na raiz do projeto
- **Produção (Vercel)**: Usa `/tmp/database.sqlite3` (único local gravável em serverless)
- **Estratégia automática**: Copia o banco da raiz para `/tmp` na primeira execução no Vercel (se existir)

### Tabelas

As tabelas são criadas automaticamente na primeira execução:

- **messages**: Armazena mensagens de contato
  - Campos: `id`, `name`, `email`, `subject`, `message`, `created_at`
  - Índice otimizado em `created_at` para consultas ordenadas
  
- **budgets**: Armazena solicitações de orçamento
  - Campos: `id`, `name`, `email`, `phone`, `service`, `details`, `company`, `city`, `created_at`
  - Índice otimizado em `created_at` para consultas ordenadas

### Otimizações Implementadas

1. **Write-Ahead Logging (WAL)**: Melhor performance em operações concorrentes
2. **Foreign Keys**: Validação de integridade referencial
3. **Índices**: Consultas mais rápidas em campos frequentemente usados
4. **Context Manager**: Gerenciamento automático de transações com `get_db_context()`
5. **Backup/Restore**: Funções para backup e restauração do banco

### Endpoints de Administração

O endpoint `/api/db-admin` permite gerenciar o banco de dados (requer autenticação):

- **GET `/api/db-admin`**: Retorna informações sobre o banco (caminho, tamanho, contagem de registros)
- **GET `/api/db-admin/backup`**: Faz download do backup do banco (retorna base64)
- **POST `/api/db-admin/restore`**: Restaura o banco a partir de um backup (envia base64 no body)
- **POST `/api/db-admin/init`**: Reinicializa as tabelas do banco

**Exemplo de uso do backup:**
```bash
# Fazer backup
curl -H "Authorization: Bearer TOKEN" https://seu-dominio.vercel.app/api/db-admin/backup > backup.json

# Restaurar backup
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup": "BASE64_DO_BACKUP"}' \
  https://seu-dominio.vercel.app/api/db-admin/restore
```

### ⚠️ Importante sobre Serverless

**Limitações do Vercel Serverless:**
- O diretório `/tmp` é efêmero - dados são perdidos entre cold starts
- Cada função serverless tem seu próprio ambiente isolado
- Não há persistência compartilhada entre execuções

**Recomendações:**
- Para produção em escala, use um banco de dados externo (PostgreSQL, MySQL, Vercel Postgres)
- Faça backups regulares usando o endpoint `/api/db-admin/backup`
- Considere migrar para um banco gerenciado se precisar de persistência garantida

## 🔒 Segurança

- ✅ Autenticação via JWT
- ✅ Tokens com expiração automática
- ✅ CORS configurado
- ✅ Validação de dados de entrada
- ✅ Headers de segurança

**Recomendações:**
- Use uma chave JWT forte em produção
- Configure `ALLOWED_ORIGINS` para restringir CORS
- Considere usar HTTPS apenas
- Implemente rate limiting para produção

## 🧪 Testes

Execute o script de testes:

```bash
python test_backend.py
```

O script testa todos os endpoints da API automaticamente.

## 📝 Notas

- Os tokens JWT são auto-contidos e não requerem armazenamento compartilhado
- Cada função serverless é isolada - o estado não é compartilhado entre invocações
- O banco SQLite é recriado em cada invocação (para produção, use banco externo)
- A interface admin está disponível em `/admin`

## 📄 Licença

Este projeto é privado e de propriedade da Starke ST.

## 🤝 Suporte

Para suporte ou dúvidas, entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ para Starke ST**

