"""
Shared state for all API endpoints
"""
import os
import json

# Token file path - shared across serverless functions via /tmp
# Lazy initialization to avoid issues during build
TOKEN_FILE = None

def _get_token_file():
    """Get token file path, initializing if necessary"""
    global TOKEN_FILE
    if TOKEN_FILE is None:
        try:
            TOKEN_FILE = os.path.join('/tmp', 'tokens.json')
        except:
            TOKEN_FILE = '/tmp/tokens.json'
    return TOKEN_FILE

def get_token_store():
    """Get token store from file"""
    try:
        token_file = _get_token_file()
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                data = json.load(f)
                return set(data.get('tokens', []))
    except:
        pass
    return set()

def save_token_store(token_set):
    """Save token store to file"""
    try:
        token_file = _get_token_file()
        with open(token_file, 'w') as f:
            json.dump({'tokens': list(token_set)}, f)
    except:
        pass

def add_token(token):
    """Add token to store"""
    tokens = get_token_store()
    tokens.add(token)
    save_token_store(tokens)

def remove_token(token):
    """Remove token from store"""
    tokens = get_token_store()
    tokens.discard(token)
    save_token_store(tokens)

def has_token(token):
    """Check if token exists"""
    return token in get_token_store()

