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

@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health():
    return jsonify({ 'status': 'ok' })

# For Vercel serverless functions
# Simple handler to test
def handler(req, res):
    try:
        # Try to use the helper
        from _vercel_helper import make_handler
        handler_func = make_handler(app)
        return handler_func(req, res)
    except Exception as e:
        # Fallback: return simple response
        if hasattr(res, 'status_code'):
            res.status_code = 200
        if hasattr(res, 'headers'):
            res.headers['Content-Type'] = 'application/json'
        return '{"status": "ok", "test": true}'
