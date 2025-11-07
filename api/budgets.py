from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

# Add api directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from _db import get_db, init_db
    from _jwt_helper import verify_token
except ImportError:
    def verify_token(token):
        return None

def require_auth(headers):
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ', 1)[1].strip()
    payload = verify_token(token)
    return payload is not None

class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_POST(self):
        init_db()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            data = {}
        
        # Create budget
        required = ['name', 'email', 'phone', 'service', 'details', 'city']
        missing = [f for f in required if not data.get(f)]
        if missing:
            response = {"error": f'Campos ausentes: {", ".join(missing)}'}
            self.send_response(400)
        else:
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
                    datetime.now(timezone.utc).isoformat()
                )
            )
            db.commit()
            db.close()
            response = {"success": True}
            self.send_response(201)
        
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_GET(self):
        init_db()
        
        if not require_auth(self.headers):
            response = {"error": "Não autorizado"}
            self.send_response(401)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Parse query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        try:
            page = int(query_params.get('page', ['1'])[0])
            page_size = int(query_params.get('page_size', ['10'])[0])
            page = max(page, 1)
            page_size = max(min(page_size, 100), 1)
        except ValueError:
            response = {"error": "Parâmetros de paginação inválidos"}
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return
        
        offset = (page - 1) * page_size
        db = get_db()
        total = db.execute('SELECT COUNT(1) as c FROM budgets').fetchone()['c']
        rows = db.execute(
            'SELECT id, name, email, phone, service, details, company, city, created_at FROM budgets ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?',
            (page_size, offset)
        ).fetchall()
        items = [dict(r) for r in rows]
        db.close()
        
        response = {"items": items, "total": total, "page": page, "page_size": page_size}
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
