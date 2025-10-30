"""
Wrapper do Google Gemini para function calling.
Implementa o loop Thought→Action→Observation com as tools do agente.
"""

import os
import json
from typing import Dict, Callable, Any, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Nome do modelo Gemini a ser utilizado
GEMINI_MODEL_NAME = "gemini-flash-lite-latest"


# Declarações de funções para o Gemini
FUNCTION_DECLARATIONS = [
    {
        "name": "analisar_demanda_salarial",
        "description": """Analisa a demanda de mercado e faixas salariais para uma área específica de TI.
        Use esta ferramenta para obter dados reais sobre:
        - Número de vagas disponíveis
        - Faixas salariais (percentis 25, 50, 75)
        - Principais empresas contratando
        - Principais cidades com vagas
        Sempre chame esta ferramenta quando o usuário perguntar sobre carreira em TI.""",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "area": {
                    "type": "STRING",
                    "description": "Área de TI para análise (ex: 'Engenheiro de DevOps', 'Cientista de Dados')"
                },
                "local": {
                    "type": "STRING",
                    "description": "Localização para busca de vagas (default: 'Brasil')"
                }
            },
            "required": ["area"]
        }
    },
    {
        "name": "sugerir_certificacoes_tendencia",
        "description": """Sugere certificações em tendência e skills em alta para uma tecnologia.
        Use esta ferramenta para obter:
        - Certificações relevantes dos principais provedores (AWS, Azure, Google Cloud)
        - Skills técnicas em alta demanda
        Sempre chame esta ferramenta quando o usuário perguntar sobre carreira em TI.""",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tecnologia": {
                    "type": "STRING",
                    "description": "Tecnologia foco (ex: 'Nuvem', 'DevOps', 'Dados', 'IA')"
                }
            },
            "required": ["tecnologia"]
        }
    }
]


SYSTEM_INSTRUCTION = """Você é um consultor sênior de carreira em TI.

REGRAS CRÍTICAS:
1. SEMPRE chame as duas ferramentas disponíveis (analisar_demanda_salarial e sugerir_certificacoes_tendencia) antes de responder.
2. NUNCA invente números ou dados. Use apenas o que as ferramentas retornam.
3. Se uma ferramenta retornar erro, informe a limitação mas continue com os dados disponíveis.
4. Sua resposta final DEVE ter EXATAMENTE 5 bullets objetivos.
5. Cada bullet DEVE citar explicitamente a fonte: "fonte: Google Jobs via SerpAPI" ou "fonte: Páginas oficiais (AWS/Microsoft/Google Cloud)".
6. Seja direto e prático. Foque em ações concretas que o profissional pode tomar.

COMO LIDAR COM DADOS DE SALÁRIO LIMITADOS:
- Muitas vagas NÃO publicam salários explicitamente (isso é normal e esperado).
- Se o campo "observacoes" mencionar "poucos salários" ou "amostra pequena", seja transparente sobre isso.
- NUNCA diga "devido a uma limitação de configuração" - a limitação é estrutural (dados públicos).
- Exemplo correto: "X vagas encontradas, mas poucas publicam salário explicitamente (fonte: Google Jobs via SerpAPI)"
- Foque na demanda (número de vagas) e empresas contratando quando salários não estiverem disponíveis.

FLUXO:
1. Receba a pergunta do usuário
2. Chame analisar_demanda_salarial com a área mencionada
3. Chame sugerir_certificacoes_tendencia com a tecnologia mencionada
4. Integre os resultados em um plano de 5 pontos

FORMATO DA RESPOSTA:
1. [Insight sobre mercado baseado em demanda/salários - fonte: ...]
2. [Recomendação de certificação específica - fonte: ...]
3. [Skill técnica prioritária - fonte: ...]
4. [Estratégia de posicionamento - fonte: ...]
5. [Ação concreta imediata - fonte: ...]"""


class GeminiAgent:
    """Agente Gemini com suporte a function calling."""
    
    def __init__(self, model_name: str = GEMINI_MODEL_NAME):
        """
        Inicializa o agente Gemini.
        
        Args:
            model_name: Nome do modelo Gemini a usar
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não configurada no .env")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_INSTRUCTION,
            tools=FUNCTION_DECLARATIONS
        )
        
        self.chat = None
    
    def start_chat(self) -> None:
        """Inicia uma nova sessão de chat."""
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)
    
    def run_turn(self, user_message: str, tool_router: Dict[str, Callable]) -> str:
        """
        Executa um turno completo do agente (loop de function calling).
        
        Args:
            user_message: Mensagem do usuário
            tool_router: Dict mapeando nome da função para callable
        
        Returns:
            str: Resposta final do agente
        """
        if not self.chat:
            raise RuntimeError("Chat não inicializado. Chame start_chat() primeiro.")
        
        print(f"\n[USER] {user_message}\n")
        
        # Envia mensagem inicial
        response = self.chat.send_message(user_message)
        
        # Loop de function calling
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Verifica se há function calls
            if not response.candidates:
                break
            
            candidate = response.candidates[0]
            
            # Se não há function calls, terminamos
            if not candidate.content.parts:
                break
            
            has_function_call = any(
                part.function_call for part in candidate.content.parts 
                if hasattr(part, 'function_call')
            )
            
            if not has_function_call:
                break
            
            # Processa cada function call
            function_responses = []
            
            for part in candidate.content.parts:
                if not hasattr(part, 'function_call'):
                    continue
                
                fc = part.function_call
                function_name = fc.name
                function_args = dict(fc.args)
                
                print(f"[AGENT] Chamando função: {function_name}")
                print(f"[AGENT] Argumentos: {json.dumps(function_args, ensure_ascii=False)}")
                
                # Chama a função correspondente
                if function_name not in tool_router:
                    print(f"[ERROR] Função {function_name} não encontrada no router")
                    result = {
                        "error": {
                            "status": "error",
                            "message": f"Função {function_name} não implementada"
                        }
                    }
                else:
                    try:
                        result = tool_router[function_name](**function_args)
                        
                        # Log do resultado
                        if "data" in result:
                            if "amostra" in result["data"]:
                                print(f"[AGENT] Resultado: {result['data']['amostra']} vagas encontradas")
                            elif "certificacoes" in result["data"]:
                                print(f"[AGENT] Resultado: {len(result['data']['certificacoes'])} certificações")
                        else:
                            print(f"[AGENT] Resultado: erro - {result.get('error', {}).get('message', 'desconhecido')}")
                    
                    except Exception as e:
                        print(f"[ERROR] Erro ao executar {function_name}: {e}")
                        result = {
                            "error": {
                                "status": "error",
                                "message": f"Erro ao executar {function_name}",
                                "details": str(e)
                            }
                        }
                
                # Adiciona resposta da função
                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=function_name,
                            response={"result": result}
                        )
                    )
                )
            
            # Envia as respostas das funções de volta ao modelo
            if function_responses:
                response = self.chat.send_message(function_responses)
            else:
                break
        
        # Extrai resposta final
        if response.candidates and response.candidates[0].content.parts:
            final_text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    final_text += part.text
            
            return final_text.strip()
        
        return "Desculpe, não consegui gerar uma resposta adequada."


def make_model(model_name: str = GEMINI_MODEL_NAME) -> GeminiAgent:
    """
    Factory function para criar e configurar o agente Gemini.
    
    Args:
        model_name: Nome do modelo a usar
    
    Returns:
        GeminiAgent configurado e pronto para uso
    """
    agent = GeminiAgent(model_name=model_name)
    agent.start_chat()
    return agent

