# 🤖 Agente Consultor de Carreira em TI

Agente inteligente baseado em **Gemini 1.5 Pro** que fornece planos de carreira personalizados para profissionais de TI, utilizando **dados reais** de mercado e certificações.

## 🎯 Objetivo

Implementar um agente que:
- Recebe uma **área** (ex: "Engenheiro de DevOps") e **tecnologia** (ex: "Nuvem")
- Chama duas **tools reais**:
  1. **analisar_demanda_salarial**: Dados de vagas e salários via Google Jobs (SerpAPI)
  2. **sugerir_certificacoes_tendencia**: Certificações via scraping de páginas oficiais (AWS/Azure/GCP)
- Retorna um **plano de ação em 5 pontos** citando explicitamente as fontes

## 🏗️ Arquitetura

```
agente_carreira/
├── main.py                      # Entrypoint: CLI e orquestração
├── llm_gemini.py                # Wrapper Gemini com function calling
├── schema.py                    # Modelos Pydantic para validação
├── tools/
│   ├── __init__.py
│   ├── demanda_salarios.py      # Tool 1: SerpAPI (Google Jobs)
│   └── certs_cloud.py           # Tool 2: Scraping (AWS/MS/GCP)
├── requirements.txt
├── .env.example
└── README.md
```

### Princípios de Design

✅ **Sem simulações**: Ambas as tools fazem chamadas HTTP reais  
✅ **Sem overengineering**: Projeto flat, separação mínima necessária  
✅ **Contratos estáveis**: Toda tool retorna `{"data": ...}` ou `{"error": ...}`  
✅ **Erros não quebram**: Se uma tool falhar, entrega o melhor plano possível  
✅ **Logs essenciais**: Nome da função, parâmetros e resumo do retorno  
✅ **Pronto para escalar**: Ports estáveis permitem trocar/adicionar provedores

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd langchain-carreira
```

### 2. Crie ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instale dependências

```bash
pip install -r requirements.txt
```

### 4. Configure variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
GOOGLE_API_KEY=sua_chave_google_gemini
SERPAPI_API_KEY=sua_chave_serpapi
```

**Onde obter as chaves:**
- **Google AI Studio**: https://aistudio.google.com/app/apikey
- **SerpAPI**: https://serpapi.com/manage-api-key

## 💻 Uso

### Execução básica (modo interativo)

```bash
python main.py
```

O sistema solicitará:
1. Área de TI (default: "Engenheiro de DevOps")
2. Tecnologia foco (default: "Nuvem")

### Execução com argumentos

```bash
python main.py "Cientista de Dados" "Machine Learning"
```

### Exemplo de saída

```
======================================================================
AGENTE CONSULTOR DE CARREIRA EM TI
Motor: Gemini 1.5 Pro | Tools: SerpAPI + Web Scraping
======================================================================

📋 Área: Engenheiro de DevOps
💡 Tecnologia: Nuvem

----------------------------------------------------------------------

[USER] Quero um plano de carreira para a área: Engenheiro de DevOps, focado em: Nuvem.

[TOOL] analisar_demanda_salarial: area=Engenheiro de DevOps, local=Brasil
[AGENT] Chamando função: analisar_demanda_salarial
[AGENT] Resultado: 45 vagas encontradas

[TOOL] sugerir_certificacoes_tendencia: tecnologia=Nuvem
[AGENT] Chamando função: sugerir_certificacoes_tendencia
[AGENT] Resultado: 3 certificações

======================================================================
📊 PLANO DE AÇÃO FINAL
======================================================================

1. O mercado para Engenheiro de DevOps está aquecido com 45 vagas ativas, 
   especialmente em São Paulo e Rio de Janeiro (fonte: Google Jobs via SerpAPI)

2. Priorize a certificação AWS Solutions Architect Associate, referência 
   para cloud computing (fonte: Páginas oficiais AWS/Microsoft/Google Cloud)

3. Invista em IaC (Terraform/Pulumi) e Kubernetes - skills em alta demanda 
   (fonte: Páginas oficiais AWS/Microsoft/Google Cloud)

4. Faixa salarial mediana de R$ 8.500-12.000/mês para nível pleno 
   (fonte: Google Jobs via SerpAPI)

5. Comece hoje: crie conta gratuita na AWS e complete o tutorial de EC2 
   (fonte: integração das análises)

======================================================================
```

## 🔧 Componentes

### 1. Tool: analisar_demanda_salarial

**Fonte**: Google Jobs via SerpAPI

**Entrada**:
- `area` (str): Área de TI para análise
- `local` (str, opcional): Localização (default: "Brasil")

