# 🏗️ Arquitetura - Agente Consultor de Carreira

## Visão Geral

Sistema de agente inteligente baseado em **function calling** do Gemini, com arquitetura **flat** e **contratos estáveis**.

```
┌─────────────────────────────────────────────────────────────┐
│                         USUÁRIO                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   main.py   │  ◄── CLI / Entrypoint
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │    llm_gemini.py        │  ◄── Gemini Wrapper
              │  (Function Calling)     │
              └────────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐     ┌─────▼─────┐
   │ Tool 1  │       │  Tool 2   │     │ Tool N... │
   │ Salários│       │  Certs    │     │  (futuro) │
   └────┬────┘       └─────┬─────┘     └───────────┘
        │                  │
   ┌────▼────┐       ┌─────▼─────┐
   │ SerpAPI │       │ Scraping  │
   │  (HTTP) │       │   (HTTP)  │
   └─────────┘       └───────────┘
```

## Componentes Principais

### 1. `main.py` - Entrypoint

**Responsabilidade**: Orquestração e interface CLI

**Fluxo**:
1. Recebe parâmetros (área, tecnologia)
2. Cria `tool_router` (dict: nome → função)
3. Inicializa agente Gemini
4. Executa turno completo (loop de function calling)
5. Valida formato da resposta (5 bullets)
6. Exibe resultado

**Pontos de extensão**:
- Adicionar UI web (FastAPI)
- Persistir histórico de consultas
- Adicionar cache de respostas

---

### 2. `llm_gemini.py` - Motor LLM

**Responsabilidade**: Abstração do Gemini + Function Calling

**Classes/Funções**:
- `GeminiAgent`: Gerencia chat e loop de function calling
- `make_model()`: Factory para criar agente configurado
- `FUNCTION_DECLARATIONS`: Esquemas das tools para o Gemini
- `SYSTEM_INSTRUCTION`: Persona e regras do agente

**Loop de execução**:
```python
while has_function_calls:
    1. Gemini retorna function_call(s)
    2. Executa tool via tool_router
    3. Envia function_response de volta
    4. Repete até Gemini retornar texto final
```

**Pontos de extensão**:
- Suportar outros modelos (OpenAI, Anthropic)
- Adicionar streaming de respostas
- Implementar cache de conversas

---

### 3. `tools/` - Ferramentas Reais

#### Tool 1: `demanda_salarios.py`

**Fonte**: Google Jobs via SerpAPI

**Contrato de entrada**:
```python
def analisar_demanda_salarial(
    area: str,           # ex: "Engenheiro de DevOps"
    local: str = "Brasil"
) -> Dict[str, Any]
```

**Contrato de saída**:
```python
{
    "data": {
        "area": str,
        "local": str,
        "amostra": int,
        "vagas_com_salario": int,
        "salarios_mensais": {"p25": float, "p50": float, "p75": float},
        "principais_empresas": List[str],
        "principais_cidades": List[str],
        "observacoes": str,
        "fonte": str
    }
}
# OU
{
    "error": {
        "status": "error",
        "message": str,
        "details": Optional[str]
    }
}
```

**Implementação**:
1. Chamada HTTP GET para SerpAPI (`engine=google_jobs`)
2. Parse de `jobs_results`
3. Extração de salários (normalização anual → mensal)
4. Cálculo de percentis (p25/p50/p75)
5. Agregação de empresas/cidades (top 3)

**Tratamento de erros**:
- Timeout (30s)
- Rate limit (429)
- Sem vagas encontradas
- Parsing de salários inconsistentes

---

#### Tool 2: `certs_cloud.py`

**Fonte**: Scraping de páginas oficiais

**Contrato de entrada**:
```python
def sugerir_certificacoes_tendencia(
    tecnologia: str = "Nuvem"  # ex: "Nuvem", "DevOps", "Dados"
) -> Dict[str, Any]
```

**Contrato de saída**:
```python
{
    "data": {
        "tecnologia": str,
        "certificacoes": [
            {"provedor": str, "nome": str, "url": str},
            ...
        ],
        "skills_em_alta": List[str],
        "fonte": str
    }
}
# OU
{"error": {...}}
```

**Implementação**:
1. Scraping paralelo de 3 páginas:
   - AWS: https://aws.amazon.com/certification/
   - Microsoft: https://learn.microsoft.com/certifications/browse/
   - Google Cloud: https://cloud.google.com/learn/certification
2. Parse com BeautifulSoup (busca por palavras-chave)
3. Filtragem: Architect/Administrator/Developer/Engineer
4. Top 1 por provedor (3 total)
5. Skills curadas internamente por tecnologia

