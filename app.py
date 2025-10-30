from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
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


token_store = set()


def require_auth():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ', 1)[1].strip()
    return token in token_store


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['ADMIN_EMAIL'] = 'Superadm@starkeST.com'
    app.config['ADMIN_PASSWORD'] = os.getenv('STARKE_ADMIN_PASSWORD', 'Starke@2025')

    @app.before_request
    def before_request():
        init_db()

    @app.teardown_appcontext
    def teardown_db(exception):
        close_db()

    @app.get('/api/health')
    def health():
        return jsonify({ 'status': 'ok' })

    @app.post('/api/login')
    def login():
        data = request.get_json(force=True, silent=True) or {}
        email = (data.get('email') or '').strip()
        password = (data.get('password') or '').strip()
        if email.lower() == app.config['ADMIN_EMAIL'].lower() and password == app.config['ADMIN_PASSWORD']:
            token = secrets.token_hex(16)
            token_store.add(token)
            return jsonify({ 'token': token })
        return jsonify({ 'error': 'Credenciais inválidas' }), 401

    @app.post('/api/logout')
    def logout():
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
            token_store.discard(token)
        return jsonify({ 'success': True })

    @app.post('/api/messages')
    def create_message():
        data = request.get_json(force=True, silent=True) or {}
        required = ['name', 'email', 'subject', 'message']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({ 'error': f'Campos ausentes: {", ".join(missing)}' }), 400

        db = get_db()
        db.execute(
            'INSERT INTO messages (name, email, subject, message, created_at) VALUES (?, ?, ?, ?, ?)',
            (
                data['name'].strip(),
                data['email'].strip(),
                data['subject'].strip(),
                data['message'].strip(),
                datetime.utcnow().isoformat()
            )
        )
        db.commit()
        return jsonify({ 'success': True }), 201

    @app.get('/api/messages')
    def list_messages():
        if not require_auth():
            return jsonify({ 'error': 'Não autorizado' }), 401
        try:
            page = int(request.args.get('page', '1'))
            page_size = int(request.args.get('page_size', '10'))
            page = max(page, 1)
            page_size = max(min(page_size, 100), 1)
        except ValueError:
            return jsonify({ 'error': 'Parâmetros de paginação inválidos' }), 400

        offset = (page - 1) * page_size
        db = get_db()
        total = db.execute('SELECT COUNT(1) as c FROM messages').fetchone()['c']
        rows = db.execute(
            'SELECT id, name, email, subject, message, created_at FROM messages ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?',
            (page_size, offset)
        ).fetchall()
        items = [dict(r) for r in rows]
        return jsonify({ 'items': items, 'total': total, 'page': page, 'page_size': page_size })

    @app.post('/api/budgets')
    def create_budget():
        data = request.get_json(force=True, silent=True) or {}
        required = ['name', 'email', 'phone', 'service', 'details', 'city']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({ 'error': f'Campos ausentes: {", ".join(missing)}' }), 400

        db = get_db()
        db.execute(
            'INSERT INTO budgets (name, email, phone, service, details, company, city, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                data['name'].strip(),
                data['email'].strip(),
                data['phone'].strip(),
                data['service'].strip(),
                data['details'].strip(),
                (data.get('company') or '').strip(),
                data['city'].strip(),
                datetime.utcnow().isoformat()
            )
        )
        db.commit()
        return jsonify({ 'success': True }), 201

    @app.get('/api/budgets')
    def list_budgets():
        if not require_auth():
            return jsonify({ 'error': 'Não autorizado' }), 401
        try:
            page = int(request.args.get('page', '1'))
            page_size = int(request.args.get('page_size', '10'))
            page = max(page, 1)
            page_size = max(min(page_size, 100), 1)
        except ValueError:
            return jsonify({ 'error': 'Parâmetros de paginação inválidos' }), 400

        offset = (page - 1) * page_size
        db = get_db()
        total = db.execute('SELECT COUNT(1) as c FROM budgets').fetchone()['c']
        rows = db.execute(
            'SELECT id, name, email, phone, service, details, company, city, created_at FROM budgets ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?',
            (page_size, offset)
        ).fetchall()
        items = [dict(r) for r in rows]
        return jsonify({ 'items': items, 'total': total, 'page': page, 'page_size': page_size })

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)


