#!/usr/bin/env python3
"""
Script para testar o backend em produção na Vercel
"""
import requests
import json
import sys
from datetime import datetime

# URL base da API - usar a URL mais recente do deployment
# Você pode alterar esta URL se necessário
BASE_URL = "https://api-stake-lsrzjkt95-edson-cesars-projects.vercel.app"

# Cores para output (se suportado)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime um cabeçalho formatado"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    """Imprime informação"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_health():
    """Testa o endpoint de health check"""
    print_header("TESTE 1: Health Check")
    try:
        print_info(f"Testando: GET {BASE_URL}/api/health")
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Resposta: {json.dumps(data, indent=2)}")
                if data.get('status') == 'ok':
                    print_success("Health check OK - API está respondendo!")
                    return True
                else:
                    print_error(f"Health check retornou status inesperado: {data}")
                    return False
            except json.JSONDecodeError:
                print_error(f"Resposta não é JSON válido: {response.text[:200]}")
                return False
        else:
            print_error(f"Health check falhou com status {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print_error("Timeout - A API não respondeu a tempo")
        return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"Erro de conexão: {e}")
        print_warning("Verifique se a URL está correta e se o projeto está deployado")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login():
    """Testa o endpoint de login"""
    print_header("TESTE 2: Login")
    try:
        data = {
            "email": "Superadm@starkeST.com",
            "password": "Starke@2025"
        }
        print_info(f"Testando: POST {BASE_URL}/api/login")
        print(f"Credenciais: email={data['email']}")
        
        response = requests.post(
            f"{BASE_URL}/api/login", 
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            json_data = response.json()
            print(f"Resposta: {json.dumps(json_data, indent=2)}")
            
            if response.status_code == 200:
                token = json_data.get('token')
                if token:
                    print_success(f"Login OK - Token obtido: {token[:30]}...")
                    return token
                else:
                    print_error("Login retornou 200 mas sem token")
                    return None
            else:
                print_error(f"Login falhou: {json_data.get('error', 'Erro desconhecido')}")
                return None
        except json.JSONDecodeError:
            print_error(f"Resposta não é JSON válido: {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_messages_create():
    """Testa criação de mensagem"""
    print_header("TESTE 3: Criar Mensagem")
    try:
        data = {
            "name": f"Teste Usuário {datetime.now().strftime('%H:%M:%S')}",
            "email": "teste@example.com",
            "subject": "Teste de Mensagem",
            "message": f"Esta é uma mensagem de teste do backend em produção - {datetime.now().isoformat()}"
        }
        print_info(f"Testando: POST {BASE_URL}/api/messages")
        print(f"Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/messages", 
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Resposta: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 201:
                print_success("Mensagem criada com sucesso!")
                return True
            else:
                print_error(f"Falha ao criar mensagem: {result.get('error', 'Erro desconhecido')}")
                return False
        except json.JSONDecodeError:
            print_error(f"Resposta não é JSON válido: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_messages_list(token):
    """Testa listagem de mensagens (requer autenticação)"""
    print_header("TESTE 4: Listar Mensagens (Autenticado)")
    if not token:
        print_warning("Pulando teste - token não disponível")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/api/messages?page=1&page_size=10"
        print_info(f"Testando: GET {url}")
        print(f"Token: {token[:30]}...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            
            if response.status_code == 200:
                total = data.get('total', 0)
                items = data.get('items', [])
                page = data.get('page', 1)
                page_size = data.get('page_size', 10)
                
                print(f"Total de mensagens: {total}")
                print(f"Página: {page}")
                print(f"Items por página: {page_size}")
                print(f"Items retornados: {len(items)}")
                
                if items:
                    print(f"\nPrimeira mensagem:")
                    print(json.dumps(items[0], indent=2, ensure_ascii=False))
                
                print_success("Listagem de mensagens OK!")
                return True
            else:
                print_error(f"Erro na listagem: {data.get('error', 'Erro desconhecido')}")
                return False
        except json.JSONDecodeError:
            print_error(f"Resposta não é JSON válido: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_budgets_create():
    """Testa criação de orçamento"""
    print_header("TESTE 5: Criar Orçamento")
    try:
        data = {
            "name": f"Teste Cliente {datetime.now().strftime('%H:%M:%S')}",
            "email": "cliente@example.com",
            "phone": "(11) 99999-9999",
            "service": "Desenvolvimento Web",
            "details": f"Preciso de um site - Teste em produção {datetime.now().isoformat()}",
            "company": "Empresa Teste",
            "city": "São Paulo/SP"
        }
        print_info(f"Testando: POST {BASE_URL}/api/budgets")
        print(f"Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/budgets", 
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Resposta: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 201:
                print_success("Orçamento criado com sucesso!")
                return True
            else:
                print_error(f"Falha ao criar orçamento: {result.get('error', 'Erro desconhecido')}")
                return False
        except json.JSONDecodeError:
            print_error(f"Resposta não é JSON válido: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_budgets_list(token):
    """Testa listagem de orçamentos (requer autenticação)"""
    print_header("TESTE 6: Listar Orçamentos (Autenticado)")
    if not token:
        print_warning("Pulando teste - token não disponível")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/api/budgets?page=1&page_size=10"
        print_info(f"Testando: GET {url}")
        print(f"Token: {token[:30]}...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            
            if response.status_code == 200:
                total = data.get('total', 0)
                items = data.get('items', [])
                page = data.get('page', 1)
                page_size = data.get('page_size', 10)
                
                print(f"Total de orçamentos: {total}")
                print(f"Página: {page}")
                print(f"Items por página: {page_size}")
                print(f"Items retornados: {len(items)}")
                
                if items:
                    print(f"\nPrimeiro orçamento:")
                    print(json.dumps(items[0], indent=2, ensure_ascii=False))
                
                print_success("Listagem de orçamentos OK!")
                return True
            else:
                print_error(f"Erro na listagem: {data.get('error', 'Erro desconhecido')}")
                return False
        except json.JSONDecodeError:
            print_error(f"Resposta não é JSON válido: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print_header("TESTANDO BACKEND EM PRODUÇÃO - API STAKE ST")
    print_info(f"URL Base: {BASE_URL}")
    print_info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        print_warning("Pulando teste de listagem de mensagens (sem token)")
        results.append(("Listar Mensagens", False))
    
    # Teste 5: Criar Orçamento
    results.append(("Criar Orçamento", test_budgets_create()))
    
    # Teste 6: Listar Orçamentos (requer token)
    if token:
        results.append(("Listar Orçamentos", test_budgets_list(token)))
    else:
        print_warning("Pulando teste de listagem de orçamentos (sem token)")
        results.append(("Listar Orçamentos", False))
    
    # Resumo
    print_header("RESUMO DOS TESTES")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSOU")
        else:
            print_error(f"{test_name}: FALHOU")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} testes passaram{Colors.RESET}")
    
    if passed == total:
        print_success("\n🎉 Todos os testes passaram! Backend está funcionando corretamente em produção.")
        return 0
    else:
        print_error(f"\n⚠️  {total - passed} teste(s) falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    # Permite passar URL como argumento
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1].rstrip('/')
        print(f"Usando URL customizada: {BASE_URL}")
    
    exit_code = main()
    sys.exit(exit_code)

