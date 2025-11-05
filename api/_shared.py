"""
Shared state for all API endpoints
"""
import os
import json

# Token file path - shared across serverless functions via /tmp
TOKEN_FILE = os.path.join('/tmp', 'tokens.json')

def get_token_store():
    """Get token store from file"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('tokens', []))
    except:
        pass
    return set()

def save_token_store(token_set):
    """Save token store to file"""
    try:
        with open(TOKEN_FILE, 'w') as f:
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

