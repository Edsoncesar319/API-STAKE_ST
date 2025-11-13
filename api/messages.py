from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import traceback
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


# Helper functions
def _send_json_response(res, status_code, payload):
    """Envia resposta JSON"""
    try:
        if hasattr(res, 'status'):
            res.status(status_code)
        elif hasattr(res, 'statusCode'):
            res.statusCode = status_code
        elif hasattr(res, 'status_code'):
            res.status_code = status_code
    except:
        pass
    
    headers = {
        "Content-type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
    }
    
    try:
        if hasattr(res, 'headers'):
            if isinstance(res.headers, dict):
                res.headers.update(headers)
        elif hasattr(res, 'setHeader'):
            for key, value in headers.items():
                res.setHeader(key, value)
    except:
        pass
    
    body = json.dumps(payload) if payload is not None else ""
    
    try:
        if hasattr(res, 'send'):
            res.send(body)
        elif hasattr(res, 'end'):
            res.end(body)
        elif hasattr(res, 'write'):
            res.write(body)
            if hasattr(res, 'end'):
                res.end()
    except:
        pass
    
    return body


def _read_json_body(req):
    """Lê e parseia o body JSON do request"""
    try:
        body = b''
        if hasattr(req, 'body'):
            body_data = req.body
            if isinstance(body_data, str):
                body = body_data.encode('utf-8')
            elif body_data:
                body = body_data if isinstance(body_data, bytes) else bytes(body_data)
        elif hasattr(req, 'data'):
            body_data = req.data
            if isinstance(body_data, str):
                body = body_data.encode('utf-8')
            elif body_data:
                body = body_data if isinstance(body_data, bytes) else bytes(body_data)
        
        if not body:
            return {}
        
        return json.loads(body.decode('utf-8'))
    except:
        return {}


def _get_headers(req):
    """Extrai headers do request"""
    try:
        if hasattr(req, 'headers'):
            headers = req.headers
            if headers:
                return dict(headers) if not isinstance(headers, dict) else headers
        if isinstance(req, dict):
            headers = req.get('headers', {})
            return dict(headers) if headers else {}
    except:
        pass
    return {}


def _get_path(req):
    """Extrai path do request"""
    try:
        if hasattr(req, 'path'):
            path = req.path
            if path:
                return str(path)
        if hasattr(req, 'url'):
            url = req.url
            if url:
                url_str = str(url)
                if '?' in url_str:
                    return url_str.split('?')[0]
                return url_str
        # Tenta acessar como dict
        if isinstance(req, dict):
            path = req.get('path') or req.get('url', '/')
            if isinstance(path, str) and '?' in path:
                return path.split('?')[0]
            return str(path) if path else '/'
    except:
        pass
    return '/'


def _get_method(req):
    """Extrai método HTTP do request"""
    try:
        if hasattr(req, 'method'):
            method = req.method
            if method:
                return str(method).upper()
        if hasattr(req, 'get'):
            method = req.get('method', 'GET')
            return str(method).upper()
        # Tenta acessar como dict
        if isinstance(req, dict):
            method = req.get('method', 'GET')
            return str(method).upper()
    except:
        pass
    return 'GET'


