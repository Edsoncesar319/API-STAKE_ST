"""
Shared database configuration

Este módulo gerencia a conexão com o banco de dados SQLite,
otimizado para funcionar tanto localmente quanto no Vercel serverless.

Estratégia:
- Local: Usa database.sqlite3 na raiz do projeto
- Vercel: Usa /tmp/database.sqlite3 (único diretório gravável em serverless)
- Copia automaticamente o banco da raiz para /tmp na primeira execução (se existir)
- Sincroniza automaticamente de /tmp para a raiz após operações de escrita
"""
import sqlite3
import os
import shutil
from contextlib import contextmanager
from typing import Optional

# Cache do caminho do banco de dados (lazy initialization)
_DB_PATH_CACHE: Optional[str] = None
_DB_INITIALIZED = False


def _get_db_path():
    """
    Determina o caminho do banco de dados baseado no ambiente.
    
    Retorna:
        str: Caminho do arquivo do banco de dados
    """
    global _DB_PATH_CACHE
    
    # Se já foi calculado, retorna do cache
    if _DB_PATH_CACHE is not None:
        return _DB_PATH_CACHE
    
    try:
        # Tenta localizar o banco na raiz do projeto
        root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')
    except Exception:
        root_db = None
    
    tmp_db = os.path.join('/tmp', 'database.sqlite3')
    
    # Ambiente local: usa banco na raiz se for gravável
    if root_db and os.path.exists(root_db):
        try:
            root_dir = os.path.dirname(root_db)
            if os.access(root_dir, os.W_OK):
                _DB_PATH_CACHE = root_db
                return _DB_PATH_CACHE
        except Exception:
            pass
    
    # Ambiente Vercel: usa /tmp
    # Tenta copiar o banco da raiz para /tmp na primeira vez (se existir)
    if root_db and os.path.exists(root_db) and not os.path.exists(tmp_db):
        try:
            os.makedirs('/tmp', exist_ok=True)
            shutil.copy2(root_db, tmp_db)
        except Exception as e:
            # Falha silenciosa - o banco será criado vazio se necessário
            pass
    
    _DB_PATH_CACHE = tmp_db
    return _DB_PATH_CACHE


def _ensure_db_path():
    """Garante que o caminho do banco está inicializado"""
    return _get_db_path()


def _get_root_db_path():
    """
    Retorna o caminho do banco na raiz do projeto.
    
    Retorna:
        str: Caminho do banco na raiz, ou None se não for possível determinar
    """
    try:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')
    except Exception:
        return None


def sync_to_root():
    """
    Sincroniza o banco de dados de /tmp para o arquivo local na raiz do projeto.
    Isso garante que os dados sejam salvos também no arquivo local, não apenas no /tmp.
    
    Esta função é chamada automaticamente após operações de escrita bem-sucedidas.
    No Vercel serverless, pode não funcionar se a raiz não for gravável.
    
    Retorna:
        bool: True se a sincronização foi bem-sucedida, False caso contrário
    """
    try:
        current_path = _ensure_db_path()
        root_path = _get_root_db_path()
        
        # Se já estamos usando a raiz, não precisa sincronizar
        if current_path == root_path:
            return True
        
        # Se não há caminho raiz ou o arquivo atual não existe, não faz nada
        if not root_path or not os.path.exists(current_path):
            return False
        
        # Tenta verificar se o diretório raiz é gravável
        root_dir = os.path.dirname(root_path)
        try:
            if not os.access(root_dir, os.W_OK):
                # Diretório não é gravável (provavelmente no Vercel)
                return False
        except Exception:
            return False
        
        # Sincroniza: copia de /tmp para a raiz
        # Fecha todas as conexões possíveis antes de copiar
        try:
            # Usa copy2 para preservar metadados (timestamp, etc)
            shutil.copy2(current_path, root_path)
            return True
        except Exception:
            return False
    
    except Exception:
        # Falha silenciosa - não é crítico se não conseguir sincronizar
        return False


def get_db():
    """
    Obtém uma conexão com o banco de dados.
    
    IMPORTANTE: Sempre feche a conexão após usar e chame sync_after_write() após commit:
        db = get_db()
        try:
            # usar db
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
        finally:
            db.close()
    
    Para uso automático, prefira get_db_context():
        with get_db_context() as db:
            # usar db (commit automático + sincronização)
    
    Retorna:
        sqlite3.Connection: Conexão com o banco de dados
    """
    path = _ensure_db_path()
    db = sqlite3.connect(path, timeout=10.0)
    db.row_factory = sqlite3.Row
    # Habilita foreign keys e otimizações
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging para melhor performance
    return db


