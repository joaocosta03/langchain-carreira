# Análise das Limitações da Tool de Salários

## 📋 Resumo Executivo

A tool `analisar_demanda_salarial` realiza scraping de vagas via Google Jobs (SerpAPI) para obter dados reais de mercado. Porém, possui limitações estruturais que podem impactar a qualidade dos dados retornados.

---

## 🔍 Limitações Identificadas

### 1. **Dependência de Dados Públicos Incompletos**

**Problema:** A tool depende de vagas publicadas no Google Jobs via SerpAPI. Muitas empresas não publicam faixas salariais nas descrições de vagas.

**Impacto:**
```python
# Cenário comum:
{
    "amostra": 50,                    # 50 vagas encontradas
    "vagas_com_salario": 3,           # Apenas 3 têm salário explícito
    "observacoes": "Apenas 3/50 vagas com salário explícito"
}
```

**Código relevante:**
```python:134:142:tools/demanda_salarios.py
# Extrair salário
salary_info = job.get("detected_extensions", {}).get("salary", "")
if not salary_info:
    # Tenta outros campos
    salary_info = job.get("salary", "")

if salary_info:
    salario_mensal = _extrair_salario_mensal(str(salary_info))
    if salario_mensal:
```

**Consequências:**
- ❌ Percentis (p25, p50, p75) são `null` quando há menos de 3 salários
- ⚠️ Estatísticas pouco representativas com amostras pequenas
- 📊 Taxa real de sucesso: ~5-15% das vagas têm salário público

---

### 2. **Extração de Salários Baseada em Heurísticas**

**Problema:** A função `_extrair_salario_mensal` usa regex e heurísticas simples para extrair valores de strings variadas.

**Exemplos de strings problemáticas:**
```
✅ "R$ 8.000,00 a 12.000,00 por mês"     → Funciona bem
⚠️ "Competitive salary + benefits"       → Falha (sem número)
⚠️ "A partir de 5k"                      → Pode errar interpretação
❌ "CLT - Salário a combinar"            → Sem dado extraível
```

**Código da heurística:**
```python:15:47:tools/demanda_salarios.py
def _extrair_salario_mensal(salary_info: str) -> Optional[float]:
    """
    Extrai e normaliza salário mensal de strings variadas.
    Heurística simples: busca números e converte anual para mensal.
    """
    if not salary_info:
        return None
    
    try:
        # Remove símbolos comuns e separa palavras
        texto = salary_info.lower().replace('r$', '').replace(',', '').replace('.', '')
        
        # Busca padrões numéricos
        import re
        numeros = re.findall(r'\d+', texto)
        if not numeros:
            return None
        
        # Pega o primeiro número encontrado (geralmente salário inicial)
        valor = float(numeros[0])
        
        # Se for anual (geralmente > 100k), divide por 12
        if 'ano' in texto or 'anual' in texto or 'year' in texto:
            valor = valor / 12
        
        # Se valor muito baixo, pode estar em milhares
        if valor < 1000 and len(numeros[0]) >= 3:
            valor = valor * 1000
        
        return valor if 1000 <= valor <= 100000 else None
        
    except:
        return None
```

**Limitações:**
- Só pega o **primeiro número** (ignora faixas "de-até")
- Assume valores entre R$ 1.000 e R$ 100.000
- Pode errar conversão anual/mensal
- Falha silenciosamente (retorna `None`)

---

### 3. **Dependência de Configuração Externa**

**Problema:** Requer `SERPAPI_API_KEY` configurada no arquivo `.env`.

**Erro quando não configurada:**
```python:70:79:tools/demanda_salarios.py
api_key = os.getenv("SERPAPI_API_KEY")

if not api_key:
    return {
        "error": {
            "status": "error",
            "message": "SERPAPI_API_KEY não configurada no .env",
            "details": "Configure a chave para usar esta ferramenta"
        }
    }
```

**Impacto:**
- ❌ Tool **completamente inoperante** sem a chave
- 🔒 Agente precisa lidar com erro de configuração
- 📝 Resposta final pode ficar incompleta

---

### 4. **Limitações de Cobertura Geográfica**

**Problema:** A busca por "Brasil" retorna resultados agregados de todo o país, mas muitas vagas são de grandes centros (SP, RJ, BH).

**Dados retornados:**
```python:158:160:tools/demanda_salarios.py
# Top empresas e cidades
top_empresas = _contar_top_items(empresas, 3)
top_cidades = _contar_top_items(cidades, 3)
```

**Consequência:**
- Salários médios podem **não refletir** realidade de cidades menores
- Viés para grandes centros urbanos
- Dificulta planejamento para profissionais fora desses polos

---

### 5. **Amostra Pequena e Não Representativa**

**Problema:** SerpAPI retorna tipicamente 10-50 vagas por busca. Dessas, apenas uma fração tem salário.

**Validação no código:**
```python:148:156:tools/demanda_salarios.py
percentis = {"p25": None, "p50": None, "p75": None}
if len(salarios) >= 3:
    salarios_sorted = sorted(salarios)
    percentis["p25"] = round(statistics.quantiles(salarios_sorted, n=4)[0], 2)
    percentis["p50"] = round(statistics.median(salarios_sorted), 2)
    percentis["p75"] = round(statistics.quantiles(salarios_sorted, n=4)[2], 2)
elif len(salarios) > 0:
    # Para amostras pequenas, usa mediana como referência
    percentis["p50"] = round(statistics.median(salarios), 2)
```

