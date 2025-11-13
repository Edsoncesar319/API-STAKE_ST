from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import base64
from urllib.parse import urlparse

# Add api directory to path for imports
try:
    api_dir = os.path.dirname(__file__)
    if api_dir and api_dir not in sys.path:
        sys.path.insert(0, api_dir)
except:
    pass

try:
    from _db import get_db_info, backup_db, restore_db, init_db
    from _jwt_helper import verify_token
except ImportError:
    def verify_token(token):
        return None
    
    def get_db_info():
        return {'error': 'Database module not available'}
    
    def backup_db():
        return None
    
    def restore_db(data):
        return False
    
    def init_db():
        pass


def require_auth(headers):
    """Verifica se o request está autenticado"""
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ', 1)[1].strip()
    payload = verify_token(token)
    return payload is not None


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, status_code, payload):
        """Envia resposta JSON"""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        if payload is not None:
            self.wfile.write(json.dumps(payload).encode())

    def _read_json(self):
        """Lê e parseia o body JSON"""
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0
        if length <= 0:
            return {}
        body = self.rfile.read(length)
        if not body:
            return {}
        try:
            return json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        """GET /api/db-admin - Retorna informações do banco ou faz download do backup"""
        if not require_auth(self.headers):
            self._send_json(401, {"error": "Não autorizado"})
            return

        parsed_url = urlparse(self.path)
        
        # Se o path termina com /backup, retorna o backup como download
        if parsed_url.path.endswith('/backup'):
            backup_data = backup_db()
            if backup_data is None:
                self._send_json(404, {"error": "Banco de dados não encontrado ou erro ao criar backup"})
                return

            # Retorna o backup como base64 no JSON
            backup_b64 = base64.b64encode(backup_data).decode('utf-8')
            self._send_json(200, {
                "success": True,
                "backup": backup_b64,
                "size": len(backup_data),
                "message": "Use POST /api/db-admin/restore para restaurar"
            })
            return

        # Caso contrário, retorna informações do banco
        info = get_db_info()
        self._send_json(200, {"success": True, "info": info})

    def do_POST(self):
        """POST /api/db-admin - Operações administrativas"""
        if not require_auth(self.headers):
            self._send_json(401, {"error": "Não autorizado"})
            return

        parsed_url = urlparse(self.path)
        data = self._read_json()

        # Restore
        if parsed_url.path.endswith('/restore'):
            if 'backup' not in data:
                self._send_json(400, {"error": "Campo 'backup' (base64) é obrigatório"})
                return

            try:
                backup_data = base64.b64decode(data['backup'])
            except Exception:
                self._send_json(400, {"error": "Backup inválido (deve ser base64)"})
                return

            if restore_db(backup_data):
                self._send_json(200, {"success": True, "message": "Banco de dados restaurado com sucesso"})
            else:
                self._send_json(500, {"error": "Erro ao restaurar banco de dados"})
            return

        # Initialize
        if parsed_url.path.endswith('/init'):
            try:
                init_db()
                info = get_db_info()
                self._send_json(200, {
                    "success": True,
                    "message": "Banco de dados inicializado",
                    "info": info
                })
            except Exception as e:
                self._send_json(500, {"error": f"Erro ao inicializar banco: {str(e)}"})
            return

        # Se nenhuma ação específica, retorna erro
        self._send_json(400, {"error": "Ação não especificada. Use /init ou /restore"})

    def do_OPTIONS(self):
        """Suporte para CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

