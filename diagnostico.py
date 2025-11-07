#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas no backend
"""
import sys
import os
import traceback

def check_imports():
    """Verifica se todas as dependências estão instaladas"""
    print("=" * 60)
    print("VERIFICANDO DEPENDÊNCIAS")
    print("=" * 60)
    
    dependencies = {
        'requests': 'requests',
        'PyJWT': 'jwt',
        'cryptography': 'cryptography'
    }
    
    missing = []
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name} está instalado")
        except ImportError:
            print(f"❌ {name} NÃO está instalado")
            missing.append(name)
    
    return missing

def check_api_files():
    """Verifica se os arquivos da API estão corretos"""
    print("\n" + "=" * 60)
    print("VERIFICANDO ARQUIVOS DA API")
    print("=" * 60)
    
    api_files = [
        'api/health.py',
        'api/login.py',
        'api/messages.py',
        'api/budgets.py',
        'api/_db.py',
        'api/_jwt_helper.py',
        'api/requirements.txt'
    ]
    
    missing = []
    for file in api_files:
        if os.path.exists(file):
            print(f"✅ {file} existe")
            # Tenta compilar apenas arquivos Python
            if file.endswith('.py'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        compile(f.read(), file, 'exec')
                    print(f"   └─ Sintaxe OK")
                except SyntaxError as e:
                    print(f"   └─ ❌ Erro de sintaxe: {e}")
                    missing.append(file)
            else:
                print(f"   └─ Arquivo de configuração")
        else:
            print(f"❌ {file} NÃO existe")
            missing.append(file)
    
    return missing

def check_vercel_config():
    """Verifica a configuração do Vercel"""
    print("\n" + "=" * 60)
    print("VERIFICANDO CONFIGURAÇÃO VERCEL")
    print("=" * 60)
    
    if os.path.exists('vercel.json'):
        print("✅ vercel.json existe")
        try:
            import json
            with open('vercel.json', 'r') as f:
                config = json.load(f)
            print(f"   └─ Versão: {config.get('version', 'N/A')}")
            print(f"   └─ Funções configuradas: {len(config.get('functions', {}))}")
            return True
        except Exception as e:
            print(f"   └─ ❌ Erro ao ler vercel.json: {e}")
            return False
    else:
        print("❌ vercel.json NÃO existe")
        return False

def test_api_imports():
    """Testa se os módulos da API podem ser importados"""
    print("\n" + "=" * 60)
    print("TESTANDO IMPORTS DA API")
    print("=" * 60)
    
    # Adiciona o diretório api ao path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
    
    modules = [
        ('_db', 'get_db, init_db'),
        ('_jwt_helper', 'generate_token, verify_token'),
    ]
    
    errors = []
    for module_name, exports in modules:
        try:
            mod = __import__(module_name)
            print(f"✅ {module_name} importado com sucesso")
            # Verifica se as funções existem
            for export in exports.split(','):
                export = export.strip()
                if hasattr(mod, export):
                    print(f"   └─ {export} disponível")
                else:
                    print(f"   └─ ⚠️  {export} não encontrado")
        except Exception as e:
            print(f"❌ Erro ao importar {module_name}: {e}")
            errors.append((module_name, str(e)))
            traceback.print_exc()
    
    return errors

def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DO BACKEND - API STAKE ST")
    print("=" * 60 + "\n")
    
    issues = []
    
    # Verifica dependências
    missing_deps = check_imports()
    if missing_deps:
        issues.append(f"Dependências faltando: {', '.join(missing_deps)}")
        print(f"\n⚠️  Para instalar: pip install {' '.join(missing_deps)}")
    
    # Verifica arquivos
    missing_files = check_api_files()
    if missing_files:
        issues.append(f"Arquivos faltando ou com erro: {', '.join(missing_files)}")
    
    # Verifica configuração Vercel
    if not check_vercel_config():
        issues.append("Problema na configuração do Vercel")
    
    # Testa imports
    import_errors = test_api_imports()
    if import_errors:
        issues.append(f"Erros de import: {len(import_errors)} erro(s)")
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    if not issues:
        print("✅ Nenhum problema encontrado!")
        print("\nO backend parece estar configurado corretamente.")
        return 0
    else:
        print(f"❌ {len(issues)} problema(s) encontrado(s):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n⚠️  Corrija os problemas acima antes de fazer deploy.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Erro fatal durante diagnóstico: {e}")
        traceback.print_exc()
        sys.exit(1)

