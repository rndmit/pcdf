from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class Metadata(BaseModel):
    name: str = Field(description="Release name")
    namespace: str = Field(description="Target kubernetes namespace")
    project: str = Field(description="Project name")
    type: Literal["service"] = Field(
        default="service",
        description="Release type",
    )


class Base(BaseModel):
    metadata: Metadata = Field(description="Metadata config")


class Runtime(BaseModel):
    image: str = Field(description="Image URI")
    tag: str = Field("Image tag")
    containerName: str = Field(
        default="app", description="Name of application container"
    )
    entrypoint: list[str] | None = Field(
        description="Container entrypoint", default=None
    )
    command: list[str] | None = Field(
        default=None,
        description="Container command",
    )
    replicas: int = Field(default=1, description="Replicas count", ge=0)


class Port(BaseModel):
    name: str = Field(description="Port name")
    number: int = Field(description="Port number", gt=0)
    protocol: Literal["TCP", "UDP", "SCTP"] = Field(
        default="TCP",
        description="Transport protocol",
    )


class EnvVar(BaseModel):
    name: str = Field(description="Variable name (key)")
    value: str = Field(description="Variable value")


class Publication(BaseModel):
    host: str = Field(description="Publication hostname (e.g. progressive-cd.io)")
    path: str = Field(default="/", description="Routing path (e.g. /docs)")
    pathType: Literal["ImplementationSpecific", "Prefix", "Exact"] = Field(
        default="ImplementationSpecific"
    )
    destPort: Union[str, int] = Field(default="http")
    destOverride: str | None = Field(
        default=None, description="Override destination to another service"
    )


class Networking(BaseModel):
    ports: list[Port] = Field(description="Application ports", default_factory=list)
    serviceType: Literal["ClusterIP", "LoadBalancer", "NodePort"] = Field(
        default="ClusterIP", description=""
    )
    ingressClass: Literal["nginx"] = Field(default="nginx")
    ingressAnnotations: dict[str, str] = Field(default_factory=dict)
    publicate: list[Publication] = Field()
    tls: bool = Field(default=True)
    tlsSecretSuffix: str = Field(default="-ingress-tls")


class CertManager(BaseModel):
    issuer: str = Field(
        default="cluster-issuer", description="Name of certmanager's issuer"
    )
    issuerType: Literal["cluster-issuer", "issuer"] = Field(default="cluster-issuer")
    annotations: dict[str, str] = Field(default_factory=dict)

    @field_validator("annotations")
    @classmethod
    def check_annotations(
        cls, v: dict[str, str], info: ValidationInfo
    ) -> dict[str, str]:
        for f in v.keys():
            assert f.startswith(
                "cert-manager.io/"
            ), "annotation key must start with 'cert-manager.io/'"
        return v


class Document(BaseModel):
    name: str
    content: str


class ResourceReqPair(BaseModel):
    cpu: str = "10m"
    memory: str = "10Mi"


class Resources(BaseModel):
    limits: ResourceReqPair = Field(default_factory=ResourceReqPair)
    requests: ResourceReqPair = Field(default_factory=ResourceReqPair)