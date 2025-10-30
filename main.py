"""
Entrypoint do Agente Consultor de Carreira em TI.
CLI simples que orquestra o agente Gemini com as duas tools reais.
"""

import sys
from tools.demanda_salarios import analisar_demanda_salarial
from tools.certs_cloud import sugerir_certificacoes_tendencia
import llm_gemini


def validar_formato_resposta(resposta: str) -> bool:
    """
    Valida se a resposta tem formato adequado (5 bullets).
    
    Args:
        resposta: Texto da resposta do agente
    
    Returns:
        bool: True se válida
    """
    # Conta bullets (linhas que começam com número seguido de ponto ou hífen)
    linhas = resposta.strip().split('\n')
    bullets = [l for l in linhas if l.strip() and (
        l.strip()[0].isdigit() or l.strip().startswith('-') or l.strip().startswith('•')
    )]
    
    return len(bullets) >= 5


def main():
    """Execução principal do agente."""
    print("=" * 70)
    print("AGENTE CONSULTOR DE CARREIRA EM TI")
    print("Motor: Gemini 1.5 Pro | Tools: SerpAPI + Web Scraping")
    print("=" * 70)
    
    # Parâmetros (pode ler de sys.argv ou input)
    if len(sys.argv) >= 3:
        area = sys.argv[1]
        tecnologia = sys.argv[2]
    else:
        area = input("\nÁrea de TI (default: Engenheiro de DevOps): ").strip()
        if not area:
            area = "Engenheiro de DevOps"
        
        tecnologia = input("Tecnologia foco (default: Nuvem): ").strip()
        if not tecnologia:
            tecnologia = "Nuvem"
    
    print(f"\n📋 Área: {area}")
    print(f"💡 Tecnologia: {tecnologia}")
    print("\n" + "-" * 70)
    
    # Configurar tool router
    tool_router = {
        "analisar_demanda_salarial": analisar_demanda_salarial,
        "sugerir_certificacoes_tendencia": sugerir_certificacoes_tendencia
    }
    
    try:
        # Criar agente Gemini
        print("\n🤖 Inicializando agente Gemini...")
        agent = llm_gemini.make_model()
        
        # Prompt do usuário
        prompt_usuario = f"Quero um plano de carreira para a área: {area}, focado em: {tecnologia}."
        
        # Executar turno completo
        resposta = agent.run_turn(prompt_usuario, tool_router)
        
        # Validar formato
        if not validar_formato_resposta(resposta):
            print("\n⚠️  Resposta não está no formato ideal, solicitando reformatação...")
            resposta = agent.run_turn(
                "Reformule a resposta final em exatamente 5 itens objetivos, cada um citando explicitamente 'fonte: ...'",
                tool_router
            )
        
        # Exibir resultado final
        print("\n" + "=" * 70)
        print("📊 PLANO DE AÇÃO FINAL")
        print("=" * 70)
        print(f"\n{resposta}\n")
        print("=" * 70)
        
    except ValueError as e:
        print(f"\n❌ ERRO DE CONFIGURAÇÃO: {e}")
        print("\nVerifique se o arquivo .env está configurado corretamente:")
        print("  GOOGLE_API_KEY=sua_chave_aqui")
        print("  SERPAPI_API_KEY=sua_chave_aqui")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário.")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

