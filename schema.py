"""
Modelos Pydantic para validação de saída das tools.
Garante contratos estáveis e tratamento de erros consistente.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SalariosPercentis(BaseModel):
    """Percentis salariais mensais."""
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None


class DemandaSalarialData(BaseModel):
    """Dados de demanda e salários para uma área."""
    area: str
    local: str
    amostra: int = 0
    vagas_com_salario: int = 0
    salarios_mensais: SalariosPercentis = Field(default_factory=SalariosPercentis)
    principais_empresas: List[str] = Field(default_factory=list)
    principais_cidades: List[str] = Field(default_factory=list)
    observacoes: str = ""
    fonte: str = "Google Jobs via SerpAPI"


class Certificacao(BaseModel):
    """Certificação individual."""
    provedor: str
    nome: str
    url: str


class CertificacoesTendenciaData(BaseModel):
    """Sugestões de certificações e skills em alta."""
    tecnologia: str
    certificacoes: List[Certificacao] = Field(default_factory=list)
    skills_em_alta: List[str] = Field(default_factory=list)
    fonte: str = "Páginas oficiais (AWS/Microsoft/Google Cloud)"


class ErrorResponse(BaseModel):
    """Resposta padrão de erro."""
    status: str = "error"
    message: str
    details: Optional[str] = None


def validar_demanda_salarial(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida e normaliza resposta de demanda salarial."""
    try:
        validated = DemandaSalarialData(**data)
        return {"data": validated.model_dump()}
    except Exception as e:
        return {
            "error": ErrorResponse(
                message="Erro na validação dos dados de demanda salarial",
                details=str(e)
            ).model_dump()
        }


def validar_certificacoes(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida e normaliza resposta de certificações."""
    try:
        validated = CertificacoesTendenciaData(**data)
        return {"data": validated.model_dump()}
    except Exception as e:
        return {
            "error": ErrorResponse(
                message="Erro na validação dos dados de certificações",
                details=str(e)
            ).model_dump()
        }

