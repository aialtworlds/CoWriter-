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
