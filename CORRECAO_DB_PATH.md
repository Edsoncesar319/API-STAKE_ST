# Correção: Problema com Inicialização do Banco de Dados

## 🔍 Problema Identificado

O erro "Python process exited with exit status: 1" estava sendo causado por código executado no **nível do módulo** em `api/_db.py`. Durante o build da Vercel, quando os módulos são importados, esse código tentava:

1. Acessar o sistema de arquivos (`os.path.exists()`, `os.access()`)
2. Copiar arquivos (`shutil.copy2()`)
3. Calcular caminhos relativos (`os.path.dirname()`)

Isso pode falhar durante o build porque:
- O ambiente de build pode não ter acesso ao sistema de arquivos completo
- O diretório `/tmp` pode não existir durante o build
- Pode haver problemas de permissão

## ✅ Solução: Lazy Initialization

Implementei **lazy initialization** - o caminho do banco de dados só é calculado quando realmente necessário (quando `get_db()` ou `init_db()` são chamados), não durante a importação do módulo.

### Mudanças em `api/_db.py`:

**Antes:**
```python
# Código executado durante a importação
_root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')
_tmp_db = os.path.join('/tmp', 'database.sqlite3')

if os.path.exists(_root_db) and os.access(os.path.dirname(_root_db), os.W_OK):
    DB_PATH = _root_db
else:
    DB_PATH = _tmp_db
    if os.path.exists(_root_db) and not os.path.exists(_tmp_db):
        try:
            shutil.copy2(_root_db, _tmp_db)
        except:
            pass
```

**Depois:**
```python
# Lazy initialization - só executa quando necessário
DB_PATH = None

def _get_db_path():
    """Get the database path, initializing it if necessary"""
    # Código movido para dentro de uma função
    # Só executa quando chamado, não durante import
    
def _ensure_db_path():
    """Ensure DB_PATH is initialized"""
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = _get_db_path()
    return DB_PATH

def get_db():
    path = _ensure_db_path()  # Inicializa apenas quando necessário
    db = sqlite3.connect(path)
    # ...
```

## ✅ Benefícios

1. **Build mais seguro**: Não tenta acessar o sistema de arquivos durante o build
2. **Inicialização sob demanda**: O caminho só é calculado quando realmente necessário
3. **Melhor tratamento de erros**: Todas as operações de I/O estão dentro de try/except
4. **Compatibilidade**: Funciona tanto em desenvolvimento quanto em produção

## 🧪 Testes Realizados

- ✅ Import de todos os módulos funciona
- ✅ `get_db()` e `init_db()` funcionam corretamente
- ✅ Todos os handlers podem ser importados
- ✅ Diagnóstico completo passou

## 🚀 Próximos Passos

1. **Fazer commit das alterações:**
   ```bash
   git add api/_db.py
   git commit -m "fix: lazy initialization do DB_PATH para evitar erros durante build"
   ```

2. **Fazer deploy:**
   ```bash
   vercel --prod
   ```

3. **Verificar o build:**
   - O build deve completar sem erros
   - Os endpoints devem funcionar normalmente

## 📝 Notas Técnicas

- A inicialização lazy é um padrão comum para evitar problemas durante imports
- O código ainda mantém a mesma funcionalidade, apenas mudou **quando** é executado
- Não há impacto de performance - a inicialização acontece na primeira chamada

---

**Data da Correção:** 2025-11-07  
**Status:** ✅ Correção aplicada e testada

