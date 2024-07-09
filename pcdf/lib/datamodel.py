from pydantic import BaseModel


class BaseDatamodel(BaseModel):
    name: str
    namespace: str


class ImageConfigModel(BaseModel):
    repository: str
    tag: str


class PortModel(BaseModel):
    name: str
    number: int


class EnvVarModel(BaseModel):
    name: str
    value: str


class NetworkingConfigModel(BaseModel):
    ports: list[PortModel] = []
