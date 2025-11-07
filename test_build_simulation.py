#!/usr/bin/env python3
"""
Simula o que a Vercel faz durante o build - importa todos os módulos
"""
import sys
import os
import traceback

# Simula o ambiente da Vercel
os.environ.setdefault('VERCEL', '1')

# Adiciona api ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

print("=" * 60)
print("SIMULANDO BUILD DA VERCEL")
print("=" * 60)
print()

errors = []

# Tenta importar cada módulo como a Vercel faria
modules_to_test = [
    'health',
    'login', 
    'messages',
    'budgets',
    '_db',
    '_jwt_helper'
]

for module_name in modules_to_test:
    try:
        print(f"Testando import de {module_name}...", end=" ")
        mod = __import__(module_name)
        
        # Verifica se tem handler
        if hasattr(mod, 'handler'):
            handler = getattr(mod, 'handler')
            print(f"✅ OK (handler encontrado: {type(handler).__name__})")
        else:
            print(f"⚠️  OK mas sem handler")
            
    except Exception as e:
        error_msg = f"❌ ERRO: {str(e)}"
        print(error_msg)
        errors.append((module_name, str(e), traceback.format_exc()))

print()
print("=" * 60)
print("RESUMO")
print("=" * 60)

if errors:
    print(f"❌ {len(errors)} erro(s) encontrado(s):\n")
    for module_name, error, trace in errors:
        print(f"Module: {module_name}")
        print(f"Erro: {error}")
        print(f"Traceback:\n{trace}")
        print("-" * 60)
    sys.exit(1)
else:
    print("✅ Todos os módulos importaram com sucesso!")
    sys.exit(0)

