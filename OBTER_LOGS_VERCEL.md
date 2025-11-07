# Como Obter Logs Completos do Build da Vercel

## 🔍 O Problema

O erro "Python process exited with exit status: 1" é genérico. Para identificar a causa real, precisamos ver os **logs completos do build** na Vercel.

## 📋 Métodos para Obter Logs

### Método 1: Dashboard da Vercel (Recomendado)

1. Acesse [vercel.com/dashboard](https://vercel.com/dashboard)
2. Selecione o projeto `api-stake-st`
3. Vá em **"Deployments"**
4. Clique no deployment que falhou (o mais recente)
5. Clique em **"Build Logs"** ou **"Function Logs"**
6. Procure por mensagens de erro específicas

### Método 2: Vercel CLI

```bash
# Listar deployments
vercel ls

# Ver logs de um deployment específico (substitua pela URL do deployment)
vercel logs https://api-stake-XXXXX.vercel.app --logs

# Ou pelo ID do deployment
vercel logs dpl_XXXXX --logs
```

### Método 3: Inspect Deployment

```bash
# Ver informações detalhadas do deployment
vercel inspect <deployment-url> --logs
```

## 🔎 O Que Procurar nos Logs

Procure por:

1. **Erros de sintaxe Python:**
   ```
   SyntaxError: ...
   ```

2. **Erros de import:**
   ```
   ImportError: ...
   ModuleNotFoundError: ...
   ```

3. **Erros de dependências:**
   ```
   ERROR: Could not find a version that satisfies the requirement
   ERROR: Failed building wheel for ...
   ```

4. **Erros de execução:**
   ```
   Traceback (most recent call last):
   ...
   ```

5. **Erros de permissão:**
   ```
   PermissionError: ...
   OSError: ...
   ```

## 📝 Informações Importantes

Quando encontrar o erro específico nos logs, anote:

- **Mensagem de erro completa**
- **Arquivo onde o erro ocorre**
- **Linha do erro**
- **Stack trace completo**

## 🆘 Próximos Passos

1. **Obtenha os logs completos** usando um dos métodos acima
2. **Identifique o erro específico** nos logs
3. **Compartilhe o erro** para que possamos corrigir

## 💡 Dica

Se os logs não mostrarem erro específico, pode ser um problema com:
- **Versão do Python** na Vercel (pode estar usando Python 3.12+)
- **Instalação de dependências** falhando silenciosamente
- **Timeout durante o build**
- **Problema com a estrutura dos handlers**

Nesses casos, pode ser necessário:
- Especificar a versão do Python no `vercel.json`
- Verificar se todas as dependências estão no `requirements.txt`
- Simplificar a estrutura dos handlers

---

**Importante:** Sem os logs completos, é difícil identificar a causa exata do erro. Os logs mostrarão exatamente o que está falhando durante o build.

