# Correção: SECRET_KEY com Lazy Initialization

## 🔍 Problema Identificado

O arquivo `api/_jwt_helper.py` tinha `os.getenv()` sendo executado no **nível do módulo**:

```python
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
```

Embora `os.getenv()` geralmente seja seguro, durante o build da Vercel pode haver problemas se:
- As variáveis de ambiente não estão disponíveis durante o build
- Há algum problema com o acesso a variáveis de ambiente durante a importação

## ✅ Solução: Lazy Initialization

Implementada **lazy initialization** - a chave secreta só é obtida quando necessário:

**Antes:**
```python
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')  # Executa durante import

def generate_token(user_email='admin'):
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')  # Usa SECRET_KEY diretamente
```

**Depois:**
```python
_SECRET_KEY = None  # Não executa nada durante import

def _get_secret_key():
    """Get JWT secret key, initializing if necessary"""
    global _SECRET_KEY
    if _SECRET_KEY is None:
        _SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    return _SECRET_KEY

def generate_token(user_email='admin'):
    token = jwt.encode(payload, _get_secret_key(), algorithm='HS256')  # Só obtém quando necessário
```

## ✅ Benefícios

1. **Build mais seguro**: Não tenta acessar variáveis de ambiente durante o build
2. **Inicialização sob demanda**: A chave só é obtida quando realmente necessário
3. **Compatibilidade**: Funciona tanto em desenvolvimento quanto em produção

## 🧪 Testes Realizados

- ✅ Import de `_jwt_helper.py` funciona
- ✅ `generate_token()` funciona corretamente
- ✅ `verify_token()` funciona corretamente
- ✅ Validação completa passa

## 📋 Resumo de TODAS as Correções

1. ✅ `datetime.utcnow()` → `datetime.now(timezone.utc)` (3 arquivos)
2. ✅ Lazy initialization do `DB_PATH` (`api/_db.py`)
3. ✅ Lazy initialization do `TOKEN_FILE` (`api/_shared.py`)
4. ✅ **Lazy initialization do `SECRET_KEY` (`api/_jwt_helper.py`)** ← NOVO
5. ✅ Proteção de `sys.path.insert` (3 arquivos)
6. ✅ Fallbacks melhorados (2 arquivos)
7. ✅ **Criado `runtime.txt` para especificar Python 3.11** ← NOVO

## 🚀 Próximos Passos

1. **Fazer commit:**
   ```bash
   git add api/_jwt_helper.py runtime.txt
   git commit -m "fix: lazy initialization do SECRET_KEY e especificar Python 3.11"
   ```

2. **Fazer deploy:**
   ```bash
   vercel --prod
   ```

3. **Verificar o build:**
   - O build deve completar sem erros
   - Os endpoints devem funcionar normalmente

---

**Data:** 2025-11-07  
**Status:** ✅ Correção aplicada e testada