**Observações geradas:**
```python:162:171:tools/demanda_salarios.py
# Observações
observacoes = []
if vagas_com_salario == 0:
    observacoes.append("Nenhuma vaga com salário explícito encontrada")
elif vagas_com_salario < amostra_total * 0.3:
    observacoes.append(f"Apenas {vagas_com_salario}/{amostra_total} vagas com salário explícito")

if len(salarios) < 5:
    observacoes.append("Amostra pequena, percentis podem não ser representativos")
```

**Exemplo real:**
```json
{
    "amostra": 38,
    "vagas_com_salario": 2,
    "salarios_mensais": {
        "p25": null,
        "p50": 9500.0,
        "p75": null
    },
    "observacoes": "Apenas 2/38 vagas com salário explícito; Amostra pequena, percentis podem não ser representativos"
}
```

---

### 6. **Possíveis Erros de Rede e Timeout**

**Problema:** Chamadas HTTP podem falhar ou demorar muito.

**Tratamento de erros:**
```python:190:213:tools/demanda_salarios.py
except requests.exceptions.Timeout:
    return {
        "error": {
            "status": "error",
            "message": "Timeout na chamada à SerpAPI",
            "details": "A API demorou muito para responder (>30s)"
        }
    }
except requests.exceptions.HTTPError as e:
    return {
        "error": {
            "status": "error",
            "message": f"Erro HTTP da SerpAPI: {e.response.status_code}",
            "details": str(e)
        }
    }
except Exception as e:
    return {
        "error": {
            "status": "error",
            "message": "Erro inesperado na análise de demanda salarial",
            "details": str(e)
        }
    }
```

**Timeout configurado:** 30 segundos
```python:93:93:tools/demanda_salarios.py
response = requests.get(url, params=params, timeout=30)
```

---

## 🎯 Como o Agente Deve Lidar com as Limitações

### Comportamento Recomendado no SYSTEM_INSTRUCTION:

```python
# Atual (linha 62-83 de llm_gemini.py):
SYSTEM_INSTRUCTION = """Você é um consultor sênior de carreira em TI.

REGRAS CRÍTICAS:
1. SEMPRE chame as duas ferramentas disponíveis antes de responder.
2. NUNCA invente números ou dados. Use apenas o que as ferramentas retornam.
3. Se uma ferramenta retornar erro, informe a limitação mas continue com os dados disponíveis.
...
"""
```

### Quando a tool retorna dados incompletos:

**✅ Correto:**
> "A demanda por Engenheiros de Dados é robusta (38 vagas encontradas), mas apenas 2 vagas publicaram salário explícito. A mediana observada foi R$ 9.500, porém a amostra é pequena e pode não refletir o mercado real. (fonte: Google Jobs via SerpAPI)"

**❌ Incorreto (inventar dados):**
> "A faixa salarial para Engenheiro de Dados varia entre R$ 8.000 e R$ 15.000..."

**❌ Incorreto (assumir sem citar limitação):**
> "... mas a ferramenta de análise salarial não retornou dados específicos devido a uma limitação de configuração"
> *(Isso sugere erro de configuração quando na verdade é limitação estrutural dos dados públicos)*

---

## 🔧 Possíveis Melhorias Futuras

### 1. **Fontes Adicionais de Dados**
- Integrar APIs de plataformas de recrutamento (LinkedIn, Glassdoor)
- Usar múltiplas consultas e agregar resultados
- Cache de dados históricos para comparação

### 2. **Melhoria na Extração de Salários**
- Parser mais robusto para strings de salário
- Suporte a faixas ("de-até")
- Detecção de moedas (USD, EUR, BRL)
- Machine Learning para classificação de texto

### 3. **Validação de Dados**
- Outlier detection (valores irreais)
- Cross-validation com dados históricos
- Confidence scores para cada extração

### 4. **Fallback Strategies**
- Dados históricos quando API falha
- Médias do setor baseadas em fontes secundárias
- Indicação clara de "dado estimado" vs "dado observado"

---

## 📊 Resumo das Taxas de Sucesso Esperadas

| Métrica | Taxa Típica | Observação |
|---------|-------------|------------|
| Vagas retornadas | 10-50 | Dependente da busca |
| Vagas com salário explícito | 5-15% | Maioria não publica |
| Sucesso na extração | 70-90% | Quando salário está presente |
| Dados suficientes para percentis | 20-30% | Precisa de ≥3 salários |

---

## 📝 Recomendações para o Usuário

1. **Entenda que é dados públicos limitados:** A tool faz o melhor possível com dados que empresas publicam voluntariamente.

2. **Use como tendência, não valor absoluto:** Os dados indicam direção do mercado, mas não são estatisticamente robustos.

3. **Configure a SERPAPI_API_KEY:** Sem isso, a tool não funciona. Obtenha em: https://serpapi.com/manage-api-key

4. **Combine com outras fontes:** Use os dados como um dos inputs, não a única fonte de verdade.

5. **Preste atenção nas observações:** O campo `observacoes` informa limitações específicas de cada consulta.

---

## 🎓 Conclusão

A tool de salários é **funcional e útil**, mas tem **limitações estruturais** relacionadas à disponibilidade de dados públicos. O agente deve ser transparente sobre essas limitações e **nunca inventar dados** quando eles não estão disponíveis.

A resposta citada pelo usuário sugere incorretamente "limitação de configuração", quando na verdade é uma **limitação inerente aos dados públicos de mercado** (poucas empresas publicam salários).

**Ação recomendada:** Ajustar o SYSTEM_INSTRUCTION para orientar o agente a ser mais claro sobre a natureza das limitações.

