"""
Wrapper para fazer BaseHTTPRequestHandler funcionar no Vercel
"""
import io
import sys
from http.server import BaseHTTPRequestHandler


class VercelRequest:
    """Mock request object para BaseHTTPRequestHandler"""
    def __init__(self, vercel_req):
        self.vercel_req = vercel_req
        
        # Extrai método HTTP
        if hasattr(vercel_req, 'method'):
            self.command = vercel_req.method or 'GET'
        elif hasattr(vercel_req, 'get'):
            self.command = vercel_req.get('method', 'GET')
        else:
            self.command = 'GET'
        
        # Extrai path
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
        
        # Extrai headers
        if hasattr(vercel_req, 'headers'):
            self.headers = vercel_req.headers or {}
        elif isinstance(vercel_req, dict):
            self.headers = vercel_req.get('headers', {})
        else:
            self.headers = {}
        
        # Extrai body
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


class VercelResponse:
    """Mock response object para capturar a resposta do BaseHTTPRequestHandler"""
    def __init__(self):
        self.status_code = 200
        self.headers = {}
        self.body = b''
        self.headers_sent = False


def make_vercel_handler(handler_class):
    """
    Cria um handler compatível com Vercel a partir de uma classe BaseHTTPRequestHandler
    
    Args:
        handler_class: Classe que herda de BaseHTTPRequestHandler
    
    Retorna:
        Função handler(req, res) compatível com Vercel
    """
    def vercel_handler(req, res):
        try:
            # Cria objetos mock
            vercel_req = VercelRequest(req)
            vercel_res = VercelResponse()
            
            # Instancia o handler
            handler = handler_class(vercel_req, vercel_res, None)
            
            # Chama o método apropriado baseado no método HTTP
            method = vercel_req.command.upper()
            
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
            
            # Extrai resposta
            response_body = vercel_res.wfile.getvalue()
            
            # Configura status code
            status = vercel_res.status_code if hasattr(vercel_res, 'status_code') else 200
            
            # Tenta definir status no response do Vercel
            try:
                if hasattr(res, 'status'):
                    res.status(status)
                elif hasattr(res, 'statusCode'):
                    res.statusCode = status
                elif hasattr(res, 'status_code'):
                    res.status_code = status
            except:
                pass
            
            # Configura headers
            try:
                if hasattr(res, 'headers'):
                    if isinstance(res.headers, dict):
                        for key, value in vercel_res.headers.items():
                            res.headers[key] = value
                elif hasattr(res, 'setHeader'):
                    for key, value in vercel_res.headers.items():
                        res.setHeader(key, value)
            except:
                pass
            
            # Envia body
            try:
                if hasattr(res, 'send'):
                    res.send(response_body.decode('utf-8') if isinstance(response_body, bytes) else str(response_body))
                elif hasattr(res, 'end'):
                    res.end(response_body.decode('utf-8') if isinstance(response_body, bytes) else str(response_body))
                elif hasattr(res, 'write'):
                    res.write(response_body.decode('utf-8') if isinstance(response_body, bytes) else str(response_body))
                    if hasattr(res, 'end'):
                        res.end()
            except:
                pass
            
            return response_body.decode('utf-8') if isinstance(response_body, bytes) else str(response_body)
            
        except Exception as e:
            # Em caso de erro, retorna erro 500
            error_msg = str(e)
            try:
                if hasattr(res, 'status_code'):
                    res.status_code = 500
                elif hasattr(res, 'status'):
                    res.status = 500
                
                if hasattr(res, 'headers'):
                    res.headers['Content-Type'] = 'application/json'
                elif hasattr(res, 'setHeader'):
                    res.setHeader('Content-Type', 'application/json')
            except:
                pass
            
            error_json = f'{{"error": "Internal server error", "message": "{error_msg}"}}'
            try:
                if hasattr(res, 'send'):
                    res.send(error_json)
                elif hasattr(res, 'end'):
                    res.end(error_json)
            except:
                pass
            
            return error_json
    
    return vercel_handler

