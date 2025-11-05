from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import os.path

# Add api directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from _jwt_helper import generate_token
except ImportError:
    # Fallback - create simple token generator
    import secrets
    def generate_token(user_email='admin'):
        return secrets.token_hex(16)

class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            data = {}
        
        # Determine endpoint by path
        if self.path == '/api/login' or self.path == '/login':
            self.handle_login(data)
        elif self.path == '/api/logout' or self.path == '/logout':
            self.handle_logout()
        else:
            self.send_error(404)
    
    def handle_login(self, data):
        email = (data.get('email') or '').strip()
        password = (data.get('password') or '').strip()
        
        admin_email = 'Superadm@starkeST.com'
        admin_password = os.getenv('STARKE_ADMIN_PASSWORD', 'Starke@2025')
        
        if email.lower() == admin_email.lower() and password == admin_password:
            token = generate_token(email.lower())
            response = {"token": token}
            self.send_response(200)
        else:
            response = {"error": "Credenciais inválidas"}
            self.send_response(401)
        
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_logout(self):
        # With JWT, logout is client-side (just remove token)
        # Token will expire naturally
        response = {"success": True}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
