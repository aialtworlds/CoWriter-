from pydantic import BaseModel
from typing import Optional


class ProjectCreate(BaseModel):
    nome: str
    idioma: str = 'pt-BR'
    genero: Optional[str] = None


class ProjectUpdate(BaseModel):
    nome: Optional[str] = None
    idioma: Optional[str] = None
    genero: Optional[str] = None


class ChapterCreate(BaseModel):
    titulo: str
    texto_bruto: str


class BannedPatternCreate(BaseModel):
    tipo: str
    texto_padrao: str
    idioma: Optional[str] = None
    project_id: Optional[str] = None
    cooldown_max: int = 1
    janela_capitulos: int = 1


class BannedPatternUpdate(BaseModel):
    texto_padrao: Optional[str] = None
    idioma: Optional[str] = None
    cooldown_max: Optional[int] = None


class BannedPatternImport(BaseModel):
    tipo: str
    texto: str
    idioma: Optional[str] = None
    project_id: Optional[str] = None
    cooldown_max: int = 1


class PaymentCheckoutCreate(BaseModel):
    pacote: str
    origin_url: str
