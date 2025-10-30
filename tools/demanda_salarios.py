"""
Tool 1: Análise de demanda salarial via SerpAPI (Google Jobs).
Realiza chamadas reais à API e agrega dados de vagas e salários.
"""

import os
import statistics
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()


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


def _contar_top_items(items: List[str], top_n: int = 3) -> List[str]:
    """Retorna os top N itens mais frequentes."""
    from collections import Counter
    if not items:
        return []
    contagem = Counter(items)
    return [item for item, _ in contagem.most_common(top_n)]


def analisar_demanda_salarial(area: str, local: str = "Brasil") -> Dict[str, Any]:
    """
    Analisa demanda e salários para uma área de TI via Google Jobs (SerpAPI).
    
    Args:
        area: Área de TI (ex: "Engenheiro de DevOps")
        local: Localização (default: "Brasil")
    
    Returns:
        dict: {"data": {...}} ou {"error": {...}}
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if not api_key:
        return {
            "error": {
                "status": "error",
                "message": "SERPAPI_API_KEY não configurada no .env",
                "details": "Configure a chave para usar esta ferramenta"
            }
        }
    
    try:
        # Chamada à SerpAPI - Google Jobs
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_jobs",
            "q": f"{area} {local}",
            "hl": "pt-BR",
            "gl": "br",
            "api_key": api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        jobs_results = data.get("jobs_results", [])
        
        if not jobs_results:
            return {
                "data": {
                    "area": area,
                    "local": local,
                    "amostra": 0,
                    "vagas_com_salario": 0,
                    "salarios_mensais": {"p25": None, "p50": None, "p75": None},
                    "principais_empresas": [],
                    "principais_cidades": [],
                    "observacoes": "Nenhuma vaga encontrada para esta busca",
                    "fonte": "Google Jobs via SerpAPI"
                }
            }
        
        # Processar vagas
        salarios = []
        empresas = []
        cidades = []
        
        for job in jobs_results:
            # Extrair empresa
            empresa = job.get("company_name", "")
            if empresa:
                empresas.append(empresa)
            
            # Extrair cidade
            location = job.get("location", "")
            if location:
                # Pega primeira parte (cidade)
                cidade = location.split(",")[0].strip()
                if cidade:
                    cidades.append(cidade)
            
            # Extrair salário
            salary_info = job.get("detected_extensions", {}).get("salary", "")
            if not salary_info:
                # Tenta outros campos
                salary_info = job.get("salary", "")
            
            if salary_info:
                salario_mensal = _extrair_salario_mensal(str(salary_info))
                if salario_mensal:
                    salarios.append(salario_mensal)
        
        # Calcular estatísticas
        amostra_total = len(jobs_results)
        vagas_com_salario = len(salarios)
        
        percentis = {"p25": None, "p50": None, "p75": None}
        if len(salarios) >= 3:
            salarios_sorted = sorted(salarios)
            percentis["p25"] = round(statistics.quantiles(salarios_sorted, n=4)[0], 2)
            percentis["p50"] = round(statistics.median(salarios_sorted), 2)
            percentis["p75"] = round(statistics.quantiles(salarios_sorted, n=4)[2], 2)
        elif len(salarios) > 0:
            # Para amostras pequenas, usa mediana como referência
            percentis["p50"] = round(statistics.median(salarios), 2)
        
        # Top empresas e cidades
        top_empresas = _contar_top_items(empresas, 3)
        top_cidades = _contar_top_items(cidades, 3)
        
        # Observações
        observacoes = []
        if vagas_com_salario == 0:
            observacoes.append("Nenhuma vaga com salário explícito encontrada")
        elif vagas_com_salario < amostra_total * 0.3:
            observacoes.append(f"Apenas {vagas_com_salario}/{amostra_total} vagas com salário explícito")
        
        if len(salarios) < 5:
            observacoes.append("Amostra pequena, percentis podem não ser representativos")
        
        observacoes_texto = "; ".join(observacoes) if observacoes else "Dados coletados com sucesso"
        
        return {
            "data": {
                "area": area,
                "local": local,
                "amostra": amostra_total,
                "vagas_com_salario": vagas_com_salario,
                "salarios_mensais": percentis,
                "principais_empresas": top_empresas,
                "principais_cidades": top_cidades,
                "observacoes": observacoes_texto,
                "fonte": "Google Jobs via SerpAPI"
            }
        }
        
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

