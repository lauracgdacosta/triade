"""Configuração base compartilhada pelos schemas Pydantic."""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
