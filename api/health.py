from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
allowed_origins = (os.getenv('ALLOWED_ORIGINS') or 'https://starkest.vercel.app').split(',')
CORS(app, origins=allowed_origins)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({ 'status': 'ok' })

# For Vercel serverless functions
def handler(request):
    return app(request.environ, lambda *args: None)
