"""
Helper para converter requests do Vercel para formato WSGI
"""
import io

def make_wsgi_environ(req):
    """Converte um request do Vercel para formato WSGI environ"""
    # Get path from req.url or req.path
    path = getattr(req, 'path', '/')
    if not path or path == '':
        # Try to extract from url
        url = getattr(req, 'url', '/')
        if '?' in url:
            path = url.split('?')[0]
        else:
            path = url
    
    # Get query string
    query_string = getattr(req, 'query_string', '')
    if not query_string:
        if '?' in getattr(req, 'url', ''):
            query_string = getattr(req, 'url', '').split('?', 1)[1]
    
    # Get body
    body = b''
    if hasattr(req, 'body'):
        if isinstance(req.body, str):
            body = req.body.encode('utf-8')
        elif req.body:
            body = req.body
    elif hasattr(req, 'data'):
        if isinstance(req.data, str):
            body = req.data.encode('utf-8')
        elif req.data:
            body = req.data
    
    # Get headers
    headers = {}
    if hasattr(req, 'headers'):
        headers = req.headers
    elif hasattr(req, 'get'):
        # Try dict-like access
        headers = req
    
    environ = {
        'REQUEST_METHOD': getattr(req, 'method', 'GET') or 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': headers.get('content-type', headers.get('Content-Type', '')),
        'CONTENT_LENGTH': str(len(body)),
        'SERVER_NAME': headers.get('host', headers.get('Host', 'localhost')),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': io.BytesIO(body),
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers
    for key, value in headers.items():
        key_upper = key.upper().replace('-', '_')
        if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH', 'HOST'):
            environ[f'HTTP_{key_upper}'] = str(value)
    
    return environ

def make_handler(wsgi_app):
    """Cria um handler para Vercel que converte req/res para WSGI"""
    def handler(req, res):
        try:
            # Debug: log request attributes
            import sys
            import traceback
            
            # Try to access req attributes safely
            req_method = 'GET'
            req_path = '/'
            req_headers = {}
            req_body = b''
            req_query = ''
            
            # Get method
            if hasattr(req, 'method'):
                req_method = req.method or 'GET'
            elif hasattr(req, 'get'):
                req_method = req.get('method', 'GET')
            
            # Get path - Vercel provides this in req.url or req.path
            if hasattr(req, 'path'):
                req_path = req.path or '/'
            elif hasattr(req, 'url'):
                req_url = req.url or '/'
                if '?' in req_url:
                    req_path, req_query = req_url.split('?', 1)
                else:
                    req_path = req_url
            else:
                req_path = '/'
            
            # Get query string
            if hasattr(req, 'query'):
                req_query = str(req.query) or ''
            elif hasattr(req, 'query_string'):
                req_query = req.query_string or ''
            
            # Get headers
            if hasattr(req, 'headers'):
                req_headers = req.headers or {}
            elif isinstance(req, dict):
                req_headers = req.get('headers', {})
            
            # Get body
            if hasattr(req, 'body'):
                body_data = req.body
                if isinstance(body_data, str):
                    req_body = body_data.encode('utf-8')
                elif body_data:
                    req_body = body_data if isinstance(body_data, bytes) else bytes(body_data)
            elif hasattr(req, 'data'):
                body_data = req.data
                if isinstance(body_data, str):
                    req_body = body_data.encode('utf-8')
                elif body_data:
                    req_body = body_data if isinstance(body_data, bytes) else bytes(body_data)
            
            # Build WSGI environ
            environ = {
                'REQUEST_METHOD': req_method,
                'SCRIPT_NAME': '',
                'PATH_INFO': req_path,
                'QUERY_STRING': req_query,
                'CONTENT_TYPE': req_headers.get('content-type', req_headers.get('Content-Type', '')),
                'CONTENT_LENGTH': str(len(req_body)),
                'SERVER_NAME': req_headers.get('host', req_headers.get('Host', 'localhost')),
                'SERVER_PORT': '443',
                'SERVER_PROTOCOL': 'HTTP/1.1',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'https',
                'wsgi.input': io.BytesIO(req_body),
                'wsgi.errors': None,
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
                'wsgi.run_once': False,
            }
            
            # Add HTTP headers
            for key, value in req_headers.items():
                key_upper = key.upper().replace('-', '_')
                if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH', 'HOST'):
                    environ[f'HTTP_{key_upper}'] = str(value)
            
            # WSGI response
            status_code = 200
            response_headers = []
            response_body = []
            
            def start_response(status, headers):
                nonlocal status_code, response_headers
                status_code = int(status.split()[0])
                response_headers = headers
            
            # Execute WSGI app
            result = wsgi_app(environ, start_response)
            
            # Collect response body
            for chunk in result:
                if isinstance(chunk, bytes):
                    response_body.append(chunk)
                else:
                    response_body.append(str(chunk).encode('utf-8'))
            
            # Set response - Vercel expects us to write to res
            # Try different ways to set status and headers
            try:
                if hasattr(res, 'status'):
                    res.status(status_code)
                elif hasattr(res, 'statusCode'):
                    res.statusCode = status_code
                elif hasattr(res, 'status_code'):
                    res.status_code = status_code
            except:
                pass
            
            # Set headers
            try:
                if hasattr(res, 'headers'):
                    headers_dict = res.headers if isinstance(res.headers, dict) else {}
                    for header, value in response_headers:
                        headers_dict[header] = value
                    res.headers = headers_dict
                elif hasattr(res, 'setHeader'):
                    for header, value in response_headers:
                        res.setHeader(header, value)
            except:
                pass
            
            # Write body to response
            body_str = b''.join(response_body).decode('utf-8')
            
            # Try to write to res
            try:
                if hasattr(res, 'send'):
                    res.send(body_str)
                    return
                elif hasattr(res, 'end'):
                    res.end(body_str)
                    return
                elif hasattr(res, 'write'):
                    res.write(body_str)
                    if hasattr(res, 'end'):
                        res.end()
                    return
            except:
                pass
            
            # Fallback: return body (Vercel should handle this)
            return body_str
            
        except Exception as e:
            # Enhanced error handling
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            # Try to set error response
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
            
            # Return error
            error_json = f'{{"error": "Internal server error", "message": "{error_msg}"}}'
            return error_json
    
    return handler