**Fallbacks**:
- Se parsing falhar → certificação core conhecida
- Se todos os provedores falharem → erro

---

### 4. `schema.py` - Validação

**Responsabilidade**: Modelos Pydantic para validação de I/O

**Modelos**:
- `DemandaSalarialData`: Valida resposta da Tool 1
- `CertificacoesTendenciaData`: Valida resposta da Tool 2
- `ErrorResponse`: Formato padrão de erro

**Uso** (opcional):
```python
from schema import validar_demanda_salarial

resultado = analisar_demanda_salarial(...)
validado = validar_demanda_salarial(resultado["data"])
```

---

## Contratos e Estabilidade

### Princípio: Ports & Adapters Leve

**Port** (interface estável):
```python
def tool_function(param: str) -> Dict[str, Any]:
    """
    Returns:
        {"data": {...}} em sucesso
        {"error": {...}} em falha
    """
```

**Adapter** (implementação intercambiável):
- SerpAPI → pode trocar por LinkedIn Jobs API
- Scraping → pode trocar por APIs oficiais quando disponíveis

### Como adicionar uma nova tool

1. **Criar função em `tools/nova_tool.py`**:
```python
def nova_funcionalidade(param: str) -> Dict[str, Any]:
    """Descrição clara do que faz."""
    try:
        # Lógica de negócio
        resultado = fazer_algo(param)
        
        return {
            "data": {
                "campo1": resultado,
                "fonte": "Nome da Fonte"
            }
        }
    except Exception as e:
        return {
            "error": {
                "status": "error",
                "message": str(e)
            }
        }
```

2. **Adicionar declaração em `llm_gemini.py`**:
```python
FUNCTION_DECLARATIONS.append({
    "name": "nova_funcionalidade",
    "description": "Use quando o usuário perguntar sobre X...",
    "parameters": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "Descrição do parâmetro"
            }
        },
        "required": ["param"]
    }
})
```

3. **Registrar no router em `main.py`**:
```python
tool_router = {
    "analisar_demanda_salarial": demanda_salarios.analisar_demanda_salarial,
    "sugerir_certificacoes_tendencia": certs_cloud.sugerir_certificacoes_tendencia,
    "nova_funcionalidade": nova_tool.nova_funcionalidade  # ← novo
}
```

4. **Atualizar `SYSTEM_INSTRUCTION`** (se necessário):
```python
SYSTEM_INSTRUCTION = """...
Sempre chame as três ferramentas disponíveis...
"""
```

---

## Decisões de Design

### Por que function calling?

**Alternativas consideradas**:
- ReAct puro (parsing de texto)
- LangChain Agents
- LlamaIndex Agents

**Escolha**: Function calling nativo do Gemini

**Motivos**:
1. ✅ Contratos estruturados (JSON)
2. ✅ Menos parsing manual
3. ✅ Melhor performance (menos tokens)
4. ✅ Suporte oficial do SDK

---

### Por que estrutura flat?

**Alternativa**: Separar em camadas (domain/infra/application)

**Escolha**: Projeto flat com `tools/`

**Motivos**:
1. ✅ MVP rápido (< 1000 linhas)
2. ✅ Menos abstrações desnecessárias
3. ✅ Fácil navegação
4. ⚠️ Refatorar para camadas quando > 5 tools

---

### Por que sem cache inicial?

**Seria útil para**:
- Evitar chamadas repetidas ao SerpAPI (custo)
- Acelerar respostas

**Motivos da ausência**:
1. Dados de vagas mudam rapidamente
2. Adiciona complexidade (Redis/file cache)
3. Pode ser adicionado depois sem breaking changes

**Como adicionar depois**:
```python
# Em tools/demanda_salarios.py
def analisar_demanda_salarial(area: str, local: str = "Brasil"):
    cache_key = f"demanda:{area}:{local}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    resultado = _fazer_chamada_real(area, local)
    set_cache(cache_key, resultado, ttl=3600)
    return resultado
```

---

## Monitoramento e Observabilidade

### Logs atuais

**Formato**:
```
[TOOL] nome_funcao: param1=valor1, param2=valor2
[AGENT] Chamando função: nome_funcao
[AGENT] Resultado: X vagas encontradas
```

### Próximos passos

1. **Estruturar logs** (JSON):
```python
import json
import logging

logging.info(json.dumps({
    "event": "tool_call",
    "tool": "analisar_demanda_salarial",
    "params": {"area": area, "local": local},
    "duration_ms": 1234,
    "status": "success"
}))
```

