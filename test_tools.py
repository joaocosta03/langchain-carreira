"""
Testes básicos das tools (smoke tests).
Execute: python test_tools.py
"""

import os
from dotenv import load_dotenv
from tools.demanda_salarios import analisar_demanda_salarial
from tools.certs_cloud import sugerir_certificacoes_tendencia

load_dotenv()


def test_demanda_salarial():
    """Testa tool de demanda salarial."""
    print("\n" + "=" * 60)
    print("Testando: analisar_demanda_salarial")
    print("=" * 60)
    
    if not os.getenv("SERPAPI_API_KEY"):
        print("⚠️  SERPAPI_API_KEY não configurada - pulando teste")
        return False
    
    resultado = analisar_demanda_salarial(
        area="Desenvolvedor Python",
        local="Brasil"
    )
    
    if "error" in resultado:
        print(f"❌ Erro: {resultado['error']['message']}")
        return False
    
    data = resultado["data"]
    print(f"✅ Amostra: {data['amostra']} vagas")
    print(f"✅ Com salário: {data['vagas_com_salario']} vagas")
    print(f"✅ Salário mediano: R$ {data['salarios_mensais']['p50']}")
    print(f"✅ Principais empresas: {', '.join(data['principais_empresas'][:3])}")
    print(f"✅ Fonte: {data['fonte']}")
    
    return True


def test_certificacoes():
    """Testa tool de certificações."""
    print("\n" + "=" * 60)
    print("Testando: sugerir_certificacoes_tendencia")
    print("=" * 60)
    
    resultado = sugerir_certificacoes_tendencia(tecnologia="Nuvem")
    
    if "error" in resultado:
        print(f"❌ Erro: {resultado['error']['message']}")
        return False
    
    data = resultado["data"]
    print(f"✅ Certificações encontradas: {len(data['certificacoes'])}")
    
    for cert in data['certificacoes']:
        print(f"  - {cert['provedor']}: {cert['nome']}")
    
    print(f"✅ Skills em alta: {', '.join(data['skills_em_alta'])}")
    print(f"✅ Fonte: {data['fonte']}")
    
    return True


def main():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("SMOKE TESTS - Tools do Agente")
    print("=" * 60)
    
    resultados = []
    
    # Teste 1
    try:
        resultados.append(("Demanda Salarial", test_demanda_salarial()))
    except Exception as e:
        print(f"❌ Exceção: {e}")
        resultados.append(("Demanda Salarial", False))
    
    # Teste 2
    try:
        resultados.append(("Certificações", test_certificacoes()))
    except Exception as e:
        print(f"❌ Exceção: {e}")
        resultados.append(("Certificações", False))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{nome}: {status}")
    
    total = len(resultados)
    passou = sum(1 for _, s in resultados if s)
    print(f"\nTotal: {passou}/{total} testes passaram")
    print("=" * 60)


if __name__ == "__main__":
    main()

