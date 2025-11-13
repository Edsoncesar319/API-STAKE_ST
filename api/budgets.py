from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

# Add api directory to path for imports
try:
    api_dir = os.path.dirname(__file__)
    if api_dir and api_dir not in sys.path:
        sys.path.insert(0, api_dir)
except:  # pragma: no cover - defensive path setup
    pass

try:
    from _db import get_db, init_db, sync_after_write
    from _jwt_helper import verify_token
except ImportError:  # pragma: no cover - fallback for local tools
    def verify_token(token):
        return None
    
    def get_db():
        import sqlite3
        return sqlite3.connect('/tmp/database.sqlite3')
    
    def init_db():
        pass
    
    def sync_after_write():
        pass


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

    # Helpers -----------------------------------------------------------------
    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        if payload is not None:
            self.wfile.write(json.dumps(payload).encode())

    def _read_json(self):
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

    def _extract_id(self, parsed_url=None):
        """
        Extrai o ID do path da URL.
        Lida com paths como: /api/budgets/123, /budgets/123, /123, etc.
        """
        if parsed_url is None:
            parsed_url = urlparse(self.path)
        
        # Remove segmentos vazios e obtém todos os segmentos do path
        segments = [segment for segment in parsed_url.path.split('/') if segment]
        
        if not segments:
            return None
        
        # O ID deve ser o último segmento numérico
        # Pode ser: /api/budgets/123 ou /budgets/123
        last = segments[-1]
        
        # Verifica se é um número
        if last.isdigit():
            return int(last)
        
        return None

    # HTTP verbs ---------------------------------------------------------------
    def do_POST(self):
        init_db()
        data = self._read_json()

        required = ['name', 'email', 'phone', 'service', 'details', 'city']
        missing = [field for field in required if not (data.get(field) or '').strip()]
        if missing:
            self._send_json(400, {"error": f'Campos ausentes: {", ".join(missing)}'})
            return

        db = get_db()
        try:
            cursor = db.execute(
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
            sync_after_write()  # Sincroniza com arquivo local
            new_id = cursor.lastrowid
            row = db.execute(
                'SELECT id, name, email, phone, service, details, company, city, created_at FROM budgets WHERE id = ?',
                (new_id,)
            ).fetchone()
        except Exception as e:
            db.rollback()
            self._send_json(500, {"error": f"Erro ao criar orçamento: {str(e)}"})
            return
        finally:
            db.close()

        self._send_json(201, {"success": True, "item": dict(row) if row else {"id": new_id}})

    def do_GET(self):
        init_db()

        if not require_auth(self.headers):
            self._send_json(401, {"error": "Não autorizado"})
            return

        parsed_url = urlparse(self.path)
        record_id = self._extract_id(parsed_url)

        # Se temos um ID, significa que é uma requisição para um registro específico
        if record_id is not None:
            db = get_db()
            try:
                row = db.execute(
                    'SELECT id, name, email, phone, service, details, company, city, created_at FROM budgets WHERE id = ?',
                    (record_id,)
                ).fetchone()
            finally:
                db.close()
            if row is None:
                self._send_json(404, {"error": "Registro não encontrado"})
            else:
                self._send_json(200, {"item": dict(row)})
            return

        query_params = parse_qs(parsed_url.query)
        try:
            page = int(query_params.get('page', ['1'])[0])
            page_size = int(query_params.get('page_size', ['10'])[0])
            page = max(page, 1)
            page_size = max(min(page_size, 100), 1)
        except ValueError:
            self._send_json(400, {"error": "Parâmetros de paginação inválidos"})
            return

        offset = (page - 1) * page_size
        db = get_db()
        try:
            total = db.execute('SELECT COUNT(1) as c FROM budgets').fetchone()['c']
            rows = db.execute(
                'SELECT id, name, email, phone, service, details, company, city, created_at FROM budgets ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?',
                (page_size, offset)
            ).fetchall()
        finally:
            db.close()

        items = [dict(r) for r in rows]
        self._send_json(200, {"items": items, "total": total, "page": page, "page_size": page_size})

    def do_PUT(self):
        init_db()
        if not require_auth(self.headers):
            self._send_json(401, {"error": "Não autorizado"})
            return

        parsed_url = urlparse(self.path)
        record_id = self._extract_id(parsed_url)
        if record_id is None:
            self._send_json(400, {"error": "ID inválido"})
            return

        data = self._read_json()
        required = ['name', 'email', 'phone', 'service', 'details', 'city']
        missing = [field for field in required if not (data.get(field) or '').strip()]
        if missing:
            self._send_json(400, {"error": f'Campos ausentes: {", ".join(missing)}'})
            return

        db = get_db()
        try:
            existing = db.execute('SELECT id FROM budgets WHERE id = ?', (record_id,)).fetchone()
            if existing is None:
                self._send_json(404, {"error": "Registro não encontrado"})
                return

            db.execute(
                'UPDATE budgets SET name = ?, email = ?, phone = ?, service = ?, details = ?, company = ?, city = ? WHERE id = ?',
                (
                    data['name'].strip(),
                    data['email'].strip(),
                    data['phone'].strip(),
                    data['service'].strip(),
                    data['details'].strip(),
                    (data.get('company') or '').strip(),
                    data['city'].strip(),
                    record_id
                )
            )
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
            row = db.execute(
                'SELECT id, name, email, phone, service, details, company, city, created_at FROM budgets WHERE id = ?',
                (record_id,)
            ).fetchone()
        except Exception as e:
            db.rollback()
            self._send_json(500, {"error": f"Erro ao atualizar orçamento: {str(e)}"})
            return
        finally:
            db.close()

        self._send_json(200, {"success": True, "item": dict(row) if row else {"id": record_id}})

    def do_DELETE(self):
        init_db()
        if not require_auth(self.headers):
            self._send_json(401, {"error": "Não autorizado"})
            return

        parsed_url = urlparse(self.path)
        record_id = self._extract_id(parsed_url)
        if record_id is None:
            self._send_json(400, {"error": "ID inválido"})
            return

        db = get_db()
        try:
            existing = db.execute('SELECT id FROM budgets WHERE id = ?', (record_id,)).fetchone()
            if existing is None:
                self._send_json(404, {"error": "Registro não encontrado"})
                return
            db.execute('DELETE FROM budgets WHERE id = ?', (record_id,))
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
        except Exception as e:
            db.rollback()
            self._send_json(500, {"error": f"Erro ao excluir orçamento: {str(e)}"})
            return
        finally:
            db.close()

        self._send_json(200, {"success": True})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
