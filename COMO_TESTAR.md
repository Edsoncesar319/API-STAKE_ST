# Como Testar o Backend

## ⚠️ Problema Identificado

O projeto está com **Password Protection** ativado no Vercel, o que bloqueia o acesso aos endpoints.

## 🔧 Solução 1: Desativar Password Protection no Vercel

1. Acesse o [Dashboard do Vercel](https://vercel.com/dashboard)
2. Vá para o projeto `api-stake-st`
3. Clique em **Settings** (Configurações)
4. Vá em **Deployment Protection** ou **Password Protection**
5. Desative a proteção por senha
6. Faça um novo deploy

## 🔧 Solução 2: Testar Localmente

Execute o backend localmente para testar:

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar o app principal (se tiver)
python app.py
```

## 📋 Formas de Testar o Backend

### 1. **Usando o Script Python** (após desativar proteção)

```bash
python test_backend.py
```

### 2. **Usando o Navegador**

Abra no navegador:
- Health Check: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/api/health`
- Admin: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/admin`

### 3. **Usando Postman ou Insomnia**

Importe estas requisições:

**Health Check:**
- Method: `GET`
- URL: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/api/health`

**Login:**
- Method: `POST`
- URL: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/api/login`
- Body (JSON):
```json
{
  "email": "Superadm@starkeST.com",
  "password": "Starke@2025"
}
```

**Criar Mensagem:**
- Method: `POST`
- URL: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/api/messages`
- Body (JSON):
```json
{
  "name": "João Silva",
  "email": "joao@example.com",
  "subject": "Contato",
  "message": "Mensagem de teste"
}
```

**Listar Mensagens (requer autenticação):**
- Method: `GET`
- URL: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/api/messages?page=1&page_size=10`
- Headers:
  - `Authorization: Bearer {seu_token_aqui}`

### 4. **Testando no Admin.html**

Acesse: `https://api-stake-m7ru4blf0-edson-cesars-projects.vercel.app/admin`

Use as credenciais:
- Email: `Superadm@starkeST.com`
- Senha: `Starke@2025`

## ✅ Endpoints Disponíveis

| Endpoint | Method | Auth | Descrição |
|----------|--------|------|-----------|
| `/api/health` | GET | ❌ | Health check |
| `/api/login` | POST | ❌ | Login do admin |
| `/api/logout` | POST | ✅ | Logout |
| `/api/messages` | POST | ❌ | Criar mensagem |
| `/api/messages` | GET | ✅ | Listar mensagens |
| `/api/budgets` | POST | ❌ | Criar orçamento |
| `/api/budgets` | GET | ✅ | Listar orçamentos |
| `/admin` | GET | ❌ | Página admin |

## 🔑 Credenciais

- **Email**: `Superadm@starkeST.com`
- **Senha**: `Starke@2025` (ou valor da variável `STARKE_ADMIN_PASSWORD`)