def sync_after_write():
    """
    Função auxiliar para sincronizar o banco após operações de escrita.
    Use esta função após fazer commit manual em operações que usam get_db().
    
    Exemplo:
        db = get_db()
        try:
            db.execute('INSERT INTO ...')
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
        finally:
            db.close()
    """
    sync_to_root()


@contextmanager
def get_db_context(sync_after_commit=True):
    """
    Context manager para obter conexão com o banco de dados.
    Faz commit automático em caso de sucesso e rollback em caso de erro.
    Sincroniza automaticamente com o arquivo local após commit (se sync_after_commit=True).
    
    Uso recomendado:
        with get_db_context() as db:
            cursor = db.execute('SELECT * FROM messages')
            results = cursor.fetchall()
            # Commit automático ao sair do bloco + sincronização com arquivo local
    
    Args:
        sync_after_commit: Se True, sincroniza com arquivo local após commit (padrão: True)
    
    Retorna:
        sqlite3.Connection: Conexão com o banco de dados
    """
    path = _ensure_db_path()
    db = None
    committed = False
    try:
        db = sqlite3.connect(path, timeout=10.0)
        db.row_factory = sqlite3.Row
        # Habilita foreign keys e otimizações
        db.execute('PRAGMA foreign_keys = ON')
        db.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging para melhor performance
        yield db
        db.commit()
        committed = True
        
        # Sincroniza com arquivo local após commit bem-sucedido
        if sync_after_commit:
            sync_to_root()
    except sqlite3.Error as e:
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()


def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias se não existirem.
    """
    global _DB_INITIALIZED
    
    # Evita re-inicialização desnecessária
    path = _ensure_db_path()
    
    with get_db_context() as db:
        # Cria tabela de mensagens
        db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Cria índice para melhor performance em consultas
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_created_at 
            ON messages(created_at DESC)
        ''')
        
        # Cria tabela de orçamentos
        db.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                details TEXT NOT NULL,
                company TEXT,
                city TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Cria índice para melhor performance
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_budgets_created_at 
            ON budgets(created_at DESC)
        ''')
    
    _DB_INITIALIZED = True


def backup_db() -> Optional[bytes]:
    """
    Cria um backup do banco de dados atual.
    
    Retorna:
        bytes: Conteúdo do arquivo de backup, ou None em caso de erro
    """
    try:
        path = _ensure_db_path()
        if not os.path.exists(path):
            return None
        
        # Lê o arquivo inteiro
        with open(path, 'rb') as f:
            return f.read()
    except Exception:
        return None


def restore_db(backup_data: bytes) -> bool:
    """
    Restaura o banco de dados a partir de um backup.
    
    Args:
        backup_data: Dados do backup (bytes do arquivo SQLite)
    
    Retorna:
        bool: True se a restauração foi bem-sucedida, False caso contrário
    """
    try:
        path = _ensure_db_path()
        
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Escreve o backup
        with open(path, 'wb') as f:
            f.write(backup_data)
        
        # Valida se o arquivo é um SQLite válido
        db = sqlite3.connect(path)
        db.execute('PRAGMA integrity_check')
        db.close()
        
        # Limpa o cache para forçar recálculo do caminho
        global _DB_PATH_CACHE
        _DB_PATH_CACHE = None
        
        return True
    except Exception:
        return False


def get_db_info() -> dict:
    """
    Retorna informações sobre o banco de dados atual.
    
    Retorna:
        dict: Informações sobre o banco (caminho, tamanho, tabelas, etc.)
    """
    try:
        path = _ensure_db_path()
        info = {
            'path': path,
            'exists': os.path.exists(path),
            'size': os.path.getsize(path) if os.path.exists(path) else 0,
            'environment': 'local' if '/tmp' not in path else 'vercel',
        }
        
        if os.path.exists(path):
            with get_db_context() as db:
                # Conta registros em cada tabela
                messages_count = db.execute('SELECT COUNT(*) as c FROM messages').fetchone()['c']
                budgets_count = db.execute('SELECT COUNT(*) as c FROM budgets').fetchone()['c']
                
                info['tables'] = {
                    'messages': {'count': messages_count},
                    'budgets': {'count': budgets_count}
                }
        
        return info
    except Exception as e:
        return {'error': str(e)}

