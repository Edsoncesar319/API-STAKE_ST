# Correção Final: api/_shared.py

## 🔍 Problema Identificado

O arquivo `api/_shared.py` tinha código executado no **nível do módulo**:

```python
TOKEN_FILE = os.path.join('/tmp', 'tokens.json')
```

Isso executa `os.path.join()` durante a importação do módulo, o que pode causar problemas durante o build da Vercel se:
- O diretório `/tmp` não existe durante o build
- Há problemas de permissão
- O ambiente de build não suporta operações de path

## ✅ Solução: Lazy Initialization

Implementada **lazy initialization** - o caminho do arquivo só é calculado quando necessário:

**Antes:**
```python
TOKEN_FILE = os.path.join('/tmp', 'tokens.json')  # Executa durante import

def get_token_store():
    if os.path.exists(TOKEN_FILE):  # Usa TOKEN_FILE diretamente
        ...
```

**Depois:**
```python
TOKEN_FILE = None  # Não executa nada durante import

def _get_token_file():
    """Get token file path, initializing if necessary"""
    global TOKEN_FILE
    if TOKEN_FILE is None:
        try:
            TOKEN_FILE = os.path.join('/tmp', 'tokens.json')
        except:
            TOKEN_FILE = '/tmp/tokens.json'
    return TOKEN_FILE

def get_token_store():
    token_file = _get_token_file()  # Só calcula quando necessário
    if os.path.exists(token_file):
        ...
```

## ✅ Benefícios

1. **Build mais seguro**: Não tenta acessar o sistema de arquivos durante o build
2. **Inicialização sob demanda**: O caminho só é calculado quando realmente necessário
3. **Melhor tratamento de erros**: Todas as operações de I/O estão dentro de try/except
4. **Compatibilidade**: Funciona tanto em desenvolvimento quanto em produção

## 🧪 Testes Realizados

- ✅ Import de `_shared.py` funciona
- ✅ `get_token_store()` funciona corretamente
- ✅ Simulação de build passa
- ✅ Diagnóstico completo passa

## 📋 Resumo de Todas as Correções

1. ✅ `datetime.utcnow()` → `datetime.now(timezone.utc)` (3 arquivos)
2. ✅ Lazy initialization do `DB_PATH` (`api/_db.py`)
3. ✅ Proteção de `sys.path.insert` (3 arquivos)
4. ✅ Fallbacks melhorados (2 arquivos)
5. ✅ **Lazy initialization do `TOKEN_FILE` (`api/_shared.py`)** ← NOVO

## 🚀 Próximos Passos

1. **Fazer commit:**
   ```bash
   git add api/_shared.py
   git commit -m "fix: lazy initialization do TOKEN_FILE para evitar erros durante build"
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

