"""
Agente LangChain (ReAct) usando Gemini como LLM.
Conecta as tools existentes via LangChain Tools e executa o loop ReAct.
"""

import os
from typing import Callable, Dict, Any, List

from langchain_core.tools import Tool
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
import json
from langchain_google_genai import ChatGoogleGenerativeAI


GEMINI_MODEL_NAME = "gemini-flash-lite-latest"


SYSTEM_INSTRUCTION = (
    "Você é um consultor sênior de carreira em TI.\n\n"
    "REGRAS CRÍTICAS:\n"
    "1. SEMPRE chame as duas ferramentas disponíveis (analisar_demanda_salarial e sugerir_certificacoes_tendencia) antes de responder.\n"
    "2. NUNCA invente números ou dados. Use apenas o que as ferramentas retornam.\n"
    "3. Se uma ferramenta retornar erro, informe a limitação mas continue com os dados disponíveis.\n"
    "4. Sua resposta final DEVE ter EXATAMENTE 5 bullets objetivos.\n"
    "5. Cada bullet DEVE citar explicitamente a fonte: \"fonte: Google Jobs via SerpAPI\" ou \"fonte: Páginas oficiais (AWS/Microsoft/Google Cloud)\".\n"
    "6. Seja direto e prático. Foque em ações concretas que o profissional pode tomar.\n\n"
    "COMO LIDAR COM DADOS DE SALÁRIO LIMITADOS:\n"
    "- Muitas vagas NÃO publicam salários explicitamente (isso é normal e esperado).\n"
    "- Se o campo \"observacoes\" mencionar \"poucos salários\" ou \"amostra pequena\", seja transparente sobre isso.\n"
    "- NUNCA diga \"devido a uma limitação de configuração\" - a limitação é estrutural (dados públicos).\n"
    "- Exemplo correto: \"X vagas encontradas, mas poucas publicam salário explicitamente (fonte: Google Jobs via SerpAPI)\"\n"
    "- Foque na demanda (número de vagas) e empresas contratando quando salários não estiverem disponíveis.\n\n"
    "FLUXO OBRIGATÓRIO:\n"
    "1. Extraia a ÁREA e a TECNOLOGIA do prompt do usuário\n"
    "2. Chame IMEDIATAMENTE analisar_demanda_salarial com a área extraída\n"
    "3. Chame IMEDIATAMENTE sugerir_certificacoes_tendencia com a tecnologia extraída\n"
    "4. APÓS receber os resultados das ferramentas, NUNCA chame as ferramentas novamente\n"
    "5. APENAS gere sua resposta final baseada nos dados já coletados\n"
    "6. NUNCA peça mais informações ao usuário - sempre assuma e extraia do que foi fornecido\n\n"
    "EXEMPLO DE PROMPT:\n"
    "Se o usuário diz: \"Quero um plano de carreira para a área: Data Engineer, focado em: Databricks.\"\n"
    "- ÁREA = \"Data Engineer\"\n"
    "- TECNOLOGIA = \"Databricks\"\n"
    "- Chame analisar_demanda_salarial com area=\"Data Engineer\"\n"
    "- Chame sugerir_certificacoes_tendencia com tecnologia=\"Databricks\"\n"
    "- Após receber os resultados, gere sua resposta diretamente\n\n"
    "FORMATO DA RESPOSTA:\n"
    "1. [Insight sobre mercado baseado em demanda/salários - fonte: ...]\n"
    "2. [Recomendação de certificação específica - fonte: ...]\n"
    "3. [Skill técnica prioritária - fonte: ...]\n"
    "4. [Estratégia de posicionamento - fonte: ...]\n"
    "5. [Ação concreta imediata - fonte: ...]"
)


def _build_tools(tool_router: Dict[str, Callable[..., Any]]) -> List[Tool]:
    """Cria a lista de LangChain Tools a partir do router existente."""
    tools: List[Tool] = []

    if "analisar_demanda_salarial" in tool_router:
        tools.append(
            Tool(
                name="analisar_demanda_salarial",
                description=(
                    "Analisa a demanda de mercado e faixas salariais para uma área específica de TI. "
                    "Entrada: area (str), local (str opcional, default: Brasil). "
                    "Retorna dados reais de vagas, percentis salariais e principais empresas/cidades."
                ),
                func=lambda area, local="Brasil": tool_router["analisar_demanda_salarial"](area=area, local=local),
            )
        )

    if "sugerir_certificacoes_tendencia" in tool_router:
        tools.append(
            Tool(
                name="sugerir_certificacoes_tendencia",
                description=(
                    "Sugere certificações em tendência e skills em alta para uma tecnologia. "
                    "Entrada: tecnologia (str). Retorna certificações (AWS/Azure/GCP) e skills em alta."
                ),
                func=lambda tecnologia: tool_router["sugerir_certificacoes_tendencia"](tecnologia=tecnologia),
            )
        )

    return tools


