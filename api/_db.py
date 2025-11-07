"""
Shared database configuration
"""
import sqlite3
import os
import shutil

# Database path configuration
# In Vercel, we need to use /tmp, but try to copy from root DB if it exists
def _get_db_path():
    """Get the database path, initializing it if necessary"""
    try:
        _root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')
    except:
        _root_db = None
    
    _tmp_db = os.path.join('/tmp', 'database.sqlite3')
    
    # For local development, use root DB if writable
    if _root_db and os.path.exists(_root_db):
        try:
            if os.access(os.path.dirname(_root_db), os.W_OK):
                return _root_db
        except:
            pass
    
    # For Vercel serverless, always use /tmp
    # Try to copy root DB to /tmp on first access (if root DB exists in deploy)
    if _root_db and os.path.exists(_root_db) and not os.path.exists(_tmp_db):
        try:
            # Ensure /tmp exists
            os.makedirs('/tmp', exist_ok=True)
            shutil.copy2(_root_db, _tmp_db)
        except:
            pass
    
    return _tmp_db

# Lazy initialization - only compute path when needed
DB_PATH = None

def _ensure_db_path():
    """Ensure DB_PATH is initialized"""
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = _get_db_path()
    return DB_PATH

def get_db():
    path = _ensure_db_path()
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    path = _ensure_db_path()
    db = sqlite3.connect(path)
    db.execute(
        '''CREATE TABLE IF NOT EXISTS messages (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email TEXT NOT NULL,
               subject TEXT NOT NULL,
               message TEXT NOT NULL,
               created_at TEXT NOT NULL
           )'''
    )
    db.execute(
        '''CREATE TABLE IF NOT EXISTS budgets (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email TEXT NOT NULL,
               phone TEXT NOT NULL,
               service TEXT NOT NULL,
               details TEXT NOT NULL,
               company TEXT,
               city TEXT NOT NULL,
               created_at TEXT NOT NULL
           )'''
    )
    db.commit()
    db.close()

