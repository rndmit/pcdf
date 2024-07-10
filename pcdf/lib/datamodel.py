from typing import Protocol, runtime_checkable
from pydantic import BaseModel


class MetadataModel(BaseModel):
    name: str
    namespace: str


class BaseDatamodel(BaseModel):
    metadata: MetadataModel


class ImageModel(BaseModel):
    repository: str
    tag: str


class RuntimeModel(BaseModel):
    image: str
    tag: str
    container_name: str = "app"
    entrypoint: list[str] | None = None
    command: list[str] | None = None
    replicas: int = 1


class PortModel(BaseModel):
    name: str
    number: int


class EnvVarModel(BaseModel):
    name: str
    value: str


class NetworkingModel(BaseModel):
    ports: list[PortModel] = []
