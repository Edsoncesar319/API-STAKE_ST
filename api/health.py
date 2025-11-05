from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({ 'status': 'ok' })

# For Vercel serverless functions
def handler(request):
    return app(request.environ, lambda *args: None)
