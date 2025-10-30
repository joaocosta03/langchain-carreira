"""
Script auxiliar de setup para o projeto.
Cria arquivo .env template se não existir.
"""

import os
from pathlib import Path


def setup_env_file():
    """Cria arquivo .env se não existir."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("[OK] Arquivo .env ja existe")
        return
    
    env_template = """# Google Gemini API Key
# Obter em: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=

# SerpAPI Key
# Obter em: https://serpapi.com/manage-api-key
SERPAPI_API_KEY=
"""
    
    env_path.write_text(env_template, encoding='utf-8')
    print("[OK] Arquivo .env criado")
    print("[AVISO] Configure suas chaves de API no arquivo .env antes de executar")


def check_dependencies():
    """Verifica se dependências estão instaladas."""
    required = [
        'langchain',
        'langchain_google_genai',
        'requests',
        'bs4',
        'dotenv',
        'pydantic'
    ]
    
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"[AVISO] Dependencias faltando: {', '.join(missing)}")
        print("Execute: pip install -r requirements.txt")
        return False
    
    print("[OK] Todas as dependencias instaladas")
    return True


def main():
    """Setup principal."""
    print("=" * 60)
    print("SETUP - Agente Consultor de Carreira em TI")
    print("=" * 60)
    print()
    
    setup_env_file()
    print()
    check_dependencies()
    
    print()
    print("=" * 60)
    print("Próximos passos:")
    print("1. Configure GOOGLE_API_KEY e SERPAPI_API_KEY no .env")
    print("2. Execute: python main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

