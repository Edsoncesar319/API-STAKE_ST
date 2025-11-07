#!/usr/bin/env python3
"""
Valida todos os arquivos Python como a Vercel faria durante o build
"""
import sys
import os
import ast
import traceback

# Simula ambiente Vercel
os.environ.setdefault('VERCEL', '1')

api_dir = os.path.join(os.path.dirname(__file__), 'api')
sys.path.insert(0, api_dir)

print("=" * 60)
print("VALIDAÇÃO COMPLETA DOS ARQUIVOS PARA BUILD VERCEL")
print("=" * 60)
print()

errors = []
warnings = []

# Lista de arquivos Python na API
python_files = [
    'health.py',
    'login.py', 
    'messages.py',
    'budgets.py',
    '_db.py',
    '_jwt_helper.py',
    '_shared.py'
]

for filename in python_files:
    filepath = os.path.join(api_dir, filename)
    print(f"Validando {filename}...")
    
    # 1. Verificar se o arquivo existe
    if not os.path.exists(filepath):
        errors.append((filename, "Arquivo não encontrado"))
        print(f"  ❌ Arquivo não encontrado")
        continue
    
    # 2. Verificar sintaxe
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=filename)
        print(f"  ✅ Sintaxe OK")
    except SyntaxError as e:
        errors.append((filename, f"Erro de sintaxe: {e}"))
        print(f"  ❌ Erro de sintaxe: {e}")
        continue
    except Exception as e:
        errors.append((filename, f"Erro ao parsear: {e}"))
        print(f"  ❌ Erro ao parsear: {e}")
        continue
    
    # 3. Verificar se tem handler (para arquivos de endpoint)
    if filename in ['health.py', 'login.py', 'messages.py', 'budgets.py']:
        try:
            # Tenta importar
            module_name = filename.replace('.py', '')
            mod = __import__(module_name)
            if hasattr(mod, 'handler'):
                handler = getattr(mod, 'handler')
                print(f"  ✅ Handler encontrado: {type(handler).__name__}")
            else:
                warnings.append((filename, "Sem handler definido"))
                print(f"  ⚠️  Sem handler definido")
        except Exception as e:
            errors.append((filename, f"Erro ao importar: {e}"))
            print(f"  ❌ Erro ao importar: {e}")
            traceback.print_exc()
    else:
        # Para arquivos auxiliares, só verifica se importa
        try:
            module_name = filename.replace('.py', '')
            mod = __import__(module_name)
            print(f"  ✅ Import OK")
        except Exception as e:
            errors.append((filename, f"Erro ao importar: {e}"))
            print(f"  ❌ Erro ao importar: {e}")
            traceback.print_exc()
    
    print()

# Resumo
print("=" * 60)
print("RESUMO")
print("=" * 60)

if errors:
    print(f"\n❌ {len(errors)} ERRO(S) ENCONTRADO(S):")
    for filename, error in errors:
        print(f"  - {filename}: {error}")
    print()
    
if warnings:
    print(f"\n⚠️  {len(warnings)} AVISO(S):")
    for filename, warning in warnings:
        print(f"  - {filename}: {warning}")
    print()

if not errors:
    print("\n✅ Todos os arquivos são válidos para build na Vercel!")
    sys.exit(0)
else:
    print("\n❌ Corrija os erros acima antes de fazer deploy.")
    sys.exit(1)

