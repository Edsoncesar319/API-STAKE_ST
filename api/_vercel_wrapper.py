"""
Wrapper para adaptar BaseHTTPRequestHandler ao formato do Vercel
"""
import io
import json
from http.server import BaseHTTPRequestHandler


class VercelRequestAdapter:
    """Adapta o request do Vercel para o formato esperado pelo BaseHTTPRequestHandler"""
    
    def __init__(self, vercel_req):
        # Método HTTP
        if hasattr(vercel_req, 'method'):
            self.command = vercel_req.method or 'GET'
        elif hasattr(vercel_req, 'get'):
            self.command = vercel_req.get('method', 'GET')
        else:
            self.command = 'GET'
        
        # Path
        if hasattr(vercel_req, 'path'):
            self.path = vercel_req.path or '/'
        elif hasattr(vercel_req, 'url'):
            url = vercel_req.url or '/'
            if '?' in url:
                self.path = url.split('?')[0]
            else:
                self.path = url
        else:
            self.path = '/'
        
        # Headers
        if hasattr(vercel_req, 'headers'):
            self.headers = vercel_req.headers or {}
        elif isinstance(vercel_req, dict):
            self.headers = vercel_req.get('headers', {})
        else:
            self.headers = {}
        
        # Body
        body = b''
        if hasattr(vercel_req, 'body'):
            body_data = vercel_req.body
            if isinstance(body_data, str):
                body = body_data.encode('utf-8')
            elif body_data:
                body = body_data if isinstance(body_data, bytes) else bytes(body_data)
        elif hasattr(vercel_req, 'data'):
            body_data = vercel_req.data
            if isinstance(body_data, str):
                body = body_data.encode('utf-8')
            elif body_data:
                body = body_data if isinstance(body_data, bytes) else bytes(body_data)
        
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        
        # Query string
        if hasattr(vercel_req, 'query'):
            self.query_string = str(vercel_req.query) or ''
        elif hasattr(vercel_req, 'query_string'):
            self.query_string = vercel_req.query_string or ''
        elif '?' in getattr(vercel_req, 'url', ''):
            self.query_string = vercel_req.url.split('?', 1)[1]
        else:
            self.query_string = ''


class VercelResponseAdapter:
    """Adapta a resposta do BaseHTTPRequestHandler para o formato do Vercel"""
    
    def __init__(self, vercel_res):
        self.vercel_res = vercel_res
        self.status_code = 200
        self.headers = {}
        self.body_written = False
    
    def send_response(self, code, message=None):
        self.status_code = code
    
    def send_header(self, keyword, value):
        self.headers[keyword] = value
    
    def end_headers(self):
        pass
    
    def write(self, data):
        if isinstance(data, bytes):
            return self.vercel_res.write(data)
        else:
            return self.vercel_res.write(data.encode('utf-8'))


def create_vercel_handler(handler_class):
    """
    Cria um handler compatível com Vercel
    
    Args:
        handler_class: Classe que herda de BaseHTTPRequestHandler
    
    Retorna:
        Função handler(req, res) compatível com Vercel
    """
    def vercel_handler(req, res):
        try:
            # Cria adaptadores
            req_adapter = VercelRequestAdapter(req)
            res_adapter = VercelResponseAdapter(res)
            
            # Instancia o handler
            handler = handler_class(req_adapter, res_adapter, None)
            
            # Chama o método apropriado
            method = req_adapter.command.upper()
            
            if method == 'GET':
                handler.do_GET()
            elif method == 'POST':
                handler.do_POST()
            elif method == 'PUT':
                handler.do_PUT()
            elif method == 'DELETE':
                handler.do_DELETE()
            elif method == 'OPTIONS':
                handler.do_OPTIONS()
            else:
                handler.send_error(405, f"Método {method} não permitido")
            
            # Configura status
            try:
                if hasattr(res, 'status'):
                    res.status(res_adapter.status_code)
                elif hasattr(res, 'statusCode'):
                    res.statusCode = res_adapter.status_code
                elif hasattr(res, 'status_code'):
                    res.status_code = res_adapter.status_code
            except:
                pass
            
            # Configura headers
            try:
                if hasattr(res, 'headers'):
                    if isinstance(res.headers, dict):
                        res.headers.update(res_adapter.headers)
                elif hasattr(res, 'setHeader'):
                    for key, value in res_adapter.headers.items():
                        res.setHeader(key, value)
            except:
                pass
            
            # Retorna o body escrito
            body = res_adapter.vercel_res.wfile.getvalue() if hasattr(res_adapter.vercel_res, 'wfile') else b''
            
            try:
                if hasattr(res, 'send'):
                    res.send(body.decode('utf-8') if isinstance(body, bytes) else str(body))
                elif hasattr(res, 'end'):
                    res.end(body.decode('utf-8') if isinstance(body, bytes) else str(body))
            except:
                pass
            
            return body.decode('utf-8') if isinstance(body, bytes) else str(body)
            
        except Exception as e:
            error_msg = str(e)
            try:
                if hasattr(res, 'status_code'):
                    res.status_code = 500
                elif hasattr(res, 'status'):
                    res.status = 500
                
                error_json = json.dumps({"error": "Internal server error", "message": error_msg})
                
                if hasattr(res, 'headers'):
                    res.headers['Content-Type'] = 'application/json'
                elif hasattr(res, 'setHeader'):
                    res.setHeader('Content-Type', 'application/json')
                
                if hasattr(res, 'send'):
                    res.send(error_json)
                elif hasattr(res, 'end'):
                    res.end(error_json)
            except:
                pass
            
            return json.dumps({"error": "Internal server error", "message": error_msg})
    
    return vercel_handler

