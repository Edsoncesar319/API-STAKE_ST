# Resolução de Erro: Python process exited with exit status: 1

## 🔍 Diagnóstico

Se você está vendo o erro "Python process exited with exit status: 1", isso indica que algum processo Python falhou. Vamos identificar onde está ocorrendo:

### Possíveis Causas:

1. **Erro no Deploy da Vercel**
   - Problema com dependências não instaladas
   - Erro de sintaxe nos arquivos Python
   - Problema com variáveis de ambiente

2. **Erro ao Executar Scripts**
   - Dependências faltando localmente
   - Problema com a URL da API
   - Erro de conexão

3. **Erro nas Funções Serverless**
   - Problema com imports
   - Erro ao acessar banco de dados
   - Timeout ou erro de memória

## ✅ Verificações

### 1. Execute o Diagnóstico

```bash
python diagnostico.py
```

Isso verificará:
- ✅ Dependências instaladas
- ✅ Arquivos da API existentes e com sintaxe correta
- ✅ Configuração do Vercel
- ✅ Imports funcionando

### 2. Verifique os Logs da Vercel

```bash
# Ver logs do deployment mais recente
vercel logs https://api-stake-lsrzjkt95-edson-cesars-projects.vercel.app

# Ou ver todos os deployments
vercel ls
```

### 3. Teste a API em Produção

```bash
python test_producao.py
```

### 4. Verifique Dependências

Certifique-se de que todas as dependências estão instaladas:

```bash
# Instalar dependências locais (para testes)
pip install requests

# Verificar dependências da API
cat api/requirements.txt
```

As dependências da API são:
- `PyJWT==2.8.0`
- `cryptography>=3.4.8`

### 5. Verifique Variáveis de Ambiente na Vercel

No dashboard da Vercel, verifique se as variáveis de ambiente estão configuradas:
- `JWT_SECRET_KEY` (recomendado para produção)
- `STARKE_ADMIN_PASSWORD` (opcional, tem padrão)

## 🔧 Soluções Comuns

### Problema: Dependências não instaladas na Vercel

**Solução:** Certifique-se de que `api/requirements.txt` existe e contém todas as dependências necessárias.

### Problema: Erro de sintaxe

**Solução:** Execute o diagnóstico para identificar arquivos com erro:
```bash
python diagnostico.py
```

### Problema: Erro ao importar módulos

**Solução:** Verifique se todos os arquivos em `api/` estão corretos:
- `api/health.py`
- `api/login.py`
- `api/messages.py`
- `api/budgets.py`
- `api/_db.py`
- `api/_jwt_helper.py`

### Problema: Erro no banco de dados

**Solução:** Em funções serverless, o banco SQLite usa `/tmp/database.sqlite3`. Certifique-se de que o código está configurado corretamente (já está em `api/_db.py`).

## 📋 Checklist de Verificação

- [ ] Executei `python diagnostico.py` e não há erros
- [ ] Todas as dependências estão instaladas localmente
- [ ] `api/requirements.txt` existe e está correto
- [ ] Todos os arquivos Python têm sintaxe válida
- [ ] A API está respondendo em produção (teste com `test_producao.py`)
- [ ] Variáveis de ambiente estão configuradas na Vercel
- [ ] Verifiquei os logs da Vercel para erros específicos

## 🆘 Se o Problema Persistir

1. **Capture o erro completo:**
   - Execute o script que está falhando
   - Copie a mensagem de erro completa
   - Verifique os logs da Vercel

2. **Informações para debug:**
   - Qual comando você executou quando o erro ocorreu?
   - O erro acontece localmente ou na Vercel?
   - Há alguma mensagem de erro específica além de "exit status: 1"?

3. **Teste isolado:**
   - Teste cada endpoint individualmente
   - Verifique se o problema é específico de um endpoint

## 📞 Próximos Passos

Se você puder fornecer mais informações sobre:
- **Onde** o erro está ocorrendo (deploy, execução de script, etc.)
- **Quando** o erro acontece (durante deploy, ao acessar endpoint, etc.)
- **Qual** comando ou ação estava sendo executada

Posso ajudar a identificar e resolver o problema específico!

