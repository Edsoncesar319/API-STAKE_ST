from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets
import os
import sys

# Suppress Flask development server warning
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['ENV'] = 'production'
allowed_origins = (os.getenv('ALLOWED_ORIGINS') or '*').split(',')
CORS(app, origins=allowed_origins if allowed_origins != ['*'] else None)

# Global token store (in production, consider using Redis or database)
token_store = set()

@app.route('/', methods=['POST'])
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    
    admin_email = 'Superadm@starkeST.com'
    admin_password = os.getenv('STARKE_ADMIN_PASSWORD', 'Starke@2025')
    
    if email.lower() == admin_email.lower() and password == admin_password:
        token = secrets.token_hex(16)
        token_store.add(token)
        return jsonify({ 'token': token })
    return jsonify({ 'error': 'Credenciais inválidas' }), 401

@app.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        token_store.discard(token)
    return jsonify({ 'success': True })

# For Vercel serverless functions
from _vercel_helper import make_handler

handler = make_handler(app)
