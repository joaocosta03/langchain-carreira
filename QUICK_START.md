# ⚡ Quick Start - Agente Consultor de Carreira

Guia rápido para rodar o projeto em **5 minutos**.

---

## 📋 Pré-requisitos

- Python 3.10+
- Conexão com internet
- Chaves de API:
  - **Google AI (Gemini)**: https://aistudio.google.com/app/apikey
  - **SerpAPI**: https://serpapi.com/manage-api-key (plano gratuito: 100 calls/mês)

---

## 🚀 Instalação Express

### Windows (PowerShell)

```powershell
# 1. Clone o repositório
git clone <seu-repo>
cd langchain-carreira

# 2. Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure .env
python setup.py
# Edite o arquivo .env criado com suas chaves

# 5. Execute
python main.py
```

### Linux/Mac

```bash
# 1. Clone o repositório
git clone <seu-repo>
cd langchain-carreira

# 2. Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure .env
python setup.py
# Edite o arquivo .env criado com suas chaves

# 5. Execute
chmod +x run.sh
./run.sh
```

---

## 🔑 Configuração do `.env`

Após executar `python setup.py`, edite o arquivo `.env`:

```bash
# Google Gemini API Key
GOOGLE_API_KEY=AIzaSy...

# SerpAPI Key
SERPAPI_API_KEY=abc123...
```

**Obter chaves**:

1. **Google AI Studio**: 
   - Acesse https://aistudio.google.com/app/apikey
   - Faça login com conta Google
   - Clique em "Get API Key"
   - Copie a chave gerada

2. **SerpAPI**:
   - Acesse https://serpapi.com/users/sign_up
   - Crie conta gratuita (100 searches/mês)
   - Vá em https://serpapi.com/manage-api-key
   - Copie sua API key

---

## ▶️ Execução

### Modo Interativo (recomendado)

```bash
python main.py
```

O sistema solicitará:
1. **Área de TI** (ex: "Engenheiro de DevOps", "Cientista de Dados")
2. **Tecnologia foco** (ex: "Nuvem", "Machine Learning", "DevOps")

### Modo Argumentos

```bash
python main.py "Engenheiro de Dados" "Big Data"
```

---

## 📊 Exemplo de Saída

```
======================================================================
AGENTE CONSULTOR DE CARREIRA EM TI
Motor: Gemini 1.5 Pro | Tools: SerpAPI + Web Scraping
======================================================================

Area: Engenheiro de DevOps
Tecnologia: Nuvem

----------------------------------------------------------------------

[TOOL] analisar_demanda_salarial: area=Engenheiro de DevOps, local=Brasil
[AGENT] Resultado: 42 vagas encontradas

[TOOL] sugerir_certificacoes_tendencia: tecnologia=Nuvem
[AGENT] Resultado: 3 certificacoes

======================================================================
PLANO DE AÇÃO FINAL
======================================================================

1. Mercado aquecido com 42 vagas para Engenheiro de DevOps, 
   concentradas em São Paulo e Rio de Janeiro 
   (fonte: Google Jobs via SerpAPI)

2. Priorize AWS Certified Solutions Architect Associate como 
   primeira certificação - é referência no mercado brasileiro 
   (fonte: Páginas oficiais AWS/Microsoft/Google Cloud)

3. Invista em Infrastructure as Code (Terraform) e Kubernetes - 
   skills em alta demanda nas vagas mapeadas 
   (fonte: Páginas oficiais AWS/Microsoft/Google Cloud)

4. Faixa salarial para DevOps: mediana de R$ 10.500/mês, 
   com variação de R$ 7.500 (júnior) a R$ 15.000 (sênior) 
   (fonte: Google Jobs via SerpAPI)

5. Ação imediata: crie conta gratuita na AWS e complete o 
   tutorial de EC2 + S3 esta semana para começar a praticar 
   (fonte: integração das análises)

======================================================================
```

---

## 🧪 Testar Ferramentas

Para validar que as tools estão funcionando:

```bash
python test_tools.py
```

Saída esperada:
```
============================================================
SMOKE TESTS - Tools do Agente
============================================================

Testando: analisar_demanda_salarial
[OK] Amostra: 15 vagas
[OK] Com salário: 5 vagas
[OK] Salário mediano: R$ 8500.0
...

Testando: sugerir_certificacoes_tendencia
[OK] Certificações encontradas: 3
  - AWS: Solutions Architect Associate
  - Microsoft: Azure Administrator Associate
  - Google Cloud: Professional Cloud Architect
...

RESUMO DOS TESTES
Demanda Salarial: [OK] PASSOU
Certificações: [OK] PASSOU

Total: 2/2 testes passaram
============================================================
```

---

## ❓ Troubleshooting

### Erro: "GOOGLE_API_KEY não configurada"

**Solução**: Verifique se o arquivo `.env` existe e tem a chave correta:

```bash
cat .env  # Linux/Mac
type .env  # Windows

# Deve mostrar:
GOOGLE_API_KEY=AIzaSy...
```

---

### Erro: "ModuleNotFoundError: No module named 'google'"

**Solução**: Ative o ambiente virtual e reinstale dependências:

```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Erro: "Rate limit exceeded" (SerpAPI)

**Causa**: Plano gratuito tem limite de 100 calls/mês

**Soluções**:
1. Aguarde reset mensal
2. Upgrade para plano pago: https://serpapi.com/pricing
3. Use outra conta (email diferente)

---

### Tool de Certificações retorna poucos dados

**Causa**: Páginas oficiais podem ter mudado estrutura HTML

**Verificação**:
```bash
python test_tools.py
```

Se mostrar `[WARN] Erro ao parsear`, o sistema usará fallbacks (certificações core conhecidas).

---

### Resposta do agente não tem 5 bullets

**Causa**: Gemini pode gerar formatos variados

**Solução automática**: O sistema detecta e pede reformatação automaticamente:

```python
if not validar_formato_resposta(resposta):
    resposta = agent.run_turn(
        "Reformule em 5 itens objetivos...",
        tool_router
    )
```

---

## 🎯 Casos de Uso

### 1. Profissional buscando transição de carreira

```bash
python main.py "Engenheiro de ML" "Inteligência Artificial"
```

### 2. Estudante planejando especialização

```bash
python main.py "Analista de Dados" "Big Data"
```

### 3. Tech Lead avaliando contratações

```bash
python main.py "Arquiteto de Software" "Microsserviços"
```

---

## 📚 Próximos Passos

Depois de rodar com sucesso:

1. **Explore o código**: Comece por `main.py` → `llm_gemini.py` → `tools/`

2. **Leia a arquitetura**: Veja `ARCHITECTURE.md` para entender decisões de design

3. **Customize**: Adicione sua própria tool seguindo o padrão em `tools/`

4. **Contribua**: Melhore parsing, adicione fontes, otimize performance

---

## 🆘 Suporte

**Documentação completa**: `README.md`  
**Arquitetura detalhada**: `ARCHITECTURE.md`  
**Issues**: <link-do-repo>/issues

---

## ✅ Checklist de Sucesso

Após seguir este guia, você deve ter:

- [x] Ambiente virtual criado e ativado
- [x] Dependências instaladas (`pip list` mostra google-generativeai, requests, etc)
- [x] Arquivo `.env` com chaves válidas
- [x] `python test_tools.py` passa sem erros
- [x] `python main.py` retorna plano de 5 pontos com fontes citadas

**Se todos os checks acima estão OK, parabéns! 🎉 Sistema funcionando perfeitamente.**

