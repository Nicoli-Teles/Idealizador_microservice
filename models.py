from pydantic import BaseModel
from typing import Optional

# Modelo do idealizador (usuário)
class Idealizador(BaseModel):
    nome: str
    telefone: str
    email: str
    senha: str
    github: Optional[str] = None
    linkedin: Optional[str] = None
    funcao: Optional[str] = None
    pais: Optional[str] = None
    cidade: Optional[str] = None
    sobre_mim: Optional[str] = None

# Modelo de habilidade
class Habilidade(BaseModel):
    idealizador_id: int
    nome: str
