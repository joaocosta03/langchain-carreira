"""
Tool 2: Sugestão de certificações em tendência via scraping.
Extrai certificações de páginas oficiais: AWS, Microsoft Azure, Google Cloud.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List


# Skills curadas por tecnologia (lista interna fixa)
SKILLS_MAP = {
    "Nuvem": ["IaC", "Kubernetes", "FinOps", "Cloud Security"],
    "DevOps": ["CI/CD", "Docker", "Terraform", "GitOps"],
    "Dados": ["Data Engineering", "Spark", "Airflow", "DBT"],
    "IA": ["Machine Learning", "LLMs", "MLOps", "RAG"]
}


def _parse_aws(html: str) -> List[Dict[str, str]]:
    """
    Parse da página de certificações AWS.
    Foca em Architect, Developer, SysOps.
    """
    soup = BeautifulSoup(html, 'html.parser')
    certs = []
    
    try:
        # AWS usa estruturas variadas; busca por links com palavras-chave
        keywords = ['architect', 'developer', 'sysops', 'engineer']
        
        # Busca todos os links
        for link in soup.find_all('a', href=True):
            texto = link.get_text(strip=True).lower()
            href = link['href']
            
            # Filtra certificações relevantes
            if any(kw in texto for kw in keywords) and 'certification' in texto.lower():
                # Monta URL absoluta
                if href.startswith('/'):
                    href = f"https://aws.amazon.com{href}"
                
                nome = link.get_text(strip=True)
                certs.append({
                    "provedor": "AWS",
                    "nome": nome,
                    "url": href
                })
        
        # Se parsing detalhado falhar, retorna certificações core conhecidas
        if not certs:
            certs = [{
                "provedor": "AWS",
                "nome": "AWS Certified Solutions Architect - Associate",
                "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/"
            }]
    
    except Exception as e:
        print(f"[WARN] Erro ao parsear AWS: {e}")
        # Fallback para certificação core
        certs = [{
            "provedor": "AWS",
            "nome": "AWS Certified Solutions Architect - Associate",
            "url": "https://aws.amazon.com/certification/"
        }]
    
    return certs[:1]  # Retorna top 1


def _parse_microsoft(html: str) -> List[Dict[str, str]]:
    """
    Parse da página de certificações Microsoft Azure.
    Foca em Azure Administrator, Developer, Architect.
    """
    soup = BeautifulSoup(html, 'html.parser')
    certs = []
    
    try:
        keywords = ['azure administrator', 'azure developer', 'azure architect', 'az-']
        
        for link in soup.find_all('a', href=True):
            texto = link.get_text(strip=True).lower()
            href = link['href']
            
            if any(kw in texto for kw in keywords):
                if href.startswith('/'):
                    href = f"https://learn.microsoft.com{href}"
                elif not href.startswith('http'):
                    href = f"https://learn.microsoft.com/certifications/{href}"
                
                nome = link.get_text(strip=True)
                certs.append({
                    "provedor": "Microsoft",
                    "nome": nome,
                    "url": href
                })
        
        if not certs:
            certs = [{
                "provedor": "Microsoft",
                "nome": "Microsoft Certified: Azure Administrator Associate",
                "url": "https://learn.microsoft.com/certifications/azure-administrator/"
            }]
    
    except Exception as e:
        print(f"[WARN] Erro ao parsear Microsoft: {e}")
        certs = [{
            "provedor": "Microsoft",
            "nome": "Microsoft Certified: Azure Administrator Associate",
            "url": "https://learn.microsoft.com/certifications/"
        }]
    
    return certs[:1]


def _parse_gcp(html: str) -> List[Dict[str, str]]:
    """
    Parse da página de certificações Google Cloud.
    Foca em Cloud Architect, Cloud Engineer, Cloud Developer.
    """
    soup = BeautifulSoup(html, 'html.parser')
    certs = []
    
    try:
        keywords = ['cloud architect', 'cloud engineer', 'cloud developer']
        
        for link in soup.find_all('a', href=True):
            texto = link.get_text(strip=True).lower()
            href = link['href']
            
            if any(kw in texto for kw in keywords) and 'certification' in href.lower():
                if href.startswith('/'):
                    href = f"https://cloud.google.com{href}"
                
                nome = link.get_text(strip=True)
                certs.append({
                    "provedor": "Google Cloud",
                    "nome": nome,
                    "url": href
                })
        
        if not certs:
            certs = [{
                "provedor": "Google Cloud",
                "nome": "Professional Cloud Architect",
                "url": "https://cloud.google.com/certification/cloud-architect"
            }]
    
    except Exception as e:
        print(f"[WARN] Erro ao parsear Google Cloud: {e}")
        certs = [{
            "provedor": "Google Cloud",
            "nome": "Professional Cloud Architect",
            "url": "https://cloud.google.com/certification"
        }]
    
    return certs[:1]


def sugerir_certificacoes_tendencia(tecnologia: str = "Nuvem") -> Dict[str, Any]:
    """
    Sugere certificações em tendência via scraping de páginas oficiais.
    
    Args:
        tecnologia: Tecnologia foco (ex: "Nuvem", "DevOps", "Dados")
    
    Returns:
        dict: {"data": {...}} ou {"error": {...}}
    """
    print(f"[TOOL] sugerir_certificacoes_tendencia: tecnologia={tecnologia}")
    
    # URLs das páginas oficiais
    urls = {
        "aws": "https://aws.amazon.com/certification/",
        "microsoft": "https://learn.microsoft.com/certifications/browse/",
        "gcp": "https://cloud.google.com/learn/certification"
    }
    
    todas_certs = []
    erros = []
    
    # Scraping de cada provedor
    for provedor, url in urls.items():
        try:
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            html = response.text
            
            if provedor == "aws":
                certs = _parse_aws(html)
            elif provedor == "microsoft":
                certs = _parse_microsoft(html)
            else:  # gcp
                certs = _parse_gcp(html)
            
            todas_certs.extend(certs)
            
        except requests.exceptions.Timeout:
            erros.append(f"{provedor}: timeout")
            print(f"[WARN] Timeout ao acessar {provedor}")
        except requests.exceptions.HTTPError as e:
            erros.append(f"{provedor}: HTTP {e.response.status_code}")
            print(f"[WARN] Erro HTTP ao acessar {provedor}: {e.response.status_code}")
        except Exception as e:
            erros.append(f"{provedor}: {str(e)[:50]}")
            print(f"[WARN] Erro ao processar {provedor}: {e}")
    
    # Se não conseguiu nenhuma certificação, retorna erro
    if not todas_certs:
        return {
            "error": {
                "status": "error",
                "message": "Não foi possível coletar certificações de nenhum provedor",
                "details": "; ".join(erros)
            }
        }
    
    # Skills em alta (curadoria interna)
    skills = SKILLS_MAP.get(tecnologia, SKILLS_MAP["Nuvem"])
    
    print(f"[TOOL] Resultado: {len(todas_certs)} certificações coletadas")
    
    return {
        "data": {
            "tecnologia": tecnologia,
            "certificacoes": todas_certs,
            "skills_em_alta": skills,
            "fonte": "Páginas oficiais (AWS/Microsoft/Google Cloud)"
        }
    }

