"""
Helper para converter requests do Vercel para formato WSGI
"""
import io

def make_wsgi_environ(req):
    """Converte um request do Vercel para formato WSGI environ"""
    environ = {
        'REQUEST_METHOD': req.method or 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': req.path or '/',
        'QUERY_STRING': req.query_string or '',
        'CONTENT_TYPE': req.headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(req.body or b'')),
        'SERVER_NAME': req.headers.get('host', 'localhost'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': io.BytesIO(req.body or b''),
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Adiciona headers HTTP
    for key, value in (req.headers or {}).items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH', 'HOST'):
            environ[f'HTTP_{key}'] = value
    
    return environ

def make_response(wsgi_app, environ, req):
    """Executa a aplicação WSGI e retorna a resposta"""
    status_code = 200
    headers = []
    response_body = []
    
    def start_response(status, response_headers):
        nonlocal status_code
        status_code = int(status.split()[0])
        headers.extend(response_headers)
    
    # Executa a aplicação WSGI
    result = wsgi_app(environ, start_response)
    
    # Coleta o body da resposta
    for chunk in result:
        if isinstance(chunk, bytes):
            response_body.append(chunk)
        else:
            response_body.append(chunk.encode('utf-8'))
    
    return {
        'statusCode': status_code,
        'headers': dict(headers),
        'body': b''.join(response_body).decode('utf-8')
    }

