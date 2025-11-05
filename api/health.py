from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging

# Suppress Flask development server warning
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['ENV'] = 'production'
allowed_origins = (os.getenv('ALLOWED_ORIGINS') or '*').split(',')
CORS(app, origins=allowed_origins if allowed_origins != ['*'] else None)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({ 'status': 'ok' })

# For Vercel serverless functions
def handler(req):
    return app(req.environ, lambda status, headers: None)