2. **Adicionar métricas**:
- Tempo de resposta por tool
- Taxa de erro por tool
- Custo acumulado (tokens/API calls)

3. **Tracing distribuído** (OpenTelemetry):
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("analisar_demanda"):
    resultado = analisar_demanda_salarial(area, local)
```

---

## Testes

### Smoke Tests Atuais

**Arquivo**: `test_tools.py`

**Cobertura**:
- ✅ Tool 1 com chamada real
- ✅ Tool 2 com chamada real
- ⚠️ Sem mock (depende de chaves reais)

### Testes Recomendados

1. **Unitários** (com mocks):
```python
# test_demanda_salarios.py
from unittest.mock import patch
import pytest

@patch('requests.get')
def test_calculo_percentis(mock_get):
    mock_get.return_value.json.return_value = {
        "jobs_results": [
            {"detected_extensions": {"salary": "R$ 10000"}},
            {"detected_extensions": {"salary": "R$ 15000"}},
            {"detected_extensions": {"salary": "R$ 20000"}},
        ]
    }
    
    resultado = analisar_demanda_salarial("Dev", "SP")
    
    assert resultado["data"]["vagas_com_salario"] == 3
    assert resultado["data"]["salarios_mensais"]["p50"] == 15000
```

2. **Integração**:
```python
def test_agent_completo():
    """Testa fluxo completo com mocks."""
    agent = make_model()
    tool_router = {
        "analisar_demanda_salarial": mock_demanda,
        "sugerir_certificacoes_tendencia": mock_certs
    }
    
    resposta = agent.run_turn("Quero virar DevOps", tool_router)
    
    assert "fonte:" in resposta
    assert len(resposta.split("\n")) >= 5
```

3. **E2E** (com rate limiting):
```python
@pytest.mark.slow
def test_e2e_real_apis():
    """Testa com APIs reais (CI noturno)."""
    resultado = analisar_demanda_salarial("Python Developer", "Brasil")
    assert "data" in resultado or "error" in resultado
```

---

## Performance

### Benchmarks Esperados

| Operação | Tempo | Custo |
|----------|-------|-------|
| Tool 1 (SerpAPI) | 2-5s | $0.005/call |
| Tool 2 (Scraping) | 3-8s | $0 |
| Gemini (function calls) | 1-3s/turn | $0.001/turn |
| **Total por consulta** | **10-20s** | **~$0.01** |

### Otimizações Futuras

1. **Paralelizar tools**:
```python
import asyncio

async def run_tools_parallel():
    results = await asyncio.gather(
        analisar_demanda_salarial_async(area, local),
        sugerir_certificacoes_tendencia_async(tecnologia)
    )
    return results
```

2. **Cache inteligente**:
- Cache de 1h para dados de vagas
- Cache de 24h para certificações

3. **Streaming de resposta**:
- Exibir resultados parciais enquanto processa

---

## Segurança

### Checklist Atual

- ✅ API keys em `.env` (não commitadas)
- ✅ Timeout em chamadas HTTP
- ✅ Validação de entrada básica (tipos)
- ⚠️ Sem sanitização de HTML (scraping)
- ⚠️ Sem rate limiting próprio

### Melhorias Recomendadas

1. **Rate limiting**:
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)  # 10 calls/min
def analisar_demanda_salarial(area, local):
    ...
```

2. **Sanitização de HTML**:
```python
from bleach import clean

html_limpo = clean(html, tags=[], strip=True)
```

3. **Validação de URLs**:
```python
from urllib.parse import urlparse

def validar_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https'] and parsed.netloc
```

---

## Roadmap

### v1.0 (Atual)
- ✅ 2 tools reais
- ✅ Function calling
- ✅ CLI básico
- ✅ Tratamento de erros

### v1.1 (Próximos passos)
- [ ] Cache (Redis)
- [ ] Logs estruturados (JSON)
- [ ] Testes unitários (pytest)
- [ ] CI/CD (GitHub Actions)

### v2.0 (Futuro)
- [ ] API REST (FastAPI)
- [ ] Frontend web (React)
- [ ] Autenticação de usuários
- [ ] Histórico de consultas
- [ ] Personalização por nível (júnior/pleno/sênior)

### v3.0 (Visão)
- [ ] Mais fontes (LinkedIn, Glassdoor)
- [ ] Análise de currículo (PDF upload)
- [ ] Recomendações de cursos
- [ ] Dashboard de métricas
- [ ] Multi-idioma

---

## Referências

- [Gemini Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [SerpAPI Google Jobs](https://serpapi.com/google-jobs-api)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Pydantic Best Practices](https://docs.pydantic.dev/latest/concepts/models/)

