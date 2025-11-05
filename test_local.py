#!/usr/bin/env python3
"""
Script para testar os endpoints do backend localmente
"""
import requests
import json
import time

# URL base da API local
BASE_URL = "http://localhost:3000"

def test_health():
    """Testa o endpoint de health check"""
    print("=" * 50)
    print("TESTE 1: Health Check (Local)")
    print("=" * 50)
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Texto da resposta: {response.text[:200]}")
        try:
            print(f"JSON: {response.json()}")
        except:
            print("Não é JSON válido")
        if response.status_code == 200:
            print("✅ Health check OK\n")
            return True
        else:
            print("❌ Health check falhou\n")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  Servidor não está rodando. Execute 'vercel dev' primeiro.\n")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_login():
    """Testa o endpoint de login"""
    print("=" * 50)
    print("TESTE 2: Login (Local)")
    print("=" * 50)
    try:
        data = {
            "email": "Superadm@starkeST.com",
            "password": "Starke@2025"
        }
        response = requests.post(f"{BASE_URL}/api/login", json=data, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Texto da resposta: {response.text[:200]}")
        try:
            json_data = response.json()
            print(f"JSON: {json_data}")
            if response.status_code == 200:
                token = json_data.get('token')
                print(f"✅ Login OK - Token: {token[:20] if token else 'None'}...\n")
                return token
            else:
                print("❌ Login falhou\n")
                return None
        except:
            print("❌ Resposta não é JSON válido\n")
            return None
    except requests.exceptions.ConnectionError:
        print("⚠️  Servidor não está rodando. Execute 'vercel dev' primeiro.\n")
        return None
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("\n" + "=" * 50)
    print("TESTANDO BACKEND LOCAL - API STAKE ST")
    print("=" * 50 + "\n")
    print("Aguardando servidor iniciar...")
    time.sleep(2)
    
    results = []
    
    # Teste 1: Health Check
    results.append(("Health Check", test_health()))
    
    # Teste 2: Login
    token = test_login()
    results.append(("Login", token is not None))
    
    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES LOCAIS")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    print(f"\nTotal: {passed}/{total} testes passaram")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()

