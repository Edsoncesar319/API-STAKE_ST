"""
Shared database configuration
"""
import sqlite3
import os
import shutil

# Database path configuration
# In Vercel, we need to use /tmp, but try to copy from root DB if it exists
_root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')
_tmp_db = os.path.join('/tmp', 'database.sqlite3')

# For local development, use root DB if writable
if os.path.exists(_root_db) and os.access(os.path.dirname(_root_db), os.W_OK):
    DB_PATH = _root_db
else:
    # For Vercel serverless, always use /tmp
    DB_PATH = _tmp_db
    # Try to copy root DB to /tmp on first access (if root DB exists in deploy)
    if os.path.exists(_root_db) and not os.path.exists(_tmp_db):
        try:
            shutil.copy2(_root_db, _tmp_db)
        except:
            pass

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = sqlite3.connect(DB_PATH)
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

