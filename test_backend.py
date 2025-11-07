#!/usr/bin/env python3
"""
Script para testar os endpoints do backend
"""
import requests
import json

# URL base da API
BASE_URL = "https://api-stake-mzrgs9srd-edson-cesars-projects.vercel.app"

def test_health():
    """Testa o endpoint de health check"""
    print("=" * 50)
    print("TESTE 1: Health Check")
    print("=" * 50)
    try:
        response = requests.get(f"{BASE_URL}/api/health")
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
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_login():
    """Testa o endpoint de login"""
    print("=" * 50)
    print("TESTE 2: Login")
    print("=" * 50)
    try:
        data = {
            "email": "Superadm@starkeST.com",
            "password": "Starke@2025"
        }
        response = requests.post(f"{BASE_URL}/api/login", json=data)
        print(f"Status: {response.status_code}")
        print(f"Texto da resposta: {response.text[:200]}")
        try:
            json_data = response.json()
            print(f"JSON: {json_data}")
            if response.status_code == 200:
                token = json_data.get('token')
                print(f"✅ Login OK - Token: {token[:20]}...\n")
                return token
            else:
                print("❌ Login falhou\n")
                return None
        except:
            print("❌ Resposta não é JSON válido\n")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def test_messages_create():
    """Testa criação de mensagem"""
    print("=" * 50)
    print("TESTE 3: Criar Mensagem")
    print("=" * 50)
    try:
        data = {
            "name": "Teste Usuário",
            "email": "teste@example.com",
            "subject": "Teste de Mensagem",
            "message": "Esta é uma mensagem de teste do backend"
        }
        response = requests.post(f"{BASE_URL}/api/messages", json=data)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.json()}")
        if response.status_code == 201:
            print("✅ Mensagem criada com sucesso\n")
            return True
        else:
            print("❌ Falha ao criar mensagem\n")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        return False

def test_messages_list(token):
    """Testa listagem de mensagens (requer autenticação)"""
    print("=" * 50)
    print("TESTE 4: Listar Mensagens (Autenticado)")
    print("=" * 50)
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/messages?page=1&page_size=10", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total de mensagens: {data.get('total', 0)}")
        print(f"Página: {data.get('page', 1)}")
        print(f"Items retornados: {len(data.get('items', []))}")
        if response.status_code == 200:
            print("✅ Listagem de mensagens OK\n")
            return True
        else:
            print(f"❌ Erro na listagem: {data}\n")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        return False

def test_budgets_create():
    """Testa criação de orçamento"""
    print("=" * 50)
    print("TESTE 5: Criar Orçamento")
    print("=" * 50)
    try:
        data = {
            "name": "Teste Cliente",
            "email": "cliente@example.com",
            "phone": "(11) 99999-9999",
            "service": "Desenvolvimento Web",
            "details": "Preciso de um site",
            "company": "Empresa Teste",
            "city": "São Paulo/SP"
        }
        response = requests.post(f"{BASE_URL}/api/budgets", json=data)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.json()}")
        if response.status_code == 201:
            print("✅ Orçamento criado com sucesso\n")
            return True
        else:
            print("❌ Falha ao criar orçamento\n")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        return False

def test_budgets_list(token):
    """Testa listagem de orçamentos (requer autenticação)"""
    print("=" * 50)
    print("TESTE 6: Listar Orçamentos (Autenticado)")
    print("=" * 50)
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/budgets?page=1&page_size=10", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total de orçamentos: {data.get('total', 0)}")
        print(f"Página: {data.get('page', 1)}")
        print(f"Items retornados: {len(data.get('items', []))}")
        if response.status_code == 200:
            print("✅ Listagem de orçamentos OK\n")
            return True
        else:
            print(f"❌ Erro na listagem: {data}\n")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        return False

def main():
    print("\n" + "=" * 50)
    print("TESTANDO BACKEND - API STAKE ST")
    print("=" * 50 + "\n")
    
    results = []
    
    # Teste 1: Health Check
    results.append(("Health Check", test_health()))
    
    # Teste 2: Login
    token = test_login()
    results.append(("Login", token is not None))
    
    # Teste 3: Criar Mensagem
    results.append(("Criar Mensagem", test_messages_create()))
    
    # Teste 4: Listar Mensagens (requer token)
    if token:
        results.append(("Listar Mensagens", test_messages_list(token)))
    else:
        print("⚠️  Pulando teste de listagem de mensagens (sem token)\n")
        results.append(("Listar Mensagens", False))
    
    # Teste 5: Criar Orçamento
    results.append(("Criar Orçamento", test_budgets_create()))
    
    # Teste 6: Listar Orçamentos (requer token)
    if token:
        results.append(("Listar Orçamentos", test_budgets_list(token)))
    else:
        print("⚠️  Pulando teste de listagem de orçamentos (sem token)\n")
        results.append(("Listar Orçamentos", False))
    
    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES")
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