def make_agent(tool_router: Dict[str, Callable[..., Any]]) -> Any:
    """
    Cria um AgentExecutor ReAct com Gemini, pronto para `invoke({"input": ...})`.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não configurada no .env")

    model_name = os.getenv("GEMINI_MODEL_NAME", GEMINI_MODEL_NAME)
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.2)

    tools = _build_tools(tool_router)

    # Retorna um executor leve que roda o loop de tool calling manualmente
    class LCReActExecutor:
        def __init__(self, llm_model: Any, tools_list: List[Tool]):
            self.llm = llm_model  # Armazena referência ao modelo original
            self.llm_with_tools = llm_model.bind_tools(tools_list)

        def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            user_input = inputs.get("input", "")
            print("\n" + "=" * 70)
            print("🤖 CHAIN OF THOUGHT")
            print("=" * 70)
            
            messages = [
                SystemMessage(content=SYSTEM_INSTRUCTION),
                HumanMessage(content=user_input),
            ]

            response = self.llm_with_tools.invoke(messages)
            
            # Mostra raciocínio inicial
            initial_content = getattr(response, "content", "")
            if initial_content:
                print(f"\n[AGENT] Raciocínio inicial: {initial_content}")

            max_iters = 3  # Reduzido para evitar loops
            it = 0
            tools_called = set()  # Registro de quais tools foram chamadas
            expected_tools = {"analisar_demanda_salarial", "sugerir_certificacoes_tendencia"}
            
            while it < max_iters:
                it += 1
                tool_calls = getattr(response, "tool_calls", None) or []
                
                # Se não há tool calls E já chamamos tools, para o loop
                if not tool_calls and tools_called:
                    # Mostra raciocínio final
                    final_content = getattr(response, "content", "")
                    if final_content:
                        print(f"\n[AGENT] Raciocínio final: {final_content}")
                    break
                
                # Se não há tool calls mas também não chamamos tools ainda, é a primeira iteração
                if not tool_calls:
                    # Mostra raciocínio inicial
                    initial_content = getattr(response, "content", "")
                    if initial_content:
                        print(f"\n[AGENT] {initial_content}")
                    break

                print(f"\n[ITERAÇÃO {it}]")
                
                for call in tool_calls:
                    name = call.get("name")
                    args = call.get("args", {})
                    call_id = call.get("id")
                    
                    print(f"[AGENT] → Chamando tool: {name} com argumentos: {args}")

                    try:
                        if name in tool_router:
                            # Converte __arg1 para o nome correto do parâmetro
                            if "__arg1" in args:
                                if name == "analisar_demanda_salarial":
                                    # Para esta tool, __arg1 é area
                                    result = tool_router[name](area=args["__arg1"])
                                elif name == "sugerir_certificacoes_tendencia":
                                    # Para esta tool, __arg1 é tecnologia
                                    result = tool_router[name](tecnologia=args["__arg1"])
                                else:
                                    result = tool_router[name](**args)
                            else:
                                result = tool_router[name](**args)
                            print(f"[AGENT] ✓ Tool {name} executada com sucesso")
                        else:
                            result = {"error": {"status": "error", "message": f"Função {name} não implementada"}}
                            print(f"[AGENT] ✗ Tool {name} não encontrada")
                    except Exception as e:
                        result = {"error": {"status": "error", "message": str(e)}}
                        print(f"[AGENT] ✗ Erro ao executar {name}: {e}")

                    # Adiciona ao registro de tools chamadas
                    if name in tool_router:
                        tools_called.add(name)

                    messages.append(
                        ToolMessage(content=json.dumps(result, ensure_ascii=False), tool_call_id=call_id)
                    )

                response = self.llm_with_tools.invoke(messages)
                
                # Mostra raciocínio após receber os resultados das tools
                thinking = getattr(response, "content", "")
                if thinking:
                    print(f"[AGENT] Após resultados: {thinking}")
                
                # Se chamamos as duas tools esperadas, força parada
                if len(tools_called) >= 2:
                    print(f"\n[AGENT] As duas tools foram chamadas. Forçando resposta final...")
                    break

            # Se saiu do loop mas ainda não tem resposta, faz uma última chamada sem tool_calls
            if not getattr(response, "content", ""):
                print(f"\n[AGENT] Gerando resposta final...")
                # Cria um novo modelo SEM ferramentas para forçar resposta final
                final_messages = messages + [HumanMessage(content="Baseado nos resultados das ferramentas, gere sua resposta final com 5 bullets objetivos citando as fontes.")]
                response_final = self.llm.invoke(final_messages)
                response = response_final

            print("=" * 70 + "\n")
            
            final_text = getattr(response, "content", "")
            if isinstance(final_text, list):
                final_text = "".join([str(c) for c in final_text])
            return {"output": str(final_text).strip()}

    return LCReActExecutor(llm, tools)


