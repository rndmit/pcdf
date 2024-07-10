from typing import Protocol, runtime_checkable, Literal
from pydantic import BaseModel


class Metadata(BaseModel):
    name: str
    namespace: str
    project: str
    type: Literal["service"] = "service"


class Base(BaseModel):
    metadata: Metadata


class Image(BaseModel):
    repository: str
    tag: str


class Runtime(BaseModel):
    image: str
    tag: str
    container_name: str = "app"
    entrypoint: list[str] | None = None
    command: list[str] | None = None
    replicas: int = 1


class Port(BaseModel):
    name: str
    number: int


class EnvVar(BaseModel):
    name: str
    value: str


class Networking(BaseModel):
    ports: list[Port] = []