def _extract_id_from_path(path):
    """Extrai ID do path"""
    parsed_url = urlparse(path)
    segments = [segment for segment in parsed_url.path.split('/') if segment]
    
    if not segments:
        return None
    
    last = segments[-1]
    if last.isdigit():
        return int(last)
    
    return None


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
        Lida com paths como: /api/messages/123, /messages/123, /123, etc.
        """
        if parsed_url is None:
            parsed_url = urlparse(self.path)
        
        # Remove segmentos vazios e obtém todos os segmentos do path
        segments = [segment for segment in parsed_url.path.split('/') if segment]
        
        if not segments:
            return None
        
        # O ID deve ser o último segmento numérico
        # Pode ser: /api/messages/123 ou /messages/123
        last = segments[-1]
        
        # Verifica se é um número
        if last.isdigit():
            return int(last)
        
        return None

    # HTTP verbs ---------------------------------------------------------------
    def do_POST(self):
        init_db()
        data = self._read_json()

        required = ['name', 'email', 'subject', 'message']
        missing = [field for field in required if not (data.get(field) or '').strip()]
        if missing:
            self._send_json(400, {"error": f'Campos ausentes: {", ".join(missing)}'})
            return

        db = get_db()
        try:
            cursor = db.execute(
                'INSERT INTO messages (name, email, subject, message, created_at) VALUES (?, ?, ?, ?, ?)',
                (
                    data['name'].strip(),
                    data['email'].strip(),
                    data['subject'].strip(),
                    data['message'].strip(),
                    datetime.now(timezone.utc).isoformat()
                )
            )
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
            new_id = cursor.lastrowid
            row = db.execute(
                'SELECT id, name, email, subject, message, created_at FROM messages WHERE id = ?',
                (new_id,)
            ).fetchone()
        except Exception as e:
            db.rollback()
            self._send_json(500, {"error": f"Erro ao criar mensagem: {str(e)}"})
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
                    'SELECT id, name, email, subject, message, created_at FROM messages WHERE id = ?',
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
            total = db.execute('SELECT COUNT(1) as c FROM messages').fetchone()['c']
            rows = db.execute(
                'SELECT id, name, email, subject, message, created_at FROM messages ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?',
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
        required = ['name', 'email', 'subject', 'message']
        missing = [field for field in required if not (data.get(field) or '').strip()]
        if missing:
            self._send_json(400, {"error": f'Campos ausentes: {", ".join(missing)}'})
            return

        db = get_db()
        try:
            existing = db.execute('SELECT id FROM messages WHERE id = ?', (record_id,)).fetchone()
            if existing is None:
                self._send_json(404, {"error": "Registro não encontrado"})
                return

            db.execute(
                'UPDATE messages SET name = ?, email = ?, subject = ?, message = ? WHERE id = ?',
                (
                    data['name'].strip(),
                    data['email'].strip(),
                    data['subject'].strip(),
                    data['message'].strip(),
                    record_id
                )
            )
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
            row = db.execute(
                'SELECT id, name, email, subject, message, created_at FROM messages WHERE id = ?',
                (record_id,)
            ).fetchone()
        except Exception as e:
            db.rollback()
            self._send_json(500, {"error": f"Erro ao atualizar mensagem: {str(e)}"})
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
            existing = db.execute('SELECT id FROM messages WHERE id = ?', (record_id,)).fetchone()
            if existing is None:
                self._send_json(404, {"error": "Registro não encontrado"})
                return
            db.execute('DELETE FROM messages WHERE id = ?', (record_id,))
            db.commit()
            sync_after_write()  # Sincroniza com arquivo local
        except Exception as e:
            db.rollback()
            self._send_json(500, {"error": f"Erro ao excluir mensagem: {str(e)}"})
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


# Handler compatível com Vercel (função direta)
def vercel_handler(req, res):
    """
    Handler direto para Vercel que processa todos os métodos HTTP
    """
    try:
        # Validação básica
        if req is None:
            _send_json_response(res, 500, {"error": "Request é None"})
            return
        
        if res is None:
            # Se res é None, pode ser que esteja sendo chamado de forma diferente
            # Tenta retornar um dict com a resposta
            return {"error": "Response é None"}
        
        method = _get_method(req)
        path = _get_path(req)
        headers = _get_headers(req)
        
        # Normaliza o path - remove /api se presente
        if path.startswith('/api/messages'):
            path = path.replace('/api/messages', '/messages', 1)
        elif path.startswith('/api'):
            path = path.replace('/api', '', 1)
        
        # OPTIONS - CORS preflight
        if method == 'OPTIONS':
            _send_json_response(res, 200, None)
            return
        
        # POST - Criar mensagem
        if method == 'POST':
            init_db()
            data = _read_json_body(req)
            
            required = ['name', 'email', 'subject', 'message']
            missing = [field for field in required if not (data.get(field) or '').strip()]
            if missing:
                _send_json_response(res, 400, {"error": f'Campos ausentes: {", ".join(missing)}'})
                return
            
            db = get_db()
            try:
                cursor = db.execute(
                    'INSERT INTO messages (name, email, subject, message, created_at) VALUES (?, ?, ?, ?, ?)',
                    (
                        data['name'].strip(),
                        data['email'].strip(),
                        data['subject'].strip(),
                        data['message'].strip(),
                        datetime.now(timezone.utc).isoformat()
                    )
                )
                db.commit()
                sync_after_write()
                new_id = cursor.lastrowid
                row = db.execute(
                    'SELECT id, name, email, subject, message, created_at FROM messages WHERE id = ?',
                    (new_id,)
                ).fetchone()
            except Exception as e:
                db.rollback()
                _send_json_response(res, 500, {"error": f"Erro ao criar mensagem: {str(e)}"})
                return
            finally:
                db.close()
            
            _send_json_response(res, 201, {"success": True, "item": dict(row) if row else {"id": new_id}})
            return
        
        # GET - Listar ou obter mensagem específica
        if method == 'GET':
            init_db()
            
            if not require_auth(headers):
                _send_json_response(res, 401, {"error": "Não autorizado"})
                return
            
            record_id = _extract_id_from_path(path)
            
            # GET específico por ID
            if record_id is not None:
                db = get_db()
                try:
                    row = db.execute(
                        'SELECT id, name, email, subject, message, created_at FROM messages WHERE id = ?',
                        (record_id,)
                    ).fetchone()
                finally:
                    db.close()
                
                if row is None:
                    _send_json_response(res, 404, {"error": "Registro não encontrado"})
                else:
                    _send_json_response(res, 200, {"item": dict(row)})
                return
            
            # GET lista com paginação
            parsed_url = urlparse(path)
            query_params = parse_qs(parsed_url.query)
            try:
                page = int(query_params.get('page', ['1'])[0])
                page_size = int(query_params.get('page_size', ['10'])[0])
                page = max(page, 1)
                page_size = max(min(page_size, 100), 1)
            except ValueError:
                _send_json_response(res, 400, {"error": "Parâmetros de paginação inválidos"})
                return
            
            offset = (page - 1) * page_size
            db = get_db()
            try:
                total = db.execute('SELECT COUNT(1) as c FROM messages').fetchone()['c']
                rows = db.execute(
                    'SELECT id, name, email, subject, message, created_at FROM messages ORDER BY datetime(created_at) DESC LIMIT ? OFFSET ?',
                    (page_size, offset)
                ).fetchall()
            finally:
                db.close()
            
            items = [dict(r) for r in rows]
            _send_json_response(res, 200, {"items": items, "total": total, "page": page, "page_size": page_size})
            return
        
        # PUT - Atualizar mensagem
        if method == 'PUT':
            init_db()
            
            if not require_auth(headers):
                _send_json_response(res, 401, {"error": "Não autorizado"})
                return
            
            record_id = _extract_id_from_path(path)
            if record_id is None:
                _send_json_response(res, 400, {"error": "ID inválido"})
                return
            
            data = _read_json_body(req)
            required = ['name', 'email', 'subject', 'message']
            missing = [field for field in required if not (data.get(field) or '').strip()]
            if missing:
                _send_json_response(res, 400, {"error": f'Campos ausentes: {", ".join(missing)}'})
                return
            
            db = get_db()
            try:
                existing = db.execute('SELECT id FROM messages WHERE id = ?', (record_id,)).fetchone()
                if existing is None:
                    _send_json_response(res, 404, {"error": "Registro não encontrado"})
                    return
                
                db.execute(
                    'UPDATE messages SET name = ?, email = ?, subject = ?, message = ? WHERE id = ?',
                    (
                        data['name'].strip(),
                        data['email'].strip(),
                        data['subject'].strip(),
                        data['message'].strip(),
                        record_id
                    )
                )
                db.commit()
                sync_after_write()
                row = db.execute(
                    'SELECT id, name, email, subject, message, created_at FROM messages WHERE id = ?',
                    (record_id,)
                ).fetchone()
            except Exception as e:
                db.rollback()
                _send_json_response(res, 500, {"error": f"Erro ao atualizar mensagem: {str(e)}"})
                return
            finally:
                db.close()
            
            _send_json_response(res, 200, {"success": True, "item": dict(row) if row else {"id": record_id}})
            return
        
        # DELETE - Excluir mensagem
        if method == 'DELETE':
            init_db()
            
            if not require_auth(headers):
                _send_json_response(res, 401, {"error": "Não autorizado"})
                return
            
            record_id = _extract_id_from_path(path)
            if record_id is None:
                _send_json_response(res, 400, {"error": "ID inválido"})
                return
            
            db = get_db()
            try:
                existing = db.execute('SELECT id FROM messages WHERE id = ?', (record_id,)).fetchone()
                if existing is None:
                    _send_json_response(res, 404, {"error": "Registro não encontrado"})
                    return
                db.execute('DELETE FROM messages WHERE id = ?', (record_id,))
                db.commit()
                sync_after_write()
            except Exception as e:
                db.rollback()
                _send_json_response(res, 500, {"error": f"Erro ao excluir mensagem: {str(e)}"})
                return
            finally:
                db.close()
            
            _send_json_response(res, 200, {"success": True})
            return
        
        # Método não suportado
        _send_json_response(res, 405, {"error": f"Método {method} não permitido"})
        
    except Exception as e:
        error_trace = traceback.format_exc()
        # Log do erro (pode ser visto nos logs do Vercel)
        try:
            print(f"Erro em vercel_handler: {str(e)}")
            print(f"Traceback: {error_trace}")
        except:
            pass
        _send_json_response(res, 500, {"error": f"Erro interno: {str(e)}", "details": error_trace if os.getenv('VERCEL_ENV') == 'development' else None})


# Substitui handler pela função vercel_handler para compatibilidade com Vercel
# Mantém a classe handler para desenvolvimento local se necessário
_handler_class = handler
handler = vercel_handler