**Saída**:
```json
{
  "data": {
    "area": "Engenheiro de DevOps",
    "local": "Brasil",
    "amostra": 45,
    "vagas_com_salario": 12,
    "salarios_mensais": {
      "p25": 7500.00,
      "p50": 10000.00,
      "p75": 15000.00
    },
    "principais_empresas": ["Empresa A", "Empresa B", "Empresa C"],
    "principais_cidades": ["São Paulo", "Rio de Janeiro", "Belo Horizonte"],
    "observacoes": "Apenas 12/45 vagas com salário explícito",
    "fonte": "Google Jobs via SerpAPI"
  }
}
```

**Notas**:
- Usa `engine=google_jobs` do SerpAPI
- Calcula percentis apenas da amostra com salário explícito
- Normaliza salários anuais para mensais (÷12)
- Retorna `{"error": {...}}` em caso de falha (rate-limit, timeout, etc)

### 2. Tool: sugerir_certificacoes_tendencia

**Fonte**: Scraping de páginas oficiais (AWS/Microsoft/Google Cloud)

**Entrada**:
- `tecnologia` (str): Tecnologia foco (ex: "Nuvem", "DevOps", "Dados")

**Saída**:
```json
{
  "data": {
    "tecnologia": "Nuvem",
    "certificacoes": [
      {
        "provedor": "AWS",
        "nome": "Solutions Architect Associate",
        "url": "https://aws.amazon.com/certification/..."
      },
      {
        "provedor": "Microsoft",
        "nome": "Azure Administrator Associate",
        "url": "https://learn.microsoft.com/certifications/..."
      },
      {
        "provedor": "Google Cloud",
        "nome": "Professional Cloud Architect",
        "url": "https://cloud.google.com/certification/..."
      }
    ],
    "skills_em_alta": ["IaC", "Kubernetes", "FinOps", "Cloud Security"],
    "fonte": "Páginas oficiais (AWS/Microsoft/Google Cloud)"
  }
}
```

**Notas**:
- Scraping com `requests` + `BeautifulSoup4`
- Páginas alvo:
  - AWS: https://aws.amazon.com/certification/
  - Microsoft: https://learn.microsoft.com/certifications/browse/
  - Google Cloud: https://cloud.google.com/learn/certification
- Filtra por trilhas core: Architect/Administrator/Developer/Engineer
- Skills curadas internamente por tecnologia
- Retorna `{"error": {...}}` se nenhum provedor responder

### 3. LLM: Gemini 1.5 Pro (Function Calling)

**Configuração**:
- Modelo: `gemini-1.5-pro`
- System instruction: Persona de consultor sênior de carreira
- Tools: 2 function declarations (tools acima)

**Regras do agente**:
1. SEMPRE chamar as duas ferramentas antes da resposta final
2. NUNCA inventar números fora das tools
3. Se tool retornar erro, informar limitação mas continuar
4. Resposta final em **5 bullets** objetivos
5. Cada bullet cita explicitamente `"fonte: ..."`

**Loop de execução**:
1. Recebe pergunta do usuário
2. Thought: analisa o que precisa
3. Action: chama `analisar_demanda_salarial`
4. Observation: processa resultado
5. Action: chama `sugerir_certificacoes_tendencia`
6. Observation: processa resultado
7. Responde com plano integrado em 5 pontos

## 📦 Dependências

```
google-generativeai==0.7.2   # Gemini API
requests==2.32.3             # HTTP client
beautifulsoup4==4.12.3       # HTML parsing
python-dotenv==1.0.1         # Variáveis de ambiente
pydantic==2.9.2              # Validação de dados
```

## 🧪 Testes

### Smoke Test

```bash
# Com valores default
python main.py

# Deve:
# - Chamar 2 funções (logs visíveis)
# - Retornar plano com 5 bullets
# - Citar fontes em cada bullet
```

### Testes Unitários (opcional)

```bash
# TODO: Implementar testes com pytest
# - Mock de resposta SerpAPI para validar cálculo de percentis
# - Mock de HTML mínimo por provedor para garantir parsing
```

## 🚨 Tratamento de Erros

### Cenários cobertos:

1. **API Keys inválidas/ausentes**
   - Mensagem clara no console
   - Exit code 1

2. **Rate limit do SerpAPI**
   - Retorna `{"error": {...}}`
   - Agente continua com dados parciais

3. **Timeout/falha de rede**
   - Timeout configurado (15-30s)
   - Retorna `{"error": {...}}`

4. **HTML mudou (scraping)**
   - Fallback para certificações core conhecidas
   - Logs de warning

5. **Gemini não chamou as ferramentas**
   - Validação de formato da resposta
   - Re-prompt para reformatar

## 📈 Evolução Futura

Arquitetura preparada para:

- [ ] Adicionar mais provedores de dados (LinkedIn, Glassdoor)
- [ ] Cache de respostas de tools (Redis)
- [ ] Interface web (FastAPI + React)
- [ ] Personalização por nível (júnior/pleno/sênior)
- [ ] Histórico de planos por usuário
- [ ] Métricas e observabilidade (OpenTelemetry)

## 📄 Licença

MIT

## 👤 Autor

Projeto de demonstração - Agente Consultor de Carreira em TI
